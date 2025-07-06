from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


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
            return Response({'msg': 'ثبت‌نام موقت انجام شد. وارد داشبورد شدی اما باید ایمیل رو وریفای کنی.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            200: openapi.Response(
                description="ورود موفق",
                examples={
                    "application/json": {
                        "access": "JWT_ACCESS_TOKEN",
                        "refresh": "JWT_REFRESH_TOKEN"
                    }
                }
            ),
            400: openapi.Response(description="ورودی ناقص یا نامعتبر"),
            401: openapi.Response(description="ایمیل یا رمز اشتباه / ایمیل وریفای نشده"),
        },
        operation_summary="ورود کاربر",
        operation_description="ایمیل و رمز عبور را دریافت کرده، احراز هویت می‌کند و در صورت موفقیت توکن JWT برمی‌گرداند."
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"detail": "لطفاً ایمیل و رمز را وارد کنید."}, status=400)

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({"detail": "ایمیل یا رمز اشتباه است."}, status=401)

        if not user.is_verified:
            return Response({"detail": "ایمیل شما هنوز وریفای نشده است."}, status=401)
        
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                try:
                    BlacklistedToken.objects.get_or_create(token=token)
                except Exception:
                    pass
        except Exception:
            pass
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


