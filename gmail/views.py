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
    import uuid
    
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
    
    # Additional check in case of collision (shouldn't happen with user ID, but just in case)
    if Campaign.objects.filter(user=user, slug=campaign_slug).exists():
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
    
    # Additional check in case of collision (shouldn't happen with user ID, but just in case)
    if Campaign.objects.filter(user=user, slug=campaign_slug).exists():
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


@api_view(['POST'])
@permission_classes([AllowAny])
def gmail_quick_signup(request):
    """Quick signup with Gmail OAuth for non-authenticated users."""
    try:
        email_address = request.data.get('email', '').strip()
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
        email_address = request.data.get('email', '').strip()
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
        
        # Get total count
        total_count = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.IMAP
        ).count()
        
        # Get paginated emails
        emails = EmailMessage.objects.filter(
            credential=credential,
            provider=EmailProvider.IMAP
        ).order_by('-received_at')[offset:offset + per_page]
        
        email_data = []
        for email in emails:
            # Extract variables from provider_data for template replacement
            provider_data = email.provider_data or {}
            folder = provider_data.get('folder', 'INBOX')
            
            # Determine recipient info based on folder
            if folder == 'Sent':
                # For sent emails, recipient is in To header
                to_names = provider_data.get('to_names', {})
                recipient_email = email.to_emails_list[0] if email.to_emails_list else email.from_email
                recipient_name = to_names.get(recipient_email, '') if recipient_email in to_names else ''
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

