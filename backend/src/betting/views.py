from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q, Sum, Count
from datetime import timedelta, datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import (
    PlatformSettings, GameRound, Bet, News, NewsAnalysis, RoundStats
)
from .serializers import (
    PlatformSettingsSerializer, GameRoundSerializer, BetSerializer, 
    BetCreateSerializer, NewsSerializer, NewsCreateSerializer,
    NewsReadOnlySerializer, CurrentRoundInfoSerializer,
    RoundParticipationSerializer, RoundParticipationResponseSerializer
)
from .services import (
    BettingService, GameRoundService, NewsService, PayoutService, AnalysisService, RoundParticipationService
)
from .pagination import GameRoundPagination, BetPagination, NewsPagination
from .filters import GameRoundFilter, BetFilter

logger = logging.getLogger(__name__)


class GameRoundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для игровых раундов
    """
    queryset = GameRound.objects.select_related('news').order_by('-start_time')
    serializer_class = GameRoundSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = GameRoundPagination
    filterset_class = GameRoundFilter
    ordering_fields = ['start_time', 'end_time', 'status']
    ordering = ['-start_time']
    search_fields = ['news__title', 'news__content']

    @swagger_auto_schema(
        operation_description="Получить список игровых раундов с возможностью фильтрации, поиска и сортировки",
        manual_parameters=[
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Статус раунда (open, closed, finished, void)",
                type=openapi.TYPE_STRING,
                enum=['open', 'closed', 'finished', 'void']
            ),
            openapi.Parameter(
                'start_time_from', openapi.IN_QUERY,
                description="Начальная дата/время раунда (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'start_time_to', openapi.IN_QUERY,
                description="Конечная дата/время раунда (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'end_time_from', openapi.IN_QUERY,
                description="Начальная дата/время окончания раунда (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'end_time_to', openapi.IN_QUERY,
                description="Конечная дата/время окончания раунда (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Поиск по заголовку и содержимому новостей",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering', openapi.IN_QUERY,
                description="Сортировка (start_time, end_time, status). Добавьте '-' для убывания",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Размер страницы (максимум 100)",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить все текущие активные раунды (short и long)"""
        from .serializers import CurrentRoundsInfoSerializer
        
        current_rounds = GameRoundService.get_current_rounds()
        
        if not current_rounds.exists():
            return Response({'message': 'No active rounds'}, status=status.HTTP_404_NOT_FOUND)
        
        settings = PlatformSettings.get_current()
        
        serializer = CurrentRoundsInfoSerializer(
            {
                'rounds': current_rounds,
                'settings': settings,
            },
            context={'user': request.user}
        )
        
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    @swagger_auto_schema(
        operation_description="Автоматическое участие в раунде с начислением бонуса (ID раунда в теле запроса)",
        request_body=RoundParticipationSerializer,
        responses={
            200: RoundParticipationResponseSerializer,
            400: 'Ошибка валидации',
            404: 'Раунд не найден',
            403: 'Доступ запрещен'
        }
    )
    def bonus_per_round(self, request):
        """
        Автоматическое участие пользователя в раунде с начислением бонуса
        ID раунда передается в теле запроса
        """
        try:
            # Валидируем данные запроса
            serializer = RoundParticipationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Получаем пользователя и ID раунда
            user = request.user.customuser
            round_id = serializer.validated_data['round_id']
            
            # Вызываем сервис участия в раунде
            success, message, bonus_info = RoundParticipationService.participate_in_round(
                user=user,
                round_id=round_id
            )
            
            response_data = {
                'success': success,
                'message': message,
                'bonus_info': bonus_info
            }
            
            if success:
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Ошибка при автоматическом участии в раунде: {str(e)}")
            return Response({
                'success': False,
                'message': f'Внутренняя ошибка: {str(e)}',
                'bonus_info': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BetViewSet(viewsets.ModelViewSet):
    """
    ViewSet для ставок
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']  # Разрешаем только GET и POST методы
    pagination_class = BetPagination
    filterset_class = BetFilter
    ordering_fields = ['created_at', 'amount', 'choice']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Получить список ставок пользователя с возможностью фильтрации и сортировки",
        manual_parameters=[
            openapi.Parameter(
                'choice', openapi.IN_QUERY,
                description="Выбор ставки (positive, negative)",
                type=openapi.TYPE_STRING,
                enum=['positive', 'negative']
            ),
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Статус ставки (pending, won, lost, refunded)",
                type=openapi.TYPE_STRING,
                enum=['pending', 'won', 'lost', 'refunded']
            ),
            openapi.Parameter(
                'amount_from', openapi.IN_QUERY,
                description="Минимальная сумма ставки",
                type=openapi.TYPE_NUMBER
            ),
            openapi.Parameter(
                'amount_to', openapi.IN_QUERY,
                description="Максимальная сумма ставки",
                type=openapi.TYPE_NUMBER
            ),
            openapi.Parameter(
                'created_at_from', openapi.IN_QUERY,
                description="Начальная дата создания ставки (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'created_at_to', openapi.IN_QUERY,
                description="Конечная дата создания ставки (ISO format)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'round_status', openapi.IN_QUERY,
                description="Статус связанного раунда",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering', openapi.IN_QUERY,
                description="Сортировка (created_at, amount, choice). Добавьте '-' для убывания",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Размер страницы (максимум 100)",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        # Защита от AnonymousUser при генерации Swagger схемы
        if getattr(self, 'swagger_fake_view', False):
            return Bet.objects.none()
        
        # Проверяем что пользователь аутентифицирован
        if not self.request.user.is_authenticated:
            return Bet.objects.none()
            
        return Bet.objects.filter(user=self.request.user).select_related(
            'round', 'round__news'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BetCreateSerializer
        return BetSerializer
    
    def create(self, request, *args, **kwargs):
        """Создать ставку"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        bet = serializer.save()
        
        response_serializer = BetSerializer(bet)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для новостей с доступом только на чтение
    """
    queryset = News.objects.filter(status='pending').order_by('-created_at')
    serializer_class = NewsReadOnlySerializer
    permission_classes = []  # Публичный доступ без аутентификации
    pagination_class = NewsPagination
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="Получить список новостей с пагинацией, отсортированный от новых к старым",
        manual_parameters=[
            openapi.Parameter(
                'page', openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size', openapi.IN_QUERY,
                description="Размер страницы (максимум 100)",
                type=openapi.TYPE_INTEGER
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Получить конкретную новость по ID"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
