from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Минимальная модель пользователя для шаблона.

    Содержит стандартные поля Django-пользователя и Telegram-идентификаторы.
    """

    telegram_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Telegram User ID",
    )
    telegram_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Telegram username (без @)",
    )
    telegram_first_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Имя из Telegram",
    )
    telegram_last_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Фамилия из Telegram",
    )
    telegram_language_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Язык интерфейса Telegram (например, ru, en)",
    )
    telegram_photo_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL аватара пользователя в Telegram",
    )

    def __str__(self) -> str:
        return self.username or f"tg_{self.telegram_id}"

