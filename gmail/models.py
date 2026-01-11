from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import uuid
import json


class EmailProvider(models.TextChoices):
    """Supported email providers."""
    GMAIL = 'gmail', _('Gmail')
    OUTLOOK = 'outlook', _('Outlook')
    IMAP = 'imap', _('IMAP')


class EmailCredential(models.Model):
    """Stores OAuth/authentication credentials for email providers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_credentials', verbose_name=_('User'))
    provider = models.CharField(_('Provider'), max_length=20, choices=EmailProvider.choices, default=EmailProvider.GMAIL)
    
    # OAuth tokens (for Gmail/Outlook)
    access_token = models.TextField(_('Access Token'), blank=True)
    refresh_token = models.TextField(_('Refresh Token'), blank=True)
    token_expiry = models.DateTimeField(_('Token Expiry'), null=True, blank=True)
    
    # IMAP credentials (for IMAP provider)
    imap_host = models.CharField(_('IMAP Host'), max_length=255, blank=True)
    imap_port = models.IntegerField(_('IMAP Port'), null=True, blank=True)
    imap_username = models.CharField(_('IMAP Username'), max_length=255, blank=True)
    imap_password = models.TextField(_('IMAP Password'), blank=True)
    imap_use_ssl = models.BooleanField(_('Use SSL'), default=True)
    
    # Common fields
    email_address = models.EmailField(_('Email Address'), blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    last_sync_at = models.DateTimeField(_('Last Sync At'), null=True, blank=True)
    sync_enabled = models.BooleanField(_('Sync Enabled'), default=True)
    
    # Additional provider-specific settings stored as JSON
    provider_settings = models.JSONField(_('Provider Settings'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Email Credential')
        verbose_name_plural = _('Email Credentials')
        unique_together = [['user', 'provider', 'email_address']]
        indexes = [
            models.Index(fields=['user', 'provider', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()} - {self.email_address}"
    
    @property
    def is_oauth_provider(self):
        """Check if provider uses OAuth."""
        return self.provider in [EmailProvider.GMAIL, EmailProvider.OUTLOOK]
    
    @property
    def is_imap_provider(self):
        """Check if provider uses IMAP."""
        return self.provider == EmailProvider.IMAP


class EmailMessage(models.Model):
    """Stores fetched emails from any provider."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_messages', verbose_name=_('User'))
    credential = models.ForeignKey(EmailCredential, on_delete=models.CASCADE, related_name='email_messages', verbose_name=_('Credential'))
    provider = models.CharField(_('Provider'), max_length=20, choices=EmailProvider.choices, default=EmailProvider.GMAIL)
    
    # Provider-specific message ID
    provider_message_id = models.CharField(_('Provider Message ID'), max_length=255, db_index=True)
    thread_id = models.CharField(_('Thread ID'), max_length=255, blank=True, db_index=True)
    
    # Email headers
    subject = models.CharField(_('Subject'), max_length=500, blank=True)
    from_email = models.EmailField(_('From Email'))
    to_emails = models.TextField(_('To Emails'), help_text=_('Comma-separated email addresses'))
    cc_emails = models.TextField(_('CC Emails'), blank=True, help_text=_('Comma-separated email addresses'))
    bcc_emails = models.TextField(_('BCC Emails'), blank=True, help_text=_('Comma-separated email addresses'))
    sender_email = models.EmailField(_('Sender Email'), blank=True)
    reply_to = models.EmailField(_('Reply To'), blank=True)
    
    # Email content
    body_text = models.TextField(_('Body Text'), blank=True)
    body_html = models.TextField(_('Body HTML'), blank=True)
    
    # Metadata
    received_at = models.DateTimeField(_('Received At'), db_index=True)
    fetched_at = models.DateTimeField(_('Fetched At'), auto_now_add=True)
    processed = models.BooleanField(_('Processed'), default=False)
    
    # Link to campaign email if auto-reply was sent
    campaign_email = models.ForeignKey('campaigns.Email', on_delete=models.SET_NULL, null=True, blank=True, related_name='email_messages', verbose_name=_('Campaign Email'))
    
    # Additional provider-specific data stored as JSON
    provider_data = models.JSONField(_('Provider Data'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Email Message')
        verbose_name_plural = _('Email Messages')
        ordering = ['-received_at']
        unique_together = [['credential', 'provider_message_id']]
        indexes = [
            models.Index(fields=['user', 'provider', '-received_at']),
            models.Index(fields=['credential', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
            models.Index(fields=['thread_id']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.from_email} ({self.get_provider_display()})"
    
    @property
    def to_emails_list(self):
        """Return to_emails as a list."""
        return [e.strip() for e in self.to_emails.split(',') if e.strip()]
    
    @property
    def cc_emails_list(self):
        """Return cc_emails as a list."""
        return [e.strip() for e in self.cc_emails.split(',') if e.strip()] if self.cc_emails else []
    
    @property
    def bcc_emails_list(self):
        """Return bcc_emails as a list."""
        return [e.strip() for e in self.bcc_emails.split(',') if e.strip()] if self.bcc_emails else []
    
    def get_recipient_emails(self):
        """Get all recipient emails (to, cc, bcc)."""
        recipients = set(self.to_emails_list)
        recipients.update(self.cc_emails_list)
        recipients.update(self.bcc_emails_list)
        return list(recipients)
