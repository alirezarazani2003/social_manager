import json
from rest_framework import serializers
from .models import Post, MediaAttachment, UserMediaFile, UserMediaStorage
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
    
    class FlexibleListField(serializers.ListField):
        def to_internal_value(self, data):
            if isinstance(data, str):
                try:
                    parsed_data = json.loads(data)
                    return super().to_internal_value(parsed_data)
                except json.JSONDecodeError:
                    pass
            if not isinstance(data, list):
                data = [data]
            return super().to_internal_value(data)
    existing_media_ids = FlexibleListField(
        child=serializers.IntegerField(),
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
        """
        اعتبارسنجی سفارشی برای اطمینان از وجود حداقل متن یا رسانه.
        """
        existing_media_ids = data.get('existing_media_ids', [])
        
        media_files = data.get('media_files', [])
        has_media_content = bool(media_files) or bool(existing_media_ids)

        if not data.get('content') and not has_media_content:
            raise serializers.ValidationError("باید حداقل یک متن یا یک رسانه ارسال کنید.")

        if data.get('types') == "media":
            if not has_media_content:
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
        existing_media_ids = validated_data.pop('existing_media_ids', [])
        
        post = Post.objects.create(**validated_data)
        post.channels.set(channels)
        
        for file in media_files:
            MediaAttachment.objects.create(post=post, file=file)
        
        if existing_media_ids:
            existing_media_files = UserMediaFile.objects.filter(
                id__in=existing_media_ids, 
                user=post.user,
                is_active=True
            )
            for media_file in existing_media_files:
                MediaAttachment.objects.create(
                    post=post, 
                    file=media_file.file,
                    user_media_file=media_file
                )
        return post

    def update(self, instance, validated_data):
        channels = validated_data.pop('channels', None)
        media_files = validated_data.pop('media_files', None)
        existing_media_ids = validated_data.pop('existing_media_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if channels is not None:
            instance.channels.set(channels)
        if media_files is not None or existing_media_ids is not None:
            instance.attachments.all().delete()
            if media_files:
                for file in media_files:
                    MediaAttachment.objects.create(post=instance, file=file)
            
            if existing_media_ids:
                existing_media_files = UserMediaFile.objects.filter(
                    id__in=existing_media_ids, 
                    user=instance.user,
                    is_active=True
                )
                for media_file in existing_media_files:
                    MediaAttachment.objects.create(
                        post=instance, 
                        file=media_file.file,
                        user_media_file=media_file
                    )
        return instance

class UserMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserMediaFile
        fields = ['id', 'title', 'file', 'file_url', 'file_size', 'media_type', 'uploaded_at']
        read_only_fields = ['file_size', 'media_type', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

class UserMediaStorageSerializer(serializers.ModelSerializer):
    used_percentage = serializers.SerializerMethodField()
    used_space_mb = serializers.SerializerMethodField()
    total_space_mb = serializers.SerializerMethodField()
    remaining_space_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = UserMediaStorage
        fields = ['total_space', 'used_space', 'remaining_space','used_percentage', 'used_space_mb', 'total_space_mb', 'remaining_space_mb']
    
    def get_used_percentage(self, obj):
        if obj.total_space > 0:
            return round((obj.used_space / obj.total_space) * 100, 2)
        return 0
    
    def get_used_space_mb(self, obj):
        return round(obj.used_space / (1024*1024), 2)
    
    def get_total_space_mb(self, obj):
        return round(obj.total_space / (1024*1024), 2)
    
    def get_remaining_space_mb(self, obj):
        return round(obj.remaining_space() / (1024*1024), 2)
