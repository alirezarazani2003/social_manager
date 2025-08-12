from django.db import models
from django.utils import timezone
from decouple import config
import secrets
from core.validator import otp_validator


class OTPPurpose(models.TextChoices):
    VERIFY = 'verify', 'Verify Email'
    LOGIN = 'login', 'Login'
    RESET = 'reset', 'Reset Password'


class EmailOTP(models.Model):
    email = models.EmailField(db_index=True)
    otp = models.CharField(
        max_length=6,
        validators=[otp_validator]
    )
    purpose = models.CharField(max_length=10, choices=OTPPurpose.choices)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        expiration_minutes = int(config("OTP_EXPIRATION_MINUTES"))
        return timezone.now() > self.created_at + timezone.timedelta(minutes=expiration_minutes)
    
    @staticmethod
    def generate_otp():
        return str(secrets.randbelow(10**6)).zfill(6)
    class Meta:
        ordering = ['-created_at']
