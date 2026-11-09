from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from labs.models import LabTest, LabResult, LabReport
from patients.models import Patient
from patients.comparison import ComparisonForm, comparison_sections


class ComparisonTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name='Synthetic comparison')
        self.other = Patient.objects.create(full_name='Synthetic other')
        self.test = LabTest.objects.create(code='SYN', name='Synthetic test')
        self.report = LabReport.objects.create(patient=self.patient, specimen='Serum', laboratory_name='Synthetic lab')
        self.user = User.objects.create_user('reviewer', password='synthetic-test-password')
        self.user.user_permissions.add(*Permission.objects.filter(codename__in=['view_patient', 'view_labresult']))
        self.url = reverse('patients:comparison', args=[self.patient.pk])

    def row(self, **kwargs):
        defaults = dict(patient=self.patient, lab_test=self.test, report=self.report,
                        test_date=date(2025, 1, 1), value='12', unit='mg/L')
        defaults.update(kwargs)
        return LabResult.objects.create(**defaults)

    def test_groups_matching_context(self):
        a, b = self.row(), self.row(value='15')
        groups = comparison_sections([a, b])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]['history_charts'][0]['points']), 2)

    def test_different_metadata_separates(self):
        a = self.row()
        for field, value in [('unit', 'MG/L'), ('reference_range', '10-20'), ('result_kind', 'numeric')]:
            self.assertEqual(len(comparison_sections([a, self.row(**{field: value})])), 2)
        report = LabReport.objects.create(patient=self.patient, specimen='Urine', laboratory_name='Synthetic lab')
        self.assertEqual(len(comparison_sections([a, self.row(report=report)])), 2)
        report.specimen = 'Serum'
        report.laboratory_name = 'Other lab'
        report.save()
        self.assertEqual(len(comparison_sections([a, self.row(report=report)])), 2)

    def test_unknown_context_isolated(self):
        groups = comparison_sections([self.row(report=None), self.row(report=None)])
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(not g['history_charts'][0]['points'] for g in groups))

    def test_cross_patient_guard(self):
        with self.assertRaises(ValueError):
            comparison_sections([self.row(), self.row(patient=self.other, report=None)])

    def test_non_numeric_preserved(self):
        row = self.row(value='<5')
        group = comparison_sections([row])[0]
        self.assertFalse(group['history_charts'])
        self.assertEqual(group['history_rows'][0]['result'].value, '<5')

    def test_authentication_and_permissions(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.user.user_permissions.clear()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_render_and_read_only(self):
        self.row(value='<script>unsafe</script>')
        self.row(value='15')
        self.client.force_login(self.user)
        before = LabResult.objects.count()
        response = self.client.get(self.url, {'tests': [self.test.pk]})
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertNotContains(response, '<script>unsafe</script>')
        self.assertEqual(LabResult.objects.count(), before)
        self.assertContains(response, 'independent value and date scales')

    def test_foreign_test_rejected(self):
        foreign = LabTest.objects.create(code='OTHER', name='Other test')
        self.row(patient=self.other, report=None, lab_test=foreign)
        form = ComparisonForm({'tests': [foreign.pk]}, patient=self.patient)
        self.assertFalse(form.is_valid())

    def test_dates_and_selection_limit(self):
        self.row()
        for data in [{'tests': [self.test.pk], 'start': 'bad'},
                     {'tests': [self.test.pk], 'start': '2025-02-01', 'end': '2025-01-01'}]:
            self.assertFalse(ComparisonForm(data, patient=self.patient).is_valid())
        tests = [self.test.pk]
        for i in range(4):
            test = LabTest.objects.create(code=f'SYN{i}', name=f'Synthetic {i}')
            self.row(lab_test=test)
            tests.append(test.pk)
        self.assertFalse(ComparisonForm({'tests': tests}, patient=self.patient).is_valid())

    def test_date_filter_inclusive(self):
        self.row()
        self.client.force_login(self.user)
        response = self.client.get(self.url, {'tests': [self.test.pk], 'start': '2025-01-01', 'end': '2025-01-01'})
        self.assertEqual(len(response.context['sections']), 1)
        response = self.client.get(self.url, {'tests': [self.test.pk], 'start': '2025-01-02'})
        self.assertEqual(response.context['sections'], [])
