from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Campaign, Email, EmailEvent, EmailSendRequest, EmailAIAnalysis


class EmailInline(admin.TabularInline):
    """Inline admin for emails within a campaign."""
    model = Email
    extra = 0
    fields = ('subject', 'order', 'wait_time', 'wait_unit', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('order',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaigns - Email drip campaign sequences."""
    list_display = ('name', 'user', 'is_active', 'emails_count', 'subscriber_list', 'sent_count', 'open_rate_display', 'click_rate_display', 'created_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'emails_count', 'open_rate_display', 'click_rate_display')
    raw_id_fields = ('user', 'subscriber_list')
    date_hierarchy = 'created_at'
    inlines = [EmailInline]
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('id', 'user', 'name', 'slug', 'description', 'subscriber_list')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('sent_count', 'open_count', 'click_count', 'emails_count', 'open_rate_display', 'click_rate_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def emails_count(self, obj):
        """Display the number of emails in the campaign."""
        return obj.emails.count()
    emails_count.short_description = 'Emails'
    
    def open_rate_display(self, obj):
        """Display open rate as a percentage with color coding."""
        rate = float(obj.open_rate) if obj.open_rate else 0.0
        color = '#28a745' if rate >= 20 else '#ffc107' if rate >= 10 else '#dc3545'
        rate_str = f'{rate:.1f}%'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, rate_str)
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        """Display click rate as a percentage with color coding."""
        rate = float(obj.click_rate) if obj.click_rate else 0.0
        color = '#28a745' if rate >= 5 else '#ffc107' if rate >= 2 else '#dc3545'
        rate_str = f'{rate:.1f}%'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, rate_str)
    click_rate_display.short_description = 'Click Rate'
    
    actions = ['activate_campaigns', 'deactivate_campaigns']
    
    def activate_campaigns(self, request, queryset):
        """Activate selected campaigns."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} campaign(s) activated.')
    activate_campaigns.short_description = 'Activate selected campaigns'
    
    def deactivate_campaigns(self, request, queryset):
        """Deactivate selected campaigns."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} campaign(s) deactivated.')
    deactivate_campaigns.short_description = 'Deactivate selected campaigns'


class EmailEventInline(admin.TabularInline):
    """Inline admin for email events."""
    model = EmailEvent
    extra = 0
    fields = ('event_type', 'subscriber_email', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    """Admin interface for Emails - Individual emails within campaigns."""
    list_display = ('subject', 'campaign', 'order', 'wait_time_display', 'footer', 'created_at')
    list_filter = ('wait_unit', 'created_at', 'campaign')
    search_fields = ('subject', 'body_html', 'body_text', 'campaign__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'wait_time_display', 'body_html_preview', 'body_text_preview')
    raw_id_fields = ('campaign', 'footer')
    date_hierarchy = 'created_at'
    inlines = [EmailEventInline]
    
    fieldsets = (
        ('Email Information', {
            'fields': ('id', 'campaign', 'subject', 'order')
        }),
        ('Content', {
            'fields': ('body_html', 'body_html_preview', 'body_text', 'body_text_preview')
        }),
        ('Scheduling', {
            'fields': ('wait_time', 'wait_unit', 'wait_time_display')
        }),
        ('Footer', {
            'fields': ('footer',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def wait_time_display(self, obj):
        """Display wait time in human-readable format."""
        return obj.wait_time_display
    wait_time_display.short_description = 'Wait Time'
    
    def body_html_preview(self, obj):
        """Show a preview of the HTML body."""
        preview = obj.body_html[:300] + '...' if len(obj.body_html) > 300 else obj.body_html
        return format_html('<div style="max-height: 200px; overflow: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">{}</div>', preview)
    body_html_preview.short_description = 'HTML Preview'
    
    def body_text_preview(self, obj):
        """Show a preview of the text body."""
        preview = obj.body_text[:300] + '...' if len(obj.body_text) > 300 else obj.body_text
        return format_html('<pre style="max-height: 200px; overflow: auto; background: #f5f5f5; padding: 10px;">{}</pre>', preview)
    body_text_preview.short_description = 'Text Preview'


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    """Admin interface for Email Events - Track opens, clicks, bounces, etc."""
    list_display = ('event_type_badge', 'email', 'subscriber_email', 'link_clicked', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('subscriber_email', 'email__subject', 'email__campaign__name', 'link_clicked', 'user_agent')
    readonly_fields = ('id', 'created_at')
    raw_id_fields = ('email',)
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'email', 'subscriber_email', 'event_type')
        }),
        ('Event Details', {
            'fields': ('link_clicked', 'user_agent', 'ip_address')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def event_type_badge(self, obj):
        """Display event type with colored badge."""
        colors = {
            'sent': '#007bff',
            'opened': '#28a745',
            'clicked': '#17a2b8',
            'bounced': '#dc3545',
            'complained': '#ffc107',
            'unsubscribed': '#6c757d',
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html('<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>', color, obj.get_event_type_display().upper())
    event_type_badge.short_description = 'Event Type'


@admin.register(EmailSendRequest)
class EmailSendRequestAdmin(admin.ModelAdmin):
    """Admin interface for Email Send Requests - Individual email send queue items."""
    list_display = ('email', 'subscriber_email', 'status_badge', 'scheduled_for', 'sent_at', 'user', 'created_at')
    list_filter = ('status', 'scheduled_for', 'sent_at', 'created_at')
    search_fields = ('subscriber_email', 'email__subject', 'email__campaign__name', 'user__username', 'error_message')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'campaign', 'email', 'subscriber')
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('Request Information', {
            'fields': ('id', 'user', 'campaign', 'email', 'subscriber', 'subscriber_email')
        }),
        ('Status', {
            'fields': ('status', 'scheduled_for', 'sent_at', 'error_message')
        }),
        ('Variables', {
            'fields': ('variables',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': '#ffc107',
            'queued': '#17a2b8',
            'sent': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html('<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>', color, obj.get_status_display().upper())
    status_badge.short_description = 'Status'
    
    actions = ['retry_failed_requests']
    
    def retry_failed_requests(self, request, queryset):
        """Reset failed requests to pending status."""
        failed = queryset.filter(status='failed')
        updated = failed.update(status='pending', error_message='')
        self.message_user(request, f'{updated} failed request(s) reset to pending.')
    retry_failed_requests.short_description = 'Retry failed requests'


@admin.register(EmailAIAnalysis)
class EmailAIAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for Email AI Analysis - AI-generated content and topic analysis."""
    list_display = ('email', 'generation_model', 'topic_analysis_count', 'created_at', 'updated_at')
    list_filter = ('generation_model', 'created_at', 'updated_at')
    search_fields = ('email__subject', 'email__campaign__name', 'generated_subject', 'generation_prompt')
    readonly_fields = ('id', 'created_at', 'updated_at', 'topics_display', 'dominant_topics_display')
    raw_id_fields = ('email',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Email Information', {
            'fields': ('id', 'email')
        }),
        ('AI-Generated Content', {
            'fields': ('generated_subject', 'generated_body_html', 'generation_prompt', 'generation_model')
        }),
        ('Topic Analysis', {
            'fields': ('topics_json', 'topics_display', 'dominant_topics', 'dominant_topics_display', 'topic_analysis_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def topics_display(self, obj):
        """Display topics in a readable format."""
        if obj.topics_json:
            topics = ', '.join([str(t) for t in obj.topics_json[:10]])
            return format_html('<span style="color: #666;">{}</span>', topics)
        return format_html('<span style="color: #999;">No topics</span>')
    topics_display.short_description = 'Topics'
    
    def dominant_topics_display(self, obj):
        """Display dominant topics."""
        if obj.dominant_topics:
            topics = ', '.join([str(t) for t in obj.dominant_topics])
            return format_html('<strong style="color: #007bff;">{}</strong>', topics)
        return format_html('<span style="color: #999;">No dominant topics</span>')
    dominant_topics_display.short_description = 'Dominant Topics'

