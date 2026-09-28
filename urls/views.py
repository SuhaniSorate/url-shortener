from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from .models import ShortURL
from .serializers import ShortURLSerializer


class ShortURLCreateView(generics.CreateAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer


def redirect_view(request, short_code):
    link = get_object_or_404(ShortURL, short_code=short_code)
    if not link.is_active:
        return HttpResponse("This link has been disabled.", status=410)
    if link.expires_at and link.expires_at < timezone.now():
        return HttpResponse("This link has expired.", status=410)
    return HttpResponseRedirect(link.original_url)