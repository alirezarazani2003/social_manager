from django.urls import path, include
from .views import PostCreateView, PostListView, PostDetailView, ProtectedMediaView, CancelScheduledPostView, RetryPostView, UserMediaViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'user-media', UserMediaViewSet, basename='user-media')

urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path('create/', PostCreateView.as_view(), name='post-create'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('media/<int:attachment_id>/', ProtectedMediaView.as_view(), name='protected-media'),
    path('<int:post_id>/cancel/', CancelScheduledPostView.as_view(), name='cancel-scheduled-post'),
    path('<int:post_id>/retry/', RetryPostView.as_view(), name='retry-post'),
    path('media/', include(router.urls)),
]