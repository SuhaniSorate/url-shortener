import hashlib
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from .models import ShortURL, ClickEvent
from .serializers import ShortURLSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ShortURLListCreateView(generics.ListCreateAPIView):
    serializer_class = ShortURLSerializer

    def get_throttles(self):
        # Rate-limit only link creation, not listing
        if self.request.method == "POST":
            self.throttle_scope = "create"
            return [ScopedRateThrottle()]
        return []

    def get_queryset(self):
        return ShortURL.objects.filter(owner=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ShortURLDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShortURLSerializer

    def get_queryset(self):
        return ShortURL.objects.filter(owner=self.request.user)


def detect_device(user_agent):
    ua = user_agent.lower()
    if "ipad" in ua or "tablet" in ua:
        return "tablet"
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    return "desktop"


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def redirect_view(request, short_code):
    cache_key = f"short:{short_code}"
    data = cache.get(cache_key)
    if data is None:
        # Cache miss: read from the database, then remember for 5 minutes
        link = get_object_or_404(ShortURL, short_code=short_code)
        data = {
            "id": link.id,
            "url": link.original_url,
            "active": link.is_active,
            "expires_at": link.expires_at,
        }
        cache.set(cache_key, data, 300)

    if not data["active"]:
        return HttpResponse("This link has been disabled.", status=410)
    if data["expires_at"] and data["expires_at"] < timezone.now():
        return HttpResponse("This link has expired.", status=410)

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
    ip_hash = hashlib.sha256(get_client_ip(request).encode()).hexdigest()
    ClickEvent.objects.create(
        url_id=data["id"],
        referrer=request.META.get("HTTP_REFERER", "")[:2048],
        user_agent=user_agent,
        device=detect_device(user_agent),
        ip_hash=ip_hash,
    )
    return HttpResponseRedirect(data["url"])


class AnalyticsView(APIView):
    def get(self, request, pk):
        link = get_object_or_404(ShortURL, pk=pk, owner=request.user)
        clicks = link.clicks.all()

        by_day = (clicks.annotate(day=TruncDate("timestamp"))
                  .values("day").annotate(count=Count("id")).order_by("day"))
        referrers = (clicks.exclude(referrer="").values("referrer")
                     .annotate(count=Count("id")).order_by("-count")[:5])
        devices = clicks.values("device").annotate(count=Count("id"))

        return Response({
            "short_code": link.short_code,
            "total_clicks": clicks.count(),
            "unique_visitors": clicks.exclude(ip_hash="").values("ip_hash").distinct().count(),
            "clicks_by_day": list(by_day),
            "top_referrers": list(referrers),
            "devices": list(devices),
        })