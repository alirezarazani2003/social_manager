# chat/views.py
import requests
import uuid
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer, ChatRequestSerializer

class ChatSessionListCreateView(APIView):
    """
    List all chat sessions or create a new chat session
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="📜 دریافت لیست سشن‌های چت",
        operation_description="لیست تمام سشن‌های چت کاربر فعلی را برمی‌گرداند.",
        responses={
            200: openapi.Response('List of chat sessions', ChatSessionSerializer(many=True)),
            401: 'Authentication required'
        }
    )
    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'لیست سشن‌های چت با موفقیت دریافت شد'
        })

    @swagger_auto_schema(
        operation_summary="➕ ایجاد سشن چت جدید",
        operation_description="یک سشن چت جدید برای کاربر فعلی ایجاد می‌کند.",
        request_body=ChatSessionSerializer,
        responses={
            201: openapi.Response('Created chat session', ChatSessionSerializer),
            400: 'Bad Request',
            401: 'Authentication required'
        }
    )
    def post(self, request):
        serializer = ChatSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'سشن چت با موفقیت ایجاد شد'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'اطلاعات نامعتبر است',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ChatSessionDetailView(APIView):
    """
    Retrieve or delete a specific chat session
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="📄 دریافت جزئیات یک سشن چت",
        operation_description="جزئیات یک سشن چت خاص را برمی‌گرداند.",
        responses={
            200: openapi.Response('Chat session details', ChatSessionSerializer),
            401: 'Authentication required',
            404: 'Session not found'
        }
    )
    def get(self, request, pk):
        try:
            try:
                session_uuid = uuid.UUID(str(pk))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=pk, user=request.user)
            
            serializer = ChatSessionSerializer(session)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'جزئیات سشن چت با موفقیت دریافت شد'
            })
        except ChatSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'سشن چت یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="🗑 حذف یک سشن چت",
        operation_description="یک سشن چت خاص را حذف می‌کند.",
        responses={
            200: 'Session deleted successfully',
            401: 'Authentication required',
            404: 'Session not found'
        }
    )
    def delete(self, request, pk):
        try:
            try:
                session_uuid = uuid.UUID(str(pk))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=pk, user=request.user)
                
            session.delete()
            return Response({
                'success': True,
                'message': 'سشن چت با موفقیت حذف شد'
            })
        except ChatSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'سشن چت یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)

class SessionMessagesView(APIView):
    """
    Get all messages for a specific chat session
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="💬 دریافت پیام‌های یک سشن چت",
        operation_description="تمام پیام‌های یک سشن چت خاص را برمی‌گرداند.",
        responses={
            200: openapi.Response('List of chat messages', ChatMessageSerializer(many=True)),
            401: 'Authentication required',
            404: 'Session not found'
        }
    )
    def get(self, request, session_id):
        try:
            try:
                session_uuid = uuid.UUID(str(session_id))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=session_id, user=request.user)
                
            messages = session.messages.all().order_by('created_at')
            serializer = ChatMessageSerializer(messages, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'پیام‌های سشن چت با موفقیت دریافت شد'
            })
        except ChatSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'سشن چت یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)


chat_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['message'],
    properties={
        'message': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='پیام کاربر برای ارسال به هوش مصنوعی',
            example='سلام، چطوری؟'
        ),
        'session_id': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='شناسه سشن چت (اختیاری - اگر نباشد سشن جدید ایجاد می‌شود)',
            example='123e4567-e89b-12d3-a456-426614174000'
        ),
    }
)

chat_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='وضعیت موفقیت عملیات'),
        'data': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'session_id': openapi.Schema(type=openapi.TYPE_STRING, description='شناسه سشن چت'),
                'user_message': openapi.Schema(type=openapi.TYPE_OBJECT, description='پیام کاربر'),
                'ai_message': openapi.Schema(type=openapi.TYPE_OBJECT, description='پاسخ هوش مصنوعی'),
            }
        ),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='پیام نتیجه عملیات')
    }
)

class ChatMessageView(APIView):
    """
    Send a message to AI and get response
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="🤖 چت با هوش مصنوعی",
        operation_description="ارسال پیام به هوش مصنوعی و دریافت پاسخ آن. اگر session_id ارسال نشود، یک سشن جدید ایجاد خواهد شد.",
        request_body=chat_request_schema,
        responses={
            200: chat_response_schema,
            400: openapi.Response('Bad Request'),
            401: openapi.Response('Authentication required'),
            500: openapi.Response('AI Service Error')
        }
    )
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'اطلاعات نامعتبر است',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')

        if session_id:
            try:
                if isinstance(session_id, str):
                    try:
                        session_uuid = uuid.UUID(session_id)
                        session = ChatSession.objects.get(pk=session_uuid, user=request.user)
                    except (ValueError, ChatSession.DoesNotExist):
                        try:
                            session = ChatSession.objects.get(pk=int(session_id), user=request.user)
                        except (ValueError, ChatSession.DoesNotExist):
                            return Response({
                                'success': False,
                                'message': 'سشن چت یافت نشد'
                            }, status=status.HTTP_404_NOT_FOUND)
                else:
                    session = ChatSession.objects.get(pk=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'سشن چت یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            session_title = message[:50] + "..." if len(message) > 50 else message
            session = ChatSession.objects.create(
                user=request.user,
                title=session_title
            )

        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )

        try:
            ai_response = self.get_ai_response(message, session)
            ai_message = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=ai_response
            )
            return Response({
                'success': True,
                'data': {
                    'session_id': str(session.id),
                    'user_message': ChatMessageSerializer(user_message).data,
                    'ai_message': ChatMessageSerializer(ai_message).data
                },
                'message': 'پاسخ هوش مصنوعی با موفقیت دریافت شد'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'خطا در ارتباط با سرویس هوش مصنوعی: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_ai_response(self, message, session):
            ai_service_url = getattr(settings, 'AI_SERVICE_URL', 'http://192.168.1.102:8001')
            history = []
            all_messages = session.messages.all().order_by('created_at')
            for msg in all_messages:
                history.append({
                    'role': msg.role,
                    'content': msg.content
                })
            payload = {'message': message, 'history': history}
            response = requests.post(f"{ai_service_url}/api/chat", json=payload, timeout=600)
            response.raise_for_status()
            return response.json().get('response', 'پاسخی از سرویس دریافت نشد')