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
    
    context = {
        'campaigns': campaigns,
        'lists': lists,
        'campaigns_count': campaigns_count,
        'lists_count': lists_count,
        'subscribers_count': subscribers_count,
        'sent_emails_count': sent_emails_count,
        'user_email_domain': user_email_domain,
        'user_timezone': user_timezone,
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
def account_settings(request):
    """Account settings page."""
    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    common_timezones = pytz.common_timezones

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'settings')

        if form_type == 'timezone':
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
    
    context = {
        'timezones': common_timezones,
        'current_timezone': profile.timezone or 'UTC',
        'send_without_unsubscribe': profile.send_without_unsubscribe,
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
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update send_without_unsubscribe if provided
        if 'send_without_unsubscribe' in request.data:
            profile.send_without_unsubscribe = request.data.get('send_without_unsubscribe', False)
        
        # Update timezone if provided
        if 'timezone' in request.data:
            new_timezone = request.data.get('timezone', 'UTC')
            # Validate timezone
            try:
                pytz.timezone(new_timezone)  # Validate it's a real timezone
                profile.timezone = new_timezone
            except pytz.UnknownTimeZoneError:
                return Response({'error': _('Invalid timezone')}, status=400)
        
        profile.save()
    
    return Response({
        'has_verified_promo': profile.has_verified_promo,
        'send_without_unsubscribe': profile.send_without_unsubscribe,
        'timezone': profile.timezone or 'UTC',
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
            """Queue the email with Celery if available."""
            try:
                send_single_email.apply_async(
                    args=[str(email_obj.id), email, variables, str(send_request.id)],
                    countdown=max(0, int(countdown_seconds))
                )
                send_request.status = 'queued'
                send_request.error_message = ''
                send_request.save(update_fields=['status', 'error_message', 'updated_at'])
                return True, None
            except (ConnectionError, OSError, Exception) as exc:
                error_msg = str(exc)
                logger.warning("Celery unavailable for scheduled email. Falling back to synchronous send. Error: %s", error_msg)
                send_request.status = 'pending'
                send_request.error_message = error_msg
                send_request.save(update_fields=['status', 'error_message', 'updated_at'])
                return False, error_msg

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
                        'message': _('Email sent successfully (Celery unavailable, sent immediately)'),
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
            # Keep as pending; user can trigger "Send Now"
            send_request.status = 'pending'
            send_request.error_message = ''
            send_request.save(update_fields=['status', 'error_message', 'updated_at'])
            return Response({
                'message': _('Email scheduled for {time}. Celery/Redis is not available; use "Send Now" in the activity list to deliver immediately.').format(time=scheduled_display),
                'request_id': str(send_request.id),
                'scheduled_for': scheduled_for_local.isoformat(),
                'status': send_request.status,
                'timezone': profile.timezone or 'UTC'
            })
        else:
            queued, error_msg = queue_with_celery(countdown_seconds)
            if queued:
                return Response({
                    'message': _('Email scheduled for {time}').format(time=scheduled_display),
                    'request_id': str(send_request.id),
                    'scheduled_for': scheduled_for_local.isoformat(),
                    'status': 'queued',
                    'timezone': profile.timezone or 'UTC'
                })
            return Response({
                'message': _('Email saved but not scheduled because Celery/Redis is unavailable. Use "Send Now" in the activity list to deliver immediately.'),
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
        unsubscribe_html = f'<p style="font-size: 12px; color: #666; margin-top: 20px;">If you no longer wish to receive these emails, you can <a href="{unsubscribe_link}">unsubscribe here</a>.</p>'
        unsubscribe_text = f"\n\nIf you no longer wish to receive these emails, you can unsubscribe here: {unsubscribe_link}"
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