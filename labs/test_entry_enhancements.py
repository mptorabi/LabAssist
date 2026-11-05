"""Synthetic regression tests for mixed panel / individual report entry."""
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from . import test_report_workflow as workflow
from .bundled_panels import PANELS
from .bundled_units import UNIT_SUGGESTIONS
from .entry_catalog import entry_catalog
from .forms import LabResultForm
from .models import LabPanel, LabPanelItem, LabTest, LabTestAlias, LabTestUnit, LabResult


class EntryEnhancementTests(TestCase):
    setUp = workflow.ReportWorkflowTests.setUp
    payload = workflow.ReportWorkflowTests.payload
    assert_not_saved = workflow.ReportWorkflowTests.assert_not_saved

    def test_blank_start_and_script_order(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['result_formset']), 0)
        text = response.content.decode()
        self.assertLess(text.index('js/catalog_search.js'), text.index('js/lab_test_search.js'))
        self.assertNotIn('value="save"', text)
        self.assert_not_saved()

    def test_add_panel_keeps_raw_fields_and_deduplicates(self):
        extra = LabTest.objects.create(code='EXTRA', name='Synthetic extra')
        panel = LabPanel.objects.create(code='extra', name='Extra')
        for test in (self.a, extra):
            LabPanelItem.objects.create(panel=panel, lab_test=test)
        data = self.payload('add_panels')
        data.update({'add_panels': panel.code, 'default_test_date': '',
                     'laboratory_name': '  Synthetic lab  ', 'notes': 'line one\nline two',
                     'results-0-value': ' <5.00 ', 'results-0-unit': ' custom ',
                     'results-0-reference_range': ' 1 - 8 ', 'results-0-notes': ' note\nnext '})
        response = self.client.post(self.url, data)
        forms = response.context['result_formset']
        self.assertEqual(len(forms), 3)
        for name in ('value', 'unit', 'reference_range', 'notes'):
            self.assertEqual(forms[0][name].value(), data['results-0-' + name])
        self.assertEqual(str(forms[2]['lab_test'].value()), str(extra.pk))
        self.assertEqual(response.context['header_form']['notes'].value(), data['notes'])
        self.assertEqual(response.context['header_form']['laboratory_name'].value(), data['laboratory_name'])
        self.assertFalse(forms.is_bound)
        self.assert_not_saved()

    def test_add_individual_and_existing_test_is_not_duplicated(self):
        extra = LabTest.objects.create(code='EXTRA', name='Synthetic extra')
        for test, count in ((extra, 3), (self.a, 2)):
            with self.subTest(test=test):
                data = self.payload('add_test')
                data['add_test'] = str(test.pk)
                response = self.client.post(self.url, data)
                self.assertEqual(len(response.context['result_formset']), count)
                self.assertEqual(response.context['result_formset'][0]['value'].value(), ' 12.50 ')
                self.assert_not_saved()

    def test_bad_add_ids_do_not_lose_entries(self):
        for identifier in ('', 'bad', '-1', '9999999', '9' * 100):
            with self.subTest(identifier=identifier):
                data = self.payload('add_test')
                data['add_test'] = identifier
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['entry_error'])
                self.assertEqual(response.context['result_formset'][0]['value'].value(), ' 12.50 ')
                self.assert_not_saved()

    def test_inactive_add_test_is_rejected(self):
        self.b.is_active = False
        self.b.save()
        data = self.payload('add_test')
        data['add_test'] = str(self.b.pk)
        self.assertTrue(self.client.post(self.url, data).context['entry_error'])
        self.assert_not_saved()

    def test_remove_blank_does_not_remove_partial_or_populated_rows(self):
        data = self.payload('remove_blank')
        response = self.client.post(self.url, data)
        self.assertEqual(len(response.context['result_formset']), 1)
        for field, value in (('unit', 'demo'), ('reference_range', '<10'), ('notes', 'note'),
                             ('test_date', self.day.isoformat())):
            with self.subTest(field=field):
                data['results-1-' + field] = value
                response = self.client.post(self.url, data)
                self.assertEqual(len(response.context['result_formset']), 2)
                data['results-1-' + field] = ''
        self.assert_not_saved()

    def test_tampered_row_ids_rejected_even_on_blank_rows(self):
        for identifier in ('', 'bad', '-1', '9999999', '9' * 100):
            for index in (0, 1):
                with self.subTest(identifier=identifier, index=index):
                    data = self.payload()
                    data[f'results-{index}-lab_test'] = identifier
                    response = self.client.post(self.url, data)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context['result_formset'][index].errors)
                    self.assert_not_saved()

    def test_bad_management_counts_cannot_save_or_add(self):
        for total, initial in (('-1', '0'), ('2', '-1'), ('2', '3'), ('101', '2'), ('bad', '2')):
            for action in ('save', 'add_test', 'add_panels', 'remove_blank'):
                with self.subTest(total=total, initial=initial, action=action):
                    data = self.payload(action)
                    data.update({'results-TOTAL_FORMS': total, 'results-INITIAL_FORMS': initial,
                                 'add_test': str(self.a.pk), 'add_panels': self.panel.code})
                    response = self.client.post(self.url, data)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context['entry_error'])
                    self.assert_not_saved()

    def test_one_hundred_rows_fit_default_post_limit_and_save(self):
        data = self.payload()
        data['results-TOTAL_FORMS'] = data['results-INITIAL_FORMS'] = '100'
        for i in range(2, 100):
            test = LabTest.objects.create(code=f'SYN_{i}', name=f'Synthetic {i}')
            for field in ('value', 'unit', 'reference_range', 'test_date', 'notes'):
                data[f'results-{i}-{field}'] = ''
            data[f'results-{i}-lab_test'] = str(test.pk)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.assertEqual(LabResult.objects.count(), 1)

    def test_add_beyond_limit_keeps_existing_rows(self):
        data = self.payload('add_test')
        data['results-TOTAL_FORMS'] = data['results-INITIAL_FORMS'] = '100'
        extra = LabTest.objects.create(code='EXTRA', name='Synthetic extra')
        data['add_test'] = str(extra.pk)
        response = self.client.post(self.url, data)
        self.assertTrue(response.context['entry_error'])
        self.assertEqual(len(response.context['result_formset']), 100)
        self.assertEqual(response.context['result_formset'][0]['value'].value(), ' 12.50 ')
        self.assert_not_saved()

    def test_free_text_units_ranges_notes_and_header_are_preserved(self):
        data = self.payload()
        values = {'laboratory_name': '  Synthetic  ', 'report_number': '  SYN  ',
                  'notes': '  note\nsecond line  ', 'results-0-unit': ' unknown unit ',
                  'results-0-reference_range': '  Report-specific text  ',
                  'results-0-notes': '  row notes  '}
        data.update(values)
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        result = LabResult.objects.get()
        for field in ('unit', 'reference_range', 'notes'):
            self.assertEqual(getattr(result, field), values['results-0-' + field])
        for field in ('laboratory_name', 'report_number', 'notes'):
            self.assertEqual(getattr(result.report, field), values[field])

    def test_suggestions_never_populate_unit_fields(self):
        LabTestUnit.objects.create(lab_test=self.a, symbol='demo/L')
        response = self.client.get(self.url, {'panels': self.panel.code})
        self.assertContains(response, '<option value="demo/L">')
        self.assertFalse(response.context['result_formset'][0]['unit'].value())
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 302)
        self.assertEqual(LabResult.objects.get().unit, '')

    def test_single_entry_preserves_text_and_rejects_whitespace(self):
        data = {'lab_test': self.a.pk, 'test_date': self.day.isoformat(),
                'value': ' <5.00 ', 'unit': ' custom ', 'reference_range': ' text ', 'notes': ' note '}
        form = LabResultForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        for field in ('value', 'unit', 'reference_range', 'notes'):
            self.assertEqual(form.cleaned_data[field], data[field])
        data['value'] = ' \t '
        self.assertFalse(LabResultForm(data).is_valid())

    def test_catalog_only_exposes_active_tests_and_units(self):
        LabTestAlias.objects.create(lab_test=self.a, name='Synthetic alias')
        LabTestUnit.objects.create(lab_test=self.a, symbol='demo/L')
        LabTestUnit.objects.create(lab_test=self.a, symbol='inactive/L', is_active=False)
        self.b.is_active = False
        self.b.save()
        catalog = entry_catalog()
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]['aliases'], ['Synthetic alias'])
        self.assertEqual(catalog[0]['units'], ['demo/L'])
        self.assertEqual(set(catalog[0]), {'id', 'code', 'name', 'category_id', 'category_name', 'aliases', 'units'})


class BundledUnitTests(TestCase):
    def setUp(self):
        call_command('install_bundled_panels', stdout=StringIO())

    def install(self, **kwargs):
        output = StringIO()
        call_command('install_bundled_units', stdout=output, **kwargs)
        return output.getvalue()

    def test_all_bundled_tests_have_suggestions(self):
        codes = {code for panel in PANELS for code, name in panel[4]}
        self.assertEqual(set(UNIT_SUGGESTIONS), codes)
        self.install()
        for code in codes:
            self.assertTrue(LabTestUnit.objects.filter(lab_test__code=code).exists())

    def test_idempotent(self):
        self.install()
        count = LabTestUnit.objects.count()
        self.install()
        self.assertEqual(LabTestUnit.objects.count(), count)

    def test_dry_run_rolls_back(self):
        self.assertIn('DRY RUN', self.install(dry_run=True))
        self.assertEqual(LabTestUnit.objects.count(), 0)

    def test_conflict_rolls_back_prior_writes(self):
        test = LabTest.objects.get(code='THYROID_T3_TOTAL')
        test.name = 'Synthetic incompatible identity'
        test.save()
        with self.assertRaises(CommandError):
            self.install()
        self.assertEqual(LabTestUnit.objects.count(), 0)

    def test_preserves_existing_inactive_and_custom_units(self):
        test = LabTest.objects.get(code='CBC_HGB')
        unit = LabTestUnit.objects.create(lab_test=test, symbol='g/dL', is_active=False)
        custom = LabTestUnit.objects.create(lab_test=test, symbol='custom')
        self.install()
        unit.refresh_from_db()
        self.assertFalse(unit.is_active)
        self.assertTrue(LabTestUnit.objects.filter(pk=custom.pk).exists())

    def test_skips_missing_and_inactive_tests(self):
        test = LabTest.objects.get(code='CBC_HGB')
        test.is_active = False
        test.save()
        LabPanelItem.objects.filter(lab_test__code='CBC_WBC').delete()
        LabTest.objects.filter(code='CBC_WBC').delete()
        output = self.install()
        self.assertIn('missing_tests=1', output)
        self.assertIn('inactive_tests=1', output)
        self.assertFalse(LabTestUnit.objects.filter(lab_test=test).exists())
        self.assertFalse(LabTest.objects.filter(code='CBC_WBC').exists())

    def test_catalog_version_mismatch_rejected(self):
        from unittest.mock import patch
        with patch('labs.management.commands.install_bundled_units.UNIT_SUGGESTIONS', {}):
            with self.assertRaises(CommandError):
                self.install()
        self.assertEqual(LabTestUnit.objects.count(), 0)