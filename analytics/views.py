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
from campaigns.tasks import process_email_click


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
def weekly_analytics(request):
    """Get analytics for the past 7 days."""
    from datetime import datetime, timedelta
    from django.db.models import Q, Count
    from django.db.models.functions import TruncDate
    
    # Get campaign_id from query params if provided
    campaign_id = request.GET.get('campaign_id')
    
    # Get campaigns for this user
    if campaign_id:
        campaigns = Campaign.objects.filter(user=request.user, id=campaign_id)
    else:
        campaigns = Campaign.objects.filter(user=request.user)

    selected_campaign = campaigns.first() if campaign_id else None
    subscriber_list = selected_campaign.subscriber_list if selected_campaign else None
    
    # Calculate date range for the past 7 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=6)  # 6 days ago + today = 7 days
    
    # Initialize data structure for all 7 days
    daily_data = {}
    for i in range(7):
        date = (start_date + timedelta(days=i)).date()
        daily_data[str(date)] = {
            'date': str(date),
            'sent': 0,
            'delivered': 0,
            'opened': 0,
            'clicked': 0,
            'bounced': 0,
            'delivery_rate': 0,
            'open_rate': 0,
            'click_rate': 0,
            'subscriber_count': 0,
        }
    
    # Get all email events for user's campaigns in the past 7 days
    events = EmailEvent.objects.filter(
        email__campaign__in=campaigns,
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date', 'event_type').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Aggregate events by date and type
    for event in events:
        date_str = str(event['date'])
        if date_str in daily_data:
            event_type = event['event_type']
            count = event['count']
            
            if event_type == 'sent':
                daily_data[date_str]['sent'] += count
            elif event_type == 'opened':
                daily_data[date_str]['opened'] += count
            elif event_type == 'clicked':
                daily_data[date_str]['clicked'] += count
            elif event_type == 'bounced':
                daily_data[date_str]['bounced'] += count
    
    # Calculate delivery and rates for each day
    for date_str, data in daily_data.items():
        sent = data['sent']
        bounced = data['bounced']
        delivered = sent - bounced
        opened = data['opened']
        clicked = data['clicked']
        
        data['delivered'] = delivered
        
        # Calculate rates
        if sent > 0:
            data['delivery_rate'] = round((delivered / sent) * 100, 2)
        if delivered > 0:
            data['open_rate'] = round((opened / delivered) * 100, 2)
            data['click_rate'] = round((clicked / delivered) * 100, 2)

        if subscriber_list:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_end = timezone.make_aware(datetime.combine(date_obj, datetime.max.time()))
            data['subscriber_count'] = subscriber_list.subscribers.filter(
                created_at__lte=day_end
            ).count()
    
    # Convert to sorted list
    result = sorted(daily_data.values(), key=lambda x: x['date'])
    
    return Response({
        'weekly_data': result
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
        # Count unique opens (distinct subscriber emails that opened)
        unique_opens = EmailEvent.objects.filter(
            email=email, 
            event_type='opened'
        ).values('subscriber_email').distinct().count()
        click_count = EmailEvent.objects.filter(email=email, event_type='clicked').count()
        bounce_count = EmailEvent.objects.filter(email=email, event_type='bounced').count()
        
        open_rate = round((unique_opens / sent_count * 100), 2) if sent_count > 0 else 0
        click_rate = round((click_count / sent_count * 100), 2) if sent_count > 0 else 0
        bounce_rate = round((bounce_count / sent_count * 100), 2) if sent_count > 0 else 0
        
        email_metrics.append({
            'id': str(email.id),
            'subject': email.subject,
            'order': email.order,
            'sent': sent_count,
            'opened': unique_opens,
            'clicked': click_count,
            'bounced': bounce_count,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'bounce_rate': bounce_rate,
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
            'bounced': campaign.bounce_count,
            'unsubscribed': campaign.unsubscribe_count,
            'complained': campaign.complaint_count,
            'open_rate': campaign.open_rate,
            'click_rate': campaign.click_rate,
            'delivery_rate': campaign.delivery_rate,
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
    """Legacy tracking endpoint - backwards compatibility wrapper for old tracking pixel URLs."""
    # This is the old URL format: /analytics/track/open/<uuid>/<email>/
    # Process tracking the same way as message_split_gif but return old-style pixel
    from urllib.parse import unquote
    import logging
    logger = logging.getLogger(__name__)
    
    subscriber_email = unquote(encoded_email)
    if subscriber_email:
        # Always process synchronously (no Celery)
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
                
                logger.info(f"Recorded open event for {subscriber_email}")
            else:
                logger.debug(f"Open event already exists for {subscriber_email}, skipping duplicate")
        except EmailEvent.DoesNotExist:
            logger.error(f"No matching sent event found for tracking ID {tracking_id}, email: {subscriber_email}")
        except Exception as e:
            logger.error(f"Failed to process email open: {str(e)}", exc_info=True)
    
    # Return a transparent 1x1 pixel (old format for backwards compatibility)
    transparent_pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
    return HttpResponse(transparent_pixel, content_type='image/gif')


def message_split_gif(request):
    """Serve a decorative separator image that also tracks email opens."""
    from urllib.parse import unquote
    import logging
    logger = logging.getLogger(__name__)
    
    # Get tracking parameters from query string (clean URL, no mention of tracking)
    tracking_id = request.GET.get('t')
    encoded_email = request.GET.get('e')
    
    if tracking_id and encoded_email:
        subscriber_email = unquote(encoded_email)
        if subscriber_email:
            # Always process synchronously (no Celery)
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
                    
                    logger.info(f"Recorded open event for {subscriber_email}")
                else:
                    logger.debug(f"Open event already exists for {subscriber_email}, skipping duplicate")
            except EmailEvent.DoesNotExist:
                logger.error(f"No matching sent event found for tracking ID {tracking_id}, email: {subscriber_email}")
            except Exception as e:
                logger.error(f"Failed to process email open: {str(e)}", exc_info=True)
    
    # Return a decorative separator GIF (2px high, gradient line)
    # This is a visible separator that looks like an HR line, not a tracking pixel
    # GIF format: 600x2px gradient line (transparent to gray to transparent)
    separator_gif = (
        b'\x47\x49\x46\x38\x39\x61'  # GIF89a header
        b'\x58\x02\x00\x02'  # Width: 600 (0x0258), Height: 2
        b'\x80\x00\x00'  # Global Color Table: 128 colors, no sort, 0
        b'\xFF\xFF\xFF'  # Color 0: White
        b'\xE2\xE8\xF0'  # Color 1: Light gray (#e2e8f0)
        b'\x00\x00\x00'  # Color 2: Black (for gradient)
        b'\x21\xF9\x04\x01\x00\x00\x00\x00'  # Graphic Control Extension: transparent, no delay
        b'\x2C\x00\x00\x00\x00\x58\x02\x00\x02\x00\x00'  # Image descriptor: 600x2, no local color table
        b'\x02\x02\x44\x01\x00'  # Image data: minimal gradient
        b'\x3B'  # Trailer
    )
    return HttpResponse(separator_gif, content_type='image/gif')


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
            # Process the click event directly (no Celery)
            process_email_click(str(tracking_id), subscriber_email, destination_url)
    
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