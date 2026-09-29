from django.db import models
from django.conf import settings

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base62(num):
    """Convert a number into a short Base62 string, e.g. 125 -> '21'."""
    if num == 0:
        return BASE62[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, 62)
        chars.append(BASE62[rem])
    return "".join(reversed(chars))


class ShortURL(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=30, unique=True, db_index=True, blank=True)
    custom_alias = models.CharField(max_length=30, blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="urls")

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class ClickEvent(models.Model):
    url = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name="clicks")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    referrer = models.CharField(max_length=2048, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    device = models.CharField(max_length=20, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)  # hashed for privacy

    def __str__(self):
        return f"click on {self.url.short_code} at {self.timestamp}"