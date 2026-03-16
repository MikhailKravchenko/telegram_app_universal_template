from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

from src.config import config

from django.contrib.auth.models import User
from django.core.cache import cache


def validate_positive_amount(value):
    """Validate that amount is positive"""
    if value <= 0:
        raise ValidationError('Amount must be positive')


def validate_balance_sufficiency(user, amount):
    """Validate that user has sufficient balance for deduction"""
    try:
        balance = user.balance.coins_balance
        if balance < amount:
            raise ValidationError(f'Insufficient balance. Required: {amount}, Available: {balance}')
    except UserBalance.DoesNotExist:
        raise ValidationError('User balance not found')


class CustomUser(User):
    telegram_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Telegram User ID"
    )
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
        db_index=True,
    )
    referral_points = models.PositiveIntegerField(default=0, db_index=True)

    def referral_count(self) -> int:
        return self.given_referrals.filter(approved=True).count()

    def __str__(self) -> str:
        return f"{self.username}"


class UserBalance(models.Model):
    """
    User balance model for tracking coins and transaction history
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="balance",
        db_index=True
    )
    coins_balance = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Current user balance in coins",
        validators=[MinValueValidator(0)]
    )
    total_earned = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Total coins earned by user",
        validators=[MinValueValidator(0)]
    )
    total_spent = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Total coins spent by user",
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        db_table = "user_balance"
        verbose_name = "User Balance"
        verbose_name_plural = "User Balances"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.coins_balance} coins"

    def clean(self):
        """Validate model data"""
        if self.coins_balance < 0:
            raise ValidationError("Balance cannot be negative")
        if self.total_earned < 0:
            raise ValidationError("Total earned cannot be negative")
        if self.total_spent < 0:
            raise ValidationError("Total spent cannot be negative")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """
    Transaction model for auditing all coin operations
    """
    TRANSACTION_TYPES = [
        ('bonus', 'Bonus'),
        ('bet', 'Bet'),
        ('win', 'Win'),
        ('referral', 'Referral'),
        ('daily_login', 'Daily Login'),
        ('social_subscription', 'Social Subscription'),
        ('starting_balance', 'Starting Balance'),
        ('transfer', 'Transfer'),
        ('rollback', 'Rollback'),
        ('presale_investment', 'Presale Investment'),
        ('refund', 'Refund for round'),
        ('platform_fee', 'Fee platform'),
        ('round_participation', 'Round Participation Bonus'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_index=True
    )
    amount = models.IntegerField(
        help_text="Transaction amount (positive for income, negative for expense)",
        validators=[MinValueValidator(-999999)]  # Allow negative amounts for deductions
    )
    type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        db_index=True
    )
    description = models.TextField(
        blank=True,
        help_text="Transaction description"
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference ID for related object (e.g., bet_id, news_id)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.type} - {self.amount} coins"

    def clean(self):
        """Validate transaction data"""
        if self.amount == 0:
            raise ValidationError("Transaction amount cannot be zero")
        
        # Validate amount based on transaction type
        if self.type in ['bet', 'transfer', 'presale_investment'] and self.amount > 0:
            raise ValidationError(f"Amount for {self.type} transactions should be negative")
        elif self.type in ['win', 'bonus', 'referral', 'daily_login', 'social_subscription', 'starting_balance', 'round_participation'] and self.amount < 0:
            raise ValidationError(f"Amount for {self.type} transactions should be positive")

    def save(self, *args, **kwargs):
        self.clean()
        # Update user balance when transaction is created
        if not self.pk:  # Only on creation
            self._update_user_balance()
        super().save(*args, **kwargs)

    def _update_user_balance(self):
        """Update user balance based on transaction amount"""
        try:
            user_balance = self.user.balance
            user_balance.coins_balance += self.amount
            
            if self.amount > 0:
                user_balance.total_earned += self.amount
            else:
                user_balance.total_spent += abs(self.amount)
            
            user_balance.save()
        except UserBalance.DoesNotExist:
            # Create user balance if it doesn't exist
            UserBalance.objects.create(
                user=self.user,
                coins_balance=self.amount if self.amount > 0 else 0,
                total_earned=self.amount if self.amount > 0 else 0,
                total_spent=abs(self.amount) if self.amount < 0 else 0
            )


class Bonus(models.Model):
    """
    Модель бонусов для пользователей
    """
    BONUS_TYPES = [
        ('daily_login', 'Daily Login'),
        ('social_subscription', 'Social Subscription'),
        ('telegram_channel_1', 'Telegram Channel 1'),
        ('telegram_channel_2', 'Telegram Channel 2'),
        ('first_bet', 'First Bet'),
        ('activity_bonus', 'Activity Bonus'),
        ('round_participation', 'Round Participation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('used', 'Used'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="bonuses",
        db_index=True
    )
    bonus_type = models.CharField(
        max_length=20,
        choices=BONUS_TYPES,
        db_index=True
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Сумма бонуса в монетах"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Дата истечения бонуса"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Дата использования бонуса"
    )
    
    # Дополнительные поля для отслеживания
    description = models.TextField(
        blank=True,
        help_text="Описание бонуса"
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID связанного объекта (например, bet_id)"
    )

    class Meta:
        db_table = "bonuses"
        verbose_name = "Bonus"
        verbose_name_plural = "Bonuses"
        ordering = ['-created_at']
        
        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['user', 'bonus_type']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['bonus_type', 'status']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.bonus_type} - {self.amount} coins ({self.status})"

    def clean(self):
        """Валидация модели"""
        if self.amount <= 0:
            raise ValidationError("Сумма бонуса должна быть положительной")
        
        # Проверка что дата истечения в будущем
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError("Дата истечения должна быть в будущем")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_expired(self):
        """Проверить истек ли бонус"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def can_be_used(self):
        """Проверить можно ли использовать бонус"""
        return self.status == 'active' and not self.is_expired()

    def activate(self):
        """Активировать бонус"""
        if self.status == 'pending':
            self.status = 'active'
            self.save(update_fields=['status'])

    def use(self):
        """Использовать бонус и начислить монеты"""
        if not self.can_be_used():
            raise ValidationError("Бонус нельзя использовать")
        
        from django.utils import timezone
        
        # Создаем транзакцию для начисления бонуса
        Transaction.objects.create(
            user=self.user,
            amount=self.amount,
            type='bonus',
            description=f"Бонус: {self.get_bonus_type_display()}",
            reference_id=str(self.id)
        )
        
        # Отмечаем бонус как использованный
        self.status = 'used'
        self.used_at = timezone.now()
        self.save(update_fields=['status', 'used_at'])


class UserActivityHour(models.Model):
    """
    Модель для отслеживания активности пользователя по часам.
    Используется ТОЛЬКО для статистики и аналитики.
    
    Бонусы за активность теперь начисляются мгновенно при каждой ставке,
    а не через эту модель.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="activity_hours",
        db_index=True
    )
    hour_start = models.DateTimeField(
        db_index=True,
        help_text="Начало часового интервала (округлено до часа)"
    )
    bets_count = models.PositiveIntegerField(
        default=0,
        help_text="Количество ставок в этом часе"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_activity_hours"
        verbose_name = "User Activity Hour"
        verbose_name_plural = "User Activity Hours"
        unique_together = ['user', 'hour_start']
        ordering = ['-hour_start']
        
        indexes = [
            models.Index(fields=['user', 'hour_start']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.hour_start.strftime('%H:00')} - {self.bets_count} ставок"


class BonusSettings(models.Model):
    """
    Модель для настраиваемых параметров бонусной системы через админ-панель
    """
    # Singleton pattern - только одна запись настроек
    id = models.AutoField(primary_key=True)
    
    # Бонусы за события
    daily_login_bonus = models.PositiveIntegerField(
        default=100,
        help_text="Размер бонуса за ежедневный вход (монет)"
    )
    social_subscription_bonus = models.PositiveIntegerField(
        default=1000,
        help_text="Размер бонуса за подписку на соцсеть (монет)"
    )
    telegram_channel_1_bonus = models.PositiveIntegerField(
        default=1000,
        help_text="Размер бонуса за подписку на Telegram канал 1 (монет)"
    )
    telegram_channel_2_bonus = models.PositiveIntegerField(
        default=1000,
        help_text="Размер бонуса за подписку на Telegram канал 2 (монет)"
    )
    first_bet_bonus = models.PositiveIntegerField(
        default=10,
        help_text="Размер бонуса за первую ставку (монет)"
    )
    round_participation_bonus = models.PositiveIntegerField(
        default=1,
        help_text="Размер бонуса за участие в раунде (монет)"
    )
    max_participations_per_round = models.PositiveIntegerField(
        default=10,
        help_text="Максимальное количество участий в одном раунде"
    )
    hourly_limit_round_participation = models.PositiveIntegerField(
        default=120,
        help_text="Максимальное количество бонусов за участие в раунде в час"
    )
    
    # Параметры бонуса за активность
    activity_coins_per_bet = models.PositiveIntegerField(
        default=10,
        help_text="Количество монет за одну ставку при расчете активности"
    )
    activity_max_bets_per_hour = models.PositiveIntegerField(
        default=12,
        help_text="Максимальное число учитываемых ставок в час для бонуса"
    )
    activity_daily_limit = models.PositiveIntegerField(
        default=2880,
        help_text="Суточный предел бонусных монет за активность"
    )
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "bonus_settings"
        verbose_name = "Настройки бонусной системы"
        verbose_name_plural = "Настройки бонусной системы"
    
    def __str__(self) -> str:
        return f"Настройки бонусов (обновлено: {self.updated_at.strftime('%d.%m.%Y %H:%M')})"
    
    def save(self, *args, **kwargs):
        """При сохранении очищаем кэш и обеспечиваем единственность записи"""
        # Удаляем все остальные записи настроек (Singleton pattern)
        if not self.pk:
            BonusSettings.objects.all().delete()
        
        super().save(*args, **kwargs)
        
        # Очищаем кэш при изменении настроек
        cache.delete('bonus_settings')
    
    @classmethod
    def get_settings(cls) -> 'BonusSettings':
        """
        Получить текущие настройки (с кэшированием)
        
        Returns:
            BonusSettings: Объект настроек
        """
        # Пытаемся получить из кэша
        settings = cache.get('bonus_settings')
        
        if settings is None:
            try:
                settings = cls.objects.first()
                if not settings:
                    # Создаем настройки по умолчанию если их нет
                    settings = cls.objects.create()
                
                # Кэшируем на 1 час
                cache.set('bonus_settings', settings, 3600)
            except Exception:
                # Возвращаем настройки по умолчанию если что-то пошло не так
                settings = cls()
        
        return settings
    
    def clean(self):
        """Валидация настроек"""
        if self.daily_login_bonus < 0:
            raise ValidationError("Размер бонуса за ежедневный вход не может быть отрицательным")
        
        if self.social_subscription_bonus < 0:
            raise ValidationError("Размер бонуса за подписку не может быть отрицательным")
        
        if self.first_bet_bonus < 0:
            raise ValidationError("Размер бонуса за первую ставку не может быть отрицательным")
        
        if self.round_participation_bonus < 0:
            raise ValidationError("Размер бонуса за участие в раунде не может быть отрицательным")
        
        if self.activity_coins_per_bet <= 0:
            raise ValidationError("Количество монет за ставку должно быть положительным")
        
        if self.activity_max_bets_per_hour <= 0:
            raise ValidationError("Максимальное число ставок в час должно быть положительным")
        
        if self.activity_daily_limit <= 0:
            raise ValidationError("Суточный лимит должен быть положительным")
        
        # Проверим что суточный лимит логично соотносится с часовыми бонусами
        max_hourly_bonus = self.activity_coins_per_bet * self.activity_max_bets_per_hour
        max_daily_from_hours = max_hourly_bonus * 24
        
        if self.activity_daily_limit > max_daily_from_hours:
            raise ValidationError(
                f"Суточный лимит ({self.activity_daily_limit}) не может быть больше "
                f"чем максимум за 24 часа ({max_daily_from_hours} = {max_hourly_bonus} * 24)"
            )


class ReferralLevel(models.Model):
    """
    Настраиваемые уровни реферальной программы
    """
    level = models.PositiveIntegerField(
        unique=True,
        db_index=True,
        help_text="Уровень (порядковый номер)"
    )
    min_referrals = models.PositiveIntegerField(
        help_text="Минимальное количество рефералов для достижения уровня"
    )
    bonus_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Процент бонуса от инвестиций рефералов (например, 5.00 для 5%)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Активен ли данный уровень"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level']
        verbose_name = "Уровень реферальной программы"
        verbose_name_plural = "Уровни реферальной программы"

    def __str__(self) -> str:
        return f"Уровень {self.level}: {self.min_referrals}+ рефералов = {self.bonus_percentage}%"


class Referral(models.Model):
    referrer = models.ForeignKey(
        CustomUser,
        related_name="given_referrals",
        on_delete=models.CASCADE,
        db_index=True,
    )
    referred = models.ForeignKey(
        CustomUser,
        related_name="received_referrals",
        on_delete=models.CASCADE,
        db_index=True,
    )
    approved = models.BooleanField(default=True)  # Теперь по умолчанию одобрено
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Статистика бонусов
    total_bonus_earned = models.PositiveIntegerField(
        default=0,
        help_text="Общая сумма заработанных бонусов с этого реферала"
    )
    last_bonus_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Время последнего начисления бонуса"
    )

    class Meta:
        unique_together = ['referrer', 'referred']
        verbose_name = "Реферал"
        verbose_name_plural = "Рефералы"

    def __str__(self) -> str:
        return f"{self.referrer} referred {self.referred}"


class ReferralBonus(models.Model):
    """
    История начислений реферальных бонусов
    """
    referrer = models.ForeignKey(
        CustomUser,
        related_name="referral_bonuses_received",
        on_delete=models.CASCADE,
        db_index=True,
    )
    referred = models.ForeignKey(
        CustomUser,
        related_name="referral_bonuses_triggered",
        on_delete=models.CASCADE,
        db_index=True,
    )
    investment_amount = models.PositiveIntegerField(
        help_text="Сумма инвестиции реферала, за которую начислен бонус"
    )
    bonus_amount = models.PositiveIntegerField(
        help_text="Размер начисленного бонуса"
    )
    bonus_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Процент бонуса на момент начисления"
    )
    referral_level = models.PositiveIntegerField(
        help_text="Уровень реферальной программы на момент начисления"
    )
    presale_round = models.PositiveIntegerField(
        help_text="Раунд пресейла, в котором была сделана инвестиция"
    )
    transaction_id = models.CharField(
        max_length=100,
        help_text="ID транзакции начисления бонуса"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Реферальный бонус"
        verbose_name_plural = "Реферальные бонусы"

    def __str__(self) -> str:
        return f"Бонус {self.bonus_amount} монет для {self.referrer} за инвестицию {self.referred}"


class BotSettings(models.Model):
    """
    Настройки бота, которые можно изменять через админпанель
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Ключ настройки"
    )
    value = models.TextField(
        help_text="Значение настройки"
    )
    description = models.TextField(
        blank=True,
        help_text="Описание настройки"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Активна ли настройка"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройка бота"
        verbose_name_plural = "Настройки бота"
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key: str, default: str = "") -> str:
        """
        Получить значение настройки по ключу
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию, если настройка не найдена
            
        Returns:
            str: Значение настройки или значение по умолчанию
        """
        try:
            setting = cls.objects.get(key=key, is_active=True)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key: str, value: str, description: str = "") -> None:
        """
        Установить значение настройки
        
        Args:
            key: Ключ настройки
            value: Значение настройки
            description: Описание настройки
        """
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            setting.description = description
            setting.save()

