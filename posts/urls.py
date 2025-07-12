from django.urls import path
from .views import PostCreateView

urlpatterns = [
    path('create/', PostCreateView.as_view(), name='create_post'),
]
