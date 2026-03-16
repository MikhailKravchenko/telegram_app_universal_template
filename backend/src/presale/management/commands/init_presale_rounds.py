from django.core.management.base import BaseCommand
from django.db import transaction

from src.presale.services import PresaleRoundService
from src.presale.models import PresaleRound


class Command(BaseCommand):
    """
    Команда для инициализации дефолтных раундов пресейла
    
    Использование:
    python manage.py init_presale_rounds
    python manage.py init_presale_rounds --clear  # удалить все существующие раунды
    """
    
    help = 'Инициализация 25 дефолтных раундов пресейла с правильными курсами и лимитами'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие раунды перед созданием новых',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительное создание без подтверждения',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Инициализация раундов пресейла')
        )
        
        # Проверяем существующие раунды
        existing_count = PresaleRound.objects.count()
        if existing_count > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Найдено существующих раундов: {existing_count}')
            )
            
            if options['clear']:
                if not options['force']:
                    confirm = input('Удалить все существующие раунды? [y/N]: ')
                    if confirm.lower() != 'y':
                        self.stdout.write(
                            self.style.ERROR('❌ Операция отменена')
                        )
                        return
                
                with transaction.atomic():
                    PresaleRound.objects.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS(f'🗑️  Удалено раундов: {existing_count}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '💡 Используйте --clear для удаления существующих раундов'
                    )
                )
        
        # Создаем новые раунды
        self.stdout.write('📦 Создание 25 дефолтных раундов...')
        
        try:
            with transaction.atomic():
                created_rounds = PresaleRoundService.create_default_rounds()
                
                if created_rounds:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Создано новых раундов: {len(created_rounds)}')
                    )
                    
                    # Показываем информацию о созданных раундах
                    self.stdout.write('\n📊 Информация о раундах:')
                    for round_obj in created_rounds[:5]:  # Показываем первые 5
                        self.stdout.write(
                            f'   Раунд {round_obj.round_number}: '
                            f'{round_obj.tokens_per_coin} токенов/монету, '
                            f'цель {round_obj.target_investment:,} монет, '
                            f'лимит {round_obj.max_user_investment:,} монет'
                        )
                    
                    if len(created_rounds) > 5:
                        self.stdout.write(f'   ... и ещё {len(created_rounds) - 5} раундов')
                    
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Новые раунды не созданы (возможно, уже существуют)')
                    )
                
                # Показываем общую статистику
                total_rounds = PresaleRound.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎯 Всего раундов в системе: {total_rounds}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при создании раундов: {e}')
            )
            raise
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Инициализация завершена! '
                'Теперь можно настроить параметры раундов через админ-панель.'
            )
        )
