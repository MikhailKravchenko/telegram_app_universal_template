from django.urls import path

from .views import TelegramLogin, me

app_name = "accounts"

urlpatterns = [
    path("telegram/login/", TelegramLogin.as_view(), name="telegram_login"),
    path("me/", me, name="me"),
]
