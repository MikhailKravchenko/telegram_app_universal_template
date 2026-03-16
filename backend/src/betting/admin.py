from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    PlatformSettings, News, GameRound, Bet, 
    NewsAnalysis, RoundStats, NewsSource
)


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'round_duration_seconds', 'platform_fee_rate', 
        'min_bet', 'max_bet', 'enabled', 'updated_at'
    ]
    list_filter = ['enabled', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основные настройки', {
            'fields': ('round_duration_seconds', 'platform_fee_rate', 'enabled')
        }),
        ('Ставки', {
            'fields': ('min_bet', 'max_bet')
        }),
        ('Новости', {
            'fields': ('news_freshness_minutes', 'min_news_content_length')
        }),
        ('OpenAI API', {
            'fields': ('openai_api_key', 'openai_model', 'openai_max_tokens', 'openai_temperature'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = [
        'title_short', 'source_name', 'category', 'status', 'language', 
        'created_at', 'has_analysis'
    ]
    list_filter = ['status', 'category', 'language', 'source', 'created_at']
    search_fields = ['title', 'content', 'source__name']
    readonly_fields = ['dedup_hash', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'category', 'language')
        }),
        ('Источники', {
            'fields': ('source', 'source_url', 'image_url')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
        ('Метаданные', {
            'fields': ('dedup_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def source_name(self, obj):
        if obj.source:
            return obj.source.name
        return 'No Source'
    source_name.short_description = 'Source'
    source_name.admin_order_field = 'source__name'
    
    def has_analysis(self, obj):
        return hasattr(obj, 'analysis')
    has_analysis.boolean = True
    has_analysis.short_description = 'Has Analysis'


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'round_type_icon', 'round_type', 'start_time', 'end_time', 
        'status', 'result', 'pot_total', 'bets_count', 'news_title'
    ]
    list_filter = ['round_type', 'status', 'result', 'start_time']
    readonly_fields = [
        'pot_total', 'pot_positive', 'pot_negative',
        'resolved_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Тип раунда', {
            'fields': ('round_type',)
        }),
        ('Временные рамки', {
            'fields': ('start_time', 'end_time', 'status')
        }),
        ('Результат', {
            'fields': ('news', 'result', 'resolved_at')
        }),
        ('Агрегаты', {
            'fields': (
                'pot_total', 'pot_positive', 'pot_negative',
                'fee_applied_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def round_type_icon(self, obj):
        """Иконка типа раунда"""
        if obj.round_type == 'short':
            return format_html('<span style="font-size: 18px;">⚡</span>')
        else:
            return format_html('<span style="font-size: 18px;">📅</span>')
    round_type_icon.short_description = ''
    
    def bets_count(self, obj):
        return obj.bets.count()
    bets_count.short_description = 'Bets Count'
    
    def news_title(self, obj):
        if obj.news:
            return obj.news.title[:30] + '...'
        return '-'
    news_title.short_description = 'News'


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'round_info', 'amount', 'choice', 
        'status', 'payout_amount', 'created_at'
    ]
    list_filter = ['choice', 'status', 'round__round_type', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'round', 'amount', 'choice')
        }),
        ('Статус и выплата', {
            'fields': ('status', 'payout_amount', 'payout_coefficient')
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def round_info(self, obj):
        """Информация о раунде с иконкой типа"""
        icon = "⚡" if obj.round.round_type == 'short' else "📅"
        return format_html(
            '{} Round #{} ({})', 
            icon, 
            obj.round.id, 
            obj.round.get_round_type_display()
        )
    round_info.short_description = 'Round'
    round_info.admin_order_field = 'round__id'


@admin.register(NewsAnalysis)
class NewsAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'news_title', 'status', 'label', 'score',
        'provider', 'created_at'
    ]
    list_filter = ['status', 'label', 'provider', 'created_at']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('news', 'status')
        }),
        ('Результат анализа', {
            'fields': ('label', 'score')
        }),
        ('Метаданные анализа', {
            'fields': ('provider', 'model_name', 'raw_payload')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    def news_title(self, obj):
        return obj.news.title[:40] + '...' if len(obj.news.title) > 40 else obj.news.title
    news_title.short_description = 'News Title'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'source_type', 'category', 'language', 'status', 'enabled',
        'priority', 'news_count', 'last_parsed_at', 'total_parsed_count'
    ]
    list_filter = ['status', 'enabled', 'source_type', 'category', 'language', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = [
        'last_parsed_at', 'last_error_at', 'total_parsed_count',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'url', 'source_type', 'category', 'language', 'status')
        }),
        ('Настройки парсинга', {
            'fields': (
                'enabled', 'priority', 'update_frequency_minutes',
                'max_items_per_update'
            )
        }),
        ('Фильтры контента', {
            'fields': (
                'min_content_length', 'keywords_filter', 'exclude_keywords'
            ),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': (
                'last_parsed_at', 'last_error_at', 'last_error_message',
                'total_parsed_count'
            ),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_sources', 'deactivate_sources', 'reset_error_status']
    
    def activate_sources(self, request, queryset):
        updated = queryset.update(enabled=True, status='active')
        self.message_user(request, f"Activated {updated} sources")
    activate_sources.short_description = "Activate selected sources"
    
    def deactivate_sources(self, request, queryset):
        updated = queryset.update(enabled=False, status='inactive')
        self.message_user(request, f"Deactivated {updated} sources")
    deactivate_sources.short_description = "Deactivate selected sources"
    
    def reset_error_status(self, request, queryset):
        updated = queryset.filter(status='error').update(
            status='active',
            last_error_message=''
        )
        self.message_user(request, f"Reset error status for {updated} sources")
    reset_error_status.short_description = "Reset error status"
    
    def news_count(self, obj):
        return obj.news_items.count()
    news_count.short_description = 'News Count'
    news_count.admin_order_field = 'news_items__count'


@admin.register(RoundStats)
class RoundStatsAdmin(admin.ModelAdmin):
    list_display = [
        'round_id', 'total_bets_count', 'total_amount',
        'positive_coefficient', 'negative_coefficient',
        'total_payout', 'platform_fee'
    ]
    readonly_fields = [
        'total_bets_count', 'positive_bets_count', 'negative_bets_count',
        'total_amount', 'positive_amount', 'negative_amount',
        'positive_coefficient', 'negative_coefficient',
        'total_payout', 'platform_fee',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Раунд', {
            'fields': ('round',)
        }),
        ('Статистика ставок', {
            'fields': (
                'total_bets_count', 'positive_bets_count', 'negative_bets_count'
            )
        }),
        ('Статистика сумм', {
            'fields': (
                'total_amount', 'positive_amount', 'negative_amount'
            )
        }),
        ('Коэффициенты', {
            'fields': (
                'positive_coefficient', 'negative_coefficient'
            )
        }),
        ('Выплаты', {
            'fields': (
                'total_payout', 'platform_fee'
            )
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def round_id(self, obj):
        return f"Round #{obj.round.id}"
    round_id.short_description = 'Round'
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        for stats in queryset:
            stats.calculate_stats()
        self.message_user(request, f"Recalculated stats for {queryset.count()} rounds")
    recalculate_stats.short_description = "Recalculate selected stats"