from django.db import models
from django.utils import timezone
from decouple import config
from django.core.validators import RegexValidator
import secrets
from core.validator import otp_validator, email_validator


class OTPPurpose(models.TextChoices):
    VERIFY = 'verify', 'Verify Email'
    LOGIN = 'login', 'Login'
    RESET = 'reset', 'Reset Password'


class EmailOTP(models.Model):
    email = models.EmailField(db_index=True, validators=[email_validator])
    otp = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$')]
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
