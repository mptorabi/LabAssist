"""Install independent bundled test definitions without overwriting records."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from labs.bundled_catalog import BUNDLED_TESTS
from labs.models import LabTest, LabTestCategory


class Command(BaseCommand):
    help = (
        "Install the independent bundled test catalog offline, "
        "preserving existing records. Does not install panels or units."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and roll back all writes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        counts = {
            "categories": 0,
            "tests": 0,
            "preserved_tests": 0,
            "inactive_tests": 0,
        }

        # Validate model compatibility before writing anything.
        allowed_input_types = {
            value
            for value, _ in LabTest._meta.get_field(
                "input_type"
            ).flatchoices
        }
        seen_codes = set()

        for definition in BUNDLED_TESTS:
            if definition.code in seen_codes:
                raise CommandError(
                    f"Duplicate catalog code: {definition.code!r}. "
                    "No changes saved."
                )

            seen_codes.add(definition.code)

            if definition.input_type not in allowed_input_types:
                raise CommandError(
                    f"Unsupported input type for {definition.code!r}: "
                    f"{definition.input_type!r}. No changes saved."
                )

        for definition in BUNDLED_TESTS:
            existing = LabTest.objects.filter(
                code=definition.code
            ).first()

            if existing is not None:
                if existing.name != definition.name:
                    raise CommandError(
                        f"Code conflict: {definition.code} is named "
                        f"{existing.name!r}, expected {definition.name!r}. "
                        "All changes rolled back. Review identity manually; "
                        "do not rename blindly."
                    )

                counts["preserved_tests"] += 1

                if not existing.is_active:
                    counts["inactive_tests"] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Preserved inactive test: {definition.code}"
                        )
                    )

                # Do not change category, input type, activity, or metadata.
                continue

            category, category_created = (
                LabTestCategory.objects.get_or_create(
                    code=definition.category_code,
                    defaults={"name": definition.category_name},
                )
            )
            counts["categories"] += int(category_created)

            # get_or_create also handles a concurrent insertion by code.
            test, created = LabTest.objects.get_or_create(
                code=definition.code,
                defaults={
                    "name": definition.name,
                    "category": category,
                    "input_type": definition.input_type,
                },
            )

            if test.name != definition.name:
                raise CommandError(
                    f"Code conflict: {definition.code} does not have "
                    "the bundled name. All changes rolled back. "
                    "Review identity manually; do not rename blindly."
                )

            counts["tests" if created else "preserved_tests"] += 1

            if not test.is_active:
                counts["inactive_tests"] += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Preserved inactive test: {definition.code}"
                    )
                )

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("DRY RUN: all writes rolled back.")

        self.stdout.write(
            "Catalog (would apply for dry run): "
            + ", ".join(
                f"{key}={value}"
                for key, value in counts.items()
            )
        )
        self.stdout.write(
            "No panels, aliases, units, reference ranges, "
            "or patient results were created or changed."
        )
