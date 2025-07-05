from django.core.mail import send_mail
from .models import EmailOTP

def send_otp_to_email(email):
    otp = EmailOTP.generate_otp()
    EmailOTP.objects.create(email=email, otp=otp)
    send_mail(
        subject="کد ورود شما به برنامه",
        message=f"کد یکبار مصرف شما: {otp}",
        from_email="alirezarazani3185@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )
