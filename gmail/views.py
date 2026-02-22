from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
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
            # Extract template variables from provider_data or email headers
            first_name = ''
            last_name = ''
            recipient_email = email.from_email
            from_display_name = email.from_email  # Default to email if no name
            
            # Try to get from provider_data (stored by Gmail service)
            if email.provider_data:
                first_name = email.provider_data.get('first_name', '')
                last_name = email.provider_data.get('last_name', '')
                recipient_email = email.provider_data.get('recipient_email', email.from_email)
                from_display_name = email.provider_data.get('from_display_name', email.from_email)
            
            # If not in provider_data, try to extract from email headers stored in provider_data
            if not first_name and not last_name:
                # Gmail stores the full message in provider_data, including headers
                if email.provider_data and isinstance(email.provider_data, dict):
                    # Try to get From header from payload.headers
                    headers = email.provider_data.get('payload', {}).get('headers', [])
                    if headers:
                        # Find From header
                        from_header = None
                        for header in headers:
                            if header.get('name', '').lower() == 'from':
                                from_header = header.get('value', '')
                                break
                        
                        if from_header:
                            # Extract name from "Name <email@example.com>" format
                            import re
                            name_match = re.match(r'^(.+?)\s*<', from_header)
                            if name_match:
                                full_name = name_match.group(1).strip().strip('"\'')
                                from_display_name = full_name
                                name_parts = full_name.split(' ', 1)
                                first_name = name_parts[0] if len(name_parts) > 0 else ''
                                last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Fallback: use email prefix as first name if still no name
            if not first_name:
                first_name = recipient_email.split('@')[0].split('.')[0].title()
                from_display_name = recipient_email
            
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
                'campaign_email_body_html': email.campaign_email.body_html if email.campaign_email else None,
                'campaign_email_body_text': email.campaign_email.body_text if email.campaign_email else None,
                # Template variables for replacement
                'template_variables': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': recipient_email,
                    'subject': email.subject,
                }
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

    def _merge_duplicate_lists(canonical_list, user_obj, target_name, target_description):
        duplicate_lists = List.objects.filter(
            user=user_obj,
            name=target_name,
            description=target_description
        ).exclude(pk=canonical_list.pk)

        for duplicate_list in duplicate_lists:
            # Preserve subscribers
            subscribers = list(duplicate_list.subscribers.all())
            if subscribers:
                canonical_list.subscribers.add(*subscribers)

            # Preserve campaign -> list linkage
            Campaign.objects.filter(subscriber_list=duplicate_list).update(subscriber_list=canonical_list)

            duplicate_list.delete()

    def _merge_duplicate_campaigns(canonical_campaign, user_obj, target_name, target_description, canonical_list):
        duplicate_campaigns = Campaign.objects.filter(
            user=user_obj,
            name=target_name,
            description=target_description
        ).exclude(pk=canonical_campaign.pk)

        if duplicate_campaigns.exists():
            for duplicate_campaign in duplicate_campaigns:
                # Preserve aggregate counters
                canonical_campaign.sent_count += duplicate_campaign.sent_count
                canonical_campaign.open_count += duplicate_campaign.open_count
                canonical_campaign.click_count += duplicate_campaign.click_count
                canonical_campaign.bounce_count += duplicate_campaign.bounce_count
                canonical_campaign.unsubscribe_count += duplicate_campaign.unsubscribe_count
                canonical_campaign.complaint_count += duplicate_campaign.complaint_count

                # Preserve campaign-linked records
                Email.objects.filter(campaign=duplicate_campaign).update(campaign=canonical_campaign)
                duplicate_campaign.email_send_requests.update(campaign=canonical_campaign)

                duplicate_campaign.delete()

            canonical_campaign.subscriber_list = canonical_list
            canonical_campaign.is_active = True
            canonical_campaign.save(update_fields=[
                'subscriber_list',
                'is_active',
                'sent_count',
                'open_count',
                'click_count',
                'bounce_count',
                'unsubscribe_count',
                'complaint_count',
                'updated_at'
            ])
    
    # Create Gmail subscriber list
    # Include user ID in slug to ensure uniqueness across users
    list_name = f"Gmail - {credential.email_address}"
    base_slug = slugify(list_name)
    # Make slug unique per user by including user ID
    unique_slug = f"{base_slug}-{user.id}"
    
    # Ensure slug doesn't exceed max length (150 chars)
    if len(unique_slug) > 150:
        # Truncate base slug if needed, keeping user ID
        max_base_length = 150 - len(str(user.id)) - 1  # -1 for the hyphen
        base_slug = base_slug[:max_base_length]
        unique_slug = f"{base_slug}-{user.id}"
    
    gmail_list, created = List.objects.get_or_create(
        user=user,
        slug=unique_slug,
        defaults={
            'name': list_name,
            'description': f"Auto-created list for Gmail account {credential.email_address}"
        }
    )
    
    # Create Gmail campaign
    # Include user ID in campaign slug as well for consistency
    campaign_name = f"Gmail Auto-Reply - {credential.email_address}"
    base_campaign_slug = slugify(campaign_name)
    campaign_slug = f"{base_campaign_slug}-{user.id}"
    
    # Ensure slug doesn't exceed max length
    if len(campaign_slug) > 150:
        max_base_length = 150 - len(str(user.id)) - 1
        base_campaign_slug = base_campaign_slug[:max_base_length]
        campaign_slug = f"{base_campaign_slug}-{user.id}"
    
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

    # Keep campaign tied to the canonical list, and clean up any duplicate auto-created campaigns
    campaign_description = f"Auto-created campaign for Gmail auto-replies from {credential.email_address}"
    if (
        gmail_campaign.name != campaign_name or
        gmail_campaign.description != campaign_description or
        gmail_campaign.subscriber_list_id != gmail_list.id or
        not gmail_campaign.is_active
    ):
        gmail_campaign.name = campaign_name
        gmail_campaign.description = campaign_description
        gmail_campaign.subscriber_list = gmail_list
        gmail_campaign.is_active = True
        gmail_campaign.save(update_fields=['name', 'description', 'subscriber_list', 'is_active', 'updated_at'])

    list_description = f"Auto-created list for Gmail account {credential.email_address}"
    _merge_duplicate_lists(gmail_list, user, list_name, list_description)
    _merge_duplicate_campaigns(gmail_campaign, user, campaign_name, campaign_description, gmail_list)
    
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

    def _merge_duplicate_lists(canonical_list, user_obj, target_name, target_description):
        duplicate_lists = List.objects.filter(
            user=user_obj,
            name=target_name,
            description=target_description
        ).exclude(pk=canonical_list.pk)

        for duplicate_list in duplicate_lists:
            subscribers = list(duplicate_list.subscribers.all())
            if subscribers:
                canonical_list.subscribers.add(*subscribers)

            Campaign.objects.filter(subscriber_list=duplicate_list).update(subscriber_list=canonical_list)
            duplicate_list.delete()

    def _merge_duplicate_campaigns(canonical_campaign, user_obj, target_name, target_description, canonical_list):
        duplicate_campaigns = Campaign.objects.filter(
            user=user_obj,
            name=target_name,
            description=target_description
        ).exclude(pk=canonical_campaign.pk)

        if duplicate_campaigns.exists():
            for duplicate_campaign in duplicate_campaigns:
                canonical_campaign.sent_count += duplicate_campaign.sent_count
                canonical_campaign.open_count += duplicate_campaign.open_count
                canonical_campaign.click_count += duplicate_campaign.click_count
                canonical_campaign.bounce_count += duplicate_campaign.bounce_count
                canonical_campaign.unsubscribe_count += duplicate_campaign.unsubscribe_count
                canonical_campaign.complaint_count += duplicate_campaign.complaint_count

                Email.objects.filter(campaign=duplicate_campaign).update(campaign=canonical_campaign)
                duplicate_campaign.email_send_requests.update(campaign=canonical_campaign)

                duplicate_campaign.delete()

            canonical_campaign.subscriber_list = canonical_list
            canonical_campaign.is_active = True
            canonical_campaign.save(update_fields=[
                'subscriber_list',
                'is_active',
                'sent_count',
                'open_count',
                'click_count',
                'bounce_count',
                'unsubscribe_count',
                'complaint_count',
                'updated_at'
            ])
    
    # Create IMAP subscriber list
    # Include user ID in slug to ensure uniqueness across users
    list_name = f"IMAP - {credential.email_address}"
    base_slug = slugify(list_name)
    # Make slug unique per user by including user ID
    unique_slug = f"{base_slug}-{user.id}"
    
    # Ensure slug doesn't exceed max length (150 chars)
    if len(unique_slug) > 150:
        # Truncate base slug if needed, keeping user ID
        max_base_length = 150 - len(str(user.id)) - 1  # -1 for the hyphen
        base_slug = base_slug[:max_base_length]
        unique_slug = f"{base_slug}-{user.id}"
    
    imap_list, created = List.objects.get_or_create(
        user=user,
        slug=unique_slug,
        defaults={
            'name': list_name,
            'description': f"Auto-created list for IMAP account {credential.email_address}"
        }
    )
    
    # Create IMAP campaign
    # Include user ID in campaign slug as well for consistency
    campaign_name = f"IMAP Auto-Reply - {credential.email_address}"
    base_campaign_slug = slugify(campaign_name)
    campaign_slug = f"{base_campaign_slug}-{user.id}"
    
    # Ensure slug doesn't exceed max length
    if len(campaign_slug) > 150:
        max_base_length = 150 - len(str(user.id)) - 1
        base_campaign_slug = base_campaign_slug[:max_base_length]
        campaign_slug = f"{base_campaign_slug}-{user.id}"
    
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

    campaign_description = f"Auto-created campaign for IMAP auto-replies from {credential.email_address}"
    if (
        imap_campaign.name != campaign_name or
        imap_campaign.description != campaign_description or
        imap_campaign.subscriber_list_id != imap_list.id or
        not imap_campaign.is_active
    ):
        imap_campaign.name = campaign_name
        imap_campaign.description = campaign_description
        imap_campaign.subscriber_list = imap_list
        imap_campaign.is_active = True
        imap_campaign.save(update_fields=['name', 'description', 'subscriber_list', 'is_active', 'updated_at'])

    list_description = f"Auto-created list for IMAP account {credential.email_address}"
    _merge_duplicate_lists(imap_list, user, list_name, list_description)
    _merge_duplicate_campaigns(imap_campaign, user, campaign_name, campaign_description, imap_list)
    
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


@api_view(['POST'])
@permission_classes([AllowAny])
def gmail_quick_signup(request):
    """Quick signup with Gmail OAuth for non-authenticated users."""
    try:
        email_address = request.data.get('email', '').strip().lower()
        account_password = request.data.get('account_password', '').strip()
        
        if not email_address or not account_password:
            return Response({'error': 'Email and password are required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email_address).exists():
            return Response({
                'error': 'An account with this email already exists. Please sign in instead.',
                'exists': True
            }, status=400)
        
        # Create new user
        username = email_address.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email_address,
            password=account_password
        )
        
        # Log the user in
        user = authenticate(request, username=username, password=account_password)
        if user:
            login(request, user)
        
        # Return auth URL for Gmail OAuth
        from .services import GmailService
        service = GmailService()
        
        if not service.client_id:
            return Response({
                'error': 'Gmail OAuth is not configured. Please use IMAP instead.',
            }, status=500)
        
        auth_url = service.get_authorization_url(user)
        
        return Response({
            'message': 'Account created successfully!',
            'auth_url': auth_url,
            'redirect_url': '/dashboard/'
        })
    except Exception as e:
        logger.error(f"Error in quick signup with Gmail: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def imap_quick_signup(request):
    """Quick signup with IMAP connection for non-authenticated users."""
    from .imap_service import IMAPService
    
    try:
        email_address = request.data.get('email', '').strip().lower()
        imap_host = request.data.get('host', '').strip()
        imap_port = int(request.data.get('port', 993))
        imap_username = request.data.get('username', '').strip()
        imap_password = request.data.get('password', '').strip()
        use_ssl = request.data.get('use_ssl', True)
        account_password = request.data.get('account_password', '').strip()
        
        if not all([email_address, imap_host, imap_username, imap_password]):
            return Response({'error': 'Missing required IMAP fields'}, status=400)
        
        if not account_password:
            return Response({'error': 'Account password is required'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(email=email_address).exists():
            return Response({
                'error': 'An account with this email already exists. Please sign in instead.',
                'exists': True
            }, status=400)
        
        # Create new user
        username = email_address.split('@')[0]  # Use email prefix as username
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email_address,
            password=account_password
        )
        
        # Log the user in
        user = authenticate(request, username=username, password=account_password)
        if user:
            login(request, user)
        
        # Create IMAP credential
        credential, created = EmailCredential.objects.update_or_create(
            user=user,
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
        connection_success, error_message = service.test_connection(credential)
        if not connection_success:
            credential.is_active = False
            credential.save()
            
            # Check for application-specific password error
            if error_message == 'app_password_required':
                return Response({
                    'error': 'Application-specific password required. Gmail requires an app password for IMAP access.',
                    'error_type': 'app_password_required',
                    'help_links': {
                        'support': 'https://support.google.com/accounts/answer/185833',
                        'app_passwords': 'https://myaccount.google.com/apppasswords'
                    }
                }, status=400)
            
            return Response({
                'error': error_message or 'Failed to connect to IMAP server. Please check your settings.'
            }, status=400)
        
        # Auto-create IMAP list and campaign
        _create_imap_resources(user, credential)
        
        return Response({
            'message': 'Account created and IMAP connected successfully!',
            'credential_id': str(credential.id),
            'redirect_url': '/dashboard/'
        })
    except Exception as e:
        logger.error(f"Error in quick signup with IMAP: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


@login_required
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def imap_connect(request):
    """Save IMAP credentials and connect."""
    from .imap_service import IMAPService
    
    try:
        email_address = request.data.get('email', '').strip().lower()
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
        connection_success, error_message = service.test_connection(credential)
        if not connection_success:
            credential.is_active = False
            credential.save()
            return Response({'error': error_message or 'Failed to connect to IMAP server. Please check your settings.'}, status=400)
        
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
    """Get IMAP emails for the authenticated user with pagination."""
    try:
        credential = EmailCredential.objects.filter(
            user=request.user,
            provider=EmailProvider.IMAP,
            is_active=True
        ).first()
        
        if not credential:
            return Response({'emails': [], 'connected': False, 'error': 'No IMAP account connected'}, status=200)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count - include both received and sent emails
        total_count = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.IMAP
        ).count()
        
        # Get paginated emails - include both received and sent
        emails = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.IMAP
        ).order_by('-received_at')[offset:offset + per_page]
        
        # Get the user's email address for sent email detection
        user_email = credential.email_address.lower() if credential.email_address else ''
        
        email_data = []
        for email in emails:
            # Extract variables from provider_data for template replacement
            provider_data = email.provider_data or {}
            folder = provider_data.get('folder', 'INBOX')
            
            # Determine if this is a sent email
            # Check if user is the sender (from_email or sender_email matches user's email)
            # Or if folder indicates it's a sent folder
            # Or if provider_data has 'sent': True flag (for emails created by send_campaign_email)
            is_sent_email = (
                provider_data.get('sent', False) or  # Check provider_data flag first
                email.from_email.lower() == user_email or 
                (email.sender_email and email.sender_email.lower() == user_email) or
                'sent' in folder.lower() or
                '[gmail]/sent' in folder.lower()
            )
            
            # Initialize original_email variable
            original_email = None
            
            if is_sent_email:
                # For sent emails, recipient is in To header
                # But for emails created by send_campaign_email, use recipient_email from provider_data
                recipient_email = provider_data.get('recipient_email', '')
                if not recipient_email and email.to_emails_list:
                    recipient_email = email.to_emails_list[0]
                
                to_names = provider_data.get('to_names', {})
                recipient_name = to_names.get(recipient_email, '') if recipient_email and recipient_email in to_names else ''
                
                # Parse name into first_name and last_name
                name_parts = recipient_name.strip().split() if recipient_name else []
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Fallback to email prefix if no name found
                if not first_name and recipient_email:
                    first_name = recipient_email.split('@')[0].split('.')[0].title()
                
                # For sent emails created by send_campaign_email, use recipient_email as the to_emails
                # Filter out the user's own email from to_emails if it's there
                display_to_emails = email.to_emails_list.copy() if email.to_emails_list else []
                if recipient_email and recipient_email not in display_to_emails:
                    # If recipient_email is not in to_emails_list, use it as the primary recipient
                    display_to_emails = [recipient_email]
                else:
                    # Filter out user's own email from the list
                    display_to_emails = [e for e in display_to_emails if e.lower() != user_email]
                    # If we filtered everything out but have recipient_email, use that
                    if not display_to_emails and recipient_email:
                        display_to_emails = [recipient_email]
                
                # Look up the original incoming email that triggered this auto-reply
                # First try to use stored original_email_id from provider_data (most reliable)
                original_email = None
                original_email_id = provider_data.get('original_email_id')
                if original_email_id:
                    try:
                        original_email = EmailMessage.objects.filter(
                            id=original_email_id,
                            credential=credential
                        ).first()
                    except Exception:
                        pass
                
                # Fallback: Match by recipient_email = from_email of incoming email, same credential, received before sent email
                if not original_email and recipient_email and email.campaign_email:
                    original_email = EmailMessage.objects.filter(
                        credential=credential,
                        provider=EmailProvider.IMAP,
                        from_email__iexact=recipient_email,
                        received_at__lt=email.received_at,
                        processed=True
                    ).order_by('-received_at').first()
                    
                    # If not found, try matching by subject (removing "Re: " prefix)
                    if not original_email:
                        subject_match = email.subject
                        if subject_match.startswith('Re: '):
                            subject_match = subject_match[4:]
                        original_email = EmailMessage.objects.filter(
                            credential=credential,
                            provider=EmailProvider.IMAP,
                            from_email__iexact=recipient_email,
                            subject__icontains=subject_match,
                            received_at__lt=email.received_at,
                            processed=True
                        ).order_by('-received_at').first()
            else:
                # For inbox emails, recipient is in From/Sender header
                recipient_email = email.from_email
                recipient_name = provider_data.get('from_name', '') or provider_data.get('sender_name', '')
                
                # Parse name into first_name and last_name
                name_parts = recipient_name.strip().split() if recipient_name else []
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Fallback to email prefix if no name found
                if not first_name:
                    first_name = recipient_email.split('@')[0].split('.')[0].title()
                
                display_to_emails = email.to_emails_list
            
            # Prepare original email data if available
            original_email_data = None
            if is_sent_email and original_email:
                original_provider_data = original_email.provider_data or {}
                original_email_data = {
                    'id': str(original_email.id),
                    'subject': original_email.subject,
                    'from_email': original_email.from_email,
                    'from_name': original_provider_data.get('from_name', '') or original_provider_data.get('sender_name', ''),
                    'body_text': original_email.body_text or '',
                    'body_html': original_email.body_html or '',
                    'received_at': original_email.received_at.isoformat(),
                }
            
            email_data.append({
                'id': str(email.id),
                'subject': email.subject,
                'from_email': email.from_email,
                'to_emails': display_to_emails,
                'cc_emails': email.cc_emails_list,
                'sender_email': email.sender_email,
                'body_text': email.body_text[:500] if email.body_text else '',
                'body_html': email.body_html[:1000] if email.body_html else '',
                'received_at': email.received_at.isoformat(),
                'is_sent_email': is_sent_email,  # Flag to indicate this is a sent email
                'campaign_email_id': str(email.campaign_email.id) if email.campaign_email else None,
                'campaign_email_subject': email.campaign_email.subject if email.campaign_email else None,
                'campaign_email_body_html': email.campaign_email.body_html if email.campaign_email else None,
                'campaign_email_body_text': email.campaign_email.body_text if email.campaign_email else None,
                'original_email': original_email_data,  # Original incoming email that triggered the reply
                # Template variables for replacement
                'template_variables': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': recipient_email,
                    'subject': email.subject,
                }
            })
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        return Response({
            'emails': email_data,
            'connected': True,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        })
    except Exception as e:
        logger.error(f"Error fetching IMAP emails: {str(e)}")
        return Response({'error': str(e)}, status=500)

