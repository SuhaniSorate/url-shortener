import re
from rest_framework import serializers
from .models import ShortURL, encode_base62

RESERVED = {"api", "admin", "static"}


class ShortURLSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortURL
        fields = ["id", "original_url", "custom_alias", "expires_at",
                  "short_code", "short_url", "is_active", "created_at"]
        read_only_fields = ["short_code", "is_active", "created_at"]

    def get_short_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(f"/{obj.short_code}") if request else obj.short_code

    def validate_custom_alias(self, value):
        if not value:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,30}", value):
            raise serializers.ValidationError(
                "Alias must be 3-30 characters: letters, numbers, - or _ only.")
        if value.lower() in RESERVED:
            raise serializers.ValidationError("This alias is reserved.")
        if ShortURL.objects.filter(short_code=value).exists():
            raise serializers.ValidationError("This alias is already taken.")
        return value

    def validate_original_url(self, value):
        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def create(self, validated_data):
        alias = validated_data.get("custom_alias")
        obj = ShortURL.objects.create(short_code=alias or "", **validated_data)
        if not alias:
            # Base62 of the row id (offset so codes are at least a few characters long)
            code = encode_base62(obj.id + 100000)
            while ShortURL.objects.filter(short_code=code).exists():
                code += "x"
            obj.short_code = code
            obj.save(update_fields=["short_code"])
        return obj