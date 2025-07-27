from django.db import models
from django.contrib.auth import get_user_model
from channels.models import Channel
from django.utils import timezone

User = get_user_model()
def user_media_path(instance, filename):
    return f'user_{instance.post.user}/{filename}'

class Post(models.Model):
    POST_STATUS_CHOICES = [
        ('pending', 'در صف ارسال'),
        ('sending', 'در حال ارسال'),
        ('sent', 'ارسال شده'),
        ('failed', 'ارسال ناموفق'),
        ('cancelled', 'لغو شده'),
    ]

    TEXT = 'text'
    MEDIA = 'media'

    POST_TYPES = [
        (TEXT, 'متنی'),
        (MEDIA, 'چندرسانه‌ای'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    channels = models.ManyToManyField(Channel, related_name='posts')
    content = models.TextField(blank=True, null=True)
    media_files = models.JSONField(blank=True, null=True)
    scheduled_time = models.DateTimeField(blank=True, null=True) 
    status = models.CharField(max_length=10, choices=POST_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    types = models.CharField(max_length=10, choices=POST_TYPES)
    
    def __str__(self):
        channel_usernames = ', '.join([channel.username for channel in self.channels.all()])
        return f"Post {self.id} to {channel_usernames} by {self.user.email}"
    
    def is_scheduled(self):
        return self.scheduled_time and self.scheduled_time > timezone.now()

class MediaAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=user_media_path)