"""Synthetic regression tests for the additive catalog expansion."""
import json
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from labs.bundled_catalog import BUNDLED_TESTS
from labs.bundled_panels import PANEL_DEFINITIONS
from labs.bundled_test_definitions import TEST_DEFINITIONS
from labs.models import LabTest, LabTestCategory, LabPanel, LabPanelItem, LabTestUnit

DOCS = Path(__file__).resolve().parents[1] / 'docs' / 'catalog'
NEW_CODES = {
    'COAG_PT', 'COAG_INR', 'COAG_APTT', 'CHEM_CALCIUM_TOTAL',
    'CHEM_CALCIUM_IONIZED', 'CHEM_MAGNESIUM', 'CHEM_PHOSPHATE',
    'CHEM_URIC_ACID', 'IRON_SERUM', 'IRON_FERRITIN', 'IRON_TIBC',
    'IRON_TRANSFERRIN', 'INFLAM_CRP', 'HEM_ESR',
}


class ExpandedCatalogDefinitionTests(SimpleTestCase):
    def test_all_original_definitions_preserved_exactly(self):
        baseline = json.loads((DOCS / 'baseline-definitions.json').read_text(encoding='utf-8'))
        self.assertEqual([list(t) for t in TEST_DEFINITIONS[:51]], baseline)
        self.assertEqual(len(TEST_DEFINITIONS), 65)
        self.assertEqual({t[0] for t in TEST_DEFINITIONS[51:]}, NEW_CODES)

    def test_all_original_panels_preserved_exactly(self):
        baseline = json.loads((DOCS / 'baseline-panels.json').read_text(encoding='utf-8'))
        self.assertEqual(json.loads(json.dumps(PANEL_DEFINITIONS[:7])), baseline)
        self.assertEqual(len(PANEL_DEFINITIONS), 14)

    def test_new_tests_do_not_infer_units_or_metadata(self):
        for test in BUNDLED_TESTS:
            if test.code in NEW_CODES:
                with self.subTest(code=test.code):
                    self.assertEqual(test.input_type, 'numeric')
                    self.assertEqual(test.suggested_units, ())
                    self.assertEqual((test.specimen, test.method, test.time_aspect), ('', '', ''))
                    self.assertEqual((test.aliases, test.source_urls), ((), ()))

    def test_references_and_coverage(self):
        catalog = {t.code: t for t in BUNDLED_TESTS}
        members = set()
        self.assertEqual(len(catalog), 65)
        self.assertEqual(len({p[0] for p in PANEL_DEFINITIONS}), 14)
        for code, _, category, _, tests in PANEL_DEFINITIONS:
            self.assertEqual(len(tests), len(set(tests)))
            for test in tests:
                self.assertIn(test, catalog)
                self.assertEqual(catalog[test].category_code, category)
            members.update(tests)
        self.assertEqual(set(catalog) - members, {'CHEM_URIC_ACID', 'INFLAM_CRP', 'HEM_ESR'})

    def test_no_automatic_coagulation_or_calcium_substitution(self):
        codes = {t.code for t in BUNDLED_TESTS}
        self.assertTrue({'COAG_PT', 'COAG_INR', 'COAG_APTT'} <= codes)
        self.assertTrue({'CHEM_CALCIUM_TOTAL', 'CHEM_CALCIUM_IONIZED'} <= codes)
        self.assertNotIn('COAG_PTT', codes)
        self.assertNotIn('CHEM_CALCIUM_CORRECTED', codes)


class ExpandedCatalogInstallationTests(TestCase):
    def run_command(self, name, **kwargs):
        call_command(name, stdout=StringIO(), **kwargs)

    def test_catalog_without_panels_and_complete_repeat(self):
        self.run_command('install_bundled_catalog')
        self.assertEqual(LabTest.objects.count(), 65)
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabTestUnit.objects.exists())
        self.run_command('install_bundled_panels')
        self.assertEqual(LabPanel.objects.count(), 14)
        self.assertEqual(LabPanelItem.objects.count(), 70)
        models = (LabTest, LabTestCategory, LabPanel, LabPanelItem)
        before = [list(m.objects.order_by('pk').values()) for m in models]
        self.run_command('install_bundled_catalog')
        self.run_command('install_bundled_panels')
        self.assertEqual(before, [list(m.objects.order_by('pk').values()) for m in models])

    def test_new_code_conflict_rolls_back_catalog(self):
        LabTest.objects.create(code='HEM_ESR', name='Local different identity')
        before = list(LabTest.objects.values())
        with self.assertRaises(CommandError):
            self.run_command('install_bundled_catalog')
        self.assertEqual(before, list(LabTest.objects.values()))
        self.assertFalse(LabTestCategory.objects.exists())

    def test_new_code_conflict_rolls_back_panels(self):
        LabTest.objects.create(code='IRON_TRANSFERRIN', name='Local different identity')
        with self.assertRaises(CommandError):
            self.run_command('install_bundled_panels')
        self.assertEqual(LabTest.objects.count(), 1)
        self.assertFalse(LabPanel.objects.exists())
        self.assertFalse(LabTestCategory.objects.exists())

    def test_custom_new_panel_is_not_rewritten(self):
        panel = LabPanel.objects.create(code='builtin-coagulation', name='Local preset', is_active=False)
        test = LabTest.objects.create(code='SYN_LOCAL', name='Synthetic local')
        LabPanelItem.objects.create(panel=panel, lab_test=test, position=9)
        before = list(panel.items.values())
        self.run_command('install_bundled_panels')
        panel.refresh_from_db()
        self.assertEqual(panel.name, 'Local preset')
        self.assertFalse(panel.is_active)
        self.assertEqual(before, list(panel.items.values()))

    def test_dry_runs_never_persist(self):
        for command in ('install_bundled_catalog', 'install_bundled_panels'):
            self.run_command(command, dry_run=True)
            for model in (LabTestCategory, LabTest, LabPanel, LabPanelItem):
                self.assertFalse(model.objects.exists())
