from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Placeholder scheduler command for the template project."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                "Scheduler is not configured in the template. "
                "Add your periodic tasks here for a specific project."
            )
        )
