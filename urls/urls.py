from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (RegisterView, ShortURLListCreateView,
                    ShortURLDetailView, AnalyticsView)

urlpatterns = [
    path("register", RegisterView.as_view()),
    path("login", TokenObtainPairView.as_view()),
    path("token/refresh", TokenRefreshView.as_view()),
    path("urls", ShortURLListCreateView.as_view()),
    path("urls/<int:pk>", ShortURLDetailView.as_view()),
    path("urls/<int:pk>/analytics", AnalyticsView.as_view()),
]