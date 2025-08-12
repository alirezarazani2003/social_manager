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
import logging
from core.logging_filters import set_user_id, set_request_id, set_client_ip

logger = logging.getLogger('chat.activity')
error_logger = logging.getLogger('chat.errors')
security_logger = logging.getLogger('chat.security')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class ChatSessionListCreateView(APIView):
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} accessed chat session list from IP={client_ip}")
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} attempting to create new chat session from IP={client_ip}")
        serializer = ChatSessionSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save(user=request.user)
            logger.info(f"User {request.user.id} created chat session {session.id}")
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'سشن چت با موفقیت ایجاد شد'
            }, status=status.HTTP_201_CREATED)
        else:
            security_logger.warning(f"Invalid chat session data from user {request.user.id}: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'اطلاعات نامعتبر است',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ChatSessionDetailView(APIView):
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        try:
            try:
                session_uuid = uuid.UUID(str(pk))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=pk, user=request.user)
            
            logger.info(f"User {request.user.id} viewed chat session {session.id}")
            serializer = ChatSessionSerializer(session)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'جزئیات سشن چت با موفقیت دریافت شد'
            })
        except ChatSession.DoesNotExist:
            security_logger.warning(f"User {request.user.id} tried to access non-existent chat session {pk}")
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        try:
            try:
                session_uuid = uuid.UUID(str(pk))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=pk, user=request.user)
                
            logger.info(f"User {request.user.id} attempting to delete chat session {session.id}")
            session.delete()
            logger.info(f"User {request.user.id} successfully deleted chat session {session.id}")
            return Response({
                'success': True,
                'message': 'سشن چت با موفقیت حذف شد'
            })
        except ChatSession.DoesNotExist:
            security_logger.warning(f"User {request.user.id} tried to delete non-existent chat session {pk}")
            return Response({
                'success': False,
                'message': 'سشن چت یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)


class SessionMessagesView(APIView):
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        try:
            try:
                session_uuid = uuid.UUID(str(session_id))
                session = ChatSession.objects.get(pk=session_uuid, user=request.user)
            except (ValueError, uuid.UUIDError):
                session = ChatSession.objects.get(pk=session_id, user=request.user)
                
            logger.info(f"User {request.user.id} accessed messages of chat session {session.id}")
            messages = session.messages.all().order_by('created_at')
            serializer = ChatMessageSerializer(messages, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'پیام‌های سشن چت با موفقیت دریافت شد'
            })
        except ChatSession.DoesNotExist:
            security_logger.warning(f"User {request.user.id} tried to access messages of non-existent chat session {session_id}")
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
        request_id = str(uuid.uuid4())[:8]
        client_ip = get_client_ip(request)
        set_request_id(request_id)
        set_client_ip(client_ip)
        set_user_id(request.user.id)

        logger.info(f"User {request.user.id} sending message to AI from IP={client_ip}")
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            security_logger.warning(f"Invalid chat message data from user {request.user.id}: {serializer.errors}")
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
                            security_logger.warning(f"User {request.user.id} tried to access invalid session ID: {session_id}")
                            return Response({
                                'success': False,
                                'message': 'سشن چت یافت نشد'
                            }, status=status.HTTP_404_NOT_FOUND)
                else:
                    session = ChatSession.objects.get(pk=session_id, user=request.user)
                logger.info(f"User {request.user.id} using existing session {session.id}")
            except ChatSession.DoesNotExist:
                security_logger.warning(f"User {request.user.id} tried to access non-existent session {session_id}")
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
            logger.info(f"User {request.user.id} created new session {session.id} for chat")

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
            logger.info(f"AI responded successfully to user {request.user.id} in session {session.id}")
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
            error_logger.error(f"Failed to get AI response for user {request.user.id} in session {session.id}: {e}")
            return Response({
                'success': False,
                'message': f'خطا در ارتباط با سرویس هوش مصنوعی: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_ai_response(self, message, session):
        ai_service_url = getattr(settings, 'AI_SERVICE_URL')
        history = []
        all_messages = session.messages.all().order_by('created_at')
        for msg in all_messages:
            history.append({
                'role': msg.role,
                'content': msg.content
            })
        payload = {'message': message, 'history': history}
        try:
            response = requests.post(
                f"{ai_service_url}/api/chat",
                json=payload,
                timeout=600,
                proxies={"http": None, "https": None}
            )
            response.raise_for_status()
            ai_response = response.json().get('response', 'پاسخی از سرویس دریافت نشد')
            logger.info(f"AI service responded successfully for session {session.id}")
            return ai_response
        except requests.exceptions.Timeout:
            error_logger.error(f"AI service timeout for session {session.id}")
            raise Exception("سرویس هوش مصنوعی در زمان تعیین شده پاسخ نداد")
        except requests.exceptions.ConnectionError:
            error_logger.error(f"Connection error to AI service for session {session.id}")
            raise Exception("عدم توانایی در اتصال به سرویس هوش مصنوعی")
        except Exception as e:
            error_logger.error(f"AI service error for session {session.id}: {e}")
            raise Exception(f"خطای سرویس هوش مصنوعی: {str(e)}")