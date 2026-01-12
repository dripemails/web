from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EmailCredential, EmailMessage, EmailProvider
from campaigns.models import Campaign, Email
from subscribers.models import List, Subscriber
import logging
import json

logger = logging.getLogger(__name__)


@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_auth_url(request):
    """Get Gmail OAuth authorization URL."""
    from .services import GmailService
    
    try:
        service = GmailService()
        
        # Verify client ID is set
        if not service.client_id:
            return Response({
                'error': 'GOOGLE_CLIENT_ID is not configured. Please set it in your .env file.'
            }, status=500)
        
        auth_url = service.get_authorization_url(request.user)
        return Response({
            'auth_url': auth_url,
            'state': service.get_state_token(request.user)
        })
    except ValueError as e:
        logger.error(f"Gmail OAuth configuration error: {str(e)}")
        return Response({'error': str(e)}, status=500)
    except Exception as e:
        logger.error(f"Error generating Gmail auth URL: {str(e)}", exc_info=True)
        return Response({'error': f'Error generating auth URL: {str(e)}'}, status=500)


@login_required
def gmail_callback(request):
    """Handle Gmail OAuth callback."""
    from .services import GmailService
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, f"Gmail authentication failed: {error}")
        return redirect('core:dashboard')
    
    if not code:
        messages.error(request, "No authorization code received.")
        return redirect('core:dashboard')
    
    try:
        service = GmailService()
        credential = service.handle_oauth_callback(request.user, code, state)
        
        if credential:
            # Auto-create Gmail list and campaign
            _create_gmail_resources(request.user, credential)
            messages.success(request, "Gmail account connected successfully!")
        else:
            messages.error(request, "Failed to save Gmail credentials.")
    except Exception as e:
        logger.error(f"Error in Gmail callback: {str(e)}")
        messages.error(request, f"Error connecting Gmail: {str(e)}")
    
    return redirect('core:dashboard')


@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gmail_emails(request):
    """Get Gmail emails for the authenticated user."""
    try:
        credential = EmailCredential.objects.filter(
            user=request.user,
            provider=EmailProvider.GMAIL,
            is_active=True
        ).first()
        
        if not credential:
            return Response({'emails': [], 'connected': False, 'error': 'No Gmail account connected'}, status=200)
        
        emails = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.GMAIL
        ).order_by('-received_at')[:50]
        
        email_data = []
        for email in emails:
            email_data.append({
                'id': str(email.id),
                'subject': email.subject,
                'from_email': email.from_email,
                'to_emails': email.to_emails_list,
                'sender_email': email.sender_email,
                'body_text': email.body_text[:500] if email.body_text else '',
                'body_html': email.body_html[:1000] if email.body_html else '',
                'received_at': email.received_at.isoformat(),
                'campaign_email_id': str(email.campaign_email.id) if email.campaign_email else None,
                'campaign_email_subject': email.campaign_email.subject if email.campaign_email else None,
            })
        
        return Response({'emails': email_data, 'connected': True})
    except Exception as e:
        logger.error(f"Error fetching Gmail emails: {str(e)}")
        return Response({'error': str(e)}, status=500)


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gmail_disconnect(request):
    """Disconnect Gmail account."""
    try:
        credential = EmailCredential.objects.filter(
            user=request.user,
            provider=EmailProvider.GMAIL,
            is_active=True
        ).first()
        
        if credential:
            credential.is_active = False
            credential.save()
            return Response({'message': 'Gmail account disconnected'})
        else:
            return Response({'error': 'No active Gmail account found'}, status=404)
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {str(e)}")
        return Response({'error': str(e)}, status=500)


def _create_gmail_resources(user, credential):
    """Auto-create Gmail subscriber list and campaign."""
    from django.utils.text import slugify
    import uuid
    
    # Create Gmail subscriber list
    list_name = f"Gmail - {credential.email_address}"
    gmail_list, created = List.objects.get_or_create(
        user=user,
        slug=slugify(list_name),
        defaults={
            'name': list_name,
            'description': f"Auto-created list for Gmail account {credential.email_address}"
        }
    )
    
    # Create Gmail campaign
    campaign_name = f"Gmail Auto-Reply - {credential.email_address}"
    campaign_slug = slugify(campaign_name)
    if Campaign.objects.filter(slug=campaign_slug).exists():
        campaign_slug = f"{campaign_slug}-{str(uuid.uuid4())[:8]}"
    
    gmail_campaign, created = Campaign.objects.get_or_create(
        user=user,
        slug=campaign_slug,
        defaults={
            'name': campaign_name,
            'description': f"Auto-created campaign for Gmail auto-replies from {credential.email_address}",
            'subscriber_list': gmail_list,
            'is_active': True
        }
    )
    
    # Create default email template
    if created or not gmail_campaign.emails.exists():
        Email.objects.create(
            campaign=gmail_campaign,
            subject="Re: {{subject}}",
            body_html="<p>Hi {{first_name}},</p><p>Thanks for emailing me. Did you have any questions?</p>",
            body_text="Hi {{first_name}},\n\nThanks for emailing me. Did you have any questions?",
            wait_time=0,
            wait_unit='minutes',
            order=1
        )
    
    return gmail_list, gmail_campaign


def _create_imap_resources(user, credential):
    """Auto-create IMAP subscriber list and campaign."""
    from django.utils.text import slugify
    import uuid
    
    # Create IMAP subscriber list
    list_name = f"IMAP - {credential.email_address}"
    imap_list, created = List.objects.get_or_create(
        user=user,
        slug=slugify(list_name),
        defaults={
            'name': list_name,
            'description': f"Auto-created list for IMAP account {credential.email_address}"
        }
    )
    
    # Create IMAP campaign
    campaign_name = f"IMAP Auto-Reply - {credential.email_address}"
    campaign_slug = slugify(campaign_name)
    if Campaign.objects.filter(slug=campaign_slug).exists():
        campaign_slug = f"{campaign_slug}-{str(uuid.uuid4())[:8]}"
    
    imap_campaign, created = Campaign.objects.get_or_create(
        user=user,
        slug=campaign_slug,
        defaults={
            'name': campaign_name,
            'description': f"Auto-created campaign for IMAP auto-replies from {credential.email_address}",
            'subscriber_list': imap_list,
            'is_active': True
        }
    )
    
    # Create default email template
    if created or not imap_campaign.emails.exists():
        Email.objects.create(
            campaign=imap_campaign,
            subject="Re: {{subject}}",
            body_html="<p>Hi {{first_name}},</p><p>I noticed that we exchanged emails. Did you have any questions?</p>",
            body_text="Hi {{first_name}},\n\nI noticed that we exchanged emails. Did you have any questions?",
            wait_time=0,
            wait_unit='minutes',
            order=1
        )
    
    return imap_list, imap_campaign


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def imap_connect(request):
    """Save IMAP credentials and connect."""
    from .imap_service import IMAPService
    
    try:
        email_address = request.data.get('email', '').strip()
        imap_host = request.data.get('host', '').strip()
        imap_port = int(request.data.get('port', 993))
        imap_username = request.data.get('username', '').strip()
        imap_password = request.data.get('password', '').strip()
        use_ssl = request.data.get('use_ssl', True)
        
        if not all([email_address, imap_host, imap_username, imap_password]):
            return Response({'error': 'Missing required fields'}, status=400)
        
        # Create or update credential
        credential, created = EmailCredential.objects.update_or_create(
            user=request.user,
            provider=EmailProvider.IMAP,
            email_address=email_address,
            defaults={
                'imap_host': imap_host,
                'imap_port': imap_port,
                'imap_username': imap_username,
                'imap_password': imap_password,
                'imap_use_ssl': use_ssl,
                'is_active': True,
                'sync_enabled': True,
            }
        )
        
        # Test connection
        service = IMAPService()
        if not service.test_connection(credential):
            credential.is_active = False
            credential.save()
            return Response({'error': 'Failed to connect to IMAP server. Please check your settings.'}, status=400)
        
        # Auto-create IMAP list and campaign
        _create_imap_resources(request.user, credential)
        
        return Response({'message': 'IMAP account connected successfully!', 'credential_id': str(credential.id)})
    except Exception as e:
        logger.error(f"Error connecting IMAP: {str(e)}")
        return Response({'error': str(e)}, status=500)


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def imap_disconnect(request):
    """Disconnect IMAP account."""
    try:
        credential = EmailCredential.objects.filter(
            user=request.user,
            provider=EmailProvider.IMAP,
            is_active=True
        ).first()
        
        if not credential:
            return Response({'error': 'No active IMAP account found'}, status=404)
        
        credential.is_active = False
        credential.sync_enabled = False
        credential.save()
        
        return Response({'message': 'IMAP account disconnected successfully'})
    except Exception as e:
        logger.error(f"Error disconnecting IMAP: {str(e)}")
        return Response({'error': str(e)}, status=500)


@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def imap_emails(request):
    """Get IMAP emails for the authenticated user."""
    try:
        credential = EmailCredential.objects.filter(
            user=request.user,
            provider=EmailProvider.IMAP,
            is_active=True
        ).first()
        
        if not credential:
            return Response({'emails': [], 'connected': False, 'error': 'No IMAP account connected'}, status=200)
        
        emails = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.IMAP
        ).order_by('-received_at')[:50]
        
        email_data = []
        for email in emails:
            email_data.append({
                'id': str(email.id),
                'subject': email.subject,
                'from_email': email.from_email,
                'to_emails': email.to_emails_list,
                'sender_email': email.sender_email,
                'body_text': email.body_text[:500] if email.body_text else '',
                'body_html': email.body_html[:1000] if email.body_html else '',
                'received_at': email.received_at.isoformat(),
                'campaign_email_id': str(email.campaign_email.id) if email.campaign_email else None,
                'campaign_email_subject': email.campaign_email.subject if email.campaign_email else None,
            })
        
        return Response({'emails': email_data, 'connected': True})
    except Exception as e:
        logger.error(f"Error fetching IMAP emails: {str(e)}")
        return Response({'error': str(e)}, status=500)

