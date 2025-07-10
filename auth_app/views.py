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


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
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
        return self.request.user


class ProtectedDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Any) -> Response:
        return Response({"msg": "خوش آمدید به داشبورد امن!"})


class RequestOTPView(APIView):
    @swagger_auto_schema(
        request_body=RequestOTPSerializer,
        responses={
            200: openapi.Response(description="OTP با موفقیت ارسال شد"),
            400: openapi.Response(description="درخواست نامعتبر یا ایمیل اشتباه"),
        },
        operation_summary="ارسال کد OTP برای تایید ایمیل",
        operation_description="دریافت ایمیل، تولید و ارسال کد OTP برای تایید ایمیل"
    )
    def post(self, request: Any) -> Response:
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        EmailOTP.objects.filter(email=email, is_used=False, purpose=OTPPurpose.VERIFY).delete()

        otp = EmailOTP.generate_otp()
        EmailOTP.objects.create(email=email, otp=otp, purpose=OTPPurpose.VERIFY)
        send_mail(
            subject="کد تأیید ایمیل",
            message=f"کد شما: {otp}",
            from_email="noreply@yourdomain.com",
            recipient_list=[email]
        )
        return Response({'msg': 'کد برای ایمیل ارسال شد.'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(description="ایمیل با موفقیت وریفای شد"),
            400: openapi.Response(description="کد اشتباه یا منقضی شده"),
        },
        operation_summary="تایید کد OTP برای ایمیل",
        operation_description="دریافت ایمیل و کد OTP، و در صورت صحت، وریفای کردن ایمیل کاربر"
    )
    def post(self, request: Any) -> Response:
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False, purpose=OTPPurpose.VERIFY).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response({'msg': 'کد اشتباه است یا وجود ندارد'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_used = True
        otp_obj.save()

        user = User.objects.get(email=email)
        user.is_verified = True
        user.save()

        return Response({'msg': 'ایمیل وریفای شد.'}, status=status.HTTP_200_OK)


class RequestLoginOTPView(APIView):
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
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return Response({'msg': 'اکانت شما غیرفعال است.'}, status=status.HTTP_403_FORBIDDEN)

            EmailOTP.objects.filter(email=email, is_used=False, purpose=OTPPurpose.LOGIN).delete()
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(email=email, otp=otp, purpose=OTPPurpose.LOGIN)

            send_mail(
                subject="کد ورود",
                message=f"کد ورود شما: {otp}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email]
            )
            return Response({'msg': 'کد ورود به ایمیل ارسال شد.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)


class LoginWithOTPView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='ایمیل'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='کد ۶ رقمی OTP'),
            }
        ),
        responses={
            200: openapi.Response(
                description="ورود موفق",
                examples={
                    "application/json": {
                        "access": "JWT_ACCESS_TOKEN",
                        "refresh": "JWT_REFRESH_TOKEN"
                    }
                }
            ),
            400: openapi.Response(description="ایمیل یا کد اشتباه است یا منقضی شده"),
            403: openapi.Response(description="ایمیل هنوز وریفای نشده"),
        },
        operation_summary="ورود با کد OTP",
        operation_description="دریافت ایمیل و کد OTP، و ورود کاربر در صورت صحت اطلاعات"
    )
    def post(self, request: Any) -> Response:
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'msg': 'ایمیل و کد OTP الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False, purpose=OTPPurpose.LOGIN).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response({'msg': 'کد اشتباه است یا وجود ندارد'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'msg': 'کاربری با این ایمیل یافت نشد'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_verified:
            return Response({'msg': 'ایمیل هنوز وریفای نشده'}, status=status.HTTP_403_FORBIDDEN)

        otp_obj.is_used = True
        otp_obj.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class RequestResetPasswordOTPView(APIView):
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
        email = request.data.get('email')
        if not email:
            return Response({'msg': 'ایمیل الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            EmailOTP.objects.filter(email=email, is_used=False, purpose=OTPPurpose.RESET).delete()
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(email=email, otp=otp, purpose=OTPPurpose.RESET)

            send_mail(
                subject="کد بازیابی رمز عبور",
                message=f"کد بازیابی شما: {otp}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email]
            )
            return Response({'msg': 'کد برای ایمیل ارسال شد.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)


class ResetPasswordWithOTPView(APIView):
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
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        if not all([email, otp, new_password]):
            return Response({'msg': 'ایمیل، کد OTP و رمز جدید باید ارسال شود'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False, purpose=OTPPurpose.RESET).latest('created_at')
            if otp_obj.is_expired():
                return Response({'msg': 'کد منقضی شده'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            otp_obj.is_used = True
            otp_obj.save()

            return Response({'msg': 'رمز عبور با موفقیت تغییر کرد'}, status=status.HTTP_200_OK)
        except EmailOTP.DoesNotExist:
            return Response({'msg': 'کد نامعتبر است'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'msg': 'کاربر یافت نشد'}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

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

        if not old_password or not new_password:
            return Response({'msg': 'رمز عبور فعلی و جدید باید ارسال شود'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'msg': 'رمز عبور فعلی اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return Response({'msg': 'رمز عبور با موفقیت تغییر کرد'}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="توکن رفرش برای بلاک کردن")
            }
        ),
        responses={
            205: openapi.Response(description="خروج موفق"),
            400: openapi.Response(description="توکن نامعتبر یا داده ناقص"),
        },
        operation_summary="خروج کاربر",
        operation_description="توکن رفرش را بلاک می‌کند و کاربر را خارج می‌سازد."
    )
    def post(self, request: Any) -> Response:
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"msg": "توکن رفرش ارسال نشده است"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"msg": "خروج موفق"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"msg": f"خطا: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
