# Core models
from django.db import models
from django.utils.text import slugify

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    summary = models.TextField(max_length=300)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class EmailLog(models.Model):
    """Model for storing incoming email metadata from the SMTP server."""
    
    sender = models.EmailField(max_length=254)
    recipient = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    message_id = models.CharField(max_length=255, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(default=0)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['recipient']),
            models.Index(fields=['received_at']),
            models.Index(fields=['processed']),
        ]
    
    def __str__(self):
        return f"{self.subject} from {self.sender} to {self.recipient}"
    
    @property
    def is_spam(self):
        """Simple spam detection based on common patterns."""
        spam_indicators = [
            'viagra', 'casino', 'lottery', 'winner', 'urgent',
            'limited time', 'act now', 'free money', 'inheritance'
        ]
        content = f"{self.subject} {self.body}".lower()
        return any(indicator in content for indicator in spam_indicators)