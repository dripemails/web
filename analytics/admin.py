from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, EmailFooter


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for User Profiles - Extended user settings and preferences."""
    list_display = ('user', 'has_verified_promo', 'send_without_unsubscribe', 'spf_verified_badge', 'timezone', 'country')
    list_filter = ('has_verified_promo', 'send_without_unsubscribe', 'spf_verified', 'country', 'timezone')
    search_fields = ('user__username', 'user__email', 'promo_url', 'city', 'state', 'country')
    readonly_fields = ('spf_verified_badge', 'spf_last_checked', 'address_display')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Promo Verification', {
            'fields': ('has_verified_promo', 'promo_url')
        }),
        ('Email Settings', {
            'fields': ('send_without_unsubscribe', 'custom_footer_html', 'timezone')
        }),
        ('Address Information', {
            'description': 'Required for CAN-SPAM, GDPR compliance in email footers',
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'address_display')
        }),
        ('SPF Verification', {
            'description': 'SPF record verification for email deliverability',
            'fields': ('spf_verified', 'spf_verified_badge', 'spf_last_checked', 'spf_record', 'spf_missing_includes'),
            'classes': ('collapse',)
        }),
    )
    
    def spf_verified_badge(self, obj):
        """Display SPF verification status with badge."""
        if obj.spf_verified:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">✓ VERIFIED</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">✗ NOT VERIFIED</span>')
    spf_verified_badge.short_description = 'SPF Status'
    spf_verified_badge.boolean = True
    
    def address_display(self, obj):
        """Display formatted address."""
        address_parts = []
        if obj.address_line1:
            address_parts.append(obj.address_line1)
        if obj.address_line2:
            address_parts.append(obj.address_line2)
        if obj.city:
            address_parts.append(obj.city)
        if obj.state:
            address_parts.append(obj.state)
        if obj.postal_code:
            address_parts.append(obj.postal_code)
        if obj.country:
            address_parts.append(obj.country)
        
        if address_parts:
            formatted = ', '.join(address_parts)
            return format_html('<div style="line-height: 1.6;">{}</div>', formatted.replace(', ', '<br>'))
        return format_html('<span style="color: #999;">No address provided</span>')
    address_display.short_description = 'Formatted Address'
    
    actions = ['verify_spf_for_selected', 'unverify_spf_for_selected']
    
    def verify_spf_for_selected(self, request, queryset):
        """Manually mark SPF as verified for selected profiles."""
        updated = queryset.update(spf_verified=True)
        self.message_user(request, f'{updated} profile(s) marked as SPF verified.')
    verify_spf_for_selected.short_description = 'Mark SPF as verified'
    
    def unverify_spf_for_selected(self, request, queryset):
        """Mark SPF as unverified for selected profiles."""
        updated = queryset.update(spf_verified=False)
        self.message_user(request, f'{updated} profile(s) marked as SPF unverified.')
    unverify_spf_for_selected.short_description = 'Mark SPF as unverified'


@admin.register(EmailFooter)
class EmailFooterAdmin(admin.ModelAdmin):
    """Admin interface for Email Footers - Custom email footer templates."""
    list_display = ('name', 'user', 'is_default_badge', 'html_preview', 'created_at', 'updated_at')
    list_filter = ('is_default', 'created_at', 'updated_at', 'user')
    search_fields = ('name', 'html_content', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'html_preview')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Footer Information', {
            'fields': ('user', 'name', 'is_default')
        }),
        ('Content', {
            'fields': ('html_content', 'html_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_default_badge(self, obj):
        """Display default status with badge."""
        if obj.is_default:
            return format_html('<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">DEFAULT</span>')
        return format_html('<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">-</span>')
    is_default_badge.short_description = 'Default'
    is_default_badge.boolean = True
    
    def html_preview(self, obj):
        """Show a preview of the HTML footer."""
        if obj.html_content:
            # Limit preview length
            preview = obj.html_content[:500] + '...' if len(obj.html_content) > 500 else obj.html_content
            return format_html('<div style="max-height: 300px; overflow: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9; font-size: 12px;">{}</div>', preview)
        return format_html('<span style="color: #999;">No content</span>')
    html_preview.short_description = 'HTML Preview'
    
    actions = ['set_as_default', 'remove_default']
    
    def set_as_default(self, request, queryset):
        """Set selected footer as default (only one per user)."""
        count = 0
        for footer in queryset:
            # Ensure only one default per user
            EmailFooter.objects.filter(user=footer.user, is_default=True).update(is_default=False)
            footer.is_default = True
            footer.save()
            count += 1
        self.message_user(request, f'{count} footer(s) set as default.')
    set_as_default.short_description = 'Set as default footer'
    
    def remove_default(self, request, queryset):
        """Remove default status from selected footers."""
        updated = queryset.update(is_default=False)
        self.message_user(request, f'{updated} footer(s) removed from default.')
    remove_default.short_description = 'Remove default status'

