#!/usr/bin/env python3
"""
Команда для инициализации дефолтных уровней реферальной программы
"""

import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.accounts.services import ReferralService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Команда для создания дефолтных уровней реферальной программы
    """
    help = 'Создать дефолтные уровни реферальной программы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие уровни перед созданием новых',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Не запрашивать подтверждение при очистке',
        )

    def handle(self, *args, **options):
        """Основная логика команды"""
        self.stdout.write("🔥 Инициализация уровней реферальной программы")
        
        try:
            from src.accounts.models import ReferralLevel
            
            # Проверяем существующие уровни
            existing_levels = ReferralLevel.objects.count()
            
            if options['clear']:
                if existing_levels > 0:
                    if not options['force']:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  Найдено {existing_levels} существующих уровней. "
                                "Все они будут удалены!"
                            )
                        )
                        confirm = input("Вы уверены? (yes/no): ")
                        if confirm.lower() not in ['yes', 'y']:
                            self.stdout.write(self.style.ERROR("❌ Операция отменена"))
                            return
                    
                    with transaction.atomic():
                        deleted_count = ReferralLevel.objects.count()
                        ReferralLevel.objects.all().delete()
                        self.stdout.write(
                            self.style.SUCCESS(f"🗑️  Удалено {deleted_count} существующих уровней")
                        )
                        logger.info(f"Удалено {deleted_count} существующих уровней реферальной программы")
            
            # Создаем дефолтные уровни
            with transaction.atomic():
                result = ReferralService.create_default_levels()
                
                if 'error' in result:
                    raise CommandError(f"Ошибка создания уровней: {result['error']}")
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {result['message']}"
                    )
                )
                
                # Показываем созданные уровни
                levels = ReferralLevel.objects.filter(is_active=True).order_by('level')
                
                self.stdout.write("\n📋 Созданные уровни:")
                self.stdout.write("-" * 60)
                for level in levels:
                    self.stdout.write(
                        f"Уровень {level.level}: {level.min_referrals}+ рефералов = {level.bonus_percentage}% бонуса"
                    )
                
                logger.info(f"Успешно инициализированы уровни реферальной программы: {result['message']}")
                
        except Exception as e:
            error_msg = f"Ошибка при инициализации уровней: {str(e)}"
            logger.error(error_msg)
            raise CommandError(error_msg)
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 Инициализация уровней реферальной программы завершена!"
            )
        )
