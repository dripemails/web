from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.template.loader import render_to_string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from campaigns.models import Campaign, Email, EmailSendRequest
from subscribers.models import List, Subscriber
from analytics.models import UserProfile
from django.conf import settings
import re
import pytz
import logging
import uuid
from .models import BlogPost, ForumPost, SuccessStory
from .forms import ForumPostForm, SuccessStoryForm

logger = logging.getLogger(__name__)

@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """API endpoint for dashboard data."""
    # Get user's campaigns
    campaigns = Campaign.objects.filter(user=request.user).order_by('-created_at')
    campaign_data = [{
        'id': str(campaign.id),
        'name': campaign.name,
        'description': campaign.description,
        'is_active': campaign.is_active,
        'emails_count': campaign.emails_count,
        'sent_count': campaign.sent_count,
        'created_at': campaign.created_at
    } for campaign in campaigns]

    # Get user's lists
    lists = List.objects.filter(user=request.user).order_by('-created_at')
    list_data = [{
        'id': str(list_obj.id),
        'name': list_obj.name,
        'description': list_obj.description,
        'subscribers_count': list_obj.subscribers_count,
        'active_subscribers_count': list_obj.active_subscribers_count,
        'created_at': list_obj.created_at
    } for list_obj in lists]

    # Get user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Count unique subscribers across all user's lists (avoid double counting)
    subscribers_count = Subscriber.objects.filter(lists__user=request.user).distinct().count()
    
    return Response({
        'campaigns': campaign_data,
        'lists': list_data,
        'stats': {
            'campaigns_count': len(campaign_data),
            'lists_count': len(list_data),
            'subscribers_count': subscribers_count,
            'sent_emails_count': sum(campaign.sent_count for campaign in campaigns),
        },
        'profile': {
            'has_verified_promo': profile.has_verified_promo,
            'send_without_unsubscribe': profile.send_without_unsubscribe,
        }
    })

@login_required
def profile(request):
    """User profile page - redirects to dashboard."""
    return redirect('core:dashboard')

@login_required
def dashboard(request):
    """Render the dashboard for authenticated users."""
    # Get user's campaigns
    campaigns = Campaign.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's lists
    lists = List.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate stats
    campaigns_count = campaigns.count()
    lists_count = lists.count()
    # Count unique subscribers across all user's lists (avoid double counting)
    subscribers_count = Subscriber.objects.filter(lists__user=request.user).distinct().count()
    sent_emails_count = sum(campaign.sent_count for campaign in campaigns)

    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    user_timezone = profile.timezone or 'UTC'
    
    # Extract email domain for SPF instructions
    user_email_domain = None
    if request.user.email and '@' in request.user.email:
        user_email_domain = request.user.email.split('@')[1]
    
    # Get SPF verification status (refresh from DB to get latest value)
    profile.refresh_from_db()
    spf_verified = profile.spf_verified
    
    # If SPF is marked as verified, do a quick re-check to ensure it's still valid
    # This handles cases where the user deleted the SPF record or moved domains
    if spf_verified and request.user.email:
        try:
            from core.spf_utils import quick_spf_check
            is_still_valid, current_spf_record = quick_spf_check(request.user.email)
            
            if not is_still_valid:
                # SPF record was removed or is no longer valid - update the profile
                profile.spf_verified = False
                profile.spf_record = current_spf_record or ''
                profile.save(update_fields=['spf_verified', 'spf_record'])
                spf_verified = False
                logger.info(f"Dashboard - User {request.user.id} SPF record no longer valid, updated status to False")
            else:
                # Update the stored SPF record in case it changed
                if current_spf_record and current_spf_record != profile.spf_record:
                    profile.spf_record = current_spf_record
                    profile.save(update_fields=['spf_record'])
                    logger.debug(f"Dashboard - User {request.user.id} SPF record updated")
        except Exception as e:
            # If DNS check fails, don't update the status (might be a temporary DNS issue)
            logger.warning(f"Dashboard - Failed to re-check SPF for user {request.user.id}: {str(e)}")
    
    # Debug logging
    logger.debug(f"Dashboard - User {request.user.id} SPF verified: {spf_verified}, SPF record: {profile.spf_record}")
    
    context = {
        'campaigns': campaigns,
        'lists': lists,
        'campaigns_count': campaigns_count,
        'lists_count': lists_count,
        'subscribers_count': subscribers_count,
        'sent_emails_count': sent_emails_count,
        'user_email_domain': user_email_domain,
        'user_timezone': user_timezone,
        'spf_verified': spf_verified,
        'show_address_name_modal': settings.SHOW_ADDRESS_NAME_MODAL_NEW_ACCOUNTS,
    }
    
    return render(request, 'core/dashboard.html', context)

def home(request):
    """Render the landing page."""
    return render(request, 'core/home.html')

def pricing(request):
    """Render pricing page."""
    return render(request, 'core/pricing.html')

def about(request):
    """Render about page."""
    return render(request, 'core/about.html')

def contact(request):
    """Render contact page."""
    return render(request, 'core/contact.html')

def send_contact_redirect(request):
    """Redirect /send-contact/ to /contact/"""
    return redirect('core:contact')

@api_view(['POST'])
def send_contact(request):
    """Handle contact form submission."""
    try:
        name = request.data.get('name')
        email = request.data.get('email')
        subject = request.data.get('subject')
        message = request.data.get('message')
        
        # Send email
        full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        send_mail(
            f"Contact Form: {subject}",
            full_message,
            email,
            ['founders@dripemails.org'],
            fail_silently=False,
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def terms(request):
    """Render terms page."""
    return render(request, 'core/terms.html')

def privacy(request):
    """Render privacy page."""
    return render(request, 'core/privacy.html')

@login_required
def account_settings(request):
    """Account settings page."""
    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    common_timezones = pytz.common_timezones

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'settings')

        if form_type == 'email':
            new_email = request.POST.get('email', '').strip()
            auto_bcc_enabled = request.POST.get('auto_bcc_enabled') == 'on'
            
            if not new_email:
                messages.error(request, _("Please provide an email address."))
            elif new_email == request.user.email:
                # Email hasn't changed, but auto_bcc setting might have
                profile.auto_bcc_enabled = auto_bcc_enabled
                profile.save(update_fields=['auto_bcc_enabled'])
                messages.success(request, _("Auto BCC setting updated successfully."))
            else:
                # Validate email format
                from django.core.validators import validate_email
                from django.core.exceptions import ValidationError
                try:
                    validate_email(new_email)
                    # Check if email is already in use by another user
                    from django.contrib.auth.models import User
                    if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                        messages.error(request, _("This email address is already in use by another account."))
                    else:
                        # Update user email
                        request.user.email = new_email
                        request.user.save(update_fields=['email'])
                        # Update auto_bcc setting
                        profile.auto_bcc_enabled = auto_bcc_enabled
                        profile.save(update_fields=['auto_bcc_enabled'])
                        messages.success(request, _("Email address and settings updated successfully to %(email)s") % {'email': new_email})
                except ValidationError:
                    messages.error(request, _("Please provide a valid email address."))
            return redirect('core:settings')

        elif form_type == 'address':
            full_name = request.POST.get('full_name', '').strip()
            address_line1 = request.POST.get('address_line1', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            country = request.POST.get('country', '').strip()
            
            # Validate required fields
            if not full_name or not address_line1 or not city or not state or not postal_code or not country:
                messages.error(request, _("Please fill in all required fields: Full Name, Address Line 1, City, State, Postal Code, and Country."))
                return redirect('core:settings')
            
            profile.full_name = full_name
            profile.address_line1 = address_line1
            profile.address_line2 = request.POST.get('address_line2', '').strip()
            profile.city = city
            profile.state = state
            profile.postal_code = postal_code
            profile.country = country
            profile.save(update_fields=['full_name', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'])
            messages.success(request, _("Address updated successfully."))
            return redirect('core:settings')

        elif form_type == 'timezone':
            selected_timezone = request.POST.get('timezone')
            if selected_timezone not in common_timezones:
                messages.error(request, _("Please select a valid time zone."))
            else:
                profile.timezone = selected_timezone
                profile.save(update_fields=['timezone'])
                messages.success(request, _("Time zone updated to %(tz)s") % {'tz': selected_timezone})
            return redirect('core:settings')
        
        elif form_type == 'unsubscribe':
            profile.send_without_unsubscribe = request.POST.get('send_without_unsubscribe') == 'on'
            profile.save(update_fields=['send_without_unsubscribe'])
            if profile.send_without_unsubscribe:
                messages.warning(request, _("Unsubscribe links are now disabled. This may violate email regulations."))
            else:
                messages.success(request, _("Unsubscribe links are now enabled."))
            return redirect('core:settings')
    
    # Get or create user's API token
    from rest_framework.authtoken.models import Token
    token, _created = Token.objects.get_or_create(user=request.user)
    
    context = {
        'timezones': common_timezones,
        'current_timezone': profile.timezone or 'UTC',
        'send_without_unsubscribe': profile.send_without_unsubscribe,
        'auto_bcc_enabled': profile.auto_bcc_enabled,
        'full_name': profile.full_name or '',
        'address_line1': profile.address_line1 or '',
        'address_line2': profile.address_line2 or '',
        'city': profile.city or '',
        'state': profile.state or '',
        'postal_code': profile.postal_code or '',
        'country': profile.country or '',
        'api_token': token.key,
    }
    return render(request, 'core/settings.html', context)

@login_required
def promo_verification(request):
    """Handle promo verification."""
    profile, _created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        promo_url = request.POST.get('promo_url')
        promo_type = request.POST.get('promo_type')
        
        if not promo_url:
            messages.error(request, _("Please provide a URL to your post"))
            return redirect('core:promo_verification')
        
        # Basic URL validation
        if not re.match(r'^https?://', promo_url):
            messages.error(request, _("Please provide a valid URL starting with http:// or https://"))
            return redirect('core:promo_verification')
        
        # Validate URL based on promo type
        valid_url = False
        if promo_type == 'x':
            valid_url = 'twitter.com' in promo_url or 'x.com' in promo_url
        elif promo_type == 'facebook':
            valid_url = 'facebook.com' in promo_url
        elif promo_type == 'linkedin':
            valid_url = 'linkedin.com' in promo_url
        elif promo_type in ['blog', 'other']:
            valid_url = True
        
        if not valid_url:
            messages.error(request, _("Please provide a valid URL for the selected platform"))
            return redirect('core:promo_verification')
        
        # Update user profile
        profile.has_verified_promo = True
        profile.promo_url = promo_url
        profile.save()
        
        messages.success(request, _("Thank you for promoting DripEmails.org! Ads have been disabled for your account."))
        return redirect('core:dashboard')
    
    return render(request, 'core/promo_verification.html')

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_settings(request):
    """Get or update profile settings."""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            # Update send_without_unsubscribe if provided
            if 'send_without_unsubscribe' in request.data:
                profile.send_without_unsubscribe = request.data.get('send_without_unsubscribe', False)
            
            # Update auto_bcc_enabled if provided
            if 'auto_bcc_enabled' in request.data:
                profile.auto_bcc_enabled = request.data.get('auto_bcc_enabled', True)
            
            # Update timezone if provided
            if 'timezone' in request.data:
                new_timezone = request.data.get('timezone', 'UTC')
                # Validate timezone
                try:
                    pytz.timezone(new_timezone)  # Validate it's a real timezone
                    profile.timezone = new_timezone
                except pytz.UnknownTimeZoneError:
                    return Response({'error': _('Invalid timezone')}, status=400)
            
            # Update full_name if provided
            if 'full_name' in request.data:
                profile.full_name = request.data.get('full_name', '').strip()
            
            # Update address fields if provided
            if 'address_line1' in request.data or 'city' in request.data or 'state' in request.data or 'postal_code' in request.data or 'country' in request.data or 'full_name' in request.data:
                # Validate required fields when updating address
                full_name = request.data.get('full_name', '').strip() if 'full_name' in request.data else profile.full_name
                address_line1 = request.data.get('address_line1', '').strip() if 'address_line1' in request.data else profile.address_line1
                city = request.data.get('city', '').strip() if 'city' in request.data else profile.city
                state = request.data.get('state', '').strip() if 'state' in request.data else profile.state
                postal_code = request.data.get('postal_code', '').strip() if 'postal_code' in request.data else profile.postal_code
                country = request.data.get('country', '').strip() if 'country' in request.data else profile.country
                
                if not full_name or not address_line1 or not city or not state or not postal_code or not country:
                    return Response({'error': _('Please fill in all required fields: Full Name, Address Line 1, City, State, Postal Code, and Country.')}, status=400)
                
                profile.full_name = full_name
                
                profile.address_line1 = address_line1
                profile.address_line2 = request.data.get('address_line2', '').strip() if 'address_line2' in request.data else profile.address_line2
                profile.city = city
                profile.state = state
                profile.postal_code = postal_code
                profile.country = country
            
            profile.save()
            return Response({
                'message': _('Settings updated successfully'),
                'has_verified_promo': profile.has_verified_promo,
                'send_without_unsubscribe': profile.send_without_unsubscribe,
                'auto_bcc_enabled': profile.auto_bcc_enabled,
                'timezone': profile.timezone or 'UTC',
                'full_name': profile.full_name or '',
                'address_line1': profile.address_line1 or '',
                'address_line2': profile.address_line2 or '',
                'city': profile.city or '',
                'state': profile.state or '',
                'postal_code': profile.postal_code or '',
                'country': profile.country or '',
            })
        
        return Response({
            'has_verified_promo': profile.has_verified_promo,
            'send_without_unsubscribe': profile.send_without_unsubscribe,
            'auto_bcc_enabled': profile.auto_bcc_enabled,
            'timezone': profile.timezone or 'UTC',
            'full_name': profile.full_name or '',
            'address_line1': profile.address_line1 or '',
            'address_line2': profile.address_line2 or '',
            'city': profile.city or '',
            'state': profile.state or '',
            'postal_code': profile.postal_code or '',
            'country': profile.country or '',
        })
    except Exception as e:
        logger.error(f"Error in profile_settings: {str(e)}", exc_info=True)
        return Response({'error': _('An error occurred while saving settings')}, status=500)

def feature_drip_campaigns(request):
    return render(request, 'core/feature_drip_campaigns.html')

def feature_email_scheduling(request):
    return render(request, 'core/feature_email_scheduling.html')

def feature_analytics(request):
    return render(request, 'core/feature_analytics.html')

def feature_subscriber_management(request):
    return render(request, 'core/feature_subscriber_management.html')

def feature_email_templates(request):
    return render(request, 'core/feature_email_templates.html')

def resource_documentation(request):
    return render(request, 'core/resource_documentation.html')

# Documentation subpages
def docs_getting_started(request):
    return render(request, 'core/docs/getting_started.html')

def docs_campaigns(request):
    return render(request, 'core/docs/campaigns.html')

def docs_subscribers(request):
    return render(request, 'core/docs/subscribers.html')

def docs_templates(request):
    return render(request, 'core/docs/templates.html')

def docs_analytics(request):
    return render(request, 'core/docs/analytics.html')

def docs_ai_features(request):
    return render(request, 'core/docs/ai_features.html')

def docs_smtp_server(request):
    return render(request, 'core/docs/smtp_server.html')

def docs_deployment(request):
    return render(request, 'core/docs/deployment.html')

def docs_deployment_prerequisites(request):
    return render(request, 'core/docs/deployment/prerequisites.html')

def docs_deployment_installation(request):
    return render(request, 'core/docs/deployment/installation.html')

def docs_deployment_configuration(request):
    return render(request, 'core/docs/deployment/configuration.html')

def docs_deployment_production(request):
    return render(request, 'core/docs/deployment/production.html')

def docs_deployment_troubleshooting(request):
    return render(request, 'core/docs/deployment/troubleshooting.html')

def resource_tutorials(request):
    return render(request, 'core/resource_tutorials.html')

# Tutorial detail pages
def tutorial_quick_start(request):
    return render(request, 'core/tutorials/quick_start.html')

def tutorial_dashboard_overview(request):
    return render(request, 'core/tutorials/dashboard_overview.html')

def tutorial_account_setup(request):
    return render(request, 'core/tutorials/account_setup.html')

def tutorial_creating_campaign(request):
    return render(request, 'core/tutorials/creating_campaign.html')

def tutorial_drip_campaigns(request):
    return render(request, 'core/tutorials/drip_campaigns.html')

def tutorial_scheduling_campaigns(request):
    return render(request, 'core/tutorials/scheduling_campaigns.html')

def tutorial_importing_subscribers(request):
    return render(request, 'core/tutorials/importing_subscribers.html')

def tutorial_managing_lists(request):
    return render(request, 'core/tutorials/managing_lists.html')

def tutorial_subscriber_segmentation(request):
    return render(request, 'core/tutorials/subscriber_segmentation.html')

def tutorial_email_editor(request):
    return render(request, 'core/tutorials/email_editor.html')

def tutorial_reusable_templates(request):
    return render(request, 'core/tutorials/reusable_templates.html')

def tutorial_design_best_practices(request):
    return render(request, 'core/tutorials/design_best_practices.html')

def tutorial_ai_setup(request):
    return render(request, 'core/tutorials/ai_setup.html')

def tutorial_ai_generation(request):
    return render(request, 'core/tutorials/ai_generation.html')

def tutorial_ai_optimization(request):
    return render(request, 'core/tutorials/ai_optimization.html')

def tutorial_email_analytics(request):
    return render(request, 'core/tutorials/email_analytics.html')

def tutorial_performance_dashboard(request):
    return render(request, 'core/tutorials/performance_dashboard.html')

def tutorial_data_optimization(request):
    return render(request, 'core/tutorials/data_optimization.html')

def tutorial_smtp_setup(request):
    return render(request, 'core/tutorials/smtp_setup.html')

def tutorial_deployment(request):
    return render(request, 'core/tutorials/deployment.html')

def tutorial_api_integration(request):
    return render(request, 'core/tutorials/api_integration.html')

def resource_api_reference(request):
    return render(request, 'core/resource_api_reference.html')

def resource_community(request):
    return render(request, 'core/resource_community.html')

# Simple blog with placeholder data
def blog_index(request):
    posts = BlogPost.objects.filter(published=True).order_by('-date')
    return render(request, 'blog/blog_index.html', {'posts': posts})

def blog_post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog/blog_post_detail.html', {'post': post})

def community_user_forum(request):
    """User forum page - allows logged in users to post."""
    posts = ForumPost.objects.all().select_related('user')
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, _('You must be logged in to post.'))
            return redirect('account_login')
        
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            
            # Send email notification to founders
            founders_email = getattr(settings, 'FOUNDERS_EMAIL', 'founders@dripemails.org')
            try:
                send_mail(
                    f'New Forum Post: {post.title}',
                    f'A new forum post has been created by {post.user.username} ({post.user.email}):\n\n'
                    f'Title: {post.title}\n\n'
                    f'Content:\n{post.content}\n\n'
                    f'View at: {request.build_absolute_uri(f"/resources/community/user-forum/")}',
                    settings.DEFAULT_FROM_EMAIL,
                    [founders_email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f'Error sending forum post notification: {e}')
            
            messages.success(request, _('Your post has been submitted successfully!'))
            return redirect('core:community_user_forum')
    else:
        form = ForumPostForm()
    
    context = {
        'posts': posts,
        'form': form,
    }
    return render(request, 'core/community_user_forum.html', context)

def community_feature_requests(request):
    return render(request, 'core/community_feature_requests.html')

def community_success_stories(request):
    """Success stories page - allows users to submit success stories with logo upload."""
    # Show only approved stories
    stories = SuccessStory.objects.filter(approved=True)
    
    if request.method == 'POST':
        form = SuccessStoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save()
            
            # Send email notification to founders
            founders_email = getattr(settings, 'FOUNDERS_EMAIL', 'founders@dripemails.org')
            try:
                send_mail(
                    f'New Success Story Submission: {story.company_name}',
                    f'A new success story has been submitted:\n\n'
                    f'Company: {story.company_name}\n'
                    f'Contact: {story.contact_name} ({story.contact_email})\n\n'
                    f'Story:\n{story.story}\n\n'
                    f'Logo uploaded: {"Yes" if story.logo else "No"}\n\n'
                    f'Review at: {request.build_absolute_uri("/admin/core/successstory/")}',
                    settings.DEFAULT_FROM_EMAIL,
                    [founders_email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f'Error sending success story notification: {e}')
            
            messages.success(request, _('Thank you for sharing your success story! We\'ll review it and may feature it on our site.'))
            return redirect('core:community_success_stories')
    else:
        form = SuccessStoryForm()
    
    context = {
        'stories': stories,
        'form': form,
    }
    return render(request, 'core/community_success_stories.html', context)

def community_social(request):
    return render(request, 'core/community_social.html')

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email_api(request):
    """Send an email to a subscriber."""
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    email = request.data.get('email')
    campaign_id = request.data.get('campaign_id')
    email_id = request.data.get('email_id')
    schedule = request.data.get('schedule', 'now')
    schedule_value = request.data.get('schedule_value', '0')
    
    if not email or not campaign_id or not email_id:
        return Response({
            'error': _('Please provide email address, campaign, and email template')
        }, status=400)
    
    try:
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        try:
            user_timezone = pytz.timezone(profile.timezone or 'UTC')
        except pytz.UnknownTimeZoneError:
            user_timezone = pytz.timezone('UTC')
            profile.timezone = 'UTC'
            profile.save(update_fields=['timezone'])

        # Verify campaign belongs to user
        campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        email_obj = Email.objects.get(id=email_id, campaign=campaign)
        
        # Get the subscriber or create one
        from subscribers.models import Subscriber
        try:
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name or '',
                    'last_name': last_name or '',
                    'is_active': True
                }
            )
            if not created:
                updated = False
                if first_name and subscriber.first_name != first_name:
                    subscriber.first_name = first_name
                    updated = True
                if last_name and subscriber.last_name != last_name:
                    subscriber.last_name = last_name
                    updated = True
                # Check is_active properly - it's a boolean field, not a callable
                is_active_value = getattr(subscriber, 'is_active', True)
                if not is_active_value:
                    subscriber.is_active = True
                    updated = True
                if updated:
                    subscriber.save()
            
            # Always subscribe the user to the campaign's list
            # If campaign doesn't have a list, create or get a default list for this campaign
            from subscribers.models import List
            if not campaign.subscriber_list:
                # Create a list for this campaign if it doesn't have one
                campaign_list, list_created = List.objects.get_or_create(
                    user=request.user,
                    name=f"Campaign: {campaign.name}",
                    defaults={
                        'description': f'Subscribers list for campaign: {campaign.name}'
                    }
                )
                campaign.subscriber_list = campaign_list
                campaign.save(update_fields=['subscriber_list'])
            
            # Add subscriber to the campaign's list
            if not campaign.subscriber_list.subscribers.filter(id=subscriber.id).exists():
                campaign.subscriber_list.subscribers.add(subscriber)
        except Exception as sub_error:
            import traceback
            import logging
            error_trace = traceback.format_exc()
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating/updating subscriber: {str(sub_error)}\n{error_trace}")
            return Response({
                'error': _('Failed to create or update subscriber: {}').format(str(sub_error)),
                'traceback': error_trace if settings.DEBUG else None
            }, status=500)
        
        # Parse the schedule
        from datetime import timedelta
        from campaigns.tasks import send_single_email, _send_single_email_sync
        
        send_delay = timedelta(0)
        if schedule == 'now':
            send_delay = timedelta(0)
        else:
            value = int(schedule_value) if schedule_value else 0
            if schedule == 'minutes':
                send_delay = timedelta(minutes=value)
            elif schedule == 'hours':
                send_delay = timedelta(hours=value)
            elif schedule == 'days':
                send_delay = timedelta(days=value)
            elif schedule == 'weeks':
                send_delay = timedelta(weeks=value)
            elif schedule == 'months':
                send_delay = timedelta(days=value * 30)
            elif schedule == 'seconds':
                send_delay = timedelta(seconds=value)
            else:
                send_delay = timedelta(0)
        
        scheduled_for = timezone.now() + send_delay
        
        # Prepare sending helpers
        import logging
        import sys
        from campaigns.tasks import send_single_email, _send_single_email_sync
        from campaigns.models import EmailSendRequest
        
        logger = logging.getLogger(__name__)
        variables = {'first_name': first_name or '', 'last_name': last_name or ''}
        use_sync = (sys.platform == 'win32' and settings.DEBUG)
        
        # Create send request record
        send_request = EmailSendRequest.objects.create(
            user=request.user,
            campaign=campaign,
            email=email_obj,
            subscriber=subscriber,
            subscriber_email=email,
            variables=variables,
            scheduled_for=scheduled_for,
        )
        
        def send_immediately():
            """Send the email immediately (synchronous)."""
            _send_single_email_sync(
                str(email_obj.id),
                email,
                variables,
                request_id=str(send_request.id)
            )
        
        def queue_with_celery(countdown_seconds):
            """Schedule the email using EmailSendRequest (no Celery)."""
            # Update status to pending - the cron job will process it
            send_request.status = 'pending'
            send_request.error_message = ''
            send_request.save(update_fields=['status', 'error_message', 'updated_at'])
            return True, None

        # Immediate send logic
        if schedule == 'now' or scheduled_for <= timezone.now():
            if use_sync:
                try:
                    send_immediately()
                    send_request.refresh_from_db()
                    return Response({
                        'message': _('Email sent successfully'),
                        'request_id': str(send_request.id),
                        'timezone': profile.timezone or 'UTC'
                    })
                except Exception as sync_error:
                    return Response({
                        'error': _('Failed to send email: {}').format(str(sync_error))
                    }, status=500)
            else:
                queued, error_msg = queue_with_celery(0)
                if queued:
                    return Response({
                        'message': _('Email scheduled successfully'),
                        'request_id': str(send_request.id),
                        'timezone': profile.timezone or 'UTC'
                    })
                # Celery failed, try synchronous fallback
                try:
                    send_immediately()
                    send_request.refresh_from_db()
                    return Response({
                        'message': _('Email sent successfully'),
                        'request_id': str(send_request.id),
                        'timezone': profile.timezone or 'UTC'
                    })
                except Exception as sync_error:
                    return Response({
                        'error': _('Failed to send email: {}').format(str(sync_error))
                    }, status=500)

        # Scheduled for future
        countdown_seconds = max(int(send_delay.total_seconds()), 0)
        scheduled_for_local = scheduled_for
        if timezone.is_naive(scheduled_for_local):
            scheduled_for_local = timezone.make_aware(scheduled_for_local, timezone.get_current_timezone())
        scheduled_for_local = timezone.localtime(scheduled_for_local, user_timezone)
        scheduled_display = scheduled_for_local.strftime('%b %d, %Y %I:%M %p')

        if use_sync:
            # Keep as pending; cron.py will process it, or user can trigger "Send Now"
            send_request.status = 'pending'
            send_request.error_message = ''
            send_request.save(update_fields=['status', 'error_message', 'updated_at'])
            return Response({
                'message': _('Email scheduled for {time}. It will be sent automatically at the scheduled time.').format(time=scheduled_display),
                'request_id': str(send_request.id),
                'scheduled_for': scheduled_for_local.isoformat(),
                'status': send_request.status,
                'timezone': profile.timezone or 'UTC'
            })
        else:
            queued, error_msg = queue_with_celery(countdown_seconds)
            if queued:
                return Response({
                    'message': _('Email scheduled for {time}. It will be sent automatically at the scheduled time.').format(time=scheduled_display),
                    'request_id': str(send_request.id),
                    'scheduled_for': scheduled_for_local.isoformat(),
                    'status': 'pending',
                    'timezone': profile.timezone or 'UTC'
                })
            return Response({
                'message': _('Email scheduled for {time}. It will be sent automatically at the scheduled time.').format(time=scheduled_display),
                'request_id': str(send_request.id),
                'scheduled_for': scheduled_for_local.isoformat(),
                'status': send_request.status,
                'timezone': profile.timezone or 'UTC'
            })
        
    except Campaign.DoesNotExist:
        return Response({'error': _('Campaign not found')}, status=404)
    except Email.DoesNotExist:
        return Response({'error': _('Email template not found')}, status=404)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in send_email_api: {str(e)}\n{error_trace}")
        return Response({
            'error': str(e),
            'traceback': error_trace if settings.DEBUG else None
        }, status=400)

def generate_email_preview(email_obj, variables=None, subscriber=None, request_obj=None):
    """
    Generate the full email preview including footer and advertisement.
    Returns both HTML and text versions.
    """
    # Get site information from request context
    from .context_processors import site_detection
    # Create a mock request to get site info
    class MockRequest:
        def get_host(self):
            return settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'dripemails.org'
    
    site_info = site_detection(MockRequest())
    site_url = site_info['site_url']
    site_name = site_info['site_name']
    site_logo = site_info['site_logo']
    
    # Replace variables in content
    html_content = email_obj.body_html
    text_content = email_obj.body_text
    subject = email_obj.subject
    
    if variables:
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            html_content = html_content.replace(placeholder, str(value))
            text_content = text_content.replace(placeholder, str(value))
            subject = subject.replace(placeholder, str(value))
    
    # Get user profile for ad settings
    user = request_obj.user if request_obj else email_obj.campaign.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    show_ads = not user_profile.has_verified_promo
    show_unsubscribe = not user_profile.send_without_unsubscribe
    
    # Add email footer if one is assigned
    if email_obj.footer:
        footer_html = email_obj.footer.html_content
        # Replace variables in footer if needed
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                footer_html = footer_html.replace(placeholder, str(value))
        html_content += footer_html
        # Convert footer HTML to text for plain text version using proper HTML to text conversion
        from campaigns.tasks import _html_to_plain_text
        footer_text = _html_to_plain_text(footer_html)
        if footer_text:
            text_content += f"\n\n{footer_text}"
    
    # Generate unsubscribe link
    if subscriber and hasattr(subscriber, 'uuid'):
        unsubscribe_link = f"{site_url}/unsubscribe/{subscriber.uuid}/"
    else:
        unsubscribe_link = f"{site_url}/unsubscribe/"
    
    # Add ads if required
    if show_ads:
        # Render ad footer with site context
        ads_html = render_to_string('emails/ad_footer.html', {
            'site_url': site_url,
            'site_name': site_name,
            'site_logo': site_logo,
        })
        ads_text = f"This email was sent using {site_name} - Free email marketing automation\nWant to send emails without this footer? Share about {site_name} and remove this message: {site_url}/promo-verification/"
        html_content += ads_html
        text_content += f"\n\n{ads_text}"
    
    # Add unsubscribe link if required
    if show_unsubscribe:
        # Format user address for footer (required by CAN-SPAM, GDPR, etc.)
        address_lines = []
        # Add full name first if available
        if user_profile.full_name:
            address_lines.append(user_profile.full_name)
        if user_profile.address_line1:
            address_lines.append(user_profile.address_line1)
        if user_profile.address_line2:
            address_lines.append(user_profile.address_line2)
        city_state = []
        if user_profile.city:
            city_state.append(user_profile.city)
        if user_profile.state:
            city_state.append(user_profile.state)
        if city_state:
            address_lines.append(', '.join(city_state))
        postal_country = []
        if user_profile.postal_code:
            postal_country.append(user_profile.postal_code)
        if user_profile.country:
            postal_country.append(user_profile.country)
        if postal_country:
            address_lines.append(' '.join(postal_country))
        
        address_html = ''
        address_text = ''
        if address_lines:
            address_html = '<p style="font-size: 11px; color: #999; margin-top: 10px; line-height: 1.4;">' + '<br>'.join(address_lines) + '</p>'
            address_text = '\n' + '\n'.join(address_lines)
        
        unsubscribe_html = f'<hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;"><p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>{address_html}'
        unsubscribe_text = f"\n\n--\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_link}{address_text}"
        html_content += unsubscribe_html
        text_content += unsubscribe_text
    
    return {
        'html': html_content,
        'text': text_content,
        'subject': subject,
    }


@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def send_email_requests_list(request):
    """Return the latest email send requests for the current user."""
    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    try:
        user_timezone = pytz.timezone(profile.timezone or 'UTC')
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone('UTC')
        profile.timezone = 'UTC'
        profile.save(update_fields=['timezone'])

    requests_qs = EmailSendRequest.objects.filter(user=request.user).select_related('campaign', 'email', 'subscriber').order_by('-created_at')[:10]

    def format_datetime(dt):
        if not dt:
            return None, ''
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        local_dt = timezone.localtime(dt, user_timezone)
        return local_dt.isoformat(), local_dt.strftime('%b %d, %Y %I:%M %p')

    data = []
    for req in requests_qs:
        scheduled_iso, scheduled_display = format_datetime(req.scheduled_for)
        sent_iso, sent_display = format_datetime(req.sent_at)
        
        # Generate email preview
        preview = generate_email_preview(req.email, req.variables, req.subscriber, req)
        
        # Create preview snippet (first 200 chars of text, strip HTML)
        import re as re_module
        preview_text = re_module.sub(r'<[^>]+>', '', preview['html'])
        preview_snippet = preview_text[:200] + ('...' if len(preview_text) > 200 else '')
        
        data.append({
            'id': str(req.id),
            'campaign': req.campaign.name,
            'email_subject': req.email.subject,
            'subscriber_email': req.subscriber_email,
            'subscriber_name': req.subscriber.full_name if req.subscriber else '',
            'status': req.status,
            'scheduled_for': scheduled_iso,
            'scheduled_for_display': scheduled_display,
            'sent_at': sent_iso,
            'sent_at_display': sent_display,
            'error_message': req.error_message or '',
            'email_preview_html': preview['html'],
            'email_preview_text': preview['text'],
            'email_preview_snippet': preview_snippet,
        })

    return Response({'requests': data, 'timezone': profile.timezone or 'UTC'})


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email_request_send_now(request, request_id):
    """Send a pending/queued email immediately."""
    request_obj = get_object_or_404(EmailSendRequest, id=request_id, user=request.user)

    if request_obj.status == 'sent':
        return Response({'message': _('Email already sent.'), 'status': request_obj.status})

    from campaigns.tasks import _send_single_email_sync

    try:
        _send_single_email_sync(
            str(request_obj.email.id),
            request_obj.subscriber_email,
            request_obj.variables or {},
            request_id=str(request_obj.id)
        )
        request_obj.refresh_from_db()
        return Response({'message': _('Email sent successfully.'), 'status': request_obj.status})
    except Exception as exc:
        return Response({'error': str(exc)}, status=500)


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email_request_unsubscribe(request, request_id):
    """Unsubscribe the recipient associated with a send request."""
    request_obj = get_object_or_404(EmailSendRequest, id=request_id, user=request.user)

    from subscribers.models import Subscriber
    from campaigns.models import EmailEvent

    subscriber = request_obj.subscriber
    if not subscriber:
        subscriber = Subscriber.objects.filter(email=request_obj.subscriber_email).first()
        if subscriber:
            request_obj.subscriber = subscriber
            request_obj.save(update_fields=['subscriber'])

    if subscriber and subscriber.is_active:
        subscriber.is_active = False
        subscriber.save(update_fields=['is_active'])

    # Record unsubscribe event
    EmailEvent.objects.create(
        email=request_obj.email,
        subscriber_email=request_obj.subscriber_email,
        event_type='unsubscribed'
    )

    return Response({'message': _('Subscriber has been unsubscribed.')} )


def unsubscribe(request, subscriber_uuid):
    """Handle unsubscribe requests from email links."""
    from subscribers.models import Subscriber
    from campaigns.models import EmailEvent
    from django.http import Http404
    
    try:
        subscriber = Subscriber.objects.get(uuid=subscriber_uuid)
    except Subscriber.DoesNotExist:
        return render(request, 'core/unsubscribe_error.html', {
            'error_message': _('Invalid unsubscribe link. The subscriber may have already been unsubscribed or the link is invalid.')
        }, status=404)
    
    # Check if already unsubscribed
    already_unsubscribed = not subscriber.is_active
    
    if not already_unsubscribed:
        # Deactivate the subscriber
        subscriber.is_active = False
        subscriber.save(update_fields=['is_active'])
        
        # Record unsubscribe event for all emails sent to this subscriber
        # We'll record it for the most recent email if we can find one
        from campaigns.models import Email
        recent_emails = Email.objects.filter(
            campaign__subscriber_list__subscribers=subscriber
        ).order_by('-created_at')[:1]
        
        if recent_emails.exists():
            EmailEvent.objects.create(
                email=recent_emails.first(),
                subscriber_email=subscriber.email,
                event_type='unsubscribed'
            )
    
    return render(request, 'core/unsubscribe_success.html', {
        'subscriber': subscriber,
        'already_unsubscribed': already_unsubscribed,
    })