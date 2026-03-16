import django_filters
from django.db import models
from .models import GameRound, Bet


class GameRoundFilter(django_filters.FilterSet):
    """
    Фильтры для игровых раундов
    """
    round_type = django_filters.ChoiceFilter(choices=GameRound.ROUND_TYPE_CHOICES)
    status = django_filters.ChoiceFilter(choices=GameRound.STATUS_CHOICES)
    start_time_from = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')
    end_time_from = django_filters.DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_time_to = django_filters.DateTimeFilter(field_name='end_time', lookup_expr='lte')
    
    class Meta:
        model = GameRound
        fields = ['round_type', 'status', 'start_time_from', 'start_time_to', 'end_time_from', 'end_time_to']


class BetFilter(django_filters.FilterSet):
    """
    Фильтры для ставок
    """
    choice = django_filters.ChoiceFilter(choices=Bet.CHOICE_CHOICES)
    status = django_filters.ChoiceFilter(choices=Bet.STATUS_CHOICES)
    amount_from = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_to = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    created_at_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    round_status = django_filters.CharFilter(field_name='round__status')
    
    class Meta:
        model = Bet
        fields = ['choice', 'status', 'amount_from', 'amount_to', 'created_at_from', 'created_at_to', 'round_status']
