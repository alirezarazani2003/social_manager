from rest_framework import serializers
from .models import Post, MediaAttachment
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from channels.models import Channel

class MediaAttachmentSerializer(serializers.ModelSerializer):
    secure_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAttachment
        fields = ['id', 'file', 'secure_url']

    def get_secure_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/media/secure/{obj.id}/")
        return None


class PostSerializer(serializers.ModelSerializer):
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    attachments = serializers.SerializerMethodField()
    channels = serializers.PrimaryKeyRelatedField(many=True, queryset=Channel.objects.all())

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ["status", "error_message", "created_at", "status_display", "user"]

    def get_attachments(self, obj):
        request = self.context.get("request")
        return MediaAttachmentSerializer(obj.attachments.all(), many=True, context={'request': request}).data

    def validate(self, data):
        if not data.get('content') and not data.get('media_files'):
            raise serializers.ValidationError("باید حداقل یک متن یا یک رسانه ارسال کنید.")
        
        if not data.get('media_files') and data.get('types')=="media":
            raise serializers.ValidationError("مدیا یافت نشد")
        
        if data.get("scheduled_time") and data["scheduled_time"] <= timezone.now():
            raise serializers.ValidationError("زمان زمان‌بندی باید در آینده باشد.")
        
        channels = data.get('channels', [])
        if not channels:
            raise serializers.ValidationError("حداقل یک کانال باید انتخاب کنید.")
        
        request = self.context.get("request")
        if request:
            for channel in channels:
                if channel.user != request.user:
                    raise ValidationError(f"کانال {channel.username} متعلق به شما نیست.")
        return data

    def create(self, validated_data):
        channels = validated_data.pop('channels', [])
        media_files = validated_data.pop('media_files', [])
        post = Post.objects.create(**validated_data)
        post.channels.set(channels)  # تنظیم چند کانال
        for file in media_files:
            MediaAttachment.objects.create(post=post, file=file)
        return post

    def update(self, instance, validated_data):
        channels = validated_data.pop('channels', None)
        media_files = validated_data.pop('media_files', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if channels is not None:
            instance.channels.set(channels)
        if media_files is not None:
            instance.attachments.all().delete()
            for file in media_files:
                MediaAttachment.objects.create(post=instance, file=file)
                
        return instance