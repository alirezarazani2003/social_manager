from django.urls import path
from .views import PostCreateView, PostListView, PostDetailView,ProtectedMediaView

urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/media/<int:attachment_id>/', ProtectedMediaView.as_view(), name='protected-media'),

]
