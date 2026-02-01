from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from subscribers.models import List, Subscriber
import uuid

class Campaign(models.Model):
    """Campaign model representing an email sequence."""
    FREQUENCY_CHOICES = [
        ('seconds', _('Seconds')),
        ('minutes', _('Minutes')),
        ('hours', _('Hours')),
        ('days', _('Days')),
        ('weeks', _('Weeks')),
        ('months', _('Months')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    slug = models.SlugField(max_length=150, unique=True)
    subscriber_list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='campaigns', verbose_name=_('Subscriber List'), null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    sent_count = models.IntegerField(_('Sent Count'), default=0)
    open_count = models.IntegerField(_('Open Count'), default=0)
    click_count = models.IntegerField(_('Click Count'), default=0)
    bounce_count = models.IntegerField(_('Bounce Count'), default=0)
    unsubscribe_count = models.IntegerField(_('Unsubscribe Count'), default=0)
    complaint_count = models.IntegerField(_('Complaint Count'), default=0)
    
    class Meta:
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness by appending a UUID segment if needed
            if Campaign.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def emails_count(self):
        return self.emails.count()
    
    @property
    def open_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.open_count / self.sent_count) * 100, 2)
    
    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return round((self.click_count / self.sent_count) * 100, 2)
    
    @property
    def delivery_rate(self):
        if self.sent_count == 0:
            return 0
        delivered = self.sent_count - self.bounce_count
        return round((delivered / self.sent_count) * 100, 2)


class Email(models.Model):
    """Email model representing a single email in a campaign sequence."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='emails', verbose_name=_('Campaign'))
    subject = models.CharField(_('Subject'), max_length=200)
    body_html = models.TextField(_('HTML Body'))
    body_text = models.TextField(_('Text Body'))
    wait_time = models.IntegerField(_('Wait Time'), default=1, help_text=_("Time to wait before sending this email"))
    wait_unit = models.CharField(_('Wait Unit'), max_length=7, choices=Campaign.FREQUENCY_CHOICES, default='days')
    order = models.PositiveIntegerField(_('Order'), default=0)
    footer = models.ForeignKey('analytics.EmailFooter', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Footer'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = _('Email')
        verbose_name_plural = _('Emails')
    
    def __str__(self):
        return f"{self.campaign.name} - {self.subject}"
    
    @property
    def wait_time_display(self):
        """Display wait time with proper unit (seconds, minutes, hours, days, weeks, months)."""
        unit_map = {
            'seconds': (_("second"), _("seconds")),
            'minutes': (_("minute"), _("minutes")),
            'hours': (_("hour"), _("hours")),
            'days': (_("day"), _("days")),
            'weeks': (_("week"), _("weeks")),
            'months': (_("month"), _("months")),
        }
        
        # Get singular or plural form based on wait_time
        unit_singular, unit_plural = unit_map.get(self.wait_unit, (_("day"), _("days")))
        unit = unit_singular if self.wait_time == 1 else unit_plural
        
        return f"{self.wait_time} {unit}"


class EmailEvent(models.Model):
    """Track events related to emails."""
    EVENT_TYPES = [
        ('sent', _('Sent')),
        ('opened', _('Opened')),
        ('clicked', _('Clicked')),
        ('bounced', _('Bounced')),
        ('complained', _('Complained')),
        ('unsubscribed', _('Unsubscribed')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='events', verbose_name=_('Email'))
    subscriber_email = models.EmailField(_('Subscriber Email'))
    event_type = models.CharField(_('Event Type'), max_length=20, choices=EVENT_TYPES)
    link_clicked = models.URLField(_('Link Clicked'), blank=True, null=True)
    user_agent = models.CharField(_('User Agent'), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Email Event')
        verbose_name_plural = _('Email Events')
    
    def __str__(self):
        return f"{self.event_type} - {self.email} - {self.subscriber_email}"


class EmailSendRequest(models.Model):
    """Store information about individual email send requests."""

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('queued', _('Queued')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_send_requests', verbose_name=_('User'))
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_send_requests', verbose_name=_('Campaign'))
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='send_requests', verbose_name=_('Email'))
    subscriber = models.ForeignKey(Subscriber, on_delete=models.SET_NULL, null=True, blank=True, related_name='send_requests', verbose_name=_('Subscriber'))
    subscriber_email = models.EmailField(_('Subscriber Email'))
    variables = models.JSONField(_('Variables'), default=dict, blank=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='pending')
    scheduled_for = models.DateTimeField(_('Scheduled For'))
    sent_at = models.DateTimeField(_('Sent At'), null=True, blank=True)
    error_message = models.TextField(_('Error Message'), blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Email Send Request')
        verbose_name_plural = _('Email Send Requests')

    def __str__(self):
        return f"{self.email.subject} -> {self.subscriber_email} ({self.status})"


class EmailAIAnalysis(models.Model):
    """Store AI-generated content and topic analysis results for emails."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.OneToOneField(Email, on_delete=models.CASCADE, related_name='ai_analysis', verbose_name=_('Email'))
    
    # AI-generated content
    generated_subject = models.CharField(_('Generated Subject'), max_length=200, blank=True)
    generated_body_html = models.TextField(_('Generated Body HTML'), blank=True)
    generation_prompt = models.TextField(_('Generation Prompt'), blank=True, help_text=_("The prompt used to generate content"))
    generation_model = models.CharField(_('Generation Model'), max_length=50, default='gpt-3.5-turbo', blank=True)
    
    # Topic analysis results
    topics_json = models.JSONField(_('Topics'), default=list, blank=True, help_text=_("Extracted topics and keywords"))
    dominant_topics = models.JSONField(_('Dominant Topics'), default=list, blank=True, help_text=_("Dominant topic for this email"))
    topic_analysis_count = models.IntegerField(_('Emails Analyzed'), default=0, help_text=_("Number of emails used in topic analysis"))
    
    # Metadata
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Email AI Analysis')
        verbose_name_plural = _('Email AI Analyses')

    def __str__(self):
        return f"AI Analysis for {self.email.subject}"