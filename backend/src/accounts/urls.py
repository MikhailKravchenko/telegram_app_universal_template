from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TelegramLogin,
    UserInfoView,
    UserBalanceView,
    BalanceSummaryView,
    TransactionView,
    BonusViewSet,
    ReferralViewSet,
    telegram_auth_status,
    logout,
)

# Создаем роутер для ViewSet'ов
router = DefaultRouter()
router.register(r'users', UserInfoView, basename='customuser')
router.register(r'balances', UserBalanceView, basename='userbalance')
router.register(r'balance-summary', BalanceSummaryView, basename='balance-summary')
router.register(r'transactions', TransactionView, basename='transaction')
router.register(r'bonuses', BonusViewSet, basename='bonus')
router.register(r'referrals', ReferralViewSet, basename='referral')

app_name = 'accounts'

urlpatterns = [
    path("balance-summary/", BalanceSummaryView.as_view({"get": "list"}), name="balance_summary"),
    path("transactions/", TransactionView.as_view({"get": "list"}), name="transactions"),
    path("telegram/login/", TelegramLogin.as_view(), name="telegram_login"),
    path("telegram/status/", telegram_auth_status, name="telegram_auth_status"),
    path("logout/", logout, name="logout"),
    # Включаем маршруты из роутера
    path("", include(router.urls)),
]
