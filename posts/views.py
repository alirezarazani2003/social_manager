from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Post, MediaAttachment
from .serializers import PostSerializer
from .tasks import send_post_task
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from auth_app.permissions import IsEmailVerified
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied


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
        channel = serializer.validated_data.get("channel")
        if channel.user != self.request.user:
            raise PermissionDenied("شما اجازه ارسال پست به این کانال را ندارید.")
        
        post = serializer.save(user=self.request.user, status='pending')
        if post.scheduled_time and post.scheduled_time > timezone.now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
        else:
            send_post_task.delay(post.id)


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        post = self.get_object()

        serializer = self.get_serializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(status='pending')

        if post.scheduled_time and post.scheduled_time > timezone.now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
        else:
            send_post_task.delay(post.id)

        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class ProtectedMediaView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="دریافت امن فایل رسانه‌ای",
        operation_description="دریافت فایل رسانه‌ای فقط توسط صاحب پست یا ادمین",
        manual_parameters=[
            openapi.Parameter(
                'attachment_id',
                openapi.IN_PATH,
                description="شناسه فایل رسانه‌ای",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: 'فایل با موفقیت بازگردانده شد',
            403: 'شما اجازه دسترسی ندارید',
            404: 'فایل پیدا نشد',
            500: 'خطا در خواندن فایل'
        }
    )
    def get(self, request, attachment_id):
        try:
            attachment = MediaAttachment.objects.select_related("post__user").get(id=attachment_id)
        except MediaAttachment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "فایل مورد نظر یافت نشد."
            }, status=status.HTTP_404_NOT_FOUND)

        if request.user != attachment.post.user and not request.user.is_staff:
            return Response({
                "status": "error",
                "message": "شما اجازه دسترسی به این فایل را ندارید."
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            response = FileResponse(attachment.file.open("rb"), content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{attachment.file.name}"'
            return response
        except Exception:
            return Response({
                "status": "error",
                "message": "خطا در خواندن فایل."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
