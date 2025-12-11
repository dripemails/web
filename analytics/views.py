from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models

from .models import UserProfile, EmailFooter
from campaigns.models import Campaign, EmailEvent
from subscribers.models import List
from campaigns.tasks import process_email_open, process_email_click


@login_required
@api_view(['GET'])
def analytics_dashboard(request):
    """Get analytics dashboard data."""
    # Get user's campaigns and lists
    campaigns = Campaign.objects.filter(user=request.user)
    lists = List.objects.filter(user=request.user)
    
    # Calculate overall metrics
    total_subscribers = sum(list_obj.subscribers.count() for list_obj in lists)
    active_subscribers = sum(list_obj.subscribers.filter(is_active=True).count() for list_obj in lists)
    total_campaigns = campaigns.count()
    total_emails_sent = sum(campaign.sent_count for campaign in campaigns)
    total_emails_opened = sum(campaign.open_count for campaign in campaigns)
    total_emails_clicked = sum(campaign.click_count for campaign in campaigns)
    
    # Calculate open and click rates
    open_rate = (total_emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0
    click_rate = (total_emails_clicked / total_emails_sent * 100) if total_emails_sent > 0 else 0
    
    # Get recent campaign activity
    recent_campaigns = Campaign.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_campaign_data = [
        {
            'id': str(campaign.id),
            'name': campaign.name,
            'sent': campaign.sent_count,
            'opened': campaign.open_count,
            'clicked': campaign.click_count,
            'open_rate': campaign.open_rate,
            'click_rate': campaign.click_rate,
        }
        for campaign in recent_campaigns
    ]
    
    # Get subscriber growth (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    new_subscribers = sum(
        list_obj.subscribers.filter(created_at__gte=thirty_days_ago).count()
        for list_obj in lists
    )
    
    return Response({
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'total_campaigns': total_campaigns,
        'total_emails_sent': total_emails_sent,
        'total_emails_opened': total_emails_opened, 
        'total_emails_clicked': total_emails_clicked,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'recent_campaigns': recent_campaign_data,
        'new_subscribers_30d': new_subscribers,
    })


@login_required
@api_view(['GET'])
def campaign_analytics(request, campaign_id):
    """Get analytics for a specific campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    # Get email-specific metrics
    emails = campaign.emails.all().order_by('order')
    email_metrics = []
    
    for email in emails:
        sent_count = EmailEvent.objects.filter(email=email, event_type='sent').count()
        open_count = EmailEvent.objects.filter(email=email, event_type='opened').count()
        click_count = EmailEvent.objects.filter(email=email, event_type='clicked').count()
        
        open_rate = (open_count / sent_count * 100) if sent_count > 0 else 0
        click_rate = (click_count / sent_count * 100) if sent_count > 0 else 0
        
        email_metrics.append({
            'id': str(email.id),
            'subject': email.subject,
            'order': email.order,
            'sent': sent_count,
            'opened': open_count,
            'clicked': click_count,
            'open_rate': open_rate,
            'click_rate': click_rate,
        })
    
    # Get link click analytics
    link_clicks = EmailEvent.objects.filter(
        email__campaign=campaign, 
        event_type='clicked'
    ).values('link_clicked').annotate(
        click_count=models.Count('id')
    ).order_by('-click_count')
    
    # Get daily activity
    # For simplicity, we'll just look at the last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    daily_activity = EmailEvent.objects.filter(
        email__campaign=campaign,
        created_at__gte=thirty_days_ago
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day', 'event_type').annotate(
        count=models.Count('id')
    ).order_by('day', 'event_type')
    
    return Response({
        'campaign': {
            'id': str(campaign.id),
            'name': campaign.name,
            'sent': campaign.sent_count,
            'opened': campaign.open_count,
            'clicked': campaign.click_count,
            'open_rate': campaign.open_rate,
            'click_rate': campaign.click_rate,
        },
        'emails': email_metrics,
        'link_clicks': link_clicks,
        'daily_activity': daily_activity,
    })


@login_required
@api_view(['GET'])
def subscriber_analytics(request, list_id):
    """Get analytics for a specific subscriber list."""
    list_obj = get_object_or_404(List, id=list_id, user=request.user)
    
    # Get basic metrics
    total_subscribers = list_obj.subscribers.count()
    active_subscribers = list_obj.subscribers.filter(is_active=True).count()
    confirmed_subscribers = list_obj.subscribers.filter(confirmed=True).count()
    
    # Get growth over time (last 6 months)
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_growth = list_obj.subscribers.filter(
        created_at__gte=six_months_ago
    ).extra(
        select={'month': "DATE_TRUNC('month', created_at)"}
    ).values('month').annotate(
        count=models.Count('id')
    ).order_by('month')
    
    # Get unsubscribe rate
    campaigns_using_list = Campaign.objects.filter(subscriber_list=list_obj)
    total_unsubscribes = EmailEvent.objects.filter(
        email__campaign__in=campaigns_using_list,
        event_type='unsubscribed'
    ).count()
    
    unsubscribe_rate = (total_unsubscribes / total_subscribers * 100) if total_subscribers > 0 else 0
    
    return Response({
        'list': {
            'id': str(list_obj.id),
            'name': list_obj.name,
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'confirmed_subscribers': confirmed_subscribers,
        },
        'monthly_growth': monthly_growth,
        'unsubscribe_rate': unsubscribe_rate,
    })


@csrf_exempt
def track_open(request, tracking_id, encoded_email):
    """Track email opens using a transparent 1x1 pixel."""
    from urllib.parse import unquote
    subscriber_email = unquote(encoded_email)
    if subscriber_email:
        # Use synchronous processing on Windows/DEBUG mode
        import sys
        from django.conf import settings
        if sys.platform == 'win32' and settings.DEBUG:
            # Process synchronously (not as a Celery task) for Windows/DEBUG mode
            try:
                from campaigns.models import EmailEvent, Campaign
                # Find the sent event with the same tracking ID
                sent_event = EmailEvent.objects.get(
                    id=tracking_id, 
                    event_type='sent',
                    subscriber_email=subscriber_email
                )
                
                # Check if open event already exists to avoid duplicates
                existing_open = EmailEvent.objects.filter(
                    email=sent_event.email,
                    subscriber_email=subscriber_email,
                    event_type='opened'
                ).exists()
                
                if not existing_open:
                    # Create an open event
                    EmailEvent.objects.create(
                        email=sent_event.email,
                        subscriber_email=subscriber_email,
                        event_type='opened'
                    )
                    
                    # Update campaign metrics
                    campaign = sent_event.email.campaign
                    campaign.open_count += 1
                    campaign.save(update_fields=['open_count'])
            except EmailEvent.DoesNotExist:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"No matching sent event found for tracking ID {tracking_id}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to process email open: {str(e)}", exc_info=True)
        else:
            # Process the open event asynchronously on production
            process_email_open.delay(str(tracking_id), subscriber_email)
    
    # Return a transparent 1x1 pixel
    transparent_pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    return HttpResponse(transparent_pixel, content_type='image/gif')


@csrf_exempt
def track_click(request, tracking_id):
    """Track link clicks and redirect user to the destination URL."""
    subscriber_email = request.GET.get('email')
    destination_url = request.GET.get('url')
    
    if subscriber_email and destination_url:
        # Use synchronous processing on Windows/DEBUG mode
        import sys
        from django.conf import settings
        if sys.platform == 'win32' and settings.DEBUG:
            # Process synchronously
            from campaigns.models import EmailEvent, Campaign
            try:
                sent_event = EmailEvent.objects.get(
                    id=tracking_id,
                    event_type='sent',
                    subscriber_email=subscriber_email
                )
                
                # Create click event
                EmailEvent.objects.create(
                    email=sent_event.email,
                    subscriber_email=subscriber_email,
                    event_type='clicked',
                    link_clicked=destination_url
                )
                
                # Update campaign metrics
                campaign = sent_event.email.campaign
                campaign.click_count += 1
                campaign.save(update_fields=['click_count'])
            except EmailEvent.DoesNotExist:
                pass
            except Exception:
                pass
        else:
            # Process the click event asynchronously on production
            process_email_click.delay(str(tracking_id), subscriber_email, destination_url)
    
    # Redirect to the destination URL
    if destination_url:
        return redirect(destination_url)
    else:
        return HttpResponse("No destination URL provided", status=400)


@login_required
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def update_profile_settings(request):
    """Get or update user profile settings."""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        return Response({
            'has_verified_promo': profile.has_verified_promo,
            'promo_url': profile.promo_url,
            'send_without_unsubscribe': profile.send_without_unsubscribe,
        })
    
    elif request.method == 'PUT':
        # Only update send_without_unsubscribe
        # The has_verified_promo can only be updated through the promo verification process
        profile.send_without_unsubscribe = request.data.get('send_without_unsubscribe', False)
        profile.save()
        
        return Response({
            'has_verified_promo': profile.has_verified_promo,
            'promo_url': profile.promo_url,
            'send_without_unsubscribe': profile.send_without_unsubscribe,
        })


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_api_key(request):
    """Regenerate the user's API key."""
    from rest_framework.authtoken.models import Token
    
    # Delete existing token if it exists
    Token.objects.filter(user=request.user).delete()
    
    # Create new token
    token = Token.objects.create(user=request.user)
    
    return Response({
        'success': True,
        'api_key': token.key,
        'message': _('API key regenerated successfully!')
    })


# Footer Management Views
@login_required
def footer_list(request):
    """List all footers for the user."""
    footers = EmailFooter.objects.filter(user=request.user)
    return render(request, 'analytics/footer_list.html', {
        'footers': footers
    })


@login_required
def footer_create(request):
    """Create a new footer."""
    if request.method == 'POST':
        name = request.POST.get('name')
        html_content = request.POST.get('html_content')
        is_default = request.POST.get('is_default') == 'on'
        
        if name and html_content:
            footer = EmailFooter.objects.create(
                user=request.user,
                name=name,
                html_content=html_content,
                is_default=is_default
            )
            messages.success(request, _('Footer created successfully!'))
            return redirect('analytics:footer_list')
        else:
            messages.error(request, _('Please provide both name and content.'))
    
    return render(request, 'analytics/footer_form.html', {
        'footer': None,
        'is_create': True
    })

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def footer_create_api(request):
    """Create a new footer via API."""
    try:
        data = request.data
        name = data.get('name', '').strip()
        html_content = data.get('html_content', '').strip()
        is_default = data.get('is_default', False)
        
        if not name:
            return Response({'error': _('Footer name is required')}, status=400)
        
        if not html_content:
            return Response({'error': _('Footer content is required')}, status=400)
        
        footer = EmailFooter.objects.create(
            user=request.user,
            name=name,
            html_content=html_content,
            is_default=is_default
        )
        
        return Response({
            'success': True,
            'footer_id': footer.id,
            'message': _('Footer created successfully!')
        }, status=201)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@login_required
def footer_edit(request, footer_id):
    """Edit an existing footer."""
    footer = get_object_or_404(EmailFooter, id=footer_id, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        html_content = request.POST.get('html_content')
        is_default = request.POST.get('is_default') == 'on'
        
        if name and html_content:
            footer.name = name
            footer.html_content = html_content
            footer.is_default = is_default
            footer.save()
            messages.success(request, _('Footer updated successfully!'))
            return redirect('analytics:footer_list')
        else:
            messages.error(request, _('Please provide both name and content.'))
    
    return render(request, 'analytics/footer_form.html', {
        'footer': footer,
        'is_create': False
    })


@login_required
def footer_delete(request, footer_id):
    """Delete a footer."""
    footer = get_object_or_404(EmailFooter, id=footer_id, user=request.user)
    
    if request.method == 'POST':
        footer.delete()
        messages.success(request, _('Footer deleted successfully!'))
        return redirect('analytics:footer_list')
    
    return render(request, 'analytics/footer_confirm_delete.html', {
        'footer': footer
    })


@login_required
def footer_set_default(request, footer_id):
    """Set a footer as default."""
    footer = get_object_or_404(EmailFooter, id=footer_id, user=request.user)
    footer.is_default = True
    footer.save()
    messages.success(request, _('Default footer updated successfully!'))
    return redirect('analytics:footer_list')