from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from .bundled_catalog import BUNDLED_TESTS
from .bundled_panels import PANELS
from .models import LabPanel, LabPanelItem, LabTest, LabTestUnit


EXPECTED = {
    "DIFF_NEUT_PCT": (
        "Neutrophils — percent of leukocytes, blood", "%",
    ),
    "DIFF_NEUT_ABS": (
        "Neutrophils — absolute count, blood", "x 10(9)/L",
    ),
    "DIFF_LYMPH_PCT": (
        "Lymphocytes — percent of leukocytes, blood", "%",
    ),
    "DIFF_LYMPH_ABS": (
        "Lymphocytes — absolute count, blood", "x 10(9)/L",
    ),
    "DIFF_MONO_PCT": (
        "Monocytes — percent of leukocytes, blood", "%",
    ),
    "DIFF_MONO_ABS": (
        "Monocytes — absolute count, blood", "x 10(9)/L",
    ),
    "DIFF_EOS_PCT": (
        "Eosinophils — percent of leukocytes, blood", "%",
    ),
    "DIFF_EOS_ABS": (
        "Eosinophils — absolute count, blood", "x 10(9)/L",
    ),
    "DIFF_BASO_PCT": (
        "Basophils — percent of leukocytes, blood", "%",
    ),
    "DIFF_BASO_ABS": (
        "Basophils — absolute count, blood", "x 10(9)/L",
    ),
}


class HematologyCatalogDefinitionTests(SimpleTestCase):
    def test_exact_definitions_and_unit_suggestions(self):
        catalog = {test.code: test for test in BUNDLED_TESTS}

        for code, (name, unit) in EXPECTED.items():
            with self.subTest(code=code):
                definition = catalog[code]
                self.assertEqual(definition.name, name)
                self.assertEqual(definition.input_type, "numeric")
                self.assertEqual(definition.category_code, "hematology")
                self.assertEqual(definition.category_name, "Hematology")
                self.assertEqual(definition.suggested_units, (unit,))

    def test_percentage_and_absolute_identities_are_distinct(self):
        catalog = {test.code: test for test in BUNDLED_TESTS}

        for cell in ("NEUT", "LYMPH", "MONO", "EOS", "BASO"):
            with self.subTest(cell=cell):
                percent = catalog[f"DIFF_{cell}_PCT"]
                absolute = catalog[f"DIFF_{cell}_ABS"]
                self.assertNotEqual(percent.code, absolute.code)
                self.assertNotEqual(percent.name, absolute.name)
                self.assertNotEqual(
                    percent.suggested_units,
                    absolute.suggested_units,
                )

    def test_new_tests_do_not_change_existing_panel_membership(self):
        member_codes = {
            code
            for *_, tests in PANELS[:7]
            for code, _ in tests
        }
        self.assertTrue(set(EXPECTED).isdisjoint(member_codes))

    def test_method_and_aliases_are_not_inferred(self):
        catalog = {test.code: test for test in BUNDLED_TESTS}

        for code in EXPECTED:
            with self.subTest(code=code):
                self.assertEqual(catalog[code].method, "")
                self.assertEqual(catalog[code].aliases, ())


class HematologyCatalogInstallationTests(TestCase):
    def run_command(self, name, **options):
        call_command(name, stdout=StringIO(), **options)

    def test_catalog_installs_new_tests_without_panels_or_units(self):
        self.run_command("install_bundled_catalog")

        self.assertEqual(
            LabTest.objects.filter(code__in=EXPECTED).count(),
            len(EXPECTED),
        )
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabPanelItem.objects.exists())
        self.assertFalse(LabTestUnit.objects.exists())

    def test_unit_installation_for_standalone_tests_is_idempotent(self):
        self.run_command("install_bundled_catalog")
        self.run_command("install_bundled_units")
        self.run_command("install_bundled_units")

        for code, (_, unit) in EXPECTED.items():
            with self.subTest(code=code):
                self.assertEqual(
                    list(
                        LabTestUnit.objects.filter(
                            lab_test__code=code,
                        ).values_list("symbol", flat=True)
                    ),
                    [unit],
                )

        self.assertFalse(LabPanel.objects.exists())

    def test_panel_installer_installs_explicit_differential_presets(self):
        self.run_command("install_bundled_panels")

        self.assertEqual(
            LabTest.objects.filter(code__in=EXPECTED).count(), len(EXPECTED)
        )

    def test_catalog_dry_run_does_not_persist_new_tests(self):
        self.run_command("install_bundled_catalog", dry_run=True)

        self.assertFalse(LabTest.objects.exists())
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabTestUnit.objects.exists())
