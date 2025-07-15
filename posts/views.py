from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from .tasks import send_post_task
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from auth_app.permissions import IsEmailVerified

class PostCreateView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        operation_summary="ارسال پست (فوری یا زمان‌بندی‌شده)",
        operation_description="این ویو به شما امکان ارسال پست متنی یا چندرسانه‌ای به یک کانال را می‌دهد. اگر `scheduled_time` مشخص شود، پست در آن زمان ارسال می‌شود.",
        responses={
            201: openapi.Response("پست با موفقیت ایجاد شد"),
            400: openapi.Response("خطای اعتبارسنجی داده‌ها"),
            403: openapi.Response("دسترسی غیرمجاز")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user, status='pending')
        if post.scheduled_time and post.scheduled_time > timezone.localtime():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
        else:
            send_post_task.delay(post.id)


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        operation_summary="جزئیات، ویرایش و حذف پست",
        operation_description="نمایش جزئیات، ویرایش یا حذف پست توسط مالک آن.",
        responses={
            200: PostSerializer(),
            400: "خطای اعتبارسنجی",
            403: "عدم دسترسی",
            404: "پست یافت نشد"
        }
    )
    def get(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user != request.user:
            return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user != request.user:
            return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(status='pending')
        
        if post.scheduled_time and post.scheduled_time > timezone.now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
        else:
            send_post_task.delay(post.id)
        
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user != request.user:
            return Response({"detail": "دسترسی غیرمجاز"}, status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)
