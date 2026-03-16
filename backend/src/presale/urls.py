from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PresaleViewSet, PresaleRoundViewSet, InvestmentViewSet,
    UserPresaleStatsViewSet, PresaleStatsViewSet
)

# Создать роутер для API
router = DefaultRouter()
router.register(r'presales', PresaleViewSet, basename='presale')
router.register(r'rounds', PresaleRoundViewSet, basename='presale-round')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'user-stats', UserPresaleStatsViewSet, basename='user-presale-stats')
router.register(r'stats', PresaleStatsViewSet, basename='presale-stats')

# URL patterns
urlpatterns = [
    path('api/', include(router.urls)),
]
