from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class PresaleRound(models.Model):
    """Настройки раунда пресейла"""
    
    round_number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)]
    )
    tokens_per_coin = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Сколько токенов получает пользователь за одну монету"
    )
    target_investment = models.PositiveIntegerField(
        default=0,
        help_text="Целевая сумма инвестиций для раунда (в монетах)"
    )
    max_user_investment = models.PositiveIntegerField(
        default=0,
        help_text="Максимальная сумма инвестиции одного пользователя в раунде (0 = без ограничений)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['round_number']
        verbose_name = "Раунд пресейла"
        verbose_name_plural = "Раунды пресейла"
    
    def __str__(self):
        return f"Раунд {self.round_number} (курс: {self.tokens_per_coin} токенов за монету)"


class Presale(models.Model):
    """Основная модель пресейла"""
    
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('paused', 'Приостановлен'),
    ]
    
    name = models.CharField(max_length=100, default="PULSE Token Presale")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_round = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    total_rounds = models.PositiveIntegerField(default=25)
    total_invested = models.PositiveIntegerField(
        default=0,
        help_text="Общая сумма инвестированных монет"
    )
    total_tokens_sold = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Общее количество проданных токенов"
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Пресейл"
        verbose_name_plural = "Пресейлы"
    
    def __str__(self):
        return f"{self.name} - Раунд {self.current_round}/{self.total_rounds}"
    
    @property
    def current_rate(self):
        """Получить текущий курс (токенов за монету)"""
        try:
            round_obj = PresaleRound.objects.get(round_number=self.current_round)
            return round_obj.tokens_per_coin
        except PresaleRound.DoesNotExist:
            return None
    
    @property
    def current_round_investment(self):
        """Сумма инвестиций в текущем раунде"""
        return Investment.objects.filter(
            presale=self,
            round_number=self.current_round
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def current_round_target(self):
        """Целевая сумма для текущего раунда"""
        try:
            round_obj = PresaleRound.objects.get(round_number=self.current_round)
            return round_obj.target_investment
        except PresaleRound.DoesNotExist:
            return 0
    
    @property
    def progress_percent(self):
        """Прогресс текущего раунда в процентах"""
        target = self.current_round_target
        if target == 0:
            return 0
        current = self.current_round_investment
        return min(100, (current / target) * 100)
    
    def is_active(self):
        """Проверить, активен ли пресейл"""
        return (
            self.status == 'active' and 
            self.current_round <= self.total_rounds
        )


class Investment(models.Model):
    """Инвестиция пользователя в пресейл"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presale_investments')
    presale = models.ForeignKey(Presale, on_delete=models.CASCADE, related_name='investments')
    amount = models.PositiveIntegerField(help_text="Количество инвестированных монет")
    tokens_received = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Количество полученных токенов"
    )
    round_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    rate_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Курс на момент покупки (токенов за монету)"
    )
    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID транзакции в системе баланса"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Инвестиция"
        verbose_name_plural = "Инвестиции"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['presale', 'round_number']),
        ]
    
    def __str__(self):
        return (
            f"{self.user} - {self.amount} монет -> "
            f"{self.tokens_received} токенов (Раунд {self.round_number})"
        )


class UserPresaleStats(models.Model):
    """Статистика пользователя по пресейлу"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presale_stats')
    total_invested = models.PositiveIntegerField(
        default=0,
        help_text="Общая сумма инвестированных монет"
    )
    total_tokens = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Общее количество токенов"
    )
    investments_count = models.PositiveIntegerField(
        default=0,
        help_text="Количество инвестиций"
    )
    first_investment_at = models.DateTimeField(null=True, blank=True)
    last_investment_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Статистика пользователя по пресейлу"
        verbose_name_plural = "Статистика пользователей по пресейлу"
    
    def __str__(self):
        return f"{self.user} - {self.total_tokens} токенов"
    
    @property
    def average_investment(self):
        """Средняя сумма инвестиции"""
        if self.investments_count == 0:
            return 0
        return self.total_invested / self.investments_count