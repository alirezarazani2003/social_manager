from django.db import models
from django.contrib.auth import get_user_model
from channels.models import Channel

User = get_user_model()

class Post(models.Model):
    POST_STATUS_CHOICES = [
        ('pending', 'در صف ارسال'),
        ('sending', 'در حال ارسال'),
        ('sent', 'ارسال شده'),
        ('failed', 'ارسال ناموفق'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    media_files = models.JSONField(blank=True, null=True)  
    # media_files می‌تواند لیستی از URL یا اطلاعات فایل‌ها باشد (برای مثال مسیر فایل یا URL آپلود شده)
    scheduled_time = models.DateTimeField(blank=True, null=True)  # اگر None باشه یعنی ارسال فوری
    status = models.CharField(max_length=10, choices=POST_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Post {self.id} to {self.channel.name} by {self.user.username}"
