from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Campaign, Email
from .serializers import CampaignSerializer, EmailSerializer
from subscribers.models import List
import uuid

@login_required
def campaign_create(request):
    """Render campaign creation page."""
    lists = List.objects.filter(user=request.user)
    return render(request, 'campaigns/create.html', {'lists': lists})

@login_required
def campaign_template(request, campaign_id=None):
    """Render template creation/edit page."""
    campaign = None
    template = None
    if campaign_id:
        campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
        template_id = request.GET.get('template_id')
        if template_id:
            template = get_object_or_404(Email, id=template_id, campaign=campaign)
    
    context = {
        'campaign': campaign,
        'template': template,
        'wait_units': [
            ('minutes', _('Minutes')),
            ('hours', _('Hours')),
            ('days', _('Days')),
            ('weeks', _('Weeks')),
            ('months', _('Months'))
        ]
    }
    return render(request, 'campaigns/template.html', context)

@login_required
def campaign_edit(request, campaign_id):
    """Edit campaign and its templates."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    emails = campaign.emails.all().order_by('order')
    return render(request, 'campaigns/edit.html', {
        'campaign': campaign,
        'emails': emails
    })

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_campaign(request):
    """Create a new campaign with templates."""
    serializer = CampaignSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        campaign = serializer.save()
        
        # Create email templates
        emails_data = request.data.get('emails', [])
        for index, email_data in enumerate(emails_data):
            email_data['campaign'] = campaign.id
            email_data['order'] = index
            email_serializer = EmailSerializer(data=email_data)
            if email_serializer.is_valid():
                email_serializer.save()
        
        return Response({
            'id': campaign.id,
            'message': _('Campaign created successfully')
        })
    return Response(serializer.errors, status=400)

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_template_order(request, campaign_id):
    """Update the order of email templates in a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    template_orders = request.data.get('template_orders', [])
    
    for order_data in template_orders:
        template_id = order_data.get('id')
        new_order = order_data.get('order')
        if template_id and new_order is not None:
            try:
                template = Email.objects.get(id=template_id, campaign=campaign)
                template.order = new_order
                template.save()
            except Email.DoesNotExist:
                continue
    
    return Response({'message': _('Template order updated successfully')})

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_template_timing(request, campaign_id, template_id):
    """Update the wait time and unit for a template."""
    template = get_object_or_404(Email, id=template_id, campaign__id=campaign_id, campaign__user=request.user)
    
    wait_time = request.data.get('wait_time')
    wait_unit = request.data.get('wait_unit')
    
    if wait_time is not None and wait_unit:
        template.wait_time = wait_time
        template.wait_unit = wait_unit
        template.save()
        
        return Response({
            'message': _('Template timing updated successfully'),
            'wait_time': template.wait_time,
            'wait_unit': template.wait_unit
        })
    
    return Response({
        'error': _('Invalid timing parameters')
    }, status=400)