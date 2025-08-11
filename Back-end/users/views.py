from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer
from utils.responses import success_response, error_response
from decouple import config
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
class RegisterView(APIView):
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            200: openapi.Response(description="ثبت‌نام موفق و ورود موقت به داشبورد"),
            400: openapi.Response(description="اطلاعات نامعتبر یا ناقص"),
        },
        operation_summary="ثبت‌نام اولیه کاربر",
        operation_description="""
اطلاعات ثبت‌نام شامل نام، نام خانوادگی، شماره تلفن، ایمیل، رمز عبور و تکرار رمز را دریافت می‌کند.
در صورت موفقیت، حساب موقت ساخته شده و کاربر به داشبورد هدایت می‌شود اما هنوز اجازه استفاده از امکانات سایت را ندارد تا زمانی که ایمیل را وریفای کند.
"""
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(
                message='ثبت‌نام موقت انجام شد. وارد داشبورد شدید اما باید ایمیل را وریفای کنید.'
            )
        return error_response(message='اطلاعات نامعتبر است.', errors=serializer.errors)


class LoginView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='ایمیل کاربر'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور کاربر'),
            }
        ),
        responses={
            200: openapi.Response(description="ورود موفق (توکن‌ها در کوکی HTTPOnly ذخیره شده‌اند)"),
            400: openapi.Response(description="ورودی ناقص یا نامعتبر"),
            401: openapi.Response(description="ایمیل یا رمز اشتباه / ایمیل وریفای نشده"),
        },
        operation_summary="ورود کاربر (امن)",
        operation_description="""
ایمیل و رمز عبور را دریافت کرده، احراز هویت می‌کند و در صورت موفقیت، توکن‌های JWT را به‌صورت امن در کوکی ذخیره می‌کند (نه در بدنه پاسخ).
"""
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return error_response(message="لطفاً ایمیل و رمز را وارد کنید.", status_code=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(message="ایمیل یا رمز اشتباه است.", status_code=status.HTTP_401_UNAUTHORIZED)
        if not check_password(password, user.password):
            return error_response(message="ایمیل یا رمز اشتباه است.", status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return error_response(
                message="حساب شما هنوز توسط ادمین تأیید نشده است. پس از تأیید، ایمیلی از ما دریافت خواهید کرد.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                data={'approval_required': True, 'email': user.email}
            )

        if not user.is_verified:
            return error_response(
                message="ایمیل شما هنوز وریفای نشده است.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                data={'verification_required': True, 'email': email}
            )

        try:
            tokens = OutstandingToken.objects.filter(user=user).order_by('created_at')
            max_tokens = getattr(settings, 'MAX_ACTIVE_TOKENS', 5)
            tokens_to_keep = tokens[:max_tokens]
            tokens_to_blacklist = tokens[max_tokens:]
            for token in tokens_to_blacklist:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            print("Token cleanup error:", e)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = success_response(message="ورود موفق بود.")

        response.set_cookie(
            key='access',
            value=access_token,
            httponly=True,
            secure=config('COOKIE_SECURE', cast=bool, default=False),
            samesite='Strict',
            max_age=config('ACCESS_TOKEN_MINUTES', cast=int) * 60
        )
        response.set_cookie(
            key='refresh',
            value=refresh_token,
            httponly=True,
            secure=config('COOKIE_SECURE', cast=bool, default=False),
            samesite='Strict',
            max_age=config('REFRESH_TOKEN_DAYS', cast=int) * 24 * 3600
        )
        return response