from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from campaigns.models import Campaign, Email
from subscribers.models import List
from analytics.models import UserProfile
from django.conf import settings
import re
from .models import BlogPost

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

    return Response({
        'campaigns': campaign_data,
        'lists': list_data,
        'stats': {
            'campaigns_count': len(campaign_data),
            'lists_count': len(list_data),
            'subscribers_count': sum(list_obj.subscribers_count for list_obj in lists),
            'sent_emails_count': sum(campaign.sent_count for campaign in campaigns),
        },
        'profile': {
            'has_verified_promo': profile.has_verified_promo,
            'send_without_unsubscribe': profile.send_without_unsubscribe,
        }
    })

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
    subscribers_count = sum(list_obj.subscribers_count for list_obj in lists)
    sent_emails_count = sum(campaign.sent_count for campaign in campaigns)
    
    context = {
        'campaigns': campaigns,
        'lists': lists,
        'campaigns_count': campaigns_count,
        'lists_count': lists_count,
        'subscribers_count': subscribers_count,
        'sent_emails_count': sent_emails_count,
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
def promo_verification(request):
    """Handle promo verification."""
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
        if promo_type == 'twitter':
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
        profile, created = UserProfile.objects.get_or_create(user=request.user)
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
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.send_without_unsubscribe = request.data.get('send_without_unsubscribe', False)
        profile.save()
    
    return Response({
        'has_verified_promo': profile.has_verified_promo,
        'send_without_unsubscribe': profile.send_without_unsubscribe,
    })

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

def resource_tutorials(request):
    return render(request, 'core/resource_tutorials.html')

def resource_api_reference(request):
    return render(request, 'core/resource_api_reference.html')

def resource_community(request):
    return render(request, 'core/resource_community.html')

# Simple blog with placeholder data
def blog_index(request):
    posts = BlogPost.objects.filter(published=True).order_by('-date')
    return render(request, 'blog/blog_index.html', {'posts': posts})

def blog_post_detail(request, slug):
    from django.shortcuts import get_object_or_404
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    return render(request, 'blog/blog_post_detail.html', {'post': post})

def community_user_forum(request):
    return render(request, 'core/community_user_forum.html')

def community_feature_requests(request):
    return render(request, 'core/community_feature_requests.html')

def community_success_stories(request):
    return render(request, 'core/community_success_stories.html')

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
        # Verify campaign belongs to user
        campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        email_obj = Email.objects.get(id=email_id, campaign=campaign)
        
        # Get the subscriber or create one
        from subscribers.models import Subscriber
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name or '',
                'last_name': last_name or '',
                'is_active': True
            }
        )
        
        # Parse the schedule
        from datetime import timedelta
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
            else:
                send_delay = timedelta(0)
        
        # Send email using Celery task
        from campaigns.tasks import send_single_email
        if schedule == 'now':
            send_single_email.delay(
                str(email_obj.id),
                email,
                {'first_name': first_name or '', 'last_name': last_name or ''}
            )
        else:
            send_single_email.apply_async(
                args=[str(email_obj.id), email, {'first_name': first_name or '', 'last_name': last_name or ''}],
                countdown=int(send_delay.total_seconds())
            )
        
        return Response({
            'message': _('Email scheduled successfully')
        })
        
    except Campaign.DoesNotExist:
        return Response({'error': _('Campaign not found')}, status=404)
    except Email.DoesNotExist:
        return Response({'error': _('Email template not found')}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)