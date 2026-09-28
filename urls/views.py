import hashlib
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ShortURL, ClickEvent
from .serializers import ShortURLSerializer


class ShortURLCreateView(generics.CreateAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer


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
    link = get_object_or_404(ShortURL, short_code=short_code)
    if not link.is_active:
        return HttpResponse("This link has been disabled.", status=410)
    if link.expires_at and link.expires_at < timezone.now():
        return HttpResponse("This link has expired.", status=410)

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
    ip_hash = hashlib.sha256(get_client_ip(request).encode()).hexdigest()
    ClickEvent.objects.create(
        url=link,
        referrer=request.META.get("HTTP_REFERER", "")[:2048],
        user_agent=user_agent,
        device=detect_device(user_agent),
        ip_hash=ip_hash,
    )
    return HttpResponseRedirect(link.original_url)


class AnalyticsView(APIView):
    def get(self, request, pk):
        link = get_object_or_404(ShortURL, pk=pk)
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