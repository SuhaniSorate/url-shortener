from django.urls import path
from .views import ShortURLCreateView, AnalyticsView

urlpatterns = [
    path("urls", ShortURLCreateView.as_view()),
    path("urls/<int:pk>/analytics", AnalyticsView.as_view()),
]