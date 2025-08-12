from rest_framework import serializers
from .models import User
import re
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'password2']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("این ایمیل قبلا ثبت شده است.")
        return value

    def validate(self, data):
        password = data['password']
        password2 = data['password2']

        if password != password2:
            raise serializers.ValidationError("رمزها یکسان نیستند.")

        if len(password) < 8:
            raise serializers.ValidationError("طول رمز باید حداقل ۸ کاراکتر باشد.")

        if password.isalpha():
            raise serializers.ValidationError("رمز عبور باید شامل عدد نیز باشد.")
        if password.isnumeric():
            raise serializers.ValidationError("رمز عبور باید شامل حروف نیز باشد.")
        if password.islower():
            raise serializers.ValidationError("رمز عبور باید شامل حروف بزرگ نیز باشد.")
        if password.isupper():
            raise serializers.ValidationError("رمز عبور باید شامل حروف کوچک نیز باشد.")
        if password.isalnum():
            raise serializers.ValidationError("رمز عبور باید شامل نمادهایی مانند !@#$ نیز باشد.")
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError("رمز عبور باید حداقل یک حرف بزرگ داشته باشد.")
        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError("رمز عبور باید حداقل یک حرف کوچک داشته باشد.")
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError("رمز عبور باید حداقل یک عدد داشته باشد.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise serializers.ValidationError("رمز عبور باید حداقل یک نماد (!@#$...) داشته باشد.")

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)
    
    def save(self, **kwargs):
            user = super().save(**kwargs)
            subject_user = "ثبت‌نام شما در حال بررسی است"
            message_user = render_to_string('emails/pending_approval.txt', {
                'user': user,
                'site': get_current_site(self.context['request']),
            })
            send_mail(
                subject=subject_user,
                message=message_user,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )

            admin_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
            if admin_emails:
                subject_admin = "درخواست ثبت‌نام جدید"
                message_admin = render_to_string('emails/admin_notification.txt', {
                    'user': user,
                    'site': get_current_site(self.context['request']),
                })
                send_mail(
                    subject=subject_admin,
                    message=message_admin,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=list(admin_emails),
                    fail_silently=False,
                )

            return user
