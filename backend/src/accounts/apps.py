from django.apps import AppConfig


class LocationConfig(AppConfig):
    name = "src.accounts"

    def ready(self):
        import src.accounts.signals
