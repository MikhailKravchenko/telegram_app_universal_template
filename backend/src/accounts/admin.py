from django.contrib import admin

from src.accounts.models import (
    CustomUser,
    UserBalance,
    Transaction,
    Referral,
    Bonus,
    UserActivityHour,
    BonusSettings,
    ReferralLevel,
    ReferralBonus,
    BotSettings,
)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "username",
        "referral_count",
        "get_balance",
    ]
    search_fields = [
        "id",
        "username",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
        "last_login",
    ]
    list_per_page = 25

    def referral_count(self, obj: CustomUser) -> int:
        return obj.referral_count()

    def get_balance(self, obj: CustomUser) -> int:
        try:
            return obj.balance.coins_balance
        except UserBalance.DoesNotExist:
            return 0

    referral_count.short_description = "Referral Count"
    get_balance.short_description = "Balance"


class UserBalanceAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "coins_balance",
        "total_earned",
        "total_spent",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "user__username",
        "user__email",
    ]
    list_filter = [
        "created_at",
        "updated_at",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    list_per_page = 25


class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "type",
        "description",
        "reference_id",
        "created_at",
    ]
    search_fields = [
        "user__username",
        "type",
        "description",
        "reference_id",
    ]
    list_filter = [
        "type",
        "created_at",
    ]
    readonly_fields = [
        "created_at",
    ]
    list_per_page = 25


class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "referrer",
        "referred",
        "approved",
        "total_bonus_earned",
        "last_bonus_at",
        "created_at",
    ]
    search_fields = [
        "referrer__username",
        "referred__username",
        "referrer__telegram_id",
        "referred__telegram_id",
    ]
    list_filter = [
        "approved",
        "created_at",
        "last_bonus_at",
    ]
    readonly_fields = [
        "total_bonus_earned",
        "last_bonus_at",
        "created_at",
    ]
    list_per_page = 25
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('referrer', 'referred')


class BonusAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "bonus_type",
        "amount",
        "status",
        "can_be_used",
        "is_expired",
        "created_at",
        "used_at",
        "expires_at",
    ]
    search_fields = [
        "user__username",
        "user__email",
        "bonus_type",
        "description",
        "reference_id",
    ]
    list_filter = [
        "bonus_type",
        "status",
        "created_at",
        "expires_at",
    ]
    readonly_fields = [
        "created_at",
        "used_at",
        "can_be_used",
        "is_expired",
    ]
    list_per_page = 25
    actions = ['activate_bonuses', 'use_bonuses', 'expire_bonuses']

    def can_be_used(self, obj: Bonus) -> bool:
        """Можно ли использовать бонус"""
        return obj.can_be_used()
    
    def is_expired(self, obj: Bonus) -> bool:
        """Истек ли бонус"""
        return obj.is_expired()

    def activate_bonuses(self, request, queryset):
        """Активировать выбранные бонусы"""
        from .services import BonusService
        
        activated_count = 0
        for bonus in queryset.filter(status='pending'):
            success, message = BonusService.activate_bonus(bonus)
            if success:
                activated_count += 1
        
        self.message_user(request, f"Активировано {activated_count} бонусов")
    
    def use_bonuses(self, request, queryset):
        """Использовать выбранные бонусы"""
        from .services import BonusService
        
        used_count = 0
        for bonus in queryset.filter(status='active'):
            if bonus.can_be_used():
                success, message = BonusService.use_bonus(bonus)
                if success:
                    used_count += 1
        
        self.message_user(request, f"Использовано {used_count} бонусов")
    
    def expire_bonuses(self, request, queryset):
        """Пометить выбранные бонусы как истекшие"""
        expired_count = queryset.filter(status__in=['pending', 'active']).update(status='expired')
        self.message_user(request, f"Помечено как истекшие {expired_count} бонусов")

    can_be_used.boolean = True
    can_be_used.short_description = "Can be used"
    
    is_expired.boolean = True
    is_expired.short_description = "Is expired"
    
    activate_bonuses.short_description = "Активировать выбранные бонусы"
    use_bonuses.short_description = "Использовать выбранные бонусы"
    expire_bonuses.short_description = "Пометить как истекшие"


class UserActivityHourAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "hour_start",
        "bets_count",
        "created_at",
    ]
    search_fields = [
        "user__username",
        "user__email",
    ]
    list_filter = [
        "hour_start",
        "created_at",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    list_per_page = 25
    date_hierarchy = 'hour_start'
    actions = ['award_bonuses_for_eligible', 'mark_as_bonus_awarded']

    def award_bonuses_for_eligible(self, request, queryset):
        """Начислить бонусы для подходящих записей активности"""
        from .services import BonusService, ActivityService
        
        awarded_count = 0
        for activity in queryset.filter(eligible_for_bonus=True, bonus_awarded=False):
            try:
                # Создаем бонус
                success, message, bonus = BonusService.create_bonus(
                    user=activity.user,
                    bonus_type='activity_bonus',
                    amount=120,
                    description=f"Админ-начисление: {activity.bets_count} ставок в час {activity.hour_start.strftime('%H:00')}",
                    reference_id=str(activity.id)
                )
                
                if success and bonus:
                    # Активируем и используем бонус
                    BonusService.activate_bonus(bonus)
                    BonusService.use_bonus(bonus)
                    
                    # Отмечаем что бонус начислен
                    activity.award_bonus()
                    awarded_count += 1
                    
            except Exception as e:
                self.message_user(request, f"Ошибка для {activity.user.username}: {str(e)}", level='ERROR')
        
        self.message_user(request, f"Начислено {awarded_count} бонусов за активность")
    
    def mark_as_bonus_awarded(self, request, queryset):
        """Отметить как награжденные (без начисления бонуса)"""
        updated_count = queryset.update(bonus_awarded=True)
        self.message_user(request, f"Отмечено как награжденные {updated_count} записей")

    award_bonuses_for_eligible.short_description = "Начислить бонусы подходящим записям"
    mark_as_bonus_awarded.short_description = "Отметить как награжденные"


class BonusSettingsAdmin(admin.ModelAdmin):
    """
    Админ-панель для настройки параметров бонусной системы
    """
    list_display = [
        "id",
        "daily_login_bonus",
        "social_subscription_bonus", 
        "first_bet_bonus",
        "round_participation_bonus",
        "max_participations_per_round",
        "hourly_limit_round_participation",
        "activity_coins_per_bet",
        "activity_max_bets_per_hour",
        "activity_daily_limit",
        "updated_at",
    ]
    
    fieldsets = (
        ("Бонусы за события", {
            "fields": (
                "daily_login_bonus",
                "social_subscription_bonus",
                "first_bet_bonus",
                "round_participation_bonus",
            ),
            "description": "Настройка размеров бонусов за различные действия пользователей"
        }),
        ("Настройки участия в раундах", {
            "fields": (
                "max_participations_per_round",
                "hourly_limit_round_participation",
            ),
            "description": "Ограничения на участие в раундах и получение бонусов"
        }),
        ("Настройки активности", {
            "fields": (
                "activity_coins_per_bet",
                "activity_max_bets_per_hour", 
                "activity_daily_limit",
            ),
            "description": "Параметры системы бонусов за активные ставки"
        }),
        ("Информация", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    
    def has_add_permission(self, request):
        """Разрешить создание только если настроек еще нет (Singleton)"""
        return not BonusSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Запретить удаление настроек"""
        return False
    
    def get_actions(self, request):
        """Убираем стандартное действие удаления"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def changelist_view(self, request, extra_context=None):
        """Переопределяем представление списка для отображения подсказок"""
        extra_context = extra_context or {}
        
        # Получаем текущие настройки
        settings = BonusSettings.get_settings()
        
        # Рассчитываем справочную информацию
        max_hourly_bonus = settings.activity_coins_per_bet * settings.activity_max_bets_per_hour
        max_daily_from_hours = max_hourly_bonus * 24
        
        extra_context.update({
            'title': 'Настройки бонусной системы',
            'bonus_info': {
                'max_hourly_bonus': max_hourly_bonus,
                'max_daily_from_hours': max_daily_from_hours,
                'efficiency_percent': round((settings.activity_daily_limit / max_daily_from_hours) * 100, 1) if max_daily_from_hours > 0 else 0,
            }
        })
        
        return super().changelist_view(request, extra_context)
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для логирования изменений"""
        if change:
            # Логируем изменение настроек
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(obj).pk,
                object_id=obj.pk,
                object_repr=str(obj),
                action_flag=CHANGE,
                change_message=f"Обновлены настройки бонусной системы пользователем {request.user.username}"
            )
        
        super().save_model(request, obj, form, change)
        
        # Отправляем сообщение об успешном сохранении
        if change:
            self.message_user(
                request, 
                "Настройки бонусной системы успешно обновлены. Изменения вступят в силу немедленно."
            )
        else:
            self.message_user(
                request,
                "Настройки бонусной системы созданы с параметрами по умолчанию."
            )


class ReferralLevelAdmin(admin.ModelAdmin):
    list_display = [
        "level",
        "min_referrals",
        "bonus_percentage",
        "is_active",
        "users_at_level",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "level",
        "min_referrals",
    ]
    list_filter = [
        "is_active",
        "created_at",
    ]
    list_editable = [
        "min_referrals",
        "bonus_percentage",
        "is_active",
    ]
    ordering = ["level"]
    list_per_page = 25
    
    def users_at_level(self, obj):
        """Показать количество пользователей на этом уровне"""
        from django.db.models import Count, Q
        from .models import CustomUser
        
        users_count = CustomUser.objects.annotate(
            referrals_count=Count('given_referrals', filter=Q(given_referrals__approved=True))
        ).filter(referrals_count__gte=obj.min_referrals).count()
        
        # Исключаем пользователей с более высоких уровней
        from .models import ReferralLevel
        next_level = ReferralLevel.objects.filter(
            min_referrals__gt=obj.min_referrals,
            is_active=True
        ).order_by('min_referrals').first()
        
        if next_level:
            users_above = CustomUser.objects.annotate(
                referrals_count=Count('given_referrals', filter=Q(given_referrals__approved=True))
            ).filter(referrals_count__gte=next_level.min_referrals).count()
            users_count -= users_above
            
        return users_count
    
    users_at_level.short_description = "Пользователей на уровне"
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для логирования изменений"""
        if change:
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(obj).pk,
                object_id=obj.pk,
                object_repr=str(obj),
                action_flag=CHANGE,
                change_message=f"Обновлен уровень реферальной программы пользователем {request.user.username}"
            )
        
        super().save_model(request, obj, form, change)


class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "referrer",
        "referred",
        "bonus_amount",
        "bonus_percentage",
        "investment_amount",
        "referral_level",
        "presale_round",
        "created_at",
    ]
    search_fields = [
        "referrer__username",
        "referred__username",
        "referrer__telegram_id",
        "referred__telegram_id",
        "transaction_id",
    ]
    list_filter = [
        "referral_level",
        "presale_round",
        "created_at",
        "bonus_percentage",
    ]
    readonly_fields = [
        "referrer",
        "referred",
        "investment_amount",
        "bonus_amount",
        "bonus_percentage",
        "referral_level",
        "presale_round",
        "transaction_id",
        "created_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 25
    
    def has_add_permission(self, request):
        """Запрещаем добавление бонусов вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение бонусов"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление только суперпользователям"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('referrer', 'referred')


class BotSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "key",
        "value",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    ]
    search_fields = [
        "key",
        "value",
        "description",
    ]
    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    list_per_page = 25
    
    actions = ['export_settings', 'import_settings']
    
    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление настроек"""
        return False
    
    def export_settings(self, request, queryset):
        """Экспорт настроек в JSON"""
        import json
        from django.http import HttpResponse
        
        settings_data = {}
        for setting in queryset:
            settings_data[setting.key] = {
                'value': setting.value,
                'description': setting.description,
                'is_active': setting.is_active
            }
        
        response = HttpResponse(
            json.dumps(settings_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="bot_settings.json"'
        return response
    
    export_settings.short_description = "Экспортировать выбранные настройки"
    
    def import_settings(self, request, queryset):
        """Импорт настроек из JSON (заглушка)"""
        from django.contrib import messages
        messages.info(request, "Импорт настроек доступен через API или команды управления")
    
    import_settings.short_description = "Импорт настроек (через API)"


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserBalance, UserBalanceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(Bonus, BonusAdmin)
admin.site.register(UserActivityHour, UserActivityHourAdmin)
admin.site.register(BonusSettings, BonusSettingsAdmin)
admin.site.register(ReferralLevel, ReferralLevelAdmin)
admin.site.register(ReferralBonus, ReferralBonusAdmin)
admin.site.register(BotSettings, BotSettingsAdmin)

