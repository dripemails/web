from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import EmailCredential, EmailMessage, EmailProvider


@admin.register(EmailCredential)
class EmailCredentialAdmin(admin.ModelAdmin):
    """Admin interface for Email Credentials - OAuth/IMAP credentials for email providers."""
    list_display = ('user', 'provider_badge', 'email_address', 'is_active', 'sync_enabled', 'last_sync_at', 'created_at')
    list_filter = ('provider', 'is_active', 'sync_enabled', 'created_at', 'last_sync_at')
    search_fields = ('user__username', 'user__email', 'email_address')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_sync_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Credential Information', {
            'fields': ('id', 'user', 'provider', 'email_address')
        }),
        ('Status', {
            'fields': ('is_active', 'sync_enabled', 'last_sync_at')
        }),
        ('OAuth Tokens (Gmail/Outlook)', {
            'fields': ('access_token', 'refresh_token', 'token_expiry'),
            'classes': ('collapse',)
        }),
        ('IMAP Settings', {
            'fields': ('imap_host', 'imap_port', 'imap_username', 'imap_password', 'imap_use_ssl'),
            'classes': ('collapse',)
        }),
        ('Provider Settings', {
            'fields': ('provider_settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def provider_badge(self, obj):
        """Display provider with colored badge."""
        colors = {
            EmailProvider.GMAIL: '#4285f4',
            EmailProvider.OUTLOOK: '#0078d4',
            EmailProvider.IMAP: '#6c757d',
        }
        color = colors.get(obj.provider, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_provider_display().upper()
        )
    provider_badge.short_description = 'Provider'


@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    """Admin interface for Email Messages - Fetched emails from providers."""
    list_display = ('subject_preview', 'from_email', 'provider_badge', 'received_at', 'processed', 'user')
    list_filter = ('provider', 'processed', 'received_at', 'fetched_at', 'credential')
    search_fields = ('subject', 'from_email', 'to_emails', 'sender_email', 'user__username', 'provider_message_id')
    readonly_fields = ('id', 'fetched_at', 'provider_data')
    raw_id_fields = ('user', 'credential', 'campaign_email')
    date_hierarchy = 'received_at'
    list_per_page = 100
    
    fieldsets = (
        ('Message Information', {
            'fields': ('id', 'user', 'credential', 'provider', 'provider_message_id', 'thread_id')
        }),
        ('Email Headers', {
            'fields': ('subject', 'from_email', 'to_emails', 'cc_emails', 'bcc_emails', 'sender_email', 'reply_to')
        }),
        ('Email Content', {
            'fields': ('body_text', 'body_html'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('received_at', 'fetched_at', 'processed', 'campaign_email')
        }),
        ('Provider Data', {
            'fields': ('provider_data',),
            'classes': ('collapse',)
        }),
    )
    
    def subject_preview(self, obj):
        """Display subject with truncation."""
        subject = obj.subject or '(No Subject)'
        if len(subject) > 50:
            return format_html('<span title="{}">{}</span>', subject, subject[:50] + '...')
        return subject
    subject_preview.short_description = 'Subject'
    
    def provider_badge(self, obj):
        """Display provider with colored badge."""
        colors = {
            EmailProvider.GMAIL: '#4285f4',
            EmailProvider.OUTLOOK: '#0078d4',
            EmailProvider.IMAP: '#6c757d',
        }
        color = colors.get(obj.provider, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_provider_display().upper()
        )
    provider_badge.short_description = 'Provider'

