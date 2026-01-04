from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import List, Subscriber, CustomField, CustomValue


class SubscriberInline(admin.TabularInline):
    """Inline admin for subscribers within a list."""
    model = Subscriber.lists.through
    extra = 0
    fields = ('subscriber', 'subscriber_email', 'is_active', 'confirmed')
    readonly_fields = ('subscriber_email',)
    
    def subscriber_email(self, obj):
        """Display subscriber email."""
        return obj.subscriber.email if obj.subscriber else '-'
    subscriber_email.short_description = 'Email'


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    """Admin interface for Subscriber Lists - Organize subscribers into groups."""
    list_display = ('name', 'user', 'subscribers_count', 'active_subscribers_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'user')
    search_fields = ('name', 'description', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'subscribers_count', 'active_subscribers_count')
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    prepopulated_fields = {"slug": ("name",)}
    
    fieldsets = (
        ('List Information', {
            'fields': ('id', 'user', 'name', 'slug', 'description')
        }),
        ('Statistics', {
            'fields': ('subscribers_count', 'active_subscribers_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subscribers_count(self, obj):
        """Display total number of subscribers."""
        count = obj.subscribers.count()
        return format_html('<strong style="color: #007bff;">{}</strong>', count)
    subscribers_count.short_description = 'Total Subscribers'
    
    def active_subscribers_count(self, obj):
        """Display number of active subscribers."""
        count = obj.subscribers.filter(is_active=True).count()
        return format_html('<strong style="color: #28a745;">{}</strong>', count)
    active_subscribers_count.short_description = 'Active Subscribers'


class CustomValueInline(admin.TabularInline):
    """Inline admin for custom field values."""
    model = CustomValue
    extra = 0
    fields = ('field', 'value')
    readonly_fields = ()


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Admin interface for Subscribers - Email subscribers and their information."""
    list_display = ('email', 'full_name_display', 'is_active_badge', 'confirmed_badge', 'lists_count', 'created_at', 'updated_at')
    list_filter = ('is_active', 'confirmed', 'created_at', 'updated_at')
    search_fields = ('email', 'first_name', 'last_name', 'uuid')
    readonly_fields = ('id', 'uuid', 'created_at', 'updated_at', 'lists_display', 'custom_values_display')
    filter_horizontal = ('lists',)
    date_hierarchy = 'created_at'
    inlines = [CustomValueInline]
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('id', 'uuid', 'email', 'first_name', 'last_name')
        }),
        ('Status', {
            'fields': ('is_active', 'confirmed', 'confirmation_sent_at', 'confirmed_at')
        }),
        ('Lists', {
            'fields': ('lists', 'lists_display')
        }),
        ('Custom Values', {
            'fields': ('custom_values_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name_display(self, obj):
        """Display full name or email if no name."""
        if obj.full_name:
            return format_html('<strong>{}</strong>', obj.full_name)
        return format_html('<span style="color: #999;">-</span>')
    full_name_display.short_description = 'Name'
    
    def is_active_badge(self, obj):
        """Display active status with badge."""
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">ACTIVE</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">INACTIVE</span>')
    is_active_badge.short_description = 'Status'
    is_active_badge.boolean = True
    
    def confirmed_badge(self, obj):
        """Display confirmation status with badge."""
        if obj.confirmed:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">✓ CONFIRMED</span>')
        return format_html('<span style="background: #ffc107; color: white; padding: 3px 8px; border-radius: 3px;">⚠ PENDING</span>')
    confirmed_badge.short_description = 'Confirmed'
    confirmed_badge.boolean = True
    
    def lists_count(self, obj):
        """Display number of lists the subscriber belongs to."""
        count = obj.lists.count()
        return format_html('<strong style="color: #007bff;">{}</strong>', count)
    lists_count.short_description = 'Lists'
    
    def lists_display(self, obj):
        """Display all lists the subscriber belongs to."""
        lists = obj.lists.all()
        if lists:
            list_names = ', '.join([list.name for list in lists])
            return format_html('<span>{}</span>', list_names)
        return format_html('<span style="color: #999;">No lists</span>')
    lists_display.short_description = 'Lists'
    
    def custom_values_display(self, obj):
        """Display custom field values."""
        values = obj.custom_values.all()
        if values:
            html = '<ul style="margin: 0; padding-left: 20px;">'
            for value in values:
                html += f'<li><strong>{value.field.name}:</strong> {value.value}</li>'
            html += '</ul>'
            return format_html(html)
        return format_html('<span style="color: #999;">No custom values</span>')
    custom_values_display.short_description = 'Custom Values'
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'confirm_subscribers', 'unconfirm_subscribers']
    
    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriber(s) activated.')
    activate_subscribers.short_description = 'Activate selected subscribers'
    
    def deactivate_subscribers(self, request, queryset):
        """Deactivate selected subscribers."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriber(s) deactivated.')
    deactivate_subscribers.short_description = 'Deactivate selected subscribers'
    
    def confirm_subscribers(self, request, queryset):
        """Confirm selected subscribers."""
        from django.utils import timezone
        updated = queryset.update(confirmed=True, confirmed_at=timezone.now())
        self.message_user(request, f'{updated} subscriber(s) confirmed.')
    confirm_subscribers.short_description = 'Confirm selected subscribers'
    
    def unconfirm_subscribers(self, request, queryset):
        """Unconfirm selected subscribers."""
        updated = queryset.update(confirmed=False, confirmed_at=None)
        self.message_user(request, f'{updated} subscriber(s) unconfirmed.')
    unconfirm_subscribers.short_description = 'Unconfirm selected subscribers'


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    """Admin interface for Custom Fields - User-defined fields for subscribers."""
    list_display = ('name', 'key', 'user', 'values_count', 'created_display')
    list_filter = ('user',)
    search_fields = ('name', 'key', 'user__username', 'user__email')
    readonly_fields = ('id', 'values_count', 'created_display')
    raw_id_fields = ('user',)
    prepopulated_fields = {"key": ("name",)}
    
    fieldsets = (
        ('Field Information', {
            'fields': ('id', 'user', 'name', 'key')
        }),
        ('Statistics', {
            'fields': ('values_count', 'created_display'),
            'classes': ('collapse',)
        }),
    )
    
    def values_count(self, obj):
        """Display number of values for this field."""
        count = obj.values.count()
        return format_html('<strong style="color: #007bff;">{}</strong>', count)
    values_count.short_description = 'Values Count'
    
    def created_display(self, obj):
        """Display when this field was created (if available)."""
        # CustomField doesn't have created_at, but we can show the first value's creation
        first_value = obj.values.first()
        if first_value:
            return format_html('<span style="color: #666;">First value: {}</span>', first_value.id)
        return format_html('<span style="color: #999;">No values yet</span>')
    created_display.short_description = 'Usage'


@admin.register(CustomValue)
class CustomValueAdmin(admin.ModelAdmin):
    """Admin interface for Custom Values - Values for custom fields."""
    list_display = ('field', 'subscriber', 'value_preview', 'subscriber_email')
    list_filter = ('field', 'field__user')
    search_fields = ('field__name', 'subscriber__email', 'subscriber__first_name', 'subscriber__last_name', 'value')
    readonly_fields = ('id',)
    raw_id_fields = ('field', 'subscriber')
    
    fieldsets = (
        ('Value Information', {
            'fields': ('id', 'field', 'subscriber', 'value')
        }),
    )
    
    def subscriber_email(self, obj):
        """Display subscriber email."""
        return obj.subscriber.email if obj.subscriber else '-'
    subscriber_email.short_description = 'Subscriber Email'
    
    def value_preview(self, obj):
        """Display value preview."""
        if len(obj.value) > 50:
            return format_html('<span title="{}">{}</span>', obj.value, obj.value[:50] + '...')
        return obj.value
    value_preview.short_description = 'Value'

