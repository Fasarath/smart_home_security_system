from django.urls import path
from .views import AuthenticateView, AuthLogView, RegisterView, DeleteView

urlpatterns = [
    path('authenticate/', AuthenticateView.as_view(), name='authenticate'),
    path('logs/', AuthLogView.as_view(), name='auth_logs'),
    path('register/', RegisterView.as_view(), name='register'),
    path('delete/', DeleteView.as_view(), name='delete'),
]
