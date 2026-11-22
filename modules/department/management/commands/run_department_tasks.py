from django.core.management.base import BaseCommand

from modules.department.services import notifications, roles


class Command(BaseCommand):
    help = "Run department scheduled tasks (role transitions and notification drain) once."

    def handle(self, *args, **options):
        transitions = roles.apply_effective_transitions()
        sent = notifications.deliver_pending()
        self.stdout.write(
            self.style.SUCCESS(
                f"Department tasks complete: {transitions} role transition(s), "
                f"{sent} notification(s) delivered."
            )
        )
