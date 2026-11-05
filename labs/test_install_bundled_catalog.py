from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .bundled_catalog import CatalogTest
from .models import (
    LabPanel,
    LabPanelItem,
    LabTest,
    LabTestAlias,
    LabTestCategory,
    LabTestUnit,
)


COMMAND_MODULE = (
    "labs.management.commands.install_bundled_catalog"
)


class InstallBundledCatalogTests(TestCase):
    def definition(
        self,
        code="SYN_A",
        *,
        input_type="numeric",
        units=(),
    ):
        return CatalogTest(
            code=code,
            name=f"Synthetic test {code}",
            category_code="synthetic",
            category_name="Synthetic category",
            input_type=input_type,
            suggested_units=units,
        )

    def install(self, definitions, **options):
        output = StringIO()

        with patch(
            f"{COMMAND_MODULE}.BUNDLED_TESTS",
            tuple(definitions),
        ):
            call_command(
                "install_bundled_catalog",
                stdout=output,
                **options,
            )

        return output.getvalue()

    def test_installs_standalone_test_without_panel_or_units(self):
        definition = self.definition()

        self.install((definition,))

        test = LabTest.objects.get(code=definition.code)

        self.assertEqual(test.name, definition.name)
        self.assertEqual(test.input_type, "numeric")
        self.assertEqual(test.category.code, "synthetic")
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabPanelItem.objects.exists())
        self.assertFalse(LabTestUnit.objects.exists())

    def test_preserves_each_explicit_input_type(self):
        definitions = tuple(
            self.definition(
                code=f"SYN_{input_type.upper()}",
                input_type=input_type,
            )
            for input_type in (
                "numeric",
                "text",
                "qualitative",
                "structured",
            )
        )

        self.install(definitions)

        for definition in definitions:
            with self.subTest(code=definition.code):
                test = LabTest.objects.get(code=definition.code)
                self.assertEqual(
                    test.input_type,
                    definition.input_type,
                )

    def test_unitless_qualitative_test_is_allowed(self):
        definition = self.definition(input_type="qualitative")

        self.install((definition,))

        test = LabTest.objects.get(code=definition.code)
        self.assertEqual(test.input_type, "qualitative")
        self.assertFalse(
            LabTestUnit.objects.filter(lab_test=test).exists()
        )

    def test_unit_suggestions_are_not_installed_by_this_command(self):
        definition = self.definition(units=("demo/L",))

        self.install((definition,))

        self.assertTrue(
            LabTest.objects.filter(code=definition.code).exists()
        )
        self.assertFalse(LabTestUnit.objects.exists())

    def test_repeated_install_is_idempotent(self):
        definition = self.definition()

        self.install((definition,))
        original = LabTest.objects.get(code=definition.code)
        category_id = original.category_id

        output = self.install((definition,))

        self.assertEqual(LabTest.objects.count(), 1)
        self.assertEqual(LabTestCategory.objects.count(), 1)

        current = LabTest.objects.get(code=definition.code)
        self.assertEqual(current.pk, original.pk)
        self.assertEqual(current.category_id, category_id)
        self.assertIn("tests=0", output)
        self.assertIn("preserved_tests=1", output)

    def test_existing_customizations_are_preserved(self):
        definition = self.definition()

        custom_category = LabTestCategory.objects.create(
            code="synthetic-custom",
            name="Synthetic custom category",
        )
        test = LabTest.objects.create(
            code=definition.code,
            name=definition.name,
            category=custom_category,
            input_type="text",
            is_active=False,
        )
        alias = LabTestAlias.objects.create(
            lab_test=test,
            name="Synthetic custom alias",
        )
        unit = LabTestUnit.objects.create(
            lab_test=test,
            symbol="custom",
            is_active=False,
        )

        output = self.install((definition,))

        test.refresh_from_db()
        unit.refresh_from_db()

        self.assertEqual(test.category_id, custom_category.pk)
        self.assertEqual(test.input_type, "text")
        self.assertFalse(test.is_active)
        self.assertFalse(unit.is_active)
        self.assertEqual(unit.symbol, "custom")
        self.assertTrue(
            LabTestAlias.objects.filter(
                pk=alias.pk,
                name="Synthetic custom alias",
            ).exists()
        )
        self.assertFalse(
            LabTestCategory.objects.filter(code="synthetic").exists()
        )
        self.assertIn("inactive_tests=1", output)

    def test_existing_category_name_is_preserved(self):
        category = LabTestCategory.objects.create(
            code="synthetic",
            name="Synthetic manually edited category",
        )

        self.install((self.definition(),))

        category.refresh_from_db()
        self.assertEqual(
            category.name,
            "Synthetic manually edited category",
        )
        self.assertEqual(
            LabTest.objects.get(code="SYN_A").category_id,
            category.pk,
        )

    def test_dry_run_rolls_back_tests_and_categories(self):
        output = self.install(
            (self.definition(),),
            dry_run=True,
        )

        self.assertIn("DRY RUN", output)
        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())

    def test_name_conflict_rolls_back_prior_writes(self):
        first = self.definition(code="SYN_FIRST")
        conflicting = self.definition(code="SYN_CONFLICT")

        existing = LabTest.objects.create(
            code=conflicting.code,
            name="Synthetic incompatible identity",
        )

        with self.assertRaisesRegex(CommandError, "Code conflict"):
            self.install((first, conflicting))

        self.assertFalse(
            LabTest.objects.filter(code=first.code).exists()
        )
        self.assertFalse(
            LabTestCategory.objects.filter(code="synthetic").exists()
        )

        existing.refresh_from_db()
        self.assertEqual(
            existing.name,
            "Synthetic incompatible identity",
        )

    def test_invalid_input_type_fails_before_writes(self):
        valid = self.definition(code="SYN_VALID")
        invalid = self.definition(
            code="SYN_INVALID",
            input_type="invalid",
        )

        with self.assertRaisesRegex(
            CommandError,
            "Unsupported input type",
        ):
            self.install((valid, invalid))

        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())

    def test_duplicate_catalog_codes_are_rejected(self):
        definition = self.definition()

        with self.assertRaisesRegex(
            CommandError,
            "Duplicate catalog code",
        ):
            self.install((definition, definition))

        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())

    def test_empty_catalog_is_a_no_op(self):
        output = self.install(())

        self.assertIn("tests=0", output)
        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())
