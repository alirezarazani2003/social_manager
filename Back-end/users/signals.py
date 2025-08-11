from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import User

@receiver(pre_save, sender=User)
def save_old_is_active(sender, instance, **kwargs):
    if instance.pk:
        old_instance = User.objects.get(pk=instance.pk)
        instance._old_is_active = old_instance.is_active
    else:
        instance._old_is_active = False

@receiver(post_save, sender=User)
def send_approval_email(sender, instance, created, **kwargs):
    if created:
        return

    if instance.is_active and hasattr(instance, '_old_is_active') and not instance._old_is_active:
        subject = "حساب شما با موفقیت تأیید شد"
        message = render_to_string('emails/approved.txt', {
            'user': instance,
        })
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[instance.email],
            fail_silently=False,
        )