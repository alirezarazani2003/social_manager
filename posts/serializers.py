from rest_framework import serializers
from .models import Post, MediaAttachment
from django.utils import timezone


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
        if data.get("scheduled_time") and data["scheduled_time"] <= timezone.now():
            raise serializers.ValidationError("زمان زمان‌بندی باید در آینده باشد.")
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        post = Post.objects.create(**validated_data)
        for file in media_files:
            MediaAttachment.objects.create(post=post, file=file)
        return post

