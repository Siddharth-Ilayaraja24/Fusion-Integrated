from django.core.management.base import BaseCommand

from modules.department.models import Department

DEFAULT_DEPARTMENTS = (
    ("CSE", "Computer Science and Engineering"),
    ("ECE", "Electronics and Communication Engineering"),
    ("ME", "Mechanical Engineering"),
    ("DESIGN", "Design"),
    ("NS", "Natural Sciences"),
    ("LA", "Liberal Arts"),
    ("SM", "Smart Manufacturing"),
)


class Command(BaseCommand):
    help = "Seed default institute departments idempotently."

    def handle(self, *args, **options):
        created = 0
        for code, name in DEFAULT_DEPARTMENTS:
            _, was_created = Department.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded departments ({created} created, {Department.objects.count()} total)."
            )
        )
