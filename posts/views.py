from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from .tasks import send_post_task
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from .models import Post
from .serializers import PostSerializer

from auth_app.permissions import IsEmailVerified

class PostCreateView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')

class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user).order_by('-created_at')
