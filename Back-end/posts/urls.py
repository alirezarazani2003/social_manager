from django.urls import path
from .views import PostCreateView, PostListView, PostDetailView, ProtectedMediaView, CancelScheduledPostView, RetryPostView

urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('media/<int:attachment_id>/', ProtectedMediaView.as_view(), name='protected-media'),
    path('<int:post_id>/cancel/', CancelScheduledPostView.as_view(), name='cancel-scheduled-post'),
    path('<int:post_id>/retry/', RetryPostView.as_view(), name='retry-post'),
]