from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal

from .models import (
    PlatformSettings, GameRound, Bet, News, NewsAnalysis, RoundStats
)
from src.accounts.models import CustomUser


class PlatformSettingsSerializer(serializers.ModelSerializer):
    """
    Сериализатор настроек платформы
    """
    class Meta:
        model = PlatformSettings
        fields = [
            'id', 'round_duration_seconds', 'platform_fee_rate',
            'min_bet', 'max_bet', 'news_freshness_minutes',
            'min_news_content_length', 'enabled'
        ]
        read_only_fields = ['id']


class NewsSerializer(serializers.ModelSerializer):
    """
    Сериализатор новостей
    """
    has_analysis = serializers.SerializerMethodField()
    analysis_result = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'image_url', 'source_url',
            'category', 'status', 'language', 'created_at',
            'has_analysis', 'analysis_result'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'has_analysis', 'analysis_result']
    
    def get_has_analysis(self, obj):
        return hasattr(obj, 'analysis')
    
    def get_analysis_result(self, obj):
        if hasattr(obj, 'analysis') and obj.analysis.label:
            return obj.analysis.label
        return None


class NewsCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания новостей
    """
    class Meta:
        model = News
        fields = ['title', 'content', 'source_url', 'category', 'image_url', 'language']
    
    def validate_source_url(self, value):
        if News.objects.filter(source_url=value).exists():
            raise serializers.ValidationError("News with this source URL already exists")
        return value


class NewsReadOnlySerializer(serializers.ModelSerializer):
    """
    Сериализатор для публичного чтения новостей
    """
    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'image_url', 'source_url',
            'category', 'language', 'created_at'
        ]
        read_only_fields = [
            'id', 'title', 'content', 'image_url', 'source_url',
            'category', 'language', 'created_at'
        ]


class NewsAnalysisSerializer(serializers.ModelSerializer):
    """
    Сериализатор анализа новостей
    """
    news_title = serializers.CharField(source='news.title', read_only=True)
    
    class Meta:
        model = NewsAnalysis
        fields = [
            'id', 'news', 'news_title', 'status', 'label', 'score',
            'provider', 'model_name', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'news_title', 'status', 'label', 'score',
            'provider', 'model_name', 'created_at', 'processed_at'
        ]


class GameRoundSerializer(serializers.ModelSerializer):
    """
    Сериализатор игровых раундов
    """
    news_title = serializers.CharField(source='news.title', read_only=True)
    news_content = serializers.CharField(source='news.content', read_only=True)
    news_image_url = serializers.URLField(source='news.image_url', read_only=True)
    bets_count = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    can_bet = serializers.SerializerMethodField()
    
    class Meta:
        model = GameRound
        fields = [
            'id', 'round_type', 'start_time', 'end_time', 'status', 'result',
            'pot_total', 'pot_positive', 'pot_negative',
            'fee_applied_rate', 'resolved_at',
            'news_title', 'news_content', 'news_image_url',
            'bets_count', 'time_remaining', 'can_bet'
        ]
        read_only_fields = [
            'id', 'round_type', 'pot_total', 'pot_positive', 'pot_negative',
            'fee_applied_rate', 'resolved_at', 'news_title',
            'news_content', 'news_image_url', 'bets_count',
            'time_remaining', 'can_bet'
        ]
    
    def get_bets_count(self, obj):
        return obj.bets.count()
    
    def get_time_remaining(self, obj):
        if obj.status == 'open' and obj.end_time > timezone.now():
            remaining = obj.end_time - timezone.now()
            return int(remaining.total_seconds())
        return 0
    
    def get_can_bet(self, obj):
        return obj.status == 'open' and obj.end_time > timezone.now()


class GameRoundStatsSerializer(serializers.ModelSerializer):
    """
    Сериализатор статистики раунда
    """
    positive_coefficient = serializers.SerializerMethodField()
    negative_coefficient = serializers.SerializerMethodField()
    
    class Meta:
        model = GameRound
        fields = [
            'id', 'status', 'result', 'pot_total', 'pot_positive', 'pot_negative',
            'positive_coefficient', 'negative_coefficient'
        ]
    
    def get_positive_coefficient(self, obj):
        if obj.pot_positive and obj.pot_total:
            settings = PlatformSettings.get_current()
            available = obj.pot_total * (1 - settings.platform_fee_rate)
            return float(available / obj.pot_positive)
        return 1.0
    
    def get_negative_coefficient(self, obj):
        if obj.pot_negative and obj.pot_total:
            settings = PlatformSettings.get_current()
            available = obj.pot_total * (1 - settings.platform_fee_rate)
            return float(available / obj.pot_negative)
        return 1.0


class BetSerializer(serializers.ModelSerializer):
    """
    Сериализатор ставок
    """
    username = serializers.CharField(source='user.username', read_only=True)
    round_status = serializers.CharField(source='round.status', read_only=True)
    round_result = serializers.CharField(source='round.result', read_only=True)
    
    class Meta:
        model = Bet
        fields = [
            'id', 'user', 'username', 'round', 'round_status', 'round_result',
            'amount', 'choice', 'status', 'payout_amount', 'payout_coefficient',
            'created_at'
        ]
        read_only_fields = [
            'id', 'username', 'round_status', 'round_result',
            'status', 'payout_amount', 'payout_coefficient', 'created_at'
        ]


class BetCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания ставок
    """
    class Meta:
        model = Bet
        fields = ['round', 'amount', 'choice']
    
    def validate(self, data):
        user = self.context['request'].user.customuser
        round_obj = data['round']
        amount = data['amount']
        
        # Проверяем статус раунда
        if round_obj.status != 'open':
            raise serializers.ValidationError("Betting is closed for this round")
        
        if round_obj.end_time <= timezone.now():
            raise serializers.ValidationError("Round has already ended")
        
        # Проверяем лимиты
        settings = PlatformSettings.get_current()
        if amount < settings.min_bet:
            raise serializers.ValidationError(f"Minimum bet is {settings.min_bet}")
        if amount > settings.max_bet:
            raise serializers.ValidationError(f"Maximum bet is {settings.max_bet}")
        
        # Проверяем баланс
        if not hasattr(user, 'balance') or user.balance.coins_balance < amount:
            raise serializers.ValidationError("Insufficient balance")
        
        # Проверяем, что пользователь ещё не делал ставку
        if Bet.objects.filter(user=user, round=round_obj).exists():
            raise serializers.ValidationError("You have already placed a bet in this round")
        
        return data
    
    def create(self, validated_data):
        from .services import BettingService
        
        user = self.context['request'].user.customuser
        return BettingService.place_bet(
            user=user,
            round_id=validated_data['round'].id,
            amount=validated_data['amount'],
            choice=validated_data['choice']
        )


class UserBetHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для истории ставок пользователя
    """
    round_start_time = serializers.DateTimeField(source='round.start_time', read_only=True)
    round_end_time = serializers.DateTimeField(source='round.end_time', read_only=True)
    round_result = serializers.CharField(source='round.result', read_only=True)
    news_title = serializers.CharField(source='round.news.title', read_only=True)
    is_winner = serializers.SerializerMethodField()
    
    class Meta:
        model = Bet
        fields = [
            'id', 'amount', 'choice', 'status', 'payout_amount',
            'payout_coefficient', 'created_at', 'round_start_time',
            'round_end_time', 'round_result', 'news_title', 'is_winner'
        ]
    
    def get_is_winner(self, obj):
        return obj.status == 'won'


class RoundStatsSerializer(serializers.ModelSerializer):
    """
    Сериализатор статистики раунда
    """
    round_id = serializers.IntegerField(source='round.id', read_only=True)
    round_status = serializers.CharField(source='round.status', read_only=True)
    round_result = serializers.CharField(source='round.result', read_only=True)
    
    class Meta:
        model = RoundStats
        fields = [
            'round_id', 'round_status', 'round_result',
            'total_bets_count', 'positive_bets_count', 'negative_bets_count',
            'total_amount', 'positive_amount', 'negative_amount',
            'positive_coefficient', 'negative_coefficient',
            'total_payout', 'platform_fee', 'updated_at'
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для лидерборда
    """
    total_winnings = serializers.SerializerMethodField()
    total_bets = serializers.SerializerMethodField()
    win_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'total_winnings', 'total_bets', 'win_rate']
    
    def get_total_winnings(self, obj):
        won_bets = obj.bets.filter(status='won')
        return sum(bet.payout_amount for bet in won_bets)
    
    def get_total_bets(self, obj):
        return obj.bets.count()
    
    def get_win_rate(self, obj):
        total_bets = obj.bets.count()
        if total_bets == 0:
            return 0.0
        won_bets = obj.bets.filter(status='won').count()
        return round(won_bets / total_bets * 100, 2)


class CurrentRoundInfoSerializer(serializers.Serializer):
    """
    Сериализатор информации о текущем раунде
    """
    current_round = GameRoundSerializer(read_only=True)
    user_bet = BetSerializer(read_only=True, allow_null=True)
    settings = PlatformSettingsSerializer(read_only=True)
    can_place_bet = serializers.BooleanField(read_only=True)


class CurrentRoundsInfoSerializer(serializers.Serializer):
    """
    Сериализатор информации о всех текущих активных раундах
    """
    rounds = serializers.SerializerMethodField()
    settings = PlatformSettingsSerializer(read_only=True)
    
    def get_rounds(self, obj):
        """
        Возвращает информацию о каждом раунде с информацией о ставке пользователя
        """
        rounds_data = []
        user = self.context.get('user')
        
        for game_round in obj.get('rounds', []):
            # Проверяем ставку пользователя для этого раунда
            user_bet = None
            if user and user.is_authenticated:
                try:
                    from .models import Bet
                    user_bet = Bet.objects.get(user=user.customuser, round=game_round)
                except Bet.DoesNotExist:
                    pass
            
            # Проверяем возможность сделать ставку
            settings = obj.get('settings')
            can_place_bet = (
                game_round.status == 'open' and 
                game_round.end_time > timezone.now() and
                user_bet is None and
                settings and settings.enabled
            )
            
            rounds_data.append({
                'round': GameRoundSerializer(game_round).data,
                'user_bet': BetSerializer(user_bet).data if user_bet else None,
                'can_place_bet': can_place_bet
            })
        
        return rounds_data


class RoundResultSerializer(serializers.Serializer):
    """
    Сериализатор результатов раунда
    """
    round = GameRoundSerializer(read_only=True)
    user_bet = BetSerializer(read_only=True, allow_null=True)
    stats = RoundStatsSerializer(read_only=True)
    winners_count = serializers.IntegerField(read_only=True)
    total_payout = serializers.IntegerField(read_only=True)


class DashboardStatsSerializer(serializers.Serializer):
    """
    Сериализатор статистики для дашборда
    """
    active_rounds = serializers.IntegerField()
    total_bets_today = serializers.IntegerField()
    total_volume_today = serializers.IntegerField()
    platform_revenue_today = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    
    recent_rounds = GameRoundSerializer(many=True, read_only=True)
    top_winners = LeaderboardSerializer(many=True, read_only=True)


class ManualActionSerializer(serializers.Serializer):
    """
    Сериализатор для ручных действий админа
    """
    action = serializers.ChoiceField(choices=[
        ('create_round', 'Create Round'),
        ('close_round', 'Close Round'),
        ('process_round', 'Process Round'),
        ('void_round', 'Void Round'),
        ('process_analysis', 'Process Analysis'),
    ])
    round_id = serializers.IntegerField(required=False)
    news_id = serializers.IntegerField(required=False)
    force_result = serializers.ChoiceField(
        choices=[('positive', 'Positive'), ('negative', 'Negative')],
        required=False
    )
    
    def validate(self, data):
        action = data['action']
        
        if action in ['close_round', 'process_round', 'void_round'] and not data.get('round_id'):
            raise serializers.ValidationError("round_id is required for this action")
        
        if action == 'process_analysis' and not data.get('news_id'):
            raise serializers.ValidationError("news_id is required for analysis processing")
        
        return data


class RoundParticipationSerializer(serializers.Serializer):
    """
    Сериализатор для участия в раунде
    """
    round_id = serializers.IntegerField()
    
    def validate_round_id(self, value):
        """
        Валидация ID раунда
        """
        try:
            from .models import GameRound
            round_obj = GameRound.objects.get(id=value)
            
            # Проверяем что раунд открыт
            if round_obj.status != 'open':
                raise serializers.ValidationError("The round is closed for participation.")
            
            # Проверяем что время раунда ещё не вышло
            if round_obj.end_time <= timezone.now():
                raise serializers.ValidationError("Round time expired")
            
            return value
            
        except GameRound.DoesNotExist:
            raise serializers.ValidationError("Round not found")


class RoundParticipationResponseSerializer(serializers.Serializer):
    """
    Сериализатор ответа на участие в раунде
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    bonus_info = serializers.DictField(required=False, allow_null=True)
