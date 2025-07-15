from rest_framework import serializers
from .models import Post , MediaAttachment
from django.utils import timezone


class PostSerializer(serializers.ModelSerializer):
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ["status", "error_message", "created_at", "status_display","user"]

    def validate(self, data):
        if not data.get('content') and not data.get('media_files'):
            raise serializers.ValidationError("باید حداقل یک متن یا یک رسانه ارسال کنید.")
        
        if data.get("scheduled_time") and data["scheduled_time"] <= timezone.now():
            raise serializers.ValidationError("زمان زمان‌بندی باید در آینده باشد.")
        return data
    
    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        attachments_data = validated_data.pop('attachments', [])
        post = Post.objects.create(**validated_data)
        
        for file in media_files:
            MediaAttachment.objects.create(post=post, file=file)
            
        for attach_data in attachments_data:
            MediaAttachment.objects.create(post=post, file=attach_data)
        return post

class MediaAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAttachment
        fields = ['id', 'file']
