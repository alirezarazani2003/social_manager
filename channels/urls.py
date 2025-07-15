from django.urls import path
from .views import ChannelCreateView, ChannelListView, ChannelDetailView

urlpatterns = [
    path('', ChannelListView.as_view(), name='channel-list'),
    path('create/', ChannelCreateView.as_view(), name='channel-create'),
    path('<int:pk>/', ChannelDetailView.as_view(), name='channel-detail'),
]