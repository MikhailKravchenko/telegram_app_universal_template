from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db.models import Q

from .models import Presale, PresaleRound, Investment, UserPresaleStats
from .serializers import (
    PresaleSerializer, PresaleRoundSerializer, InvestmentSerializer,
    CreateInvestmentSerializer, UserPresaleStatsSerializer,
    PresaleSummarySerializer, CurrentRoundInfoSerializer,
    UserInvestmentSummarySerializer, RoundStatsSerializer,
    GlobalStatsSerializer
)
from .services import (
    PresaleService, InvestmentService, PresaleRoundService,
    PresaleStatsService
)


class PresaleInvestmentPagination(PageNumberPagination):
    """Пагинация для инвестиций"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(ratelimit(key='user', rate='60/m'), name='dispatch')
class PresaleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для пресейлов"""
    
    queryset = Presale.objects.all()
    serializer_class = PresaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущий активный пресейл"""
        presale = PresaleService.get_active_presale()
        if not presale:
            return Response(
                {'detail': 'Активный пресейл не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        summary = PresaleService.get_presale_summary(presale)
        serializer = PresaleSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def round_info(self, request, pk=None):
        """Получить информацию о текущем раунде пресейла"""
        presale = self.get_object()
        round_info = PresaleService.get_current_round_info(presale)
        serializer = CurrentRoundInfoSerializer(round_info)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rounds_stats(self, request, pk=None):
        """Получить статистику по всем раундам пресейла"""
        presale = self.get_object()
        rounds_stats = PresaleStatsService.get_round_stats(presale)
        serializer = RoundStatsSerializer(rounds_stats, many=True)
        return Response(serializer.data)


@method_decorator(ratelimit(key='user', rate='30/m'), name='dispatch')
class PresaleRoundViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для раундов пресейла"""
    
    queryset = PresaleRound.objects.all()
    serializer_class = PresaleRoundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_defaults(self, request):
        """Создать дефолтные раунды (только для администраторов)"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Доступ запрещен'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        created_rounds = PresaleRoundService.create_default_rounds()
        serializer = PresaleRoundSerializer(created_rounds, many=True)
        return Response({
            'created_count': len(created_rounds),
            'rounds': serializer.data
        })


@method_decorator(ratelimit(key='user', rate='10/m'), name='create')
@method_decorator(ratelimit(key='user', rate='60/m'), name='list')
class InvestmentViewSet(viewsets.ModelViewSet):
    """ViewSet для инвестиций"""
    
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PresaleInvestmentPagination
    
    def get_queryset(self):
        """Получить инвестиции текущего пользователя"""
        if not self.request.user.is_authenticated:
            return Investment.objects.none()
        return Investment.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Выбрать сериализатор в зависимости от действия"""
        if self.action == 'create':
            return CreateInvestmentSerializer
        return InvestmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Создать инвестицию"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Получить активный пресейл
        presale = PresaleService.get_active_presale()
        if not presale:
            return Response(
                {'detail': 'Активный пресейл не найден'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создать инвестицию
        amount = serializer.validated_data['amount']
        success, message, investment = InvestmentService.make_investment(
            user=request.user.customuser,
            presale=presale,
            amount=amount
        )
        
        if not success:
            return Response(
                {'detail': message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Вернуть созданную инвестицию
        response_serializer = InvestmentSerializer(investment)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Получить сводку инвестиций пользователя"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        presale = PresaleService.get_active_presale()
        summary = InvestmentService.get_user_investment_summary(
            user=request.user.customuser,
            presale=presale
        )
        serializer = UserInvestmentSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def all_presales(self, request):
        """Получить инвестиции пользователя по всем пресейлам"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        summary = InvestmentService.get_user_investment_summary(
            user=request.user.customuser,
            presale=None
        )
        serializer = UserInvestmentSummarySerializer(summary)
        return Response(serializer.data)


@method_decorator(ratelimit(key='user', rate='30/m'), name='dispatch')
class UserPresaleStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для статистики пользователей"""
    
    queryset = UserPresaleStats.objects.all()
    serializer_class = UserPresaleStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Получить только статистику текущего пользователя"""
        if not self.request.user.is_authenticated:
            return UserPresaleStats.objects.none()
        if self.request.user.is_staff:
            # Администраторы могут видеть всю статистику
            return UserPresaleStats.objects.all()
        return UserPresaleStats.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Получить статистику текущего пользователя"""
        # Проверка аутентификации на всякий случай
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        try:
            stats = UserPresaleStats.objects.get(user=request.user.customuser)
            serializer = UserPresaleStatsSerializer(stats)
            return Response(serializer.data)
        except UserPresaleStats.DoesNotExist:
            return Response({
                'user': request.user.id,
                'user_username': request.user.username,
                'total_invested': 0,
                'total_tokens': '0.00',
                'investments_count': 0,
                'first_investment_at': None,
                'last_investment_at': None,
                'updated_at': None
            })
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Получить топ инвесторов"""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Доступ запрещен'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Топ по общему количеству токенов
        top_by_tokens = UserPresaleStats.objects.filter(
            total_tokens__gt=0
        ).order_by('-total_tokens')[:10]
        
        # Топ по общей сумме инвестиций
        top_by_investment = UserPresaleStats.objects.filter(
            total_invested__gt=0
        ).order_by('-total_invested')[:10]
        
        return Response({
            'top_by_tokens': UserPresaleStatsSerializer(top_by_tokens, many=True).data,
            'top_by_investment': UserPresaleStatsSerializer(top_by_investment, many=True).data,
        })


@method_decorator(ratelimit(key='user', rate='30/m'), name='dispatch')
class PresaleStatsViewSet(viewsets.ViewSet):
    """ViewSet для глобальной статистики пресейла"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def global_stats(self, request):
        """Получить глобальную статистику"""
        stats = PresaleStatsService.get_global_stats()
        serializer = GlobalStatsSerializer(stats)
        return Response(serializer.data)