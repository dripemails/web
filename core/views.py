from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from campaigns.models import Campaign, Email, EmailSendRequest
from subscribers.models import List
from analytics.models import UserProfile
from django.conf import settings
import re
import pytz
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

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_timezone = profile.timezone or 'UTC'
    
    context = {
        'campaigns': campaigns,
        'lists': lists,
        'campaigns_count': campaigns_count,
        'lists_count': lists_count,
        'subscribers_count': subscribers_count,
        'sent_emails_count': sent_emails_count,
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
def promo_verification(request):
    """Handle promo verification and account settings updates."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    common_timezones = pytz.common_timezones

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'promo')

        if form_type == 'timezone':
            selected_timezone = request.POST.get('timezone')
            if selected_timezone not in common_timezones:
                messages.error(request, _("Please select a valid time zone."))
            else:
                profile.timezone = selected_timezone
                profile.save(update_fields=['timezone'])
                messages.success(request, _("Time zone updated to %(tz)s") % {'tz': selected_timezone})
            return redirect('core:promo_verification')

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
        profile.has_verified_promo = True
        profile.promo_url = promo_url
        profile.save()
        
        messages.success(request, _("Thank you for promoting DripEmails.org! Ads have been disabled for your account."))
        return redirect('core:dashboard')
    
    context = {
        'timezones': common_timezones,
        'current_timezone': profile.timezone or 'UTC',
    }
    return render(request, 'core/promo_verification.html', context)

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
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
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
            if not subscriber.is_active:
                subscriber.is_active = True
                updated = True
            if updated:
                subscriber.save()
        
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
        return Response({'error': str(e)}, status=400)

@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def send_email_requests_list(request):
    """Return the latest email send requests for the current user."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
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