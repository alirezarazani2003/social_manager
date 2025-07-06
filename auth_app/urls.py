from django.urls import path
from .views import *

urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('request-login-otp/', RequestLoginOTPView.as_view(), name='request-login-otp'),
    path('login-with-otp/', LoginWithOTPView.as_view(), name='login-with-otp'),
    path('request-otp/', RequestOTPView.as_view(), name='request_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('login-with-otp/', LoginWithOTPView.as_view(), name='login_with_otp'),
    path('me/', MeView.as_view(), name='me'),
    path('logout/', LogoutView.as_view(), name='logout')
    ]