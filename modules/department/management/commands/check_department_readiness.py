from django.core.management.base import BaseCommand, CommandError

from modules.department.registry import readiness


class Command(BaseCommand):
    help = "Verify prerequisites for the department module."

    def handle(self, *args, **options):
        unmet = readiness()
        if unmet:
            for item in unmet:
                self.stderr.write(self.style.ERROR(f"  - {item}"))
            raise CommandError(f"Department module has {len(unmet)} unmet prerequisite(s).")
        self.stdout.write(self.style.SUCCESS("Department module is ready."))
