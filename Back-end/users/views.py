from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer
from utils.responses import success_response, error_response
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
import logging
from core.logging_filters import set_user_id, set_request_id, set_client_ip
import uuid
from config.throttles import RoleBasedRateThrottle

logger = logging.getLogger('users.activity')
security_logger = logging.getLogger('users.security')
error_logger = logging.getLogger('users.errors')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RegisterView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'anon'
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        logger.info(f"Registration attempt from IP={client_ip}")
        
        serializer = RegisterSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User {user.id} registered successfully. Email verification required.")
            return success_response(
                message='ثبت‌نام موقت انجام شد. وارد داشبورد شدید اما باید ایمیل را وریفای کنید.'
            )
        else:
            security_logger.warning(f"Invalid registration data from IP={client_ip}: {serializer.errors}")
            return error_response(message='اطلاعات نامعتبر است.', errors=serializer.errors)


class LoginView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'anon'

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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        email = request.data.get("email")
        password = request.data.get("password")

        logger.info(f"Login attempt for email={email} from IP={client_ip}")

        if not email or not password:
            security_logger.warning(f"Missing email or password from IP={client_ip}")
            return error_response(message="لطفاً ایمیل و رمز را وارد کنید.", status_code=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            security_logger.warning(f"Failed login attempt for email={email} from IP={client_ip}")
            return error_response(message="ایمیل یا رمز اشتباه است.", status_code=status.HTTP_401_UNAUTHORIZED)
        if not check_password(password, user.password):
            return error_response(message="ایمیل یا رمز اشتباه است.", status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            security_logger.warning(f"Failed login attempt for email={email} from IP={client_ip}")
            return error_response(
                message="حساب شما هنوز توسط ادمین تأیید نشده است. پس از تأیید، ایمیلی از ما دریافت خواهید کرد.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                data={'approval_required': True, 'email': user.email}
            )

        if not user.is_verified:
            security_logger.info(f"Login blocked: email not verified for user {user.id}")
            return error_response(
                message="ایمیل شما هنوز وریفای نشده است.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                data={'verification_required': True, 'email': email}
            )

        set_user_id(user.id)

        try:
            tokens = OutstandingToken.objects.filter(user=user).order_by('created_at')
            max_tokens = getattr(settings, 'MAX_ACTIVE_TOKENS', 5)
            tokens_to_blacklist = tokens[max_tokens:]
            for token in tokens_to_blacklist:
                BlacklistedToken.objects.get_or_create(token=token)
            if tokens_to_blacklist:
                logger.info(f"Cleaned up {len(tokens_to_blacklist)} old tokens for user {user.id}")
        except Exception as e:
            error_logger.error(f"Token cleanup failed for user {user.id}: {e}")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = success_response(message="ورود موفق بود.")

        response.set_cookie(
            key=settings.JWT_COOKIE_NAME,
            value=access_token,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite='Strict',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        )
        response.set_cookie(
            key=settings.JWT_COOKIE_REFRESH_NAME,
            value=refresh_token,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite='Strict',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        )

        logger.info(f"User {user.id} logged in successfully from IP={client_ip}")
        return response