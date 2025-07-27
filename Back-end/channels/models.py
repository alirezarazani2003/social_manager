from django.db import models
from django.conf import settings
# Create your models here.


class Channel(models.Model):
    PLATFORM_CHOICES = (
        ('telegram', 'Telegram'),
        ('bale', 'Bale'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100, help_text='مثلاً: جامعه بزرگان')
    username = models.CharField(max_length=100, help_text='مثلاً: @boz_community')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    is_verified = models.BooleanField(default=False)  # در صورت تأیید توسط ربات
    failed_reason = models.TextField(blank=True, null=True)
    platform_channel_id = models.CharField(max_length=200, null=True, blank=True, help_text="شناسه کانال در پلتفرم مربوطه (مثلاً chat_id)")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.platform})"
