# WebSocket URL routing
from django.urls import re_path
from src.betting.routing import websocket_urlpatterns as betting_websocket_urlpatterns

websocket_urlpatterns = [
    # WebSocket маршруты для betting системы
    *betting_websocket_urlpatterns,
]

