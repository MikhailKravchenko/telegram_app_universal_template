from django.apps import AppConfig


class PresaleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.presale'
    verbose_name = 'Пресейл'
    
    def ready(self):
        # Импорт сигналов если понадобятся
        try:
            from . import signals  # noqa F401
        except ImportError:
            pass