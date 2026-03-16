from django.core.management.base import BaseCommand
from src.betting.models import PlatformSettings


class Command(BaseCommand):
    help = 'Инициализация настроек OpenAI API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='OpenAI API ключ'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-3.5-turbo',
            help='Модель OpenAI (по умолчанию: gpt-3.5-turbo)'
        )
        parser.add_argument(
            '--max-tokens',
            type=int,
            default=150,
            help='Максимальное количество токенов (по умолчанию: 150)'
        )
        parser.add_argument(
            '--temperature',
            type=float,
            default=0.1,
            help='Температура генерации (по умолчанию: 0.1)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Инициализация настроек OpenAI ==='))
        
        # Получаем или создаем настройки платформы
        settings = PlatformSettings.get_current()
        
        # Обновляем настройки OpenAI
        if options['api_key']:
            settings.openai_api_key = options['api_key']
            self.stdout.write('✅ API ключ установлен')
        
        settings.openai_model = options['model']
        settings.openai_max_tokens = options['max_tokens']
        settings.openai_temperature = options['temperature']
        settings.save()
        
        self.stdout.write(f'✅ Модель: {settings.openai_model}')
        self.stdout.write(f'✅ Максимум токенов: {settings.openai_max_tokens}')
        self.stdout.write(f'✅ Температура: {settings.openai_temperature}')
        
        if not settings.openai_api_key:
            self.stdout.write(self.style.WARNING('⚠️  API ключ не установлен. Установите его через админ панель или используйте --api-key'))
        
        self.stdout.write(self.style.SUCCESS('Настройки OpenAI успешно обновлены!'))
