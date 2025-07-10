from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer
from utils.responses import success_response, error_response
from decouple import config
from django.conf import settings

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
        serializer = RegisterSerializer(data=request.data)
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

        user = authenticate(request, email=email, password=password)

        if not user:
            return error_response(message="ایمیل یا رمز اشتباه است.", status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return error_response(message="ایمیل شما هنوز وریفای نشده است.", status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            tokens = OutstandingToken.objects.filter(user=user).order_by('created_at')
            max_tokens = getattr(settings, 'MAX_ACTIVE_TOKENS',)
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
        print("Set refresh_token cookie:", refresh_token)
        return response
