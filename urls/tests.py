from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import ShortURL, encode_base62


class Base62Tests(TestCase):
    def test_zero(self):
        self.assertEqual(encode_base62(0), "0")

    def test_known_values(self):
        self.assertEqual(encode_base62(61), "Z")
        self.assertEqual(encode_base62(62), "10")

    def test_codes_are_unique(self):
        codes = {encode_base62(i) for i in range(1, 2000)}
        self.assertEqual(len(codes), 1999)


class ApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("alice", password="pass1234")
        self.other = User.objects.create_user("bob", password="pass1234")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_generates_short_code(self):
        r = self.client.post("/api/urls", {"original_url": "https://example.com"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["short_code"])

    def test_custom_alias_and_duplicate(self):
        body = {"original_url": "https://example.com", "custom_alias": "mylink"}
        self.assertEqual(self.client.post("/api/urls", body, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/urls", body, format="json").status_code, 400)

    def test_invalid_url_rejected(self):
        r = self.client.post("/api/urls", {"original_url": "not-a-url"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_requires_login(self):
        r = APIClient().get("/api/urls")
        self.assertEqual(r.status_code, 401)

    def test_user_cannot_touch_others_links(self):
        link = ShortURL.objects.create(original_url="https://a.com", short_code="abc", owner=self.other)
        self.assertEqual(self.client.delete(f"/api/urls/{link.id}").status_code, 404)


class RedirectTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_redirect_works(self):
        ShortURL.objects.create(original_url="https://example.com", short_code="abc")
        r = self.client.get("/abc")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com")

    def test_missing_code_is_404(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)

    def test_expired_link_is_410(self):
        ShortURL.objects.create(original_url="https://example.com", short_code="old",
                                expires_at=timezone.now() - timedelta(days=1))
        self.assertEqual(self.client.get("/old").status_code, 410)

    def test_disabled_link_is_410(self):
        ShortURL.objects.create(original_url="https://example.com", short_code="off", is_active=False)
        self.assertEqual(self.client.get("/off").status_code, 410)

    def test_cache_invalidated_on_edit(self):
        link = ShortURL.objects.create(original_url="https://example.com", short_code="abc")
        self.assertEqual(self.client.get("/abc").status_code, 302)  # now cached
        link.is_active = False
        link.save()
        self.assertEqual(self.client.get("/abc").status_code, 410)