from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import hashlib

from src.accounts.models import CustomUser, UserBalance, Transaction


class PlatformSettings(models.Model):
    """
    Настройки платформы для управления бизнес-правилами
    """
    round_duration_seconds = models.PositiveIntegerField(
        default=300,
        help_text="Длительность раунда в секундах"
    )
    platform_fee_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.0500'),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Доля комиссии платформы (0.05 = 5%)"
    )
    min_bet = models.PositiveIntegerField(
        default=10,
        help_text="Минимальная ставка"
    )
    max_bet = models.PositiveIntegerField(
        default=10000,
        help_text="Максимальная ставка"
    )
    # Флаги для подбора новостей
    news_freshness_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Максимальный возраст новости в минутах"
    )
    min_news_content_length = models.PositiveIntegerField(
        default=100,
        help_text="Минимальная длина контента новости"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Включены ли игры на платформе"
    )
    # OpenAI API настройки
    openai_api_key = models.CharField(
        max_length=200,
        blank=True,
        help_text="OpenAI API ключ для анализа тональности"
    )
    openai_model = models.CharField(
        max_length=100,
        default="gpt-3.5-turbo",
        help_text="Модель OpenAI для анализа (gpt-3.5-turbo, gpt-4, gpt-4o-mini)"
    )
    openai_max_tokens = models.PositiveIntegerField(
        default=150,
        help_text="Максимальное количество токенов в ответе"
    )
    openai_temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.1'),
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        help_text="Температура для генерации (0.0-2.0)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "platform_settings"
        verbose_name = "Platform Settings"
        verbose_name_plural = "Platform Settings"

    def __str__(self):
        openai_status = "✓" if self.openai_api_key else "✗"
        return f"Platform Settings (fee: {self.platform_fee_rate}%, duration: {self.round_duration_seconds}s, OpenAI: {openai_status}, model: {self.openai_model}, openai_api_key: {self.openai_api_key})"

    @classmethod
    def get_current(cls):
        """Получить текущие настройки платформы"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'round_duration_seconds': 300,
                'platform_fee_rate': Decimal('0.0500'),
                'min_bet': 10,
                'max_bet': 10000,
            }
        )
        return settings


class News(models.Model):
    """
    Новости для игровых раундов
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),     # Доступна для назначения
        ('active', 'Active'),       # Закреплена за раундом
        ('completed', 'Completed'), # Результат получен
    ]

    CATEGORY_CHOICES = [
        ('finance', 'Finance'),
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('general', 'General'),
    ]

    title = models.TextField()
    content = models.TextField(null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    source_url = models.URLField(unique=True)
    source = models.ForeignKey(
        'NewsSource',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='news_items',
        help_text="Источник новости (может быть NULL при удалении источника)"
    )
    category = models.CharField(
        max_length=2000,
        choices=CATEGORY_CHOICES,
        default='general',
        null=True,
    )
    status = models.CharField(
        max_length=2000,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Дополнительные поля
    dedup_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hash для дедупликации"
    )
    language = models.CharField(max_length=500, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "news"
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title[:50]}... ({self.status})"

    def save(self, *args, **kwargs):
        # Генерируем dedup_hash если не задан
        if not self.dedup_hash:
            content_for_hash = f"{self.source_url}{self.title}{self.content}"
            self.dedup_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
        super().save(*args, **kwargs)


class GameRound(models.Model):
    """
    Игровой раунд
    """
    STATUS_CHOICES = [
        ('open', 'Open'),           # Идёт приём ставок
        ('closed', 'Closed'),       # Ставки закрыты, идёт подбор новости
        ('finished', 'Finished'),   # Выплаты сделаны
        ('void', 'Void'),          # Аннулирован
    ]

    RESULT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ]

    ROUND_TYPE_CHOICES = [
        ('short', 'Short Round'),   # Короткий раунд (5 минут)
        ('long', 'Long Round'),     # Длинный раунд (24 часа)
    ]

    round_type = models.CharField(
        max_length=20,
        choices=ROUND_TYPE_CHOICES,
        default='short',
        db_index=True,
        help_text="Тип раунда: короткий (5 мин) или длинный (24 часа)"
    )
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )
    news = models.ForeignKey(
        News,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='game_rounds'
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        null=True,
        blank=True,
        db_index=True
    )
    
    # Агрегаты для быстрого вывода
    pot_total = models.PositiveIntegerField(default=0)
    pot_positive = models.PositiveIntegerField(default=0)
    pot_negative = models.PositiveIntegerField(default=0)
    fee_applied_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_rounds"
        verbose_name = "Game Round"
        verbose_name_plural = "Game Rounds"
        ordering = ['-start_time']

    def __str__(self):
        type_icon = "⚡" if self.round_type == 'short' else "📅"
        return f"{type_icon} Round {self.id} ({self.round_type} - {self.start_time.strftime('%H:%M')} - {self.status})"

    def clean(self):
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

    def update_pot_totals(self):
        """Обновить агрегаты по ставкам"""
        bets = self.bets.all()
        self.pot_total = sum(bet.amount for bet in bets)
        self.pot_positive = sum(bet.amount for bet in bets if bet.choice == 'positive')
        self.pot_negative = sum(bet.amount for bet in bets if bet.choice == 'negative')
        self.save(update_fields=['pot_total', 'pot_positive', 'pot_negative'])


class Bet(models.Model):
    """
    Ставка пользователя
    """
    CHOICE_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="bets",
        db_index=True
    )
    round = models.ForeignKey(
        GameRound,
        on_delete=models.CASCADE,
        related_name="bets",
        db_index=True
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    choice = models.CharField(
        max_length=20,
        choices=CHOICE_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Для расчёта выплат
    payout_amount = models.PositiveIntegerField(default=0)
    payout_coefficient = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "bets"
        verbose_name = "Bet"
        verbose_name_plural = "Bets"
        ordering = ['-created_at']
        unique_together = ['user', 'round']  # Один пользователь - одна ставка на раунд

    def __str__(self):
        return f"{self.user.username} - {self.amount} on {self.choice} (Round {self.round.id})"

    def clean(self):
        # Проверка лимитов ставки
        settings = PlatformSettings.get_current()
        if self.amount < settings.min_bet:
            raise ValidationError(f"Minimum bet is {settings.min_bet}")
        if self.amount > settings.max_bet:
            raise ValidationError(f"Maximum bet is {settings.max_bet}")
        
        # Проверка статуса раунда
        if self.round.status != 'open':
            raise ValidationError("Cannot place bet on closed round")


class NewsAnalysis(models.Model):
    """
    Результаты анализа новостей нейросетью
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]

    LABEL_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ]

    news = models.OneToOneField(
        News,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES,
        null=True,
        blank=True
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Уверенность от 0 до 1"
    )
    
    # Метаданные анализа
    provider = models.CharField(max_length=100, blank=True, help_text="Провайдер нейросети")
    model_name = models.CharField(max_length=100, blank=True, help_text="Название модели")
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Уверенность анализа от 0 до 1"
    )
    processing_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Время обработки в секундах"
    )
    raw_response = models.TextField(
        blank=True,
        help_text="Сырой ответ нейросети"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Сообщение об ошибке",
        null=True,
    )
    raw_payload = models.JSONField(null=True, blank=True, help_text="Дополнительные данные")
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "news_analysis"
        verbose_name = "News Analysis"
        verbose_name_plural = "News Analyses"

    def __str__(self):
        return f"Analysis for {self.news.title[:30]}... ({self.status})"


class NewsSource(models.Model):
    """
    Источники новостей для парсинга (RSS, Atom, Feed)
    """
    STATUS_CHOICES = [
        ('active', 'Active'),         # Активный источник
        ('inactive', 'Inactive'),     # Неактивный источник
        ('error', 'Error'),          # Ошибка парсинга
    ]

    SOURCE_TYPE_CHOICES = [
        ('rss', 'RSS Feed'),
        ('atom', 'Atom Feed'),
        ('feed', 'Generic Feed'),
        ('json', 'JSON Feed'),
    ]

    CATEGORY_CHOICES = [
        ('finance', 'Finance'),
        ('politics', 'Politics'),
        ('technology', 'Technology'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('general', 'General'),
    ]

    name = models.CharField(
        max_length=200,
        help_text="Название источника новостей"
    )
    url = models.URLField(
        unique=True,
        help_text="URL ленты новостей"
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default='rss',
        help_text="Тип источника новостей"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        help_text="Категория новостей"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="Язык новостей (en, ru, etc.)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Статус источника"
    )
    
    # Настройки парсинга
    enabled = models.BooleanField(
        default=True,
        help_text="Включен ли источник для парсинга"
    )
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Приоритет источника (1 - высший)"
    )
    update_frequency_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Частота обновления в минутах"
    )
    max_items_per_update = models.PositiveIntegerField(
        default=50,
        help_text="Максимальное количество новостей за одно обновление"
    )
    
    # Фильтры контента
    min_content_length = models.PositiveIntegerField(
        default=100,
        help_text="Минимальная длина контента новости"
    )
    keywords_filter = models.TextField(
        blank=True,
        help_text="Ключевые слова для фильтрации (по одному на строку)"
    )
    exclude_keywords = models.TextField(
        blank=True,
        help_text="Ключевые слова для исключения (по одному на строку)"
    )
    
    # Статистика
    last_parsed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Время последнего успешного парсинга"
    )
    last_error_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Время последней ошибки парсинга"
    )
    last_error_message = models.TextField(
        blank=True,
        help_text="Сообщение о последней ошибке"
    )
    total_parsed_count = models.PositiveIntegerField(
        default=0,
        help_text="Общее количество успешно спарсенных новостей"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "news_sources"
        verbose_name = "News Source"
        verbose_name_plural = "News Sources"
        ordering = ['priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"

    def get_keywords_list(self):
        """Получить список ключевых слов для фильтрации"""
        if not self.keywords_filter:
            return []
        return [kw.strip() for kw in self.keywords_filter.split('\n') if kw.strip()]

    def get_exclude_keywords_list(self):
        """Получить список ключевых слов для исключения"""
        if not self.exclude_keywords:
            return []
        return [kw.strip() for kw in self.exclude_keywords.split('\n') if kw.strip()]

    def update_parsing_stats(self, success=True, error_message=None):
        """Обновить статистику парсинга"""
        from django.utils import timezone
        
        if success:
            self.last_parsed_at = timezone.now()
            self.total_parsed_count += 1
            self.status = 'active'
            self.last_error_message = ''
        else:
            self.last_error_at = timezone.now()
            self.last_error_message = error_message or 'Unknown error'
            self.status = 'error'
        
        self.save(update_fields=[
            'last_parsed_at', 'last_error_at', 'last_error_message',
            'total_parsed_count', 'status'
        ])


class RoundStats(models.Model):
    """
    Кэш статистики раунда для быстрого отображения
    """
    round = models.OneToOneField(
        GameRound,
        on_delete=models.CASCADE,
        related_name='stats'
    )
    
    # Статистика ставок
    total_bets_count = models.PositiveIntegerField(default=0)
    positive_bets_count = models.PositiveIntegerField(default=0)
    negative_bets_count = models.PositiveIntegerField(default=0)
    
    # Статистика сумм
    total_amount = models.PositiveIntegerField(default=0)
    positive_amount = models.PositiveIntegerField(default=0)
    negative_amount = models.PositiveIntegerField(default=0)
    
    # Коэффициенты
    positive_coefficient = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    negative_coefficient = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    
    # Выплаты
    total_payout = models.PositiveIntegerField(default=0)
    platform_fee = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "round_stats"
        verbose_name = "Round Stats"
        verbose_name_plural = "Round Stats"

    def __str__(self):
        return f"Stats for Round {self.round.id}"

    def calculate_stats(self):
        """Пересчитать статистику раунда"""
        bets = self.round.bets.all()
        
        self.total_bets_count = bets.count()
        self.positive_bets_count = bets.filter(choice='positive').count()
        self.negative_bets_count = bets.filter(choice='negative').count()
        
        self.total_amount = sum(bet.amount for bet in bets)
        self.positive_amount = sum(bet.amount for bet in bets if bet.choice == 'positive')
        self.negative_amount = sum(bet.amount for bet in bets if bet.choice == 'negative')
        
        # Расчёт коэффициентов
        settings = PlatformSettings.get_current()
        fee_rate = settings.platform_fee_rate
        
        if self.total_amount > 0:
            available_for_payout = self.total_amount * (1 - fee_rate)
            
            if self.positive_amount > 0:
                self.positive_coefficient = available_for_payout / self.positive_amount
            if self.negative_amount > 0:
                self.negative_coefficient = available_for_payout / self.negative_amount
        
        self.save()