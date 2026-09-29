from django.contrib import admin
from .models import ShortURL, ClickEvent


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ("short_code", "original_url", "owner", "is_active", "expires_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("short_code", "original_url")


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("url", "timestamp", "device", "referrer")
    list_filter = ("device",)