from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from labs.bundled_panels import DESCRIPTION, PANELS
from labs.models import LabPanel, LabPanelItem, LabTest, LabTestCategory


class Command(BaseCommand):
    help = "Install bundled entry presets offline, preserving existing records."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Validate and roll back all writes.")

    @transaction.atomic
    def handle(self, *args, **options):
        counts = dict(categories=0, tests=0, panels=0, items=0)
        for code, name, category_code, category_name, tests in PANELS:
            category, created = LabTestCategory.objects.get_or_create(
                code=category_code, defaults={"name": category_name}
            )
            counts["categories"] += int(created)
            resolved = []
            for test_code, test_name in tests:
                test, created = LabTest.objects.get_or_create(
                    code=test_code,
                    defaults={"name": test_name, "category": category, "input_type": "numeric"},
                )
                if not created and test.name != test_name:
                    raise CommandError(
                        f"Code conflict: {test_code} is named {test.name!r}, expected {test_name!r}. "
                        "No changes saved. Review identity manually; do not rename blindly."
                    )
                counts["tests"] += int(created)
                if not test.is_active:
                    self.stdout.write(self.style.WARNING(f"Preserved inactive test: {test_code}"))
                resolved.append(test)
            panel, created = LabPanel.objects.get_or_create(
                code=code, defaults={"name": name, "description": DESCRIPTION, "version": 1}
            )
            if not created:
                self.stdout.write(f"Preserved existing panel and membership: {code}")
                continue
            counts["panels"] += 1
            for position, test in enumerate(resolved, start=1):
                LabPanelItem.objects.create(panel=panel, lab_test=test, position=position)
                counts["items"] += 1
        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("DRY RUN: all writes rolled back.")
        self.stdout.write("Created (would create for dry run): " + ", ".join(
            f"{key}={value}" for key, value in counts.items()
        ))