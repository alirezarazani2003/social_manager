from django.urls import path
from . import views

urlpatterns = [
    path('sessions/', views.ChatSessionListCreateView.as_view(), name='session-list'),
    path('sessions/<uuid:pk>/', views.ChatSessionDetailView.as_view(), name='session-detail'),
    path('chat/', views.ChatMessageView.as_view(), name='chat-message'),
    path('sessions/<uuid:session_id>/messages/', views.SessionMessagesView.as_view(), name='session-messages'),
    path('prompts/', views.SavedPromptView.as_view(), name='saved-prompts'),
    path('prompts/<uuid:pk>/', views.SavedPromptView.as_view(), name='saved-prompt-detail'),
]
