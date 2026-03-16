from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import GameRoundViewSet, BetViewSet, NewsViewSet

app_name = 'betting'

router = DefaultRouter()
router.register(r'rounds', GameRoundViewSet, basename='gameround')
router.register(r'bets', BetViewSet, basename='bet')
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    path('', include(router.urls)),
]
