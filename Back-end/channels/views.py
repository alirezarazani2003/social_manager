from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Channel
from .serializers import ChannelSerializer
from .services import verify_telegram_channel, verify_bale_channel
from auth_app.permissions import IsEmailVerified
from rest_framework import generics
import logging
from core.logging_filters import set_user_id, set_request_id, set_client_ip
import uuid
from config.throttles import RoleBasedRateThrottle

logger = logging.getLogger('channels.activity')
security_logger = logging.getLogger('channels.security')
error_logger = logging.getLogger('channels.errors')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ChannelCreateView(generics.CreateAPIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    queryset = Channel.objects.all().order_by('id')
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    @swagger_auto_schema(
        operation_summary="ثبت کانال جدید (در صورت موفقیت در وریفای)",
        operation_description="اگر ربات دسترسی به کانال داشته باشد، کانال ذخیره می‌شود. در غیر این صورت پیام خطا برمی‌گردد.",
        responses={
            201: openapi.Response("کانال با موفقیت ثبت شد"),
            400: openapi.Response("خطای اعتبارسنجی یا عدم دسترسی ربات به کانال"),
            403: openapi.Response("دسترسی غیرمجاز یا ایمیل وریفای نشده"),
        }
    )
    def post(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform = serializer.validated_data['platform']
        username = serializer.validated_data['username']

        logger.info(f"User {request.user.id} attempting to add {platform} channel @{username} from IP={client_ip}")

        if platform == 'telegram':
            is_ok, result = verify_telegram_channel(username)
        elif platform == 'bale':
            is_ok, result = verify_bale_channel(username)
        else:
            security_logger.warning(f"Invalid platform '{platform}' requested by user {request.user.id}")
            return Response({"detail": _("پلتفرم نامعتبر است.")}, status=status.HTTP_400_BAD_REQUEST)

        if not is_ok:
            security_logger.warning(f"Channel verification failed for @{username} on {platform} by user {request.user.id}: {result}")
            return Response(
                {
                    "detail": _("عدم توانایی در تأیید کانال"),
                    "reason": result
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(
            user=request.user,
            is_verified=True,
            platform_channel_id=result.get("chat_id", "unknown")
        )

        logger.info(f"User {request.user.id} successfully added {platform} channel @{username}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChannelListView(generics.ListAPIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Channel.objects.all().order_by('-id')

    @swagger_auto_schema(
        operation_summary="لیست کانال‌های ثبت‌شده",
        operation_description="لیست کانال‌هایی که کاربر فعلی ثبت کرده را نمایش می‌دهد.",
        responses={200: ChannelSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} accessed channel list from IP={client_ip}")
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user)


class ChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [RoleBasedRateThrottle]
    throttle_scope = 'user'

    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified, IsOwner]

    @swagger_auto_schema(
        operation_summary="مشاهده اطلاعات کانال",
        operation_description="نمایش جزئیات یک کانال خاص (فقط درصورتی که مالک آن باشید).",
        responses={
            200: ChannelSerializer(),
            403: "دسترسی غیرمجاز یا ایمیل تایید نشده",
            404: "کانال پیدا نشد"
        }
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"User {request.user.id} viewed channel {instance.id} ({instance.platform}:@{instance.username})")
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="ویرایش کانال",
        operation_description="ویرایش اطلاعات یک کانال ثبت‌شده (فقط توسط مالک مجاز است).",
        responses={
            200: ChannelSerializer(),
            400: "ورودی نامعتبر",
            403: "عدم دسترسی",
            404: "یافت نشد"
        }
    )
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        old_username = instance.username
        old_platform = instance.platform

        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        new_username = serializer.validated_data.get('username')
        new_platform = serializer.validated_data.get('platform')

        logger.info(f"User {request.user.id} updating channel {instance.id}: {old_platform}:@{old_username} -> {new_platform}:@{new_username}")
        if (new_username != old_username) or (new_platform != old_platform):
            if new_platform == 'telegram':
                is_ok, result = verify_telegram_channel(new_username)
            elif new_platform == 'bale':
                is_ok, result = verify_bale_channel(new_username)
            else:
                security_logger.warning(f"Invalid new platform '{new_platform}' in update by user {request.user.id}")
                return Response(
                    {"detail": _("پلتفرم نامعتبر است.")},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not is_ok:
                security_logger.warning(f"Verification failed during update of channel {instance.id}: {result}")
                return Response(
                    {"detail": _("عدم توانایی در تأیید کانال پس از ویرایش"), "reason": result},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save(is_verified=True, failed_reason="", platform_channel_id=result.get("chat_id", "unknown"))
        else:
            serializer.save()

        logger.info(f"User {request.user.id} successfully updated channel {instance.id}")
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="حذف کانال",
        operation_description="حذف یک کانال (فقط توسط مالک مجاز است).",
        responses={
            204: "با موفقیت حذف شد",
            403: "عدم دسترسی",
            404: "یافت نشد"
        }
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        platform = instance.platform
        username = instance.username

        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} attempting to delete {platform} channel @{username}")

        response = super().delete(request, *args, **kwargs)
        
        if response.status_code == 204:
            logger.info(f"User {request.user.id} successfully deleted {platform} channel @{username}")
        else:
            security_logger.warning(f"Delete failed for channel {instance.id} by user {request.user.id}")

        return response