from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Max
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Presale, PresaleRound, Investment, UserPresaleStats


@admin.register(PresaleRound)
class PresaleRoundAdmin(admin.ModelAdmin):
    """Админка для раундов пресейла"""
    
    list_display = [
        'round_number', 
        'tokens_per_coin', 
        'target_investment',
        'max_user_investment',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    list_editable = ['tokens_per_coin', 'target_investment', 'max_user_investment', 'is_active']
    ordering = ['round_number']
    search_fields = ['round_number']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('round_number', 'tokens_per_coin', 'target_investment')
        }),
        ('Ограничения', {
            'fields': ('max_user_investment',),
            'description': 'Максимальная сумма инвестиции одного пользователя в раунде. 0 = без ограничений.'
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )


class InvestmentInline(admin.TabularInline):
    """Инлайн для инвестиций в админке пресейла"""
    
    model = Investment
    extra = 0
    readonly_fields = [
        'user', 'amount', 'tokens_received', 
        'round_number', 'rate_at_purchase', 'created_at'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False


@admin.register(Presale)
class PresaleAdmin(admin.ModelAdmin):
    """Админка для пресейлов"""
    
    list_display = [
        'name', 
        'status', 
        'current_round_display',
        'total_invested_display',
        'total_tokens_sold_display',
        'progress_display',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    readonly_fields = [
        'total_invested', 
        'total_tokens_sold',
        'current_rate_display',
        'current_round_stats',
        'created_at', 
        'updated_at'
    ]
    inlines = [InvestmentInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'status', 'current_round', 'total_rounds'),
            'description': 'Основные настройки пресейла. Можно изменить общее количество раундов.'
        }),
        ('Статистика', {
            'fields': (
                'total_invested', 
                'total_tokens_sold',
                'current_rate_display',
                'current_round_stats'
            ),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('start_time', 'end_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Настройка формы для редактирования"""
        form = super().get_form(request, obj, **kwargs)
        
        # Делаем total_rounds редактируемым только для суперпользователей
        if not request.user.is_superuser:
            if 'total_rounds' in form.base_fields:
                form.base_fields['total_rounds'].disabled = True
                form.base_fields['total_rounds'].help_text = (
                    'Изменение количества раундов доступно только суперпользователям'
                )
        else:
            if 'total_rounds' in form.base_fields:
                form.base_fields['total_rounds'].help_text = (
                    'Общее количество раундов в пресейле. '
                    'ВНИМАНИЕ: Убедитесь что созданы все необходимые раунды!'
                )
        
        return form
    
    def current_round_display(self, obj):
        """Отображение текущего раунда"""
        return f"{obj.current_round}/{obj.total_rounds}"
    current_round_display.short_description = "Раунд"
    
    def total_invested_display(self, obj):
        """Отображение общей суммы инвестиций"""
        return format_html(
            '<strong>{}</strong> монет', 
            f"{obj.total_invested:,}"
        )
    total_invested_display.short_description = "Инвестировано"
    
    def total_tokens_sold_display(self, obj):
        """Отображение проданных токенов"""
        return format_html(
            '<strong>{}</strong> токенов', 
            f"{obj.total_tokens_sold:,.2f}"
        )
    total_tokens_sold_display.short_description = "Продано токенов"
    
    def progress_display(self, obj):
        """Отображение прогресса текущего раунда"""
        progress = obj.progress_percent
        color = 'green' if progress >= 100 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, f"{progress:.1f}%"
        )
    progress_display.short_description = "Прогресс раунда"
    
    def current_rate_display(self, obj):
        """Отображение текущего курса"""
        rate = obj.current_rate
        if rate:
            return f"{rate} токенов за монету"
        return "Не настроен"
    current_rate_display.short_description = "Текущий курс"
    
    def current_round_stats(self, obj):
        """Статистика текущего раунда"""
        current_investment = obj.current_round_investment
        target = obj.current_round_target
        investors_count = Investment.objects.filter(
            presale=obj,
            round_number=obj.current_round
        ).values('user').distinct().count()
        
        return format_html(
            '''
            <div>
                <strong>Раунд {}:</strong><br>
                Инвестировано: {} / {} монет<br>
                Прогресс: {:.1f}%<br>
                Инвесторов: {}
            </div>
            ''',
            obj.current_round,
            f"{current_investment:,}",
            f"{target:,}",
            obj.progress_percent,
            investors_count
        )
    current_round_stats.short_description = "Статистика раунда"
    
    actions = ['advance_to_next_round', 'complete_presale', 'create_missing_rounds']
    
    def advance_to_next_round(self, request, queryset):
        """Действие для перехода к следующему раунду"""
        from .services import PresaleService
        
        updated_count = 0
        for presale in queryset.filter(status='active'):
            if PresaleService.advance_to_next_round(presale):
                updated_count += 1
        
        self.message_user(
            request,
            f'Переведено к следующему раунду: {updated_count} пресейлов'
        )
    advance_to_next_round.short_description = "Перейти к следующему раунду"
    
    def complete_presale(self, request, queryset):
        """Действие для завершения пресейла"""
        updated_count = queryset.filter(status='active').update(status='completed')
        self.message_user(
            request,
            f'Завершено пресейлов: {updated_count}'
        )
    complete_presale.short_description = "Завершить пресейл"
    
    def create_missing_rounds(self, request, queryset):
        """Действие для создания недостающих раундов"""
        from .services import PresaleRoundService
        from .models import PresaleRound
        
        created_total = 0
        for presale in queryset:
            # Найти максимальный существующий раунд
            max_existing = PresaleRound.objects.filter(
                round_number__lte=presale.total_rounds
            ).aggregate(max_round=Max('round_number'))['max_round'] or 0
            
            # Создать недостающие раунды
            for round_num in range(max_existing + 1, presale.total_rounds + 1):
                # Базовые настройки для новых раундов
                tokens_per_coin = max(5.0, 105.0 - round_num * 4.0)  # Падающий курс
                target_investment = 5000 + round_num * 2000  # Растущие цели
                max_user_investment = 500 + round_num * 500  # Растущие лимиты
                
                round_obj, created = PresaleRound.objects.get_or_create(
                    round_number=round_num,
                    defaults={
                        'tokens_per_coin': tokens_per_coin,
                        'target_investment': target_investment,
                        'max_user_investment': max_user_investment,
                    }
                )
                if created:
                    created_total += 1
        
        self.message_user(
            request,
            f'Создано новых раундов: {created_total}. '
            f'Проверьте и настройте их параметры при необходимости.'
        )
    create_missing_rounds.short_description = "Создать недостающие раунды"


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Админка для инвестиций"""
    
    list_display = [
        'user',
        'presale',
        'amount_display',
        'tokens_received_display',
        'round_number',
        'rate_at_purchase',
        'created_at'
    ]
    list_filter = [
        'presale',
        'round_number',
        'created_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    readonly_fields = [
        'user', 'presale', 'amount', 'tokens_received',
        'round_number', 'rate_at_purchase', 'transaction_id', 'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'transaction_id'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def amount_display(self, obj):
        """Отображение суммы инвестиции"""
        return format_html(
            '<strong>{}</strong> монет',
            f"{obj.amount:,}"
        )
    amount_display.short_description = "Сумма"
    amount_display.admin_order_field = 'amount'
    
    def tokens_received_display(self, obj):
        """Отображение полученных токенов"""
        return format_html(
            '<strong>{}</strong> токенов',
            f"{obj.tokens_received:,.2f}"
        )
    tokens_received_display.short_description = "Токены"
    tokens_received_display.admin_order_field = 'tokens_received'
    
    def has_add_permission(self, request):
        """Запретить создание инвестиций через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запретить изменение инвестиций"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Запретить удаление инвестиций"""
        return False


@admin.register(UserPresaleStats)
class UserPresaleStatsAdmin(admin.ModelAdmin):
    """Админка для статистики пользователей"""
    
    list_display = [
        'user',
        'total_invested_display',
        'total_tokens_display',
        'investments_count',
        'average_investment_display',
        'last_investment_at'
    ]
    list_filter = [
        'investments_count',
        'first_investment_at',
        'last_investment_at'
    ]
    readonly_fields = [
        'user', 'total_invested', 'total_tokens',
        'investments_count', 'first_investment_at',
        'last_investment_at', 'updated_at',
        'average_investment_display'
    ]
    search_fields = ['user__username', 'user__email']
    ordering = ['-total_tokens']
    
    def total_invested_display(self, obj):
        """Отображение общей суммы инвестиций"""
        return format_html(
            '<strong>{}</strong> монет',
            f"{obj.total_invested:,}"
        )
    total_invested_display.short_description = "Инвестировано"
    total_invested_display.admin_order_field = 'total_invested'
    
    def total_tokens_display(self, obj):
        """Отображение общего количества токенов"""
        return format_html(
            '<strong>{}</strong> токенов',
            f"{obj.total_tokens:,.2f}"
        )
    total_tokens_display.short_description = "Токены"
    total_tokens_display.admin_order_field = 'total_tokens'
    
    def average_investment_display(self, obj):
        """Отображение средней инвестиции"""
        avg = obj.average_investment
        return format_html(
            '{} монет',
            f"{avg:,.0f}"
        )
    average_investment_display.short_description = "Средняя инвестиция"
    
    def has_add_permission(self, request):
        """Запретить создание статистики через админку"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запретить изменение статистики"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление статистики только суперпользователям"""
        return request.user.is_superuser