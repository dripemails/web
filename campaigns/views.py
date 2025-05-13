from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Campaign, Email
from .serializers import CampaignSerializer, EmailSerializer
import uuid

@login_required
def campaign_create(request):
    """Render campaign creation page."""
    return render(request, 'campaigns/create.html')

@login_required
def campaign_template(request, campaign_id=None):
    """Render template creation/edit page."""
    campaign = None
    if campaign_id:
        campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    return render(request, 'campaigns/template.html', {'campaign': campaign})

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
        for email_data in emails_data:
            email_data['campaign'] = campaign.id
            email_serializer = EmailSerializer(data=email_data)
            if email_serializer.is_valid():
                email_serializer.save()
        
        return Response({
            'id': campaign.id,
            'message': _('Campaign created successfully')
        })
    return Response(serializer.errors, status=400)