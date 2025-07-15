from django.db import models
from django.contrib.auth import get_user_model
from channels.models import Channel
from django.utils import timezone

User = get_user_model()

class Post(models.Model):
    POST_STATUS_CHOICES = [
        ('pending', 'در صف ارسال'),
        ('sending', 'در حال ارسال'),
        ('sent', 'ارسال شده'),
        ('failed', 'ارسال ناموفق'),
    ]

    TEXT = 'text'
    MEDIA = 'media'

    POST_TYPES = [
        (TEXT, 'متنی'),
        (MEDIA, 'چندرسانه‌ای'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    media_files = models.JSONField(blank=True, null=True)
    scheduled_time = models.DateTimeField(blank=True, null=True) 
    status = models.CharField(max_length=10, choices=POST_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    types = models.CharField(max_length=10, choices=POST_TYPES)
    
    def __str__(self):
        return f"Post {self.id} to {self.channel.username} by {self.user.email}"
    
    def is_scheduled(self):
        return self.scheduled_time and self.scheduled_time > timezone.now()

class MediaAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='post_media/')