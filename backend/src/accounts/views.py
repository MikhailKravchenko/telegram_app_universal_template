import logging
from random import choice
from string import ascii_letters

from django.db.models import QuerySet
from rest_framework import serializers, status
from rest_framework.decorators import api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .jwt_utils import create_custom_jwt_payload

from src.rate_limits import (
    rate_limit_api_method,
    rate_limit_auth,
    rate_limit_game_method, rate_limit_auth_method,
)
from src.security_logging import SecurityLogger

from .models import (
    CustomUser,
    UserBalance,
    Transaction,
    Bonus,
    ReferralLevel,
    ReferralBonus,
)
from .serializers import (
    TelegramLoginSerializer,
    UserInfoSerializer,
    UserBalanceSerializer,
    TransactionSerializer,
    BonusSerializer,
    BonusStatisticsSerializer,
    ReferralLevelSerializer,
    ReferralBonusSerializer,

)
from .services import BalanceService, BonusService, ActivityService, ReferralService

logger = logging.getLogger(__name__)


class TelegramLogin(APIView):
    """Validate Telegram initData and authenticate user with JWT."""

    permission_classes = []
    
    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Получаем пользователя из сериализатора
                user = serializer.validated_data['user']
                
                # Генерируем JWT токены с кастомным payload
                jwt_data = create_custom_jwt_payload(user)
                
                response = Response(jwt_data, status=status.HTTP_200_OK)
                
                # Устанавливаем cookies
                response.set_cookie(
                    'access_token', 
                    jwt_data['access'], 
                    httponly=False, 
                    secure=False,  # Set to True in production
                    samesite='Lax',
                    max_age=3600  # 1 hour
                )
                response.set_cookie(
                    'refresh_token', 
                    jwt_data['refresh'], 
                    httponly=False, 
                    secure=False,  # Set to True in production
                    samesite='Lax',
                    max_age=604800  # 7 days
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Error in Telegram login: {str(e)}")
                return Response(
                    {'error': 'Authentication failed'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@rate_limit_auth
@api_view(http_method_names=["GET"])
def telegram_auth_status(request: Request):
    """Check Telegram authentication status."""
    return Response({
        "status": "Telegram authentication is enabled",
        "message": "Use POST /accounts/telegram/login/ with telegramData parameter"
    })


@api_view(http_method_names=["POST"])
def logout(request: Request):
    """Logout user and clear JWT cookies."""
    response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    
    # Очищаем cookies
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response


class UserInfoView(ModelViewSet):
    """
    Access point for requesting user information including balance

    auth_token in cookie
    """

    pagination_class = None
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']  # Только для чтения

    serializer_class = UserInfoSerializer

    def get_queryset(self):
        queryset = self.queryset

        if isinstance(queryset, QuerySet):
            queryset = queryset.filter(id=self.request.user.id).select_related('balance')
        return queryset

    @rate_limit_api_method
    def list(self, request: object, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @rate_limit_api_method
    def retrieve(self, request: object, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class UserBalanceView(ModelViewSet):
    """
    Access point for requesting user balance details

    auth_token in cookie
    """

    pagination_class = None
    queryset = UserBalance.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserBalanceSerializer
    http_method_names = ['get', 'head', 'options']  # Только для чтения

    def get_queryset(self):
        return self.queryset.filter(user_id=self.request.user.id)

    @rate_limit_api_method
    def list(self, request: object, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @rate_limit_api_method
    def retrieve(self, request: object, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class BalanceSummaryView(ViewSet):
    """
    Access point for requesting comprehensive user balance summary

    auth_token in cookie
    """

    permission_classes = [IsAuthenticated]

    @rate_limit_api_method
    def list(self, request: object, *args, **kwargs):
        """Get comprehensive balance summary for authenticated user"""
        try:
            # Get CustomUser object instead of base User
            user = CustomUser.objects.get(id=request.user.id)
            balance_summary = BalanceService.get_balance_summary(user)
            
            if 'error' in balance_summary:
                return Response(
                    {'error': balance_summary['error']}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(balance_summary, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            logger.error(f"CustomUser not found for user_id: {request.user.id}")
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting balance summary for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to get balance summary'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @rate_limit_api_method
    def retrieve(self, request: object, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class TransactionView(ModelViewSet):
    """
    Access point for requesting user transaction history

    auth_token in cookie
    """

    pagination_class = None
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    http_method_names = ['get', 'head', 'options']  # Только для чтения

    def get_queryset(self):
        return self.queryset.filter(user_id=self.request.user.id)

    @rate_limit_api_method
    def list(self, request: object, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @rate_limit_api_method
    def retrieve(self, request: object, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class BonusViewSet(ModelViewSet):
    """
    ViewSet для управления бонусами пользователя
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BonusSerializer
    http_method_names = ['get', 'post']  # GET для просмотра, POST для получения бонусов

    def get_queryset(self):
        """Получить бонусы текущего пользователя"""
        if getattr(self, 'swagger_fake_view', False):
            return Bonus.objects.none()
        
        if not self.request.user.is_authenticated:
            return Bonus.objects.none()
            
        return Bonus.objects.filter(user=self.request.user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Запретить прямое создание бонусов через POST"""
        return Response(
            {'error': 'Method not allowed. Use specific bonus endpoints like /claim_daily/ or /claim_social/'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        """Запретить изменение бонусов через PUT/PATCH"""
        return Response(
            {'error': 'Method not allowed'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def partial_update(self, request, *args, **kwargs):
        """Запретить частичное изменение бонусов через PATCH"""
        return Response(
            {'error': 'Method not allowed'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Запретить удаление бонусов через DELETE"""
        return Response(
            {'error': 'Method not allowed'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @rate_limit_api_method
    def list(self, request, *args, **kwargs):
        """Получить список бонусов пользователя с фильтрацией по статусу"""
        queryset = self.get_queryset()
        
        # Фильтр по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтр по типу бонуса
        bonus_type_filter = request.query_params.get('bonus_type')
        if bonus_type_filter:
            queryset = queryset.filter(bonus_type=bonus_type_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @rate_limit_api_method
    def retrieve(self, request, *args, **kwargs):
        """Получить детали конкретного бонуса"""
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    @rate_limit_api_method
    def statistics(self, request):
        """Получить статистику по бонусам пользователя"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            stats = BonusService.get_bonus_statistics(user)
            
            if 'error' in stats:
                return Response(
                    {'error': stats['error']}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            serializer = BonusStatisticsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting bonus statistics for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to get bonus statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @rate_limit_api_method
    def claim_daily(self, request):
        """Получить ежедневный бонус"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            created, message, bonus = BonusService.check_daily_login_bonus(user)
            
            if created and bonus:
                serializer = BonusSerializer(bonus)
                return Response({
                    'success': True,
                    'message': message,
                    'bonus': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error claiming daily bonus for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to claim daily bonus'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @rate_limit_api_method
    def claim_social(self, request):
        """Получить бонус за подписку на соцсеть"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            created, message, bonus = BonusService.check_social_subscription_bonus(user)
            
            if created and bonus:
                # Автоматически активируем и используем бonus
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                serializer = BonusSerializer(bonus)
                return Response({
                    'success': True,
                    'message': "Бонус за подписку получен +1000 монет!",
                    'bonus': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error claiming social bonus for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to claim social bonus'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @rate_limit_api_method
    def claim_telegram_channel_1(self, request):
        """Получить бонус за подписку на Telegram канал 1"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            created, message, bonus = BonusService.check_telegram_channel_1_bonus(user)
            
            if created and bonus:
                # Автоматически активируем и используем бonus
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                serializer = BonusSerializer(bonus)
                return Response({
                    'success': True,
                    'message': f"Бонус за подписку на Telegram канал 1 получен +{bonus.amount} монет!",
                    'bonus': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error claiming telegram channel 1 bonus for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to claim telegram channel 1 bonus'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @rate_limit_api_method
    def claim_telegram_channel_2(self, request):
        """Получить бонус за подписку на Telegram канал 2"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            created, message, bonus = BonusService.check_telegram_channel_2_bonus(user)
            
            if created and bonus:
                # Автоматически активируем и используем бonus
                BonusService.activate_bonus(bonus)
                BonusService.use_bonus(bonus)
                
                serializer = BonusSerializer(bonus)
                return Response({
                    'success': True,
                    'message': f"Бонус за подписку на Telegram канал 2 получен +{bonus.amount} монет!",
                    'bonus': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error claiming telegram channel 2 bonus for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to claim telegram channel 2 bonus'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @rate_limit_api_method
    def activity_stats(self, request):
        """Получить статистику активности пользователя"""
        try:
            user = CustomUser.objects.get(id=request.user.id)
            
            # Получаем параметр hours из запроса (по умолчанию 24)
            hours = int(request.query_params.get('hours', 24))
            if hours < 1 or hours > 168:  # Максимум неделя
                hours = 24
            
            stats = ActivityService.get_user_activity_stats(user, hours)
            
            if 'error' in stats:
                return Response(
                    {'error': stats['error']}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Invalid hours parameter'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting activity stats for user {request.user.id}: {str(e)}")
            return Response(
                {'error': 'Failed to get activity statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReferralViewSet(ViewSet):
    """
    ViewSet для управления реферальной программой
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='my-stats')
    def my_stats(self, request: Request) -> Response:
        """
        Получить статистику реферальной программы текущего пользователя
        """
        try:
            stats = ReferralService.get_referral_stats(request.user.customuser)
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting referral stats for user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to get referral statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='my-link')
    def my_link(self, request: Request) -> Response:
        """
        Получить реферальную ссылку текущего пользователя
        """
        try:
            link = ReferralService.get_referral_link(request.user.customuser)
            return Response({
                'referral_link': link,
                'telegram_id': request.user.customuser.telegram_id,
                'user_id': request.user.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting referral link for user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to get referral link'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='my-bonuses')
    def my_bonuses(self, request: Request) -> Response:
        """
        Получить историю реферальных бонусов текущего пользователя
        """
        try:
            bonuses = ReferralBonus.objects.filter(
                referrer=request.user.customuser
            ).order_by('-created_at')[:50]  # Последние 50 бонусов
            
            serializer = ReferralBonusSerializer(bonuses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting referral bonuses for user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to get referral bonuses'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='levels')
    def levels(self, request: Request) -> Response:
        """
        Получить список всех доступных уровней реферальной программы
        """
        try:
            levels = ReferralLevel.objects.filter(is_active=True).order_by('level')
            serializer = ReferralLevelSerializer(levels, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting referral levels: {str(e)}")
            return Response(
                {'error': 'Failed to get referral levels'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='global-stats')
    def global_stats(self, request: Request) -> Response:
        """
        Получить глобальную статистику реферальной программы
        """
        try:
            stats = ReferralService.get_global_referral_stats()
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting global referral stats: {str(e)}")
            return Response(
                {'error': 'Failed to get global referral statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


