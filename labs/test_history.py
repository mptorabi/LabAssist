from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from unittest.mock import Mock
from patients.models import Patient
from labs.models import LabResult, LabTest
from patients.views import patient_lab_history
from django.template.loader import get_template
from labs.history import build_history, numeric_value


class HistoryTests(SimpleTestCase):
    def row(self, pk=1, value='12.5', unit='g/dL', day=1, patient=1, test=1):
        return SimpleNamespace(pk=pk, value=value, unit=unit, test_date=date(2025, 1, day),
                               patient_id=patient, lab_test_id=test)

    def test_plain_decimals(self):
        for text in ['0', '-2', '+3', '.25', '12.', ' 12.50 ']:
            self.assertEqual(numeric_value(text), Decimal(text.strip()))

    def test_ambiguous_and_nonfinite_values_excluded(self):
        for text in ['<5', '>2', '1,234', '1,2', '1e3', 'NaN', 'Infinity', 'Positive', '', '12 mg', '١٢']:
            self.assertIsNone(numeric_value(text), text)

    def test_bounds(self):
        self.assertIsNone(numeric_value('1000000000001'))
        self.assertIsNone(numeric_value('0.0000000000001'))
        self.assertIsNotNone(numeric_value('0'))

    def test_empty(self):
        self.assertEqual(build_history([]), {'history_rows': [], 'history_charts': []})

    def test_identity_guard(self):
        for other in [self.row(patient=2), self.row(test=2)]:
            with self.assertRaises(ValueError):
                build_history([self.row(), other])

    def test_exact_units_separate(self):
        result = build_history([self.row(unit=u) for u in ['g/dL', 'g/L', 'G/dL', 'g/dL ']])
        self.assertEqual(len(result['history_charts']), 4)
        self.assertTrue(all(not c['points'] for c in result['history_charts']))

    def test_missing_units_not_plotted(self):
        data = build_history([self.row(unit=''), self.row(unit=' ')])
        self.assertEqual(len(data['history_rows']), 2)
        self.assertFalse(data['history_charts'])

    def test_text_preserved(self):
        row = self.row(value='<0.01')
        data = build_history([row])
        self.assertIs(data['history_rows'][0]['result'], row)
        self.assertEqual(row.value, '<0.01')
        self.assertTrue(data['history_rows'][0]['reason'])

    def test_same_day_not_averaged(self):
        chart = build_history([self.row(1), self.row(2, value='14')])['history_charts'][0]
        self.assertEqual(len(chart['points']), 2)
        self.assertEqual({p['x'] for p in chart['points']}, {'360.00'})

    def test_equal_values_centered(self):
        points = build_history([self.row(1), self.row(2, day=3)])['history_charts'][0]['points']
        self.assertEqual({p['y'] for p in points}, {'140.00'})

    def test_date_spacing_and_order(self):
        chart = build_history([self.row(3, day=11), self.row(1), self.row(2, day=2)])['history_charts'][0]
        self.assertEqual([p['x'] for p in chart['points']], ['140.00', '184.00', '580.00'])
        self.assertEqual([p['result'].pk for p in chart['points']], [1, 2, 3])

    def test_coordinates_not_localized(self):
        with self.settings(LANGUAGE_CODE='de'):
            points = build_history([self.row(1), self.row(2, value='13', day=2)])['history_charts'][0]['points']
            self.assertTrue(all(',' not in p['x'] + p['y'] for p in points))

    def test_points_have_padding_and_numeric_ticks(self):
        chart = build_history([self.row(1), self.row(2, value='13.8', day=10)])['history_charts'][0]
        self.assertEqual([p['y'] for p in chart['points']], ['220.00', '60.00'])
        self.assertEqual([t['label'] for t in chart['ticks']], ['12.5', '13.15', '13.8'])
        for point in chart['points']:
            self.assertTrue(120 < float(point['x']) < 600)
            self.assertTrue(40 < float(point['y']) < 240)
        self.assertFalse(chart['same_day'])

    def test_constant_zero_has_one_centered_tick(self):
        chart = build_history([self.row(1, value='0'), self.row(2, value='0')])['history_charts'][0]
        self.assertEqual(chart['ticks'], [{'y': '140.00', 'label': '0'}])
        self.assertTrue(chart['same_day'])

    def test_negative_values_and_rounded_tick_labels(self):
        chart = build_history([self.row(1, value='-1.23456789'), self.row(2, value='-1')])['history_charts'][0]
        self.assertTrue(chart['ticks'][0]['label'].startswith('~'))
        self.assertEqual(chart['points'][0]['result'].value, '-1.23456789')
        self.assertEqual([p['y'] for p in chart['points']], ['220.00', '60.00'])

    def test_extreme_scales_have_finite_interior_coordinates(self):
        for low, high in [('0.000000000001', '0.000000000002'),
                          ('-1000000000000', '1000000000000')]:
            chart = build_history([self.row(1, value=low), self.row(2, value=high)])['history_charts'][0]
            self.assertEqual([p['y'] for p in chart['points']], ['220.00', '60.00'])
            self.assertEqual(len(chart['ticks']), 3)

    def test_template_compiles(self):
        get_template('patients/patient_lab_history.html')


class HistoryViewTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name='Synthetic patient')
        self.other = Patient.objects.create(full_name='Other synthetic patient')
        self.test = LabTest.objects.create(code='SYN_HIST', name='Synthetic history')
        self.request = RequestFactory().get('/history/')
        self.request.user = Mock(is_authenticated=True)
        self.request.user.has_perms.return_value = True

    def test_anonymous_redirected(self):
        self.request.user = AnonymousUser()
        response = patient_lab_history(self.request, self.patient.pk, self.test.pk)
        self.assertEqual(response.status_code, 302)

    def test_missing_permission_denied(self):
        self.request.user.has_perms.return_value = False
        with self.assertRaises(PermissionDenied):
            patient_lab_history(self.request, self.patient.pk, self.test.pk)

    def test_render_is_scoped_and_escaped(self):
        for patient, value in [(self.patient, '<script>alert(1)</script>'), (self.other, 'PRIVATE_OTHER_RESULT')]:
            LabResult.objects.create(patient=patient, lab_test=self.test, test_date=date(2025, 1, 1), value=value)
        response = patient_lab_history(self.request, self.patient.pk, self.test.pk)
        text = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('PRIVATE_OTHER_RESULT', text)
        self.assertNotIn('<script>', text)
        self.assertIn('&lt;script&gt;', text)

    def test_preserves_template_accessibility_and_multiline_notes(self):
        LabResult.objects.create(
            patient=self.patient, lab_test=self.test,
            test_date=date(2025, 1, 1), value='12', unit='g/dL',
            notes='First line\nSecond line <script>unsafe</script>',
        )
        response = patient_lab_history(self.request, self.patient.pk, self.test.pk)
        text = response.content.decode()
        self.assertIn('aria-labelledby="lab-history-title"', text)
        self.assertIn('id="lab-history-title"', text)
        self.assertEqual(text.count('scope="col"'), 6)
        self.assertIn('First line<br>Second line', text)
        self.assertNotIn('<script>', text)
        self.assertIn('Results are shown as recorded, newest first.', text)
        self.assertIn('Back to Patient', text)

    def test_chart_renders_axis_labels_and_single_date(self):
        for value in ['12.5', '13.8']:
            LabResult.objects.create(patient=self.patient, lab_test=self.test,
                                     test_date=date(2025, 1, 1), value=value, unit='g/dL')
        text = patient_lab_history(self.request, self.patient.pk, self.test.pk).content.decode()
        self.assertIn('Vertical axis: recorded value (g/dL)', text)
        self.assertIn('>Test date</text>', text)
        self.assertIn('>13.15</text>', text)
        svg = text.split('<svg', 1)[1].split('</svg>', 1)[0]
        self.assertEqual(svg.count('<circle'), 2)
        self.assertEqual(svg.count('text-anchor="middle" font-size="13"'), 1)
        self.assertNotIn('<polyline', svg)

    def test_empty_history_preserves_message(self):
        response = patient_lab_history(self.request, self.patient.pk, self.test.pk)
        text = response.content.decode()
        self.assertIn('No results recorded for this test for this patient.', text)
        self.assertNotIn('<svg', text)