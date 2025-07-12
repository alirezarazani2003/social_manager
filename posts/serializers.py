from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['status', 'error_message', 'created_at', 'sent_at', 'user']

    def validate(self, data):
        if not data.get('text') and not data.get('media_files'):
            raise serializers.ValidationError("باید حداقل یک متن یا یک رسانه ارسال کنید.")
        return data
