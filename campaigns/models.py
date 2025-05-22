from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from subscribers.models import List
import uuid

class Campaign(models.Model):
    """Campaign model representing an email sequence."""
    FREQUENCY_CHOICES = [
        ('hours', _('Hours')),
        ('days', _('Days')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    slug = models.SlugField(max_length=150, unique=True)
    subscriber_list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='campaigns', verbose_name=_('Subscriber List'), null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    sent_count = models.IntegerField(_('Sent Count'), default=0)
    open_count = models.IntegerField(_('Open Count'), default=0)
    click_count = models.IntegerField(_('Click Count'), default=0)
    
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
        return (self.open_count / self.sent_count) * 100
    
    @property
    def click_rate(self):
        if self.sent_count == 0:
            return 0
        return (self.click_count / self.sent_count) * 100


class Email(models.Model):
    """Email model representing a single email in a campaign sequence."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='emails', verbose_name=_('Campaign'))
    subject = models.CharField(_('Subject'), max_length=200)
    body_html = models.TextField(_('HTML Body'))
    body_text = models.TextField(_('Text Body'))
    wait_time = models.IntegerField(_('Wait Time'), default=1, help_text=_("Time to wait before sending this email"))
    wait_unit = models.CharField(_('Wait Unit'), max_length=5, choices=Campaign.FREQUENCY_CHOICES, default='days')
    order = models.PositiveIntegerField(_('Order'), default=0)
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
        unit = _("hour") if self.wait_unit == "hours" else _("day")
        if self.wait_time != 1:
            unit = _("hours") if self.wait_unit == "hours" else _("days")
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