from django.contrib import admin
from django.urls import path, include
from urls.views import redirect_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("urls.urls")),
    path("<str:short_code>", redirect_view),
]