from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserProfile
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
def track_open(request, tracking_id):
    """Track email opens using a transparent 1x1 pixel."""
    subscriber_email = request.GET.get('email')
    if subscriber_email:
        # Process the open event asynchronously
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
        # Process the click event asynchronously
        process_email_click.delay(str(tracking_id), subscriber_email, destination_url)
    
    # Redirect to the destination URL
    return redirect(destination_url)


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