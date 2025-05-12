from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
import uuid

class List(models.Model):
    """Subscriber list model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber_lists', verbose_name=_('User'))
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    slug = models.SlugField(max_length=150, unique=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('List')
        verbose_name_plural = _('Lists')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness by appending a UUID segment if needed
            if List.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def subscribers_count(self):
        return self.subscribers.count()
    
    @property
    def active_subscribers_count(self):
        return self.subscribers.filter(is_active=True).count()


class Subscriber(models.Model):
    """Subscriber model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lists = models.ManyToManyField(List, related_name='subscribers', verbose_name=_('Lists'))
    email = models.EmailField(_('Email'))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(_('First Name'), max_length=100, blank=True)
    last_name = models.CharField(_('Last Name'), max_length=100, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    confirmed = models.BooleanField(_('Confirmed'), default=False)
    confirmation_sent_at = models.DateTimeField(_('Confirmation Sent At'), null=True, blank=True)
    confirmed_at = models.DateTimeField(_('Confirmed At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        unique_together = ('email',)
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')
    
    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name} <{self.email}>"
        return self.email
    
    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return ""


class CustomField(models.Model):
    """Custom field for subscribers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_fields', verbose_name=_('User'))
    name = models.CharField(_('Name'), max_length=100)
    key = models.CharField(_('Key'), max_length=100)
    
    class Meta:
        verbose_name = _('Custom Field')
        verbose_name_plural = _('Custom Fields')
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class CustomValue(models.Model):
    """Custom field value for a subscriber."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values', verbose_name=_('Field'))
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='custom_values', verbose_name=_('Subscriber'))
    value = models.TextField(_('Value'))
    
    class Meta:
        unique_together = ('field', 'subscriber')
        verbose_name = _('Custom Value')
        verbose_name_plural = _('Custom Values')
    
    def __str__(self):
        return f"{self.field.name}: {self.value}"