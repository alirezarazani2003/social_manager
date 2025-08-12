from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from typing import Any
from .models import EmailOTP, OTPPurpose
from .serializers import RequestOTPSerializer, VerifyOTPSerializer, UserSerializer
from users.models import User
from .permissions import IsEmailVerified
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from config.throttles import RequestOTPThrottle
import logging
from core.logging_filters import set_user_id, set_request_id, set_client_ip
import uuid
from config.throttles import RoleBasedRateThrottle

logger = logging.getLogger('auth_app.activity')
security_logger = logging.getLogger('auth_app.security')
error_logger = logging.getLogger('auth_app.errors')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
class MeView(generics.RetrieveAPIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    permission_classes = [IsAuthenticated, IsEmailVerified]
    serializer_class = UserSerializer

    @swagger_auto_schema(
        responses={
            200: UserSerializer,
            401: openapi.Response(description="Authentication required")
        },
        operation_summary="دریافت اطلاعات کاربر فعلی",
        operation_description="اطلاعات پروفایل کاربری که لاگین کرده را برمی‌گرداند."
    )
    def get_object(self) -> User:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(self.request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(self.request.user.id)

        logger.info(f"User {self.request.user.id} accessed /me from IP={client_ip}")
        return self.request.user


class ProtectedDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Any) -> Response:
        logger.info(f"User {request.user.id} accessed dashboard from IP={get_client_ip(request)}")
        return Response({
            "msg": "خوش آمدید!",
            "email": request.user.email
        })


class RequestOTPView(APIView):
    throttle_classes = [RequestOTPThrottle]
    @swagger_auto_schema(
        request_body=RequestOTPSerializer,
        responses={200: openapi.Response(
            description="OTP با موفقیت ارسال شد")},
        operation_summary="ارسال کد OTP برای تایید ایمیل"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        logger.info(f"OTP request for email={email} from IP={client_ip}")

        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                security_logger.warning(f"OTP request for already verified email={email} from IP={client_ip}")
                return Response({'msg': 'این ایمیل قبلاً وریفای شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            security_logger.warning(f"OTP request for non-existent email={email} from IP={client_ip}")
            return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_400_BAD_REQUEST)
        EmailOTP.objects.filter(
            email=email, is_used=False, purpose=OTPPurpose.VERIFY).delete()

        otp = EmailOTP.generate_otp()
        EmailOTP.objects.create(email=email, otp=otp,
                                purpose=OTPPurpose.VERIFY)

        send_mail(
            subject="کد تأیید ایمیل",
            message=f"کد شما: {otp}",
            from_email="noreply@yourdomain.com",
            recipient_list=[email]
        )

        security_logger.info(f"Verification OTP sent to email={email} from IP={client_ip}")
        return Response({'msg': 'در صورت وجود حساب، کد تأیید ارسال شد.'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'anon'
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={200: openapi.Response(description="ایمیل وریفای شد")},
        operation_summary="تایید کد OTP"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        logger.info(f"OTP verification attempt for email={email} from IP={client_ip}")

        try:
            otp_obj = EmailOTP.objects.filter(
                email=email,
                otp=otp,
                is_used=False,
                purpose=OTPPurpose.VERIFY
            ).latest('created_at')
        except EmailOTP.DoesNotExist:
            security_logger.warning(f"Invalid OTP verification attempt for email={email} from IP={client_ip}")
            return Response({'msg': 'کد اشتباه است یا وجود ندارد'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            security_logger.warning(f"Expired OTP verification for email={email} from IP={client_ip}")
            return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({'msg': 'ایمیل قبلاً وریفای شده است'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'msg': 'کاربر یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_used = True
        otp_obj.save()

        user.is_verified = True
        user.save()

        logger.info(f"User {user.id} verified email={email} successfully from IP={client_ip}")
        return Response({'msg': 'ایمیل وریفای شد.'}, status=status.HTTP_200_OK)



class RequestLoginOTPView(APIView):
    throttle_classes = [RequestOTPThrottle]
    @swagger_auto_schema(
        request_body=RequestOTPSerializer,
        responses={
            200: openapi.Response(description="کد ورود با موفقیت ارسال شد"),
            400: openapi.Response(description="درخواست نامعتبر"),
            403: openapi.Response(description="اکانت غیرفعال است"),
            404: openapi.Response(description="کاربر یافت نشد"),
        },
        operation_summary="ارسال OTP برای ورود",
        operation_description="دریافت ایمیل و ارسال کد ورود (OTP) به ایمیل کاربر"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        logger.info(f"Login OTP request for email={email} from IP={client_ip}")

        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                security_logger.warning(f"Login OTP requested for inactive account: {email} from IP={client_ip}")
                return Response({'msg': 'اکانت شما غیرفعال است.'}, status=status.HTTP_403_FORBIDDEN)

            EmailOTP.objects.filter(
                email=email, is_used=False, purpose=OTPPurpose.LOGIN).delete()
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(
                email=email, otp=otp, purpose=OTPPurpose.LOGIN)

            send_mail(
                subject="کد ورود",
                message=f"کد ورود شما: {otp}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email]
            )
            security_logger.info(f"Login OTP sent to email={email} from IP={client_ip}")
            return Response({'msg': 'کد ورود به ایمیل ارسال شد.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            security_logger.warning(f"Login OTP requested for non-existent email={email} from IP={client_ip}")
            return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)


class LoginWithOTPView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'anon'

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'otp': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={200: openapi.Response(description="ورود موفق")},
        operation_summary="ورود با OTP"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        email = request.data.get('email')
        otp = request.data.get('otp')

        logger.info(f"Login with OTP attempt for email={email} from IP={client_ip}")

        if not email or not otp:
            security_logger.warning(f"Missing email or OTP from IP={client_ip}")
            return Response({'msg': 'ایمیل و کد OTP الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = EmailOTP.objects.filter(
                email=email, otp=otp, is_used=False, purpose=OTPPurpose.LOGIN).latest('created_at')
        except EmailOTP.DoesNotExist:
            security_logger.warning(f"Invalid OTP login attempt for email={email} from IP={client_ip}")
            return Response({'msg': 'کد اشتباه است یا وجود ندارد'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            security_logger.warning(f"Expired OTP login attempt for email={email} from IP={client_ip}")
            return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            set_user_id(user.id)
        except User.DoesNotExist:
            return Response({'msg': 'کاربری با این ایمیل یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            security_logger.info(f"Login blocked: email not verified for user {user.id}")
            return Response({'msg': 'ایمیل هنوز وریفای نشده'}, status=status.HTTP_403_FORBIDDEN)


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

        otp_obj.is_used = True
        otp_obj.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        response = Response({'msg': 'ورود موفق'}, status=status.HTTP_200_OK)

        response.set_cookie(
            key=settings.JWT_COOKIE_NAME,
            value=access_token,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        )
        response.set_cookie(
            key=settings.JWT_COOKIE_REFRESH_NAME,
            value=str(refresh),
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
        )

        logger.info(f"User {user.id} logged in via OTP from IP={client_ip}")
        return response


class RequestResetPasswordOTPView(APIView):
    throttle_classes = [RequestOTPThrottle]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='ایمیل')
            }
        ),
        responses={
            200: openapi.Response(description="کد بازیابی رمز عبور ارسال شد"),
            404: openapi.Response(description="کاربر با این ایمیل یافت نشد"),
        },
        operation_summary="درخواست کد OTP برای بازیابی رمز عبور",
        operation_description="دریافت ایمیل و ارسال کد OTP برای ریست کردن رمز عبور"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        email = request.data.get('email')
        if not email:
            security_logger.warning(f"Password reset requested without email from IP={client_ip}")
            return Response({'msg': 'ایمیل الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Password reset OTP requested for email={email} from IP={client_ip}")

        try:
            user = User.objects.get(email=email)
            EmailOTP.objects.filter(email=email, is_used=False, purpose=OTPPurpose.RESET).delete()
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(
                email=email, otp=otp, purpose=OTPPurpose.RESET)

            send_mail(
                subject="کد بازیابی رمز عبور",
                message=f"کد بازیابی شما: {otp}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email]
            )
            security_logger.info(f"Password reset OTP sent to email={email} from IP={client_ip}")
            return Response({'msg': 'کد برای ایمیل ارسال شد.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            security_logger.warning(f"Password reset requested for non-existent email={email} from IP={client_ip}")
            return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordWithOTPView(APIView):
    throttle_classes = [RequestOTPThrottle]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp', 'new_password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='ایمیل'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='کد OTP'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور جدید'),
            }
        ),
        responses={
            200: openapi.Response(description="رمز عبور با موفقیت تغییر کرد"),
            400: openapi.Response(description="کد اشتباه یا منقضی شده است"),
            404: openapi.Response(description="کاربر یافت نشد"),
        },
        operation_summary="ریست رمز عبور با OTP",
        operation_description="پس از دریافت کد OTP، تعیین رمز عبور جدید"
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        logger.info(f"Password reset attempt for email={email} from IP={client_ip}")

        if not all([email, otp, new_password]):
            security_logger.warning(f"Password reset missing fields from IP={client_ip}")
            return Response({'msg': 'ایمیل، کد OTP و رمز جدید باید ارسال شود'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = EmailOTP.objects.filter(
                email=email, otp=otp, is_used=False, purpose=OTPPurpose.RESET).latest('created_at')
            if otp_obj.is_expired():
                security_logger.warning(f"Expired OTP for password reset of email={email} from IP={client_ip}")
                return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            set_user_id(user.id)
            user.set_password(new_password)
            user.save()

            otp_obj.is_used = True
            otp_obj.save()

            logger.info(f"User {user.id} reset password successfully from IP={client_ip}")
            return Response({'msg': 'رمز عبور با موفقیت تغییر کرد'}, status=status.HTTP_200_OK)
        except EmailOTP.DoesNotExist:
            security_logger.warning(f"Invalid OTP for password reset of email={email} from IP={client_ip}")
            return Response({'msg': 'کد نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'msg': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور فعلی'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور جدید'),
            }
        ),
        responses={
            200: openapi.Response(description="رمز عبور با موفقیت تغییر کرد"),
            400: openapi.Response(description="رمز عبور فعلی اشتباه است"),
        },
        operation_summary="تغییر رمز عبور برای کاربر وارد شده",
        operation_description="تغییر رمز عبور با وارد کردن رمز فعلی و رمز جدید"
    )
    def post(self, request: Any) -> Response:
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(user.id)

        if not old_password or not new_password:
            security_logger.warning(f"Change password missing fields for user {user.id} from IP={client_ip}")
            return Response({'msg': 'رمز عبور فعلی و جدید باید ارسال شود'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            security_logger.warning(f"Failed password change: wrong old password for user {user.id} from IP={client_ip}")
            return Response({'msg': 'رمز عبور فعلی اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        logger.info(f"User {user.id} changed password successfully from IP={client_ip}")
        return Response({'msg': 'رمز عبور با موفقیت تغییر کرد'}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    permission_classes = [IsAuthenticated]
    throttle_scope = 'user'
    @swagger_auto_schema(
        request_body=None,
        responses={
            205: openapi.Response(description="خروج موفق"),
            400: openapi.Response(description="توکن رفرش در کوکی‌ها پیدا نشد"),
            401: openapi.Response(description="کاربر احراز هویت نشده است"),
        },
        operation_summary="خروج کاربر و حذف توکن‌ها از کوکی‌ها",
        operation_description="با حذف توکن‌ها از کوکی‌ها، کاربر از سیستم خارج می‌شود."
    )
    def post(self, request: Any) -> Response:
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            security_logger.warning(f"Logout attempt without refresh token for user {request.user.id} from IP={client_ip}")
            return Response({'msg': 'توکن یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User {request.user.id} logged out successfully from IP={client_ip}")
        except Exception as e:
            error_logger.error(f"Failed to blacklist token for user {request.user.id}: {e}")

        response = Response({'msg': 'خروج موفق'}, status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response


class CookieTokenRefreshView(APIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'

    @swagger_auto_schema(
        operation_summary="تجدید توکن دسترسی با استفاده از توکن رفرش کوکی",
        operation_description="توکن رفرش را از کوکی دریافت می‌کند و در صورت معتبر بودن توکن جدید دسترسی (Access Token) را صادر می‌کند و در کوکی ذخیره می‌کند.",
        responses={
            200: openapi.Response(
                description="توکن جدید صادر شد",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, description='پیغام موفقیت'),
                    },
                ),
            ),
            401: openapi.Response(
                description="توکن یافت نشد یا نامعتبر",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, description='پیغام خطا'),
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)

        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            security_logger.warning(f"Token refresh requested without refresh token from IP={client_ip}")
            return Response({'msg': 'توکن یافت نشد'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
            logger.info(f"Token refreshed successfully from IP={client_ip}")
        except Exception:
            security_logger.warning(f"Invalid refresh token attempt from IP={client_ip}")
            return Response({'msg': 'توکن نامعتبر است'}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'msg': 'توکن جدید صادر شد'},
                            status=status.HTTP_200_OK)
        response.set_cookie(
            key=settings.JWT_COOKIE_NAME,
            value=access_token,
            httponly=settings.JWT_COOKIE_HTTPONLY,
            secure=settings.JWT_COOKIE_SECURE,
            samesite='Lax',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        )
        return response
