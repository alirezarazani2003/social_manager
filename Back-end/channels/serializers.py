from rest_framework import serializers
from .models import Channel


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'username', 'platform', 'is_verified', 'failed_reason', 'platform_channel_id', 'created_at']
        read_only_fields = ['is_verified', 'failed_reason', 'platform_channel_id', 'created_at']

    def validate_username(self, value):
        if not value.startswith('@'):
            raise serializers.ValidationError("شناسه کانال باید با @ شروع شود.")

        user = self.context['request'].user
        qs = Channel.objects.filter(user=user, username=value)
        
        if self.instance:
            # qs = Channel.objects.filter(user=user, username=value).exclude(id=self.instance.id)
            qs = qs.exclude(id=self.instance.id)
        else:
            qs = Channel.objects.filter(user=user, username=value)

        if qs.exists():
            raise serializers.ValidationError("این کانال قبلاً توسط شما ثبت شده است.")
        return value
