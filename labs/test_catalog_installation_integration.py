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
    LabTestCategory,
    LabTestUnit,
)


PANEL_COMMAND = "labs.management.commands.install_bundled_panels"
UNIT_COMMAND = "labs.management.commands.install_bundled_units"


class CatalogInstallationIntegrationTests(TestCase):
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

    def panel(self, code, *definitions):
        return (
            code,
            f"Synthetic panel {code}",
            "synthetic",
            "Synthetic category",
            tuple(
                (definition.code, definition.name)
                for definition in definitions
            ),
        )

    def install_panels(self, definitions, panels, **options):
        output = StringIO()

        with (
            patch(
                f"{PANEL_COMMAND}.BUNDLED_TESTS",
                tuple(definitions),
            ),
            patch(
                f"{PANEL_COMMAND}.PANELS",
                tuple(panels),
            ),
        ):
            call_command(
                "install_bundled_panels",
                stdout=output,
                **options,
            )

        return output.getvalue()

    def install_units(self, definitions, mappings, **options):
        output = StringIO()

        with (
            patch(
                f"{UNIT_COMMAND}.BUNDLED_TESTS",
                tuple(definitions),
            ),
            patch(
                f"{UNIT_COMMAND}.UNIT_SUGGESTIONS",
                mappings,
            ),
        ):
            call_command(
                "install_bundled_units",
                stdout=output,
                **options,
            )

        return output.getvalue()

    def test_panel_installs_explicit_qualitative_type_without_units(self):
        definition = self.definition(input_type="qualitative")

        self.install_panels(
            (definition,),
            (self.panel("synthetic-a", definition),),
        )

        test = LabTest.objects.get(code=definition.code)
        self.assertEqual(test.input_type, "qualitative")
        self.assertEqual(test.category.code, definition.category_code)
        self.assertEqual(LabPanelItem.objects.count(), 1)
        self.assertFalse(LabTestUnit.objects.exists())

    def test_shared_test_is_created_once_for_two_panels(self):
        definition = self.definition()

        self.install_panels(
            (definition,),
            (
                self.panel("synthetic-a", definition),
                self.panel("synthetic-b", definition),
            ),
        )

        self.assertEqual(LabTest.objects.count(), 1)
        self.assertEqual(LabPanel.objects.count(), 2)
        self.assertEqual(LabPanelItem.objects.count(), 2)

    def test_panel_install_does_not_install_unrelated_standalone_test(self):
        member = self.definition(code="SYN_MEMBER")
        standalone = self.definition(code="SYN_STANDALONE")

        self.install_panels(
            (member, standalone),
            (self.panel("synthetic-a", member),),
        )

        self.assertTrue(
            LabTest.objects.filter(code=member.code).exists()
        )
        self.assertFalse(
            LabTest.objects.filter(code=standalone.code).exists()
        )

    def test_unknown_panel_member_fails_without_writes(self):
        unknown = self.definition(code="SYN_UNKNOWN")

        with self.assertRaisesRegex(
            CommandError,
            "Unknown catalog test",
        ):
            self.install_panels(
                (),
                (self.panel("synthetic-a", unknown),),
            )

        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())
        self.assertFalse(LabPanel.objects.exists())

    def test_panel_catalog_name_mismatch_is_rejected(self):
        definition = self.definition()
        invalid_panel = (
            "synthetic-a",
            "Synthetic panel",
            "synthetic",
            "Synthetic category",
            ((definition.code, "Synthetic different identity"),),
        )

        with self.assertRaisesRegex(
            CommandError,
            "Panel/catalog name mismatch",
        ):
            self.install_panels(
                (definition,),
                (invalid_panel,),
            )

        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabPanel.objects.exists())

    def test_panel_preserves_existing_input_type(self):
        definition = self.definition(input_type="qualitative")
        test = LabTest.objects.create(
            code=definition.code,
            name=definition.name,
            input_type="text",
        )

        self.install_panels(
            (definition,),
            (self.panel("synthetic-a", definition),),
        )

        test.refresh_from_db()
        self.assertEqual(test.input_type, "text")
        self.assertIsNone(test.category_id)

    def test_units_can_be_installed_for_test_without_panel(self):
        definition = self.definition(units=("demo/L",))
        test = LabTest.objects.create(
            code=definition.code,
            name=definition.name,
        )

        self.install_units(
            (definition,),
            {definition.code: ("demo/L",)},
        )

        self.assertTrue(
            LabTestUnit.objects.filter(
                lab_test=test,
                symbol="demo/L",
            ).exists()
        )
        self.assertFalse(LabPanel.objects.exists())

    def test_missing_and_empty_unit_mappings_are_allowed_for_unitless_test(self):
        definition = self.definition(input_type="qualitative")
        LabTest.objects.create(
            code=definition.code,
            name=definition.name,
            input_type=definition.input_type,
        )

        for mapping in ({}, {definition.code: ()}):
            with self.subTest(mapping=mapping):
                output = self.install_units(
                    (definition,),
                    mapping,
                )

                self.assertIn("without_suggestions=1", output)
                self.assertFalse(LabTestUnit.objects.exists())

    def test_units_do_not_create_missing_test(self):
        definition = self.definition(units=("demo/L",))

        output = self.install_units(
            (definition,),
            {definition.code: ("demo/L",)},
        )

        self.assertIn("missing_tests=1", output)
        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestUnit.objects.exists())

    def test_unknown_unit_mapping_is_rejected(self):
        definition = self.definition()

        with self.assertRaisesRegex(
            CommandError,
            "unknown catalog tests",
        ):
            self.install_units(
                (definition,),
                {"SYN_UNKNOWN": ("demo/L",)},
            )

        self.assertFalse(LabTestUnit.objects.exists())

    def test_catalog_unit_mismatch_is_rejected(self):
        definition = self.definition(units=("demo/L",))

        with self.assertRaisesRegex(
            CommandError,
            "versions differ",
        ):
            self.install_units(
                (definition,),
                {definition.code: ("different/L",)},
            )

        self.assertFalse(LabTestUnit.objects.exists())

    def test_units_dry_run_rolls_back(self):
        definition = self.definition(units=("demo/L",))
        LabTest.objects.create(
            code=definition.code,
            name=definition.name,
        )

        output = self.install_units(
            (definition,),
            {definition.code: ("demo/L",)},
            dry_run=True,
        )

        self.assertIn("DRY RUN", output)
        self.assertFalse(LabTestUnit.objects.exists())

    def test_panel_dry_run_rolls_back(self):
        definition = self.definition(input_type="qualitative")

        output = self.install_panels(
            (definition,),
            (self.panel("synthetic-a", definition),),
            dry_run=True,
        )

        self.assertIn("DRY RUN", output)
        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabPanelItem.objects.exists())
