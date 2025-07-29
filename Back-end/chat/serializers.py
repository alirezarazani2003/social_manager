from rest_framework import serializers
from .models import ChatSession, ChatMessage
import uuid

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    session_id = serializers.CharField(required=False)
    
    def validate_session_id(self, value):
        """اعتبارسنجی session_id برای پذیرش هم UUID و هم int"""
        if value is None:
            return None
            
        try:
            if isinstance(value, str):
                if value.isdigit():
                    return int(value)
                else:
                    uuid.UUID(value)
                    return value
        except (ValueError, TypeError):
            raise serializers.ValidationError("شناسه سشن نامعتبر است")
        
        return value