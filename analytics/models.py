from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    """Extended user profile with additional settings."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('User'))
    has_verified_promo = models.BooleanField(_('Has Verified Promo'), default=False)
    promo_url = models.URLField(_('Promo URL'), blank=True)
    send_without_unsubscribe = models.BooleanField(_('Send Without Unsubscribe'), default=False)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return _("Profile for %(username)s") % {'username': self.user.username}