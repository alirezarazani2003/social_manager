from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from .models import EmailOTP
from .serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    UserSerializer
)
from users.models import User
from .permissions import IsEmailVerified
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RequestOTPView(APIView):
    @swagger_auto_schema(
        request_body=RequestOTPSerializer,
        responses={
            200: openapi.Response(description="OTP sent successfully"),
            400: openapi.Response(description="Invalid email or bad request"),
        },
        operation_summary="ارسال OTP به ایمیل",
        operation_description="ایمیل را دریافت می‌کند، یک کد OTP تولید و به ایمیل ارسال می‌کند."
    )
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(email=email, otp=otp)
            send_mail(
                subject="کد تأیید ایمیل",
                message=f"کد شما: {otp}",
                from_email="noreply@yourdomain.com",
                recipient_list=[email]
            )
            return Response({'msg': 'کد برای ایمیل ارسال شد.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response(description="Email verified successfully"),
            400: openapi.Response(description="Invalid OTP or expired"),
        },
        operation_summary="تأیید OTP",
        operation_description="ایمیل و کد را دریافت می‌کند و در صورت صحیح بودن، حساب را وریفای می‌کند."
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False).latest('created_at')
            except EmailOTP.DoesNotExist:
                return Response({'msg': 'کد اشتباه است یا وجود ندارد'}, status=400)
            if otp_obj.is_expired():
                return Response({'msg': 'کد منقضی شده'}, status=400)
            otp_obj.is_used = True
            otp_obj.save()
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save()
            return Response({'msg': 'ایمیل وریفای شد.'})
        return Response(serializer.errors, status=400)


class ProtectedDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="Authenticated and verified user"),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Email not verified"),
        },
        operation_summary="دسترسی محافظت‌شده برای کاربران وریفای‌شده",
        operation_description="فقط کاربرانی که لاگین کرده‌اند و ایمیل آن‌ها وریفای شده می‌توانند این پیام را ببینند."
    )
    def get(self, request):
        return Response({"message": "You are verified and authenticated!"})


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @swagger_auto_schema(
        responses={
            200: UserSerializer,
            401: openapi.Response(description="Authentication required"),
        },
        operation_summary="دریافت اطلاعات کاربر فعلی",
        operation_description="اطلاعات پروفایل کاربری که لاگین کرده را برمی‌گرداند."
    )
    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist')
            },
        ),
        responses={
            205: openapi.Response(description="Logout successful"),
            400: openapi.Response(description="Invalid token or missing data"),
        },
        operation_summary="خروج کاربر",
        operation_description="توکن رفرش را بلاک می‌کند و کاربر را خارج می‌سازد."
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RequestLoginOTPView(APIView):
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    return Response({'msg': 'اکانت شما غیرفعال است.'}, status=403)
                otp = EmailOTP.generate_otp()
                EmailOTP.objects.create(email=email, otp=otp)
                send_mail(
                    subject="کد ورود",
                    message=f"کد ورود شما: {otp}",
                    from_email="noreply@yourdomain.com",
                    recipient_list=[email]
                )
                return Response({'msg': 'کد ورود به ایمیل ارسال شد.'})
            except User.DoesNotExist:
                return Response({'msg': 'کاربری با این ایمیل یافت نشد.'}, status=404)
        return Response(serializer.errors, status=400)

class LoginWithOTPView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='کد تایید ۶ رقمی ارسال شده به ایمیل')
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
            400: "ایمیل یا کد اشتباه است یا منقضی شده",
            403: "کاربر هنوز وریفای نشده"
        }
    )
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        try:
            otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"msg": "کد اشتباه است یا وجود ندارد"}, status=400)

        if otp_obj.is_expired():
            return Response({"msg": "کد منقضی شده"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"msg": "کاربری با این ایمیل یافت نشد"}, status=400)

        if not user.is_verified:
            return Response({"msg": "ایمیل هنوز وریفای نشده"}, status=403)

        otp_obj.is_used = True
        otp_obj.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

