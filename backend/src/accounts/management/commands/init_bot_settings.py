from django.core.management.base import BaseCommand
from src.accounts.models import BotSettings


class Command(BaseCommand):
    help = 'Инициализация настроек бота'

    def handle(self, *args, **options):
        """Инициализировать настройки бота"""
        
        # Список настроек по умолчанию
        default_settings = [
            {
                'key': 'telegram_bot_username',
                'value': 'pulse_bot',
                'description': 'Имя пользователя Telegram бота (без @)'
            },
            {
                'key': 'telegram_bot_name',
                'value': 'Pulse Bot',
                'description': 'Отображаемое имя Telegram бота'
            },
            {
                'key': 'telegram_bot_description',
                'value': 'Официальный бот проекта Pulse',
                'description': 'Описание Telegram бота'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for setting_data in default_settings:
            setting, created = BotSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults={
                    'value': setting_data['value'],
                    'description': setting_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создана настройка: {setting.key} = {setting.value}'
                    )
                )
            else:
                # Обновляем описание, если оно изменилось
                if setting.description != setting_data['description']:
                    setting.description = setting_data['description']
                    setting.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Обновлено описание настройки: {setting.key}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Инициализация завершена. Создано: {created_count}, обновлено: {updated_count}'
            )
        )
