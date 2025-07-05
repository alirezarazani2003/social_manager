from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from .models import EmailOTP
from .utils import send_otp_to_email
from users.models import CustomUser


class RequestOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'ایمیل الزامی است'}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = EmailOTP.generate_otp()
        EmailOTP.objects.create(email=email, otp=otp_code)
        send_otp_to_email(email, otp_code)

        return Response({'message': 'کد یک‌بار مصرف ارسال شد'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'ایمیل و کد OTP الزامی هستند'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = EmailOTP.objects.filter(email=email, otp=otp, is_used=False).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response({'error': 'کد OTP اشتباه است'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            return Response({'error': 'کد OTP منقضی شده است'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_used = True
        otp_obj.save()

        user, created = CustomUser.objects.get_or_create(email=email)

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'ورود با موفقیت انجام شد',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


from rest_framework.permissions import IsAuthenticated

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.get_full_name(),
            # در صورت نیاز فیلدهای دیگر اضافه شود
        }
        return Response(data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "با موفقیت خارج شدید"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "توکن معتبر نیست"}, status=status.HTTP_400_BAD_REQUEST)
