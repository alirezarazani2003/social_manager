from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Channel
from .serializers import ChannelSerializer
from .services import verify_telegram_channel
from auth_app.permissions import IsEmailVerified


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ChannelCreateView(generics.CreateAPIView):
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform = serializer.validated_data['platform']
        username = serializer.validated_data['username']

        if platform == 'telegram':
            is_ok, result = verify_telegram_channel(username)
        else:
            return Response({"detail": _("پلتفرم نامعتبر است.")}, status=status.HTTP_400_BAD_REQUEST)

        if not is_ok:
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
            platform_channel_id=result["chat_id"]
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ChannelListView(generics.ListAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Channel.objects.all().order_by('-id')
    @swagger_auto_schema(
        operation_summary="لیست کانال‌های ثبت‌شده",
        operation_description="لیست کانال‌هایی که کاربر فعلی ثبت کرده را نمایش می‌دهد.",
        responses={200: ChannelSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Channel.objects.filter(user=self.request.user)


class ChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
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
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        new_username = serializer.validated_data.get('username')
        new_platform = serializer.validated_data.get('platform')

        if (new_username != instance.username) or (new_platform != instance.platform):
            is_ok, result = verify_channel(new_platform, new_username)
            if not is_ok:
                return Response(
                    {"detail": _("عدم توانایی در تأیید کانال پس از ویرایش"), "reason": result},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save(is_verified=True, failed_reason="", platform_channel_id=result)
        else:
            serializer.save()

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
        return super().delete(request, *args, **kwargs)

