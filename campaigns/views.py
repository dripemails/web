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

@login_required
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def campaign_list_create(request):
    """List all campaigns or create a new one."""
    if request.method == 'GET':
        campaigns = Campaign.objects.filter(user=request.user)
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    serializer = CampaignSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        campaign = serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@login_required
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def campaign_detail(request, campaign_id):
    """Retrieve, update or delete a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if request.method == 'GET':
        serializer = CampaignSerializer(campaign)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CampaignSerializer(campaign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    elif request.method == 'DELETE':
        campaign.delete()
        return Response(status=204)

@login_required
def campaign_create(request):
    """Render campaign creation page."""
    lists = List.objects.filter(user=request.user)
    return render(request, 'campaigns/create.html', {'lists': lists})

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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_campaign(request, campaign_id):
    """Activate a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    if campaign.emails.count() == 0:
        return Response({
            'error': _('Cannot activate a campaign with no emails')
        }, status=400)
    
    campaign.is_active = True
    campaign.save()
    
    return Response({
        'message': _('Campaign activated successfully')
    })

@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_campaign(request, campaign_id):
    """Deactivate a campaign."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    campaign.is_active = False
    campaign.save()
    
    return Response({
        'message': _('Campaign deactivated successfully')
    })