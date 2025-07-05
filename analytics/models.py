from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    """Extended user profile with additional settings."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('User'))
    has_verified_promo = models.BooleanField(_('Has Verified Promo'), default=False)
    promo_url = models.URLField(_('Promo URL'), blank=True)
    send_without_unsubscribe = models.BooleanField(_('Send Without Unsubscribe'), default=False)
    custom_footer_html = models.TextField(_('Custom Footer HTML'), blank=True, help_text=_('Custom footer HTML for emails'))
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return _("Profile for %(username)s") % {'username': self.user.username}

class EmailFooter(models.Model):
    """Email footer template for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_footers', verbose_name=_('User'))
    name = models.CharField(_('Name'), max_length=100)
    html_content = models.TextField(_('HTML Content'))
    is_default = models.BooleanField(_('Is Default'), default=False)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Email Footer')
        verbose_name_plural = _('Email Footers')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default footer per user
        if self.is_default:
            EmailFooter.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)