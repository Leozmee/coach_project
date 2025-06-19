from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Page principale du chatbot
    path('', views.ChatbotView.as_view(), name='index'),
    
    # API pour les conversations
    path('api/chat/', views.ChatAPIView.as_view(), name='chat_api'),
    
    # Health check
    path('api/health/', views.health_check, name='health_check'),
]