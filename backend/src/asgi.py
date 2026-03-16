"""
ASGI config for src project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Устанавливаем настройки Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")

# Получаем Django ASGI application для HTTP запросов
django_asgi_app = get_asgi_application()

# Импортируем routing для WebSocket
from src.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP запросы обрабатываются Django
    "http": django_asgi_app,
    
    # WebSocket запросы обрабатываются channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
