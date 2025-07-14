from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from .tasks import send_post_task
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class PostCreateView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="ایجاد پست جدید (فوری یا زمان‌بندی‌شده)",
        operation_description="""
        این API به شما امکان می‌دهد یک پست جدید ایجاد کنید. اگر `scheduled_time` مشخص شده باشد و در آینده باشد، پست در زمان تعیین‌شده ارسال می‌شود.
        در غیر این صورت، بلافاصله ارسال خواهد شد.
        """,
        responses={
            201: openapi.Response("پست با موفقیت ایجاد شد", PostSerializer),
            400: "درخواست نامعتبر (مثلاً داده ناقص یا فرمت نادرست)",
            403: "عدم احراز هویت"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        if post.scheduled_time and post.scheduled_time > now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
        else:
            send_post_task.delay(post.id)
