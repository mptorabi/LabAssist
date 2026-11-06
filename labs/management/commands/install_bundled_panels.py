from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from labs.bundled_catalog import BUNDLED_TESTS
from labs.bundled_panels import DESCRIPTION, PANELS
from labs.models import LabPanel, LabPanelItem, LabTest, LabTestCategory


class Command(BaseCommand):
    help = (
        "Install bundled entry presets using independent catalog definitions, "
        "preserving existing records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and roll back all writes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        counts = dict(categories=0, tests=0, panels=0, items=0)

        catalog = {}
        allowed_input_types = {
            value
            for value, _ in LabTest._meta.get_field(
                "input_type"
            ).flatchoices
        }

        for definition in BUNDLED_TESTS:
            if definition.code in catalog:
                raise CommandError(
                    f"Duplicate catalog code: {definition.code!r}."
                )

            if definition.input_type not in allowed_input_types:
                raise CommandError(
                    f"Unsupported input type for {definition.code!r}: "
                    f"{definition.input_type!r}."
                )

            catalog[definition.code] = definition

        # Validate all references before writing anything.
        panel_codes = set()

        for code, name, category_code, category_name, tests in PANELS:
            if code in panel_codes:
                raise CommandError(
                    f"Duplicate panel code: {code!r}."
                )
            panel_codes.add(code)

            member_codes = set()

            for test_code, test_name in tests:
                if test_code in member_codes:
                    raise CommandError(
                        f"Duplicate test {test_code!r} in panel {code!r}."
                    )
                member_codes.add(test_code)

                definition = catalog.get(test_code)

                if definition is None:
                    raise CommandError(
                        f"Unknown catalog test {test_code!r} "
                        f"in panel {code!r}."
                    )

                if definition.name != test_name:
                    raise CommandError(
                        f"Panel/catalog name mismatch for {test_code!r}. "
                        "No changes saved."
                    )

        for code, name, category_code, category_name, tests in PANELS:
            resolved = []

            for test_code, test_name in tests:
                definition = catalog[test_code]

                # Category belongs to the test definition,
                # not to the panel containing it.
                category, created = LabTestCategory.objects.get_or_create(
                    code=definition.category_code,
                    defaults={"name": definition.category_name},
                )
                counts["categories"] += int(created)

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
                        f"Code conflict: {test_code} is named "
                        f"{test.name!r}, expected {definition.name!r}. "
                        "All changes rolled back. Review identity manually; "
                        "do not rename blindly."
                    )

                counts["tests"] += int(created)

                if not test.is_active:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Preserved inactive test: {test_code}"
                        )
                    )

                resolved.append(test)

            panel, created = LabPanel.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": DESCRIPTION,
                    "version": 1,
                },
            )

            if not created:
                self.stdout.write(
                    f"Preserved existing panel and membership: {code}"
                )
                continue

            counts["panels"] += 1

            for position, test in enumerate(resolved, start=1):
                LabPanelItem.objects.create(
                    panel=panel,
                    lab_test=test,
                    position=position,
                )
                counts["items"] += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("DRY RUN: all writes rolled back.")

        self.stdout.write(
            "Created (would create for dry run): "
            + ", ".join(
                f"{key}={value}"
                for key, value in counts.items()
            )
        )
