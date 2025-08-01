from django.db import models
from django.contrib.auth import get_user_model
from channels.models import Channel
from django.utils import timezone
import os
from django.conf import settings

User = get_user_model()

def user_media_path(instance, filename):
    if hasattr(instance, 'user'):
        return f'user_{instance.user.id}/{filename}'
    elif hasattr(instance, 'post'):
        return f'user_{instance.post.user.id}/{filename}'
    return f'uploads/{filename}'

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
    user_media_file = models.ForeignKey('UserMediaFile', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Attachment for post {self.post.id}"

class UserMediaStorage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='media_storage')
    total_space = models.BigIntegerField(default=getattr(settings, 'USER_SPACE_STORAGE')*1024*1024)
    used_space = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def remaining_space(self):
        return max(0, self.total_space - self.used_space)
    
    def can_upload(self, file_size):
        return self.remaining_space() >= file_size
    
    def add_used_space(self, size):
        self.used_space += size
        self.save()
    
    def remove_used_space(self, size):
        self.used_space = max(0, self.used_space - size)
        self.save()
    
    def __str__(self):
        return f"{self.user.email} - {self.used_space}/{self.total_space}"

class UserMediaFile(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to=user_media_path)
    title = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField()
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = os.path.basename(self.file.name)
        
        if not self.file_size and self.file:
            self.file_size = self.file.size
            
        if not self.media_type:
            self.set_media_type()
            
        super().save(*args, **kwargs)
    
    def set_media_type(self):
        if self.file:
            mime_type = self.get_file_mime_type()
            if mime_type.startswith('image'):
                self.media_type = 'image'
            elif mime_type.startswith('video'):
                self.media_type = 'video'
            else:
                self.media_type = 'document'
    
    def get_file_mime_type(self):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(self.file.name)
        return mime_type or 'application/octet-stream'
    
    def delete(self, *args, **kwargs):
        if hasattr(self.user, 'media_storage'):
            self.user.media_storage.remove_used_space(self.file_size)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"