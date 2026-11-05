from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from labs.bundled_panels import PANELS
from labs.bundled_units import UNIT_SUGGESTIONS
from labs.models import LabTest, LabTestUnit


class Command(BaseCommand):
    help = "Install optional offline unit spellings for exact bundled test identities."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Validate and roll back all writes.")

    @transaction.atomic
    def handle(self, *args, **options):
        expected = {code: name for panel in PANELS for code, name in panel[4]}
        if set(expected) != set(UNIT_SUGGESTIONS):
            raise CommandError("Bundled panel/unit versions differ. No changes saved.")
        counts = dict(created=0, preserved=0, missing_tests=0, inactive_tests=0)
        for code, symbols in UNIT_SUGGESTIONS.items():
            test = LabTest.objects.filter(code=code).first()
            if test is None:
                counts["missing_tests"] += 1
                self.stdout.write(f"Skipped missing test: {code}")
                continue
            if test.name != expected[code]:
                raise CommandError(
                    f"Code conflict: {code} does not have the bundled name. "
                    "All changes rolled back. Review identity manually; do not rename blindly."
                )
            if not test.is_active:
                counts["inactive_tests"] += 1
                self.stdout.write(f"Skipped inactive test: {code}")
                continue
            for symbol in symbols:
                _, created = LabTestUnit.objects.get_or_create(lab_test=test, symbol=symbol)
                counts["created" if created else "preserved"] += 1
        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("DRY RUN: all writes rolled back.")
        self.stdout.write("Units (would create for dry run): " + ", ".join(
            f"{key}={value}" for key, value in counts.items()
        ))
        self.stdout.write("No units selected, converted or added to recorded results.")