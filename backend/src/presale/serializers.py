from rest_framework import serializers
from decimal import Decimal
from .models import Presale, PresaleRound, Investment, UserPresaleStats


class PresaleRoundSerializer(serializers.ModelSerializer):
    """Сериализатор раунда пресейла"""
    
    class Meta:
        model = PresaleRound
        fields = [
            'round_number',
            'tokens_per_coin', 
            'target_investment',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['created_at']


class PresaleSerializer(serializers.ModelSerializer):
    """Сериализатор пресейла"""
    
    current_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    current_round_investment = serializers.IntegerField(read_only=True)
    current_round_target = serializers.IntegerField(read_only=True)
    progress_percent = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Presale
        fields = [
            'id',
            'name',
            'status',
            'current_round',
            'total_rounds',
            'total_invested',
            'total_tokens_sold',
            'current_rate',
            'current_round_investment',
            'current_round_target',
            'progress_percent',
            'start_time',
            'end_time',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'total_invested', 
            'total_tokens_sold',
            'current_rate',
            'current_round_investment', 
            'current_round_target',
            'progress_percent',
            'created_at', 
            'updated_at'
        ]


class InvestmentSerializer(serializers.ModelSerializer):
    """Сериализатор инвестиции"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id',
            'user',
            'user_username',
            'presale',
            'amount',
            'tokens_received',
            'round_number',
            'rate_at_purchase',
            'transaction_id',
            'created_at'
        ]
        read_only_fields = [
            'user',
            'user_username', 
            'tokens_received',
            'rate_at_purchase',
            'transaction_id',
            'created_at'
        ]


class CreateInvestmentSerializer(serializers.Serializer):
    """Сериализатор для создания инвестиции"""
    
    amount = serializers.IntegerField(min_value=1, max_value=1000000)
    
    def validate_amount(self, value):
        """Валидация суммы инвестиции"""
        if value < 10:
            raise serializers.ValidationError("Минимальная сумма инвестиции: 10 монет")
        return value


class UserPresaleStatsSerializer(serializers.ModelSerializer):
    """Сериализатор статистики пользователя"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserPresaleStats
        fields = [
            'user',
            'user_username',
            'total_invested',
            'total_tokens',
            'investments_count',
            'first_investment_at',
            'last_investment_at',
            'updated_at'
        ]
        read_only_fields = [
            'user',
            'user_username',
            'total_invested',
            'total_tokens', 
            'investments_count',
            'first_investment_at',
            'last_investment_at',
            'updated_at'
        ]


class PresaleSummarySerializer(serializers.Serializer):
    """Сериализатор сводки пресейла"""
    
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    current_round = serializers.IntegerField()
    total_rounds = serializers.IntegerField()
    total_invested = serializers.IntegerField()
    total_tokens_sold = serializers.DecimalField(max_digits=20, decimal_places=2)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField(allow_null=True)
    current_round_info = serializers.DictField()


class CurrentRoundInfoSerializer(serializers.Serializer):
    """Сериализатор информации о текущем раунде"""
    
    round_number = serializers.IntegerField()
    tokens_per_coin = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    target_investment = serializers.IntegerField()
    current_investment = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    remaining_investment = serializers.IntegerField()
    is_completed = serializers.BooleanField()


class UserInvestmentSummarySerializer(serializers.Serializer):
    """Сериализатор сводки инвестиций пользователя"""
    
    total_invested = serializers.IntegerField()
    total_tokens = serializers.DecimalField(max_digits=20, decimal_places=2)
    investments_count = serializers.IntegerField()
    average_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    first_investment = InvestmentSerializer(allow_null=True)
    last_investment = InvestmentSerializer(allow_null=True)


class RoundStatsSerializer(serializers.Serializer):
    """Сериализатор статистики раунда"""
    
    round_number = serializers.IntegerField()
    total_invested = serializers.IntegerField()
    total_tokens = serializers.DecimalField(max_digits=20, decimal_places=2)
    investors_count = serializers.IntegerField()
    target_investment = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    rate = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    is_current = serializers.BooleanField()
    is_completed = serializers.BooleanField()


class GlobalStatsSerializer(serializers.Serializer):
    """Сериализатор глобальной статистики"""
    
    total_presales = serializers.IntegerField()
    active_presales = serializers.IntegerField()
    total_investments = serializers.IntegerField()
    total_invested = serializers.IntegerField()
    total_tokens_sold = serializers.DecimalField(max_digits=20, decimal_places=2)
    average_investment = serializers.FloatField()
    unique_investors = serializers.IntegerField()
