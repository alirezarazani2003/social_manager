from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.validator import email_validator, otp_validator

User = get_user_model()

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_validator])
    purpose = serializers.ChoiceField(choices=["verify", "login", "reset"])

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[email_validator])
    otp = serializers.CharField(validators=[otp_validator])



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'is_verified')