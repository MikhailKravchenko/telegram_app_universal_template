import json
import os
from django.core.management.base import BaseCommand, CommandError
from src.accounts.models import BotSettings


class Command(BaseCommand):
    help = 'Импорт настроек бота из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON файлу с настройками'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Обновить существующие настройки'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет изменено без сохранения'
        )

    def handle(self, *args, **options):
        """Импортировать настройки бота из JSON файла"""
        
        file_path = options['file_path']
        update_existing = options['update']
        dry_run = options['dry_run']
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise CommandError(f'Файл {file_path} не найден')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Ошибка парсинга JSON: {e}')
        except Exception as e:
            raise CommandError(f'Ошибка чтения файла: {e}')
        
        if not isinstance(settings_data, dict):
            raise CommandError('JSON должен содержать объект')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for key, data in settings_data.items():
            if not isinstance(data, dict):
                self.stdout.write(
                    self.style.WARNING(f'Пропускаем {key}: неверный формат данных')
                )
                skipped_count += 1
                continue
            
            value = data.get('value', '')
            description = data.get('description', '')
            is_active = data.get('is_active', True)
            
            try:
                setting, created = BotSettings.objects.get_or_create(
                    key=key,
                    defaults={
                        'value': value,
                        'description': description,
                        'is_active': is_active
                    }
                )
                
                if created:
                    created_count += 1
                    if not dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(f'Создана настройка: {key} = {value}')
                        )
                    else:
                        self.stdout.write(f'Будет создана настройка: {key} = {value}')
                else:
                    if update_existing:
                        if not dry_run:
                            setting.value = value
                            setting.description = description
                            setting.is_active = is_active
                            setting.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Обновлена настройка: {key} = {value}')
                            )
                        else:
                            self.stdout.write(f'Будет обновлена настройка: {key} = {value}')
                    else:
                        skipped_count += 1
                        if not dry_run:
                            self.stdout.write(
                                self.style.WARNING(f'Пропущена существующая настройка: {key}')
                            )
                        else:
                            self.stdout.write(f'Пропущена существующая настройка: {key}')
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при обработке {key}: {e}')
                )
                skipped_count += 1
        
        # Итоговая статистика
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Будет создано: {created_count}, обновлено: {updated_count}, пропущено: {skipped_count}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Импорт завершен. Создано: {created_count}, обновлено: {updated_count}, пропущено: {skipped_count}'
                )
            )
