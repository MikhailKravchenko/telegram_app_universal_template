
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import CustomUser
from .telegram_utils import extract_user_data


class TelegramLoginSerializer(serializers.Serializer):
    """
    Минимальный сериализатор для авторизации через Telegram WebApp.
    """

    telegramData = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
        help_text="Telegram initData string",
    )

    def validate(self, attrs):
        telegram_data = attrs["telegramData"]

        if not telegram_data:
            raise serializers.ValidationError("Telegram data is required")

        try:
            user_data = extract_user_data(telegram_data)
        except Exception as exc:
            raise serializers.ValidationError(f"Failed to extract Telegram data: {exc}")

        if "id" not in user_data:
            raise serializers.ValidationError("Invalid user data: missing id")

        telegram_id = str(user_data["id"])
        username = user_data.get("username") or f"tg_{telegram_id}"

        user, _created = CustomUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username,
                "telegram_username": user_data.get("username") or "",
                "telegram_first_name": user_data.get("first_name") or "",
                "telegram_last_name": user_data.get("last_name") or "",
                "telegram_language_code": user_data.get("language_code") or "",
            },
        )

        # Обновляем базовую информацию при повторном входе
        user.username = username
        user.telegram_username = user_data.get("username") or user.telegram_username
        user.telegram_first_name = user_data.get("first_name") or user.telegram_first_name
        user.telegram_last_name = user_data.get("last_name") or user.telegram_last_name
        user.telegram_language_code = user_data.get("language_code") or user.telegram_language_code
        user.save(update_fields=[
            "username",
            "telegram_username",
            "telegram_first_name",
            "telegram_last_name",
            "telegram_language_code",
        ])

        attrs["user"] = user
        return attrs


class UserMeSerializer(ModelSerializer):
    """
    Минимальный сериализатор профиля текущего пользователя.
    """

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "telegram_id",
            "telegram_username",
            "telegram_first_name",
            "telegram_last_name",
            "telegram_language_code",
        )
        read_only_fields = fields


