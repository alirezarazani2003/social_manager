from rest_framework import permissions
from rest_framework import serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'is_email_verified')

class IsEmailVerified(permissions.BasePermission):
    """
    اجازه فقط برای کاربرانی که ایمیلشون وریفای شده.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_email_verified



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'is_email_verified')
