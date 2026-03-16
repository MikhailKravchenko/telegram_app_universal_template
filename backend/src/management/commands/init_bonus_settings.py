#!/usr/bin/env python3
"""
Команда инициализации настроек бонусной системы

Использование:
    python manage.py init_bonus_settings                # Создать настройки по умолчанию
    python manage.py init_bonus_settings --force        # Пересоздать настройки принудительно
    python manage.py init_bonus_settings --reset        # Сбросить к значениям по умолчанию
    
Команда создает запись настроек бонусной системы с параметрами по умолчанию,
если настроек еще не существует. Если настройки уже есть, команда предложит
их обновить или сбросить.
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from src.accounts.models import BonusSettings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Инициализация настроек бонусной системы с параметрами по умолчанию.
    
    Создает запись настроек бонусов если её не существует или обновляет существующую.
    """
    
    def add_arguments(self, parser):
        """Добавляем аргументы командной строки"""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительно пересоздать настройки (удаляет существующие)'
        )
        
        parser.add_argument(
            '--reset',
            action='store_true', 
            help='Сбросить существующие настройки к значениям по умолчанию'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без выполнения изменений'
        )
        
        # Параметры настройки (возможность кастомизации)
        parser.add_argument(
            '--daily-login',
            type=int,
            default=300,
            help='Размер бонуса за ежедневный вход (по умолчанию: 300)'
        )
        
        parser.add_argument(
            '--social-subscription',
            type=int,
            default=1000,
            help='Размер бонуса за подписку на соцсеть (по умолчанию: 1000)'
        )
        
        parser.add_argument(
            '--telegram-channel-1',
            type=int,
            default=1000,
            help='Размер бонуса за подписку на Telegram канал 1 (по умолчанию: 1000)'
        )
        
        parser.add_argument(
            '--telegram-channel-2',
            type=int,
            default=1000,
            help='Размер бонуса за подписку на Telegram канал 2 (по умолчанию: 1000)'
        )
        
        parser.add_argument(
            '--first-bet',
            type=int,
            default=10,
            help='Размер бонуса за первую ставку (по умолчанию: 10)'
        )
        
        parser.add_argument(
            '--activity-coins-per-bet',
            type=int,
            default=10,
            help='Количество монет за одну ставку при расчете активности (по умолчанию: 10)'
        )
        
        parser.add_argument(
            '--activity-max-bets',
            type=int,
            default=12,
            help='Максимальное число учитываемых ставок в час (по умолчанию: 12)'
        )
        
        parser.add_argument(
            '--activity-daily-limit',
            type=int,
            default=2880,
            help='Суточный предел бонусных монет за активность (по умолчанию: 2880)'
        )
    
    def handle(self, *args, **options):
        """Основной обработчик команды"""
        try:
            self.stdout.write(
                self.style.SUCCESS(
                    "🎁 Инициализация настроек бонусной системы"
                )
            )
            
            # Проверяем текущее состояние
            existing_settings = BonusSettings.objects.first()
            
            if options['dry_run']:
                self._handle_dry_run(existing_settings, options)
                return
            
            if options['force']:
                self._handle_force_recreate(options)
            elif options['reset']:
                self._handle_reset_settings(existing_settings, options)
            else:
                self._handle_default_creation(existing_settings, options)
            
            # Показываем итоговые настройки
            self._display_current_settings()
            
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Настройки бонусной системы успешно инициализированы!"
                )
            )
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации настроек бонусов: {str(e)}")
            raise CommandError(f"Не удалось инициализировать настройки: {str(e)}")
    
    def _handle_dry_run(self, existing_settings, options):
        """Обработка режима dry-run (только показать что будет сделано)"""
        self.stdout.write(
            self.style.WARNING("🔍 Режим dry-run: показываем что будет сделано")
        )
        
        if existing_settings:
            self.stdout.write("📋 Существующие настройки:")
            self._display_settings(existing_settings)
            
            if options['force']:
                self.stdout.write(
                    self.style.WARNING("🔄 С флагом --force настройки будут пересозданы")
                )
            elif options['reset']:
                self.stdout.write(
                    self.style.WARNING("🔄 С флагом --reset настройки будут сброшены")
                )
            else:
                self.stdout.write("ℹ️  Настройки уже существуют, изменений не будет")
        else:
            self.stdout.write("📝 Настройки будут созданы с параметрами:")
            
        self.stdout.write("\n💡 Параметры по умолчанию:")
        self._display_default_params(options)
    
    def _handle_force_recreate(self, options):
        """Принудительное пересоздание настроек"""
        self.stdout.write(
            self.style.WARNING("🔄 Принудительное пересоздание настроек...")
        )
        
        with transaction.atomic():
            # Удаляем все существующие настройки
            deleted_count = BonusSettings.objects.all().delete()[0]
            if deleted_count > 0:
                self.stdout.write(f"🗑️  Удалено {deleted_count} старых записей настроек")
            
            # Создаем новые настройки
            settings = self._create_settings(options)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✨ Созданы новые настройки (ID: {settings.id})"
                )
            )
    
    def _handle_reset_settings(self, existing_settings, options):
        """Сброс существующих настроек к значениям по умолчанию"""
        if not existing_settings:
            self.stdout.write(
                self.style.WARNING("ℹ️  Настройки не существуют, создаем новые...")
            )
            self._create_settings(options)
            return
        
        self.stdout.write(
            self.style.WARNING("🔄 Сброс настроек к значениям по умолчанию...")
        )
        
        with transaction.atomic():
            # Обновляем существующие настройки
            existing_settings.daily_login_bonus = options['daily_login']
            existing_settings.social_subscription_bonus = options['social_subscription']
            existing_settings.telegram_channel_1_bonus = options['telegram_channel_1']
            existing_settings.telegram_channel_2_bonus = options['telegram_channel_2']
            existing_settings.first_bet_bonus = options['first_bet']
            existing_settings.activity_coins_per_bet = options['activity_coins_per_bet']
            existing_settings.activity_max_bets_per_hour = options['activity_max_bets']
            existing_settings.activity_daily_limit = options['activity_daily_limit']
            existing_settings.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"🔄 Настройки сброшены к значениям по умолчанию (ID: {existing_settings.id})"
                )
            )
    
    def _handle_default_creation(self, existing_settings, options):
        """Создание настроек по умолчанию если их нет"""
        if existing_settings:
            self.stdout.write(
                self.style.WARNING(
                    f"ℹ️  Настройки уже существуют (ID: {existing_settings.id})"
                )
            )
            self.stdout.write(
                "💡 Для обновления используйте флаги --force или --reset"
            )
            return
        
        self.stdout.write("📝 Создание настроек по умолчанию...")
        settings = self._create_settings(options)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✨ Созданы настройки по умолчанию (ID: {settings.id})"
            )
        )
    
    def _create_settings(self, options):
        """Создать объект настроек с указанными параметрами"""
        settings = BonusSettings.objects.create(
            daily_login_bonus=options['daily_login'],
            social_subscription_bonus=options['social_subscription'],
            telegram_channel_1_bonus=options['telegram_channel_1'],
            telegram_channel_2_bonus=options['telegram_channel_2'],
            first_bet_bonus=options['first_bet'],
            activity_coins_per_bet=options['activity_coins_per_bet'],
            activity_max_bets_per_hour=options['activity_max_bets'],
            activity_daily_limit=options['activity_daily_limit']
        )
        
        logger.info(f"Созданы настройки бонусной системы с ID: {settings.id}")
        return settings
    
    def _display_current_settings(self):
        """Показать текущие настройки"""
        settings = BonusSettings.objects.first()
        if settings:
            self.stdout.write("\n📋 Текущие настройки бонусной системы:")
            self._display_settings(settings)
    
    def _display_settings(self, settings):
        """Показать настройки в удобном формате"""
        self.stdout.write(f"  🎯 ID: {settings.id}")
        self.stdout.write(f"  📅 Обновлено: {settings.updated_at.strftime('%d.%m.%Y %H:%M:%S')}")
        self.stdout.write("\n  🎁 Бонусы за события:")
        self.stdout.write(f"    • Ежедневный вход: {settings.daily_login_bonus} монет")
        self.stdout.write(f"    • Подписка на соцсеть: {settings.social_subscription_bonus} монет")
        self.stdout.write(f"    • Telegram канал 1: {settings.telegram_channel_1_bonus} монет")
        self.stdout.write(f"    • Telegram канал 2: {settings.telegram_channel_2_bonus} монет")
        self.stdout.write(f"    • Первая ставка: {settings.first_bet_bonus} монет")
        self.stdout.write("\n  ⚡ Параметры активности:")
        self.stdout.write(f"    • Монет за ставку: {settings.activity_coins_per_bet}")
        self.stdout.write(f"    • Лимит ставок в час: {settings.activity_max_bets_per_hour}")
        self.stdout.write(f"    • Суточный лимит: {settings.activity_daily_limit} монет")
        
        # Расчетные значения
        max_hourly = settings.activity_coins_per_bet * settings.activity_max_bets_per_hour
        max_daily_calc = max_hourly * 24
        efficiency = round((settings.activity_daily_limit / max_daily_calc) * 100, 1) if max_daily_calc > 0 else 0
        
        self.stdout.write("\n  📊 Расчетные значения:")
        self.stdout.write(f"    • Максимум за час: {max_hourly} монет")
        self.stdout.write(f"    • Теоретический максимум за сутки: {max_daily_calc} монет")
        self.stdout.write(f"    • Эффективность лимита: {efficiency}%")
    
    def _display_default_params(self, options):
        """Показать параметры по умолчанию"""
        self.stdout.write(f"  • daily-login: {options['daily_login']}")
        self.stdout.write(f"  • social-subscription: {options['social_subscription']}")
        self.stdout.write(f"  • telegram-channel-1: {options['telegram_channel_1']}")
        self.stdout.write(f"  • telegram-channel-2: {options['telegram_channel_2']}")
        self.stdout.write(f"  • first-bet: {options['first_bet']}")
        self.stdout.write(f"  • activity-coins-per-bet: {options['activity_coins_per_bet']}")
        self.stdout.write(f"  • activity-max-bets: {options['activity_max_bets']}")
        self.stdout.write(f"  • activity-daily-limit: {options['activity_daily_limit']}")
