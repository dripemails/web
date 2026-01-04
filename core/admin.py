from django.contrib import admin
from django.utils.html import format_html
from .models import BlogPost, ForumPost, SuccessStory, EmailLog


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for Blog Posts - Content management for blog articles."""
    list_display = ('title', 'date', 'published', 'slug', 'content_preview')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'summary', 'content')
    list_filter = ('published', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('date',)
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'summary', 'content')
        }),
        ('Publishing', {
            'fields': ('published', 'date')
        }),
    )
    
    def content_preview(self, obj):
        """Show a preview of the content."""
        return format_html('<span style="color: #666;">{}</span>', obj.summary[:100] + '...' if len(obj.summary) > 100 else obj.summary)
    content_preview.short_description = 'Summary'


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    """Admin interface for Forum Posts - User-generated forum content."""
    list_display = ('title', 'user', 'created_at', 'updated_at', 'content_preview')
    search_fields = ('title', 'content', 'user__username', 'user__email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Post Information', {
            'fields': ('user', 'title', 'content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show a preview of the content."""
        return format_html('<span style="color: #666;">{}</span>', obj.content[:100] + '...' if len(obj.content) > 100 else obj.content)
    content_preview.short_description = 'Content Preview'


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    """Admin interface for Success Stories - Customer testimonials and case studies."""
    list_display = ('company_name', 'contact_name', 'contact_email', 'approved', 'submitted_at', 'logo_preview')
    search_fields = ('company_name', 'contact_name', 'contact_email', 'story')
    list_filter = ('approved', 'submitted_at')
    list_editable = ('approved',)
    readonly_fields = ('submitted_at', 'logo_preview')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'logo', 'logo_preview')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email')
        }),
        ('Story Content', {
            'fields': ('story',)
        }),
        ('Moderation', {
            'fields': ('approved', 'submitted_at')
        }),
    )
    
    def logo_preview(self, obj):
        """Show logo preview if available."""
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.logo.url)
        return format_html('<span style="color: #999;">No logo</span>')
    logo_preview.short_description = 'Logo'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin interface for Email Logs - SMTP server email metadata and processing status."""
    list_display = ('subject', 'sender', 'recipient', 'received_at', 'processed', 'is_spam_badge', 'size_display')
    search_fields = ('subject', 'sender', 'recipient', 'message_id', 'body')
    list_filter = ('processed', 'received_at')
    readonly_fields = ('received_at', 'is_spam_badge', 'size_display', 'body_preview')
    date_hierarchy = 'received_at'
    list_per_page = 50
    
    fieldsets = (
        ('Email Information', {
            'fields': ('sender', 'recipient', 'subject', 'message_id')
        }),
        ('Content', {
            'fields': ('body', 'body_preview')
        }),
        ('Metadata', {
            'fields': ('received_at', 'size_display', 'processed', 'is_spam_badge', 'error_message')
        }),
    )
    
    def is_spam_badge(self, obj):
        """Display spam status with colored badge."""
        if obj.is_spam:
            return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">SPAM</span>')
        return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">OK</span>')
    is_spam_badge.short_description = 'Spam Status'
    is_spam_badge.boolean = True
    
    def size_display(self, obj):
        """Display file size in human-readable format."""
        if obj.size < 1024:
            return f"{obj.size} B"
        elif obj.size < 1024 * 1024:
            return f"{obj.size / 1024:.1f} KB"
        else:
            return f"{obj.size / (1024 * 1024):.1f} MB"
    size_display.short_description = 'Size'
    
    def body_preview(self, obj):
        """Show a preview of the email body."""
        preview = obj.body[:500] + '...' if len(obj.body) > 500 else obj.body
        return format_html('<pre style="max-height: 200px; overflow: auto; background: #f5f5f5; padding: 10px;">{}</pre>', preview)
    body_preview.short_description = 'Body Preview'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        """Mark selected emails as processed."""
        updated = queryset.update(processed=True)
        self.message_user(request, f'{updated} email(s) marked as processed.')
    mark_as_processed.short_description = 'Mark selected emails as processed'
    
    def mark_as_unprocessed(self, request, queryset):
        """Mark selected emails as unprocessed."""
        updated = queryset.update(processed=False)
        self.message_user(request, f'{updated} email(s) marked as unprocessed.')
    mark_as_unprocessed.short_description = 'Mark selected emails as unprocessed'
