from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from labs.bundled_catalog import BUNDLED_TESTS
from labs.bundled_units import UNIT_SUGGESTIONS
from labs.models import LabTest, LabTestUnit


class Command(BaseCommand):
    help = (
        "Install optional offline unit spellings for exact independent "
        "catalog identities. Does not create tests or select result units."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and roll back all writes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        catalog = {}

        for definition in BUNDLED_TESTS:
            if definition.code in catalog:
                raise CommandError(
                    f"Duplicate catalog code: {definition.code!r}."
                )
            catalog[definition.code] = definition

        unknown_codes = set(UNIT_SUGGESTIONS) - set(catalog)

        if unknown_codes:
            raise CommandError(
                "Unit suggestions reference unknown catalog tests: "
                + ", ".join(sorted(unknown_codes))
                + ". No changes saved."
            )

        # Missing mapping and an explicitly empty mapping both mean
        # that no unit suggestions exist for that test.
        for code, definition in catalog.items():
            symbols = UNIT_SUGGESTIONS.get(code, ())

            if not isinstance(symbols, (tuple, list)):
                raise CommandError(
                    f"Invalid unit mapping for {code!r}. No changes saved."
                )

            if (
                any(
                    not isinstance(symbol, str) or not symbol.strip()
                    for symbol in symbols
                )
                or len(symbols) != len(set(symbols))
            ):
                raise CommandError(
                    f"Invalid unit suggestions for {code!r}. "
                    "No changes saved."
                )

            if tuple(symbols) != definition.suggested_units:
                raise CommandError(
                    "Bundled catalog/unit versions differ. "
                    "No changes saved."
                )

        counts = dict(
            created=0,
            preserved=0,
            missing_tests=0,
            inactive_tests=0,
            without_suggestions=0,
        )

        for definition in BUNDLED_TESTS:
            symbols = definition.suggested_units

            if not symbols:
                counts["without_suggestions"] += 1
                continue

            test = LabTest.objects.filter(
                code=definition.code
            ).first()

            if test is None:
                counts["missing_tests"] += 1
                self.stdout.write(
                    f"Skipped missing test: {definition.code}"
                )
                continue

            if test.name != definition.name:
                raise CommandError(
                    f"Code conflict: {definition.code} does not have "
                    "the bundled name. All changes rolled back. "
                    "Review identity manually; do not rename blindly."
                )

            if not test.is_active:
                counts["inactive_tests"] += 1
                self.stdout.write(
                    f"Skipped inactive test: {definition.code}"
                )
                continue

            for symbol in symbols:
                _, created = LabTestUnit.objects.get_or_create(
                    lab_test=test,
                    symbol=symbol,
                )
                counts["created" if created else "preserved"] += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("DRY RUN: all writes rolled back.")

        self.stdout.write(
            "Units (would create for dry run): "
            + ", ".join(
                f"{key}={value}"
                for key, value in counts.items()
            )
        )
        self.stdout.write(
            "No units selected, converted or added to recorded results."
        )
