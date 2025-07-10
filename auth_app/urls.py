from django.urls import path
from .views import *

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('request-login-otp/', RequestLoginOTPView.as_view(), name='request-login-otp'),
    path('login-with-otp/', LoginWithOTPView.as_view(), name='login-with-otp'),
    path('me/', MeView.as_view(), name='me'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('request-reset-otp/', RequestResetPasswordOTPView.as_view(), name='request-reset-otp'),
    path('reset-password/', ResetPasswordWithOTPView.as_view(), name='reset-password'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh')
    ]