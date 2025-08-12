from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Post, MediaAttachment, UserMediaFile, UserMediaStorage
from .serializers import PostSerializer, UserMediaSerializer, UserMediaStorageSerializer
from .tasks import send_post_task
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from auth_app.permissions import IsEmailVerified
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
import os
import logging
import uuid
from core.logging_filters import set_user_id, set_request_id, set_client_ip
from config.throttles import RoleBasedRateThrottle

logger = logging.getLogger('posts.activity')
security_logger = logging.getLogger('posts.security')
error_logger = logging.getLogger('posts.errors')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PostCreateView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'

    @swagger_auto_schema(
        operation_summary="ارسال پست (فوری یا زمان‌بندی‌شده)",
        operation_description="این ویو به شما امکان ارسال پست متنی یا چندرسانه‌ای به یک یا چند کانال را می‌دهد. اگر `scheduled_time` مشخص شود، پست در آن زمان ارسال می‌شود.",
        responses={
            201: openapi.Response("پست با موفقیت ایجاد شد"),
            400: openapi.Response("خطای اعتبارسنجی داده‌ها"),
            403: openapi.Response("دسترسی غیرمجاز")
        }
    )
    def post(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} attempting to create new post from IP={client_ip}")
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user, status='pending')
        logger.info(f"Post {post.id} created by user {self.request.user.id} (scheduled: {bool(post.scheduled_time)})")

        if post.scheduled_time and post.scheduled_time > timezone.now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
            logger.info(f"Post {post.id} scheduled for {post.scheduled_time}")
        else:
            send_post_task.delay(post.id)
            logger.info(f"Post {post.id} sent to immediate queue")


class PostPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    pagination_class = PostPagination
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Post.objects.none()

        queryset = Post.objects.filter(user=self.request.user).order_by('-created_at')
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            logger.info(f"User {self.request.user.id} filtering posts by status={status}")

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} accessed post list from IP={client_ip}")
        return super().get(request, *args, **kwargs)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Post.objects.none()
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
        instance = self.get_object()
        logger.info(f"User {request.user.id} viewed post {instance.id}")
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        old_status = post.status

        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} updating post {post.id} (status: {old_status})")

        serializer = self.get_serializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(status='pending')

        if post.scheduled_time and post.scheduled_time > timezone.now():
            send_post_task.apply_async(args=[post.id], eta=post.scheduled_time)
            logger.info(f"Post {post.id} rescheduled for {post.scheduled_time}")
        else:
            send_post_task.delay(post.id)
            logger.info(f"Post {post.id} sent to immediate queue after update")

        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user.id} attempting to delete post {instance.id}")
        response = super().delete(request, *args, **kwargs)
        if response.status_code == 204:
            logger.info(f"Post {instance.id} successfully deleted by user {request.user.id}")
        return response


class ProtectedMediaView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        try:
            attachment = MediaAttachment.objects.select_related("post__user").get(id=attachment_id)
            logger.info(f"User {request.user.id} attempting to access media attachment {attachment_id}")
        except MediaAttachment.DoesNotExist:
            security_logger.warning(f"User {request.user.id} tried to access non-existent attachment {attachment_id}")
            return Response({
                "status": "error",
                "message": "فایل مورد نظر یافت نشد."
            }, status=status.HTTP_404_NOT_FOUND)

        if request.user != attachment.post.user and not request.user.is_staff:
            security_logger.warning(f"User {request.user.id} tried to access unauthorized attachment {attachment_id}")
            return Response({
                "status": "error",
                "message": "شما اجازه دسترسی به این فایل را ندارید."
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            response = FileResponse(attachment.file.open("rb"), content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{attachment.file.name}"'
            logger.info(f"User {request.user.id} successfully downloaded attachment {attachment_id}")
            return response
        except Exception as e:
            error_logger.error(f"Failed to read file {attachment.file.path}: {e}")
            return Response({
                "status": "error",
                "message": "خطا در خواندن فایل."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelScheduledPostView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    @swagger_auto_schema(
        operation_summary="لغو پست زمان‌بندی‌شده",
        operation_description="این API به شما اجازه می‌دهد پست‌هایی که هنوز ارسال نشده‌اند (و زمان‌بندی‌شده‌اند) را لغو کنید.",
        responses={
            200: openapi.Response("پست با موفقیت لغو شد"),
            400: openapi.Response("پست قبلاً ارسال شده یا لغو آن ممکن نیست"),
            403: openapi.Response("دسترسی غیرمجاز"),
            404: openapi.Response("پست یافت نشد")
        }
    )
    def post(self, request, post_id):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        post = get_object_or_404(Post, id=post_id, user=request.user)
        logger.info(f"User {request.user.id} attempting to cancel scheduled post {post.id}")

        if post.status != 'pending' or not post.scheduled_time:
            security_logger.warning(f"Cancel failed: post {post.id} not pending or not scheduled")
            return Response({
                "detail": "امکان لغو این پست وجود ندارد. یا ارسال شده یا زمان‌بندی ندارد."
            }, status=status.HTTP_400_BAD_REQUEST)

        if post.scheduled_time <= timezone.now():
            security_logger.warning(f"Cancel failed: post {post.id} is already past scheduled time")
            return Response({
                "detail": "زمان ارسال پست گذشته است. امکان لغو وجود ندارد."
            }, status=status.HTTP_400_BAD_REQUEST)

        post.status = 'cancelled'
        post.save()
        logger.info(f"Post {post.id} cancelled by user {request.user.id}")

        return Response({"detail": "پست با موفقیت لغو شد."}, status=status.HTTP_200_OK)


class RetryPostView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    @swagger_auto_schema(
        operation_summary="ارسال مجدد پست ناموفق",
        operation_description="این API پست ناموفق را دوباره به صف ارسال می‌افزاید",
        responses={
            200: openapi.Response("پست با موفقیت به صف ارسال مجدد اضافه شد"),
            400: openapi.Response("پست قابل ارسال مجدد نیست"),
            403: openapi.Response("دسترسی غیرمجاز"),
            404: openapi.Response("پست یافت نشد")
        }
    )
    def post(self, request, post_id):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        post = get_object_or_404(Post, id=post_id, user=request.user)
        logger.info(f"User {request.user.id} attempting to retry failed post {post.id}")

        if post.status != 'failed':
            security_logger.warning(f"Retry failed: post {post.id} is not in 'failed' status")
            return Response({
                "detail": "فقط پست‌های ناموفق قابل ارسال مجدد هستند."
            }, status=status.HTTP_400_BAD_REQUEST)

        post.status = 'pending'
        post.error_message = None
        post.save()

        send_post_task.delay(post.id)
        logger.info(f"Post {post.id} retried by user {request.user.id}")

        return Response({
            "detail": "پست با موفقیت به صف ارسال مجدد اضافه شد."
        }, status=status.HTTP_200_OK)


class UserMediaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    serializer_class = UserMediaSerializer
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    def get_queryset(self):
        return UserMediaFile.objects.filter(user=self.request.user, is_active=True)

    def create(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        storage, created = UserMediaStorage.objects.get_or_create(user=request.user)
        logger.info(f"User {request.user.id} attempting to upload media file from IP={client_ip}")

        if 'file' not in request.FILES:
            security_logger.warning(f"User {request.user.id} tried to upload without file")
            return Response({'error': 'فایل ارسال نشده'}, status=status.HTTP_400_BAD_REQUEST)

        file_size = request.FILES['file'].size
        if not storage.can_upload(file_size):
            logger.warning(f"User {request.user.id} exceeded storage limit (file size: {file_size})")
            return Response(
                {'error': 'فضای کافی وجود ندارد'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            media_file = serializer.save(user=request.user, file_size=file_size)
            storage.add_used_space(file_size)
            logger.info(f"User {request.user.id} uploaded media file {media_file.id} ({file_size} bytes)")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            security_logger.warning(f"Invalid media upload data from user {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def storage_info(self, request):
        storage, created = UserMediaStorage.objects.get_or_create(user=request.user)
        serializer = UserMediaStorageSerializer(storage)
        logger.info(f"User {request.user.id} accessed storage info")
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_media_list(self, request):
        media_files = self.get_queryset().order_by('-uploaded_at')
        serializer = UserMediaSerializer(media_files, many=True, context={'request': request})
        logger.info(f"User {request.user.id} accessed media list")
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        media_file = self.get_object()
        logger.info(f"User {request.user.id} attempting to delete media file {media_file.id}")

        if media_file.file:
            file_path = media_file.file.path
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Media file {file_path} deleted from filesystem")

        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            logger.info(f"Media file {media_file.id} successfully deleted from database")
        return response