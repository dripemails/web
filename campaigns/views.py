from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Campaign, Email
from .serializers import CampaignSerializer, EmailSerializer
from .tasks import send_campaign_emails

class CampaignListCreateAPIView(generics.ListCreateAPIView):
    """List and create campaigns."""
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only campaigns belonging to the current user."""
        return Campaign.objects.filter(user=self.request.user).order_by('-created_at')


class CampaignRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete a campaign."""
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only campaigns belonging to the current user."""
        return Campaign.objects.filter(user=self.request.user)


class EmailListCreateAPIView(generics.ListCreateAPIView):
    """List and create emails for a campaign."""
    serializer_class = EmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only emails for the specified campaign belonging to the current user."""
        campaign_id = self.kwargs.get('campaign_id')
        return Email.objects.filter(campaign__id=campaign_id, campaign__user=self.request.user).order_by('order')
    
    def perform_create(self, serializer):
        """Create email and associate with the specified campaign."""
        campaign_id = self.kwargs.get('campaign_id')
        campaign = get_object_or_404(Campaign, id=campaign_id, user=self.request.user)
        
        # Set order to next available if not provided
        if 'order' not in serializer.validated_data:
            next_order = Email.objects.filter(campaign=campaign).count()
            serializer.save(campaign=campaign, order=next_order)
        else:
            serializer.save(campaign=campaign)


class EmailRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete an email from a campaign."""
    serializer_class = EmailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only emails for the specified campaign belonging to the current user."""
        campaign_id = self.kwargs.get('campaign_id')
        return Email.objects.filter(campaign__id=campaign_id, campaign__user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def activate_campaign(request, campaign_id):
    """Activate a campaign to start sending emails."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    # Check if campaign has emails
    if campaign.emails.count() == 0:
        return Response(
            {"error": "Cannot activate a campaign with no emails."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    campaign.is_active = True
    campaign.save()
    
    # Schedule emails to be sent
    send_campaign_emails.delay(campaign_id=str(campaign.id))
    
    return Response(
        {"message": "Campaign activated successfully. Emails will be sent according to schedule."},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def deactivate_campaign(request, campaign_id):
    """Deactivate a campaign to stop sending emails."""
    campaign = get_object_or_404(Campaign, id=campaign_id, user=request.user)
    
    campaign.is_active = False
    campaign.save()
    
    return Response(
        {"message": "Campaign deactivated successfully. No more emails will be sent."},
        status=status.HTTP_200_OK
    )


@login_required
def campaign_edit_view(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, user=request.user)
    emails = campaign.emails.all() # Emails are already ordered by the 'order' field in the model's Meta
    context = {
        'campaign': campaign,
        'emails': emails,
    }
    return render(request, 'campaigns/campaign_edit_page.html', context)