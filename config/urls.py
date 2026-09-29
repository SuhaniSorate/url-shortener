from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from urls.views import redirect_view

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("admin/", admin.site.urls),
    path("api/", include("urls.urls")),
    path("<str:short_code>", redirect_view),
]