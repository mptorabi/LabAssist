from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from labs.bundled_panels import PANELS
from labs.models import (
    LabPanel, LabPanelItem, LabTest, LabTestCategory, LabTestUnit, LabTestAlias,
    LabReport, LabResult,
)


class BundledPanelTests(TestCase):
    def install(self, **kwargs):
        call_command("install_bundled_panels", stdout=StringIO(), **kwargs)

    def test_complete_installation(self):
        self.install()
        self.assertEqual(LabPanel.objects.count(), 7)
        self.assertEqual(LabTest.objects.count(), 35)
        self.assertEqual(LabPanelItem.objects.count(), 35)
        self.assertEqual(LabTestCategory.objects.count(), 3)
        for code, name, _, _, tests in PANELS:
            panel = LabPanel.objects.get(code=code)
            self.assertEqual(panel.name, name)
            self.assertEqual(panel.version, 1)
            self.assertEqual(list(panel.items.values_list("lab_test__code", flat=True)),
                             [code for code, _ in tests])

    def test_repeat_is_idempotent(self):
        self.install()
        before = list(LabPanel.objects.values())
        items = list(LabPanelItem.objects.values())
        tests = list(LabTest.objects.values())
        self.install()
        self.assertEqual(before, list(LabPanel.objects.values()))
        self.assertEqual(items, list(LabPanelItem.objects.values()))
        self.assertEqual(tests, list(LabTest.objects.values()))

    def test_existing_hemoglobin_preserved(self):
        test = LabTest.objects.create(code="CBC_HGB", name="Hemoglobin", input_type="text")
        self.install()
        test.refresh_from_db()
        self.assertEqual(test.input_type, "text")
        self.assertIsNone(test.category_id)
        self.assertEqual(LabPanelItem.objects.get(lab_test=test).panel.code, "builtin-cbc")

    def test_no_units_aliases_or_patient_records_created(self):
        self.install()
        for model in (LabTestUnit, LabTestAlias, LabReport, LabResult):
            self.assertEqual(model.objects.count(), 0)

    def test_dry_run_leaves_empty_database_unchanged(self):
        self.install(dry_run=True)
        for model in (LabTestCategory, LabTest, LabPanel, LabPanelItem):
            self.assertEqual(model.objects.count(), 0)

    def test_dry_run_preserves_existing_test(self):
        LabTest.objects.create(code="CBC_HGB", name="Hemoglobin")
        before = list(LabTest.objects.values())
        self.install(dry_run=True)
        self.assertEqual(before, list(LabTest.objects.values()))
        self.assertFalse(LabPanel.objects.exists())

    def test_conflict_rolls_back_everything(self):
        LabTest.objects.create(code="THYROID_T3_TOTAL", name="Different measurement")
        with self.assertRaises(CommandError):
            self.install()
        self.assertEqual(LabTest.objects.count(), 1)
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())

    def test_inactive_test_not_reactivated(self):
        test = LabTest.objects.create(code="CBC_HGB", name="Hemoglobin", is_active=False)
        self.install()
        test.refresh_from_db()
        self.assertFalse(test.is_active)

    def test_custom_panel_and_synthetic_test_preserved(self):
        test = LabTest.objects.create(code="SYN_DEMO", name="Synthetic demo test")
        panel = LabPanel.objects.create(code="synthetic-basic", name="Demo")
        item = LabPanelItem.objects.create(panel=panel, lab_test=test)
        self.install()
        self.assertTrue(LabPanelItem.objects.filter(pk=item.pk, lab_test=test, panel=panel).exists())
        self.assertFalse(LabPanelItem.objects.filter(panel__code__startswith="builtin-", lab_test=test).exists())

    def test_existing_panel_customizations_preserved(self):
        self.install()
        panel = LabPanel.objects.get(code="builtin-cbc")
        panel.name = "Local title"
        panel.is_active = False
        panel.version = 2
        panel.save()
        panel.items.first().delete()
        self.install()
        panel.refresh_from_db()
        self.assertEqual(panel.name, "Local title")
        self.assertEqual(panel.version, 2)
        self.assertFalse(panel.is_active)
        self.assertEqual(panel.items.count(), 7)

    def test_measurements_have_distinct_identities(self):
        self.install()
        for a, b in (("CHEM_UREA", "CHEM_BUN"),
                     ("THYROID_FT4", "THYROID_T4_TOTAL"),
                     ("LIPID_LDL_DIRECT", "LIPID_LDL_CALCULATED")):
            self.assertNotEqual(LabTest.objects.get(code=a).pk, LabTest.objects.get(code=b).pk)

    def test_each_panel_has_unique_member_codes(self):
        for panel_code, _, _, _, tests in PANELS:
            with self.subTest(panel=panel_code):
                codes = [code for code, _ in tests]
                self.assertEqual(len(codes), len(set(codes)))
