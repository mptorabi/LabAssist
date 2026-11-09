"""Synthetic-only coverage for search, transcription metadata and audit/PDF integration."""
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfReader

from core.models import RecordAudit
from labs.models import LabReport, LabResult, LabTest
from patients.models import Patient


class Phase45Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(username='synthetic-phase45')
        self.client.force_login(self.user)
        self.patient = Patient.objects.create(full_name='Synthetic target')
        self.other = Patient.objects.create(full_name='Other synthetic')
        self.test = LabTest.objects.create(code='SYN45', name='Synthetic search test')
        self.report = LabReport.objects.create(patient=self.patient, laboratory_name='Synthetic lab', report_number='SYN-45')
        self.detail = reverse('labs:report_detail', args=[self.patient.pk, self.report.pk])
        self.create = reverse('labs:report_create', args=[self.patient.pk])

    def result(self, **extra):
        data = dict(patient=self.patient, report=self.report, lab_test=self.test, test_date=date(2025, 1, 2), value=' 12.00 ')
        data.update(extra)
        return LabResult.objects.create(**data)

    def payload(self, action='save'):
        return {'action': action, 'default_test_date': '2025-01-02',
                'specimen': '  Source specimen  ', 'collection_time_text': '  1403/10/13 08:30  ',
                'received_time_text': '  unknown timezone  ',
                'results-TOTAL_FORMS': '1', 'results-INITIAL_FORMS': '0',
                'results-0-lab_test': str(self.test.pk), 'results-0-value': '  <0.01  ',
                'results-0-result_kind': 'qualitative'}

    def test_patient_search_pagination_and_exact_id(self):
        for i in range(22):
            Patient.objects.create(full_name=f'Synthetic page {i:02}')
        url = reverse('patients:list')
        first = self.client.get(url, {'q': 'Synthetic page'})
        second = self.client.get(url, {'q': 'Synthetic page', 'page': 2})
        self.assertEqual(len(first.context['patients']), 20)
        self.assertEqual(len(second.context['patients']), 2)
        self.assertFalse(set(p.pk for p in first.context['patients']) & set(p.pk for p in second.context['patients']))
        self.assertContains(first, 'q=Synthetic%20page&amp;page=2')
        exact = self.client.get(url, {'q': str(self.patient.pk)})
        self.assertIn(self.patient.pk, [p.pk for p in exact.context['patients']])
        for patient in exact.context['patients']:
            self.assertTrue(patient.pk == self.patient.pk or str(self.patient.pk) in patient.full_name)

    def test_query_and_page_are_bounded(self):
        url = reverse('patients:list')
        for q in ['9' * 1000, '<script>alert(1)</script>', '۱۲۳', '%_']:
            for page in ['bad', '-1', '999999999999999999999999999999']:
                response = self.client.get(url, {'q': q, 'page': page})
                self.assertEqual(response.status_code, 200)
                self.assertLessEqual(len(response.context['query']), 200)
                self.assertNotContains(response, '<script>alert(1)</script>')

    def test_report_search_is_patient_scoped(self):
        LabReport.objects.create(patient=self.other, laboratory_name='Synthetic lab', report_number='PRIVATE')
        url = reverse('labs:report_list', args=[self.patient.pk])
        for q in ['synthetic LAB', 'SYN-45']:
            response = self.client.get(url, {'q': q})
            self.assertEqual([r.pk for r in response.context['page_obj']], [self.report.pk])
            self.assertNotContains(response, 'PRIVATE')

    def test_result_search_and_pagination_on_both_pages(self):
        for i in range(23):
            self.result(value=f'Row {i}')
        self.result(patient=self.other, report=None, value='PRIVATE')
        for url in [self.detail, reverse('patients:detail', args=[self.patient.pk])]:
            for q in ['syn45', 'search test']:
                response = self.client.get(url, {'q': q, 'page': 2})
                self.assertEqual(len(response.context['page_obj']), 3)
                self.assertNotContains(response, 'PRIVATE')
            self.assertContains(self.client.get(url, {'q': 'missing'}), 'No matching results')

    def test_search_does_not_bypass_permissions(self):
        reader = get_user_model().objects.create_user(username='limited45')
        reader.user_permissions.add(Permission.objects.get(codename='view_patient'))
        self.client.force_login(reader)
        self.result(value='PRIVATE')
        response = self.client.get(reverse('patients:detail', args=[self.patient.pk]), {'q': 'SYN45'})
        self.assertNotContains(response, 'PRIVATE')
        self.assertIsNone(response.context['page_obj'])
        self.assertEqual(self.client.get(self.detail, {'q': 'SYN45'}).status_code, 403)

    def test_metadata_review_edit_add_remove_and_save(self):
        for action in ['review', 'edit', 'remove_blank', 'add_test']:
            data = self.payload(action)
            data['add_test'] = str(self.test.pk)
            response = self.client.post(self.create, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['header_form']['specimen'].value(), data['specimen'])
            self.assertEqual(response.context['result_formset'][0]['result_kind'].value(), 'qualitative')
            self.assertEqual(LabResult.objects.count(), 0)
        self.assertEqual(self.client.post(self.create, self.payload()).status_code, 302)
        result = LabResult.objects.get()
        self.assertEqual(result.value, '  <0.01  ')
        self.assertEqual(result.result_kind, 'qualitative')
        for field in ['specimen', 'collection_time_text', 'received_time_text']:
            self.assertEqual(getattr(result.report, field), self.payload()[field])
        event = RecordAudit.objects.get(record_type='labs.labreport')
        self.assertEqual(event.after['specimen'], self.payload()['specimen'])
        self.assertEqual(RecordAudit.objects.get(record_type='labs.labresult').after['result_kind'], 'qualitative')

    def test_invalid_kind_or_metadata_never_saves(self):
        for field, value in [('results-0-result_kind', 'invented'), ('specimen', 'X' * 201),
                             ('collection_time_text', 'X' * 201), ('received_time_text', 'X' * 201),
                             ('results-0-value', '')]:
            data = self.payload()
            data[field] = value
            self.assertEqual(self.client.post(self.create, data).status_code, 200)
            self.assertFalse(LabResult.objects.exists())
            self.assertFalse(RecordAudit.objects.exists())

    def test_absent_kind_is_not_inferred_from_numeric_value(self):
        data = self.payload()
        data.pop('results-0-result_kind')
        data['results-0-value'] = '12.50'
        self.assertEqual(self.client.post(self.create, data).status_code, 302)
        self.assertEqual(LabResult.objects.get().result_kind, '')

    def test_corrections_capture_metadata_and_classification(self):
        report_url = reverse('labs:report_corrections', args=[self.patient.pk, self.report.pk])
        data = {'laboratory_name': 'Synthetic lab', 'report_number': 'SYN-45', 'report_date': '',
                'notes': '', 'specimen': '  corrected source  ', 'collection_time_text': '  literal time  ',
                'received_time_text': '', 'revision': 0, 'reason': 'Synthetic source checked'}
        self.assertEqual(self.client.post(report_url, data).status_code, 302)
        event = RecordAudit.objects.get(record_type='labs.labreport')
        self.assertEqual(event.before['specimen'], '')
        self.assertEqual(event.after['specimen'], data['specimen'])
        self.assertEqual(self.client.post(report_url, data).status_code, 409)
        result = self.result()
        url = reverse('labs:result_corrections', args=[self.patient.pk, result.pk])
        data = {'test_date': '2025-01-02', 'value': result.value, 'unit': '', 'reference_range': '',
                'notes': '', 'result_kind': 'numeric', 'revision': 0, 'reason': 'Explicit source classification'}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        event = RecordAudit.objects.get(record_type='labs.labresult')
        self.assertEqual(event.before['result_kind'], '')
        self.assertEqual(event.after['result_kind'], 'numeric')
        result.refresh_from_db()
        self.assertEqual(result.value, ' 12.00 ')

    def test_pdf_includes_metadata_and_all_pages_despite_search(self):
        self.report.specimen = 'Literal specimen'
        self.report.collection_time_text = 'Literal collection time'
        self.report.received_time_text = 'Literal receipt time'
        self.report.save()
        for i in range(21):
            self.result(value=f'ROW_{i:02}_END', result_kind='text')
        url = reverse('labs:report_pdf', args=[self.patient.pk, self.report.pk])
        response = self.client.get(url, {'q': 'missing', 'page': 2})
        self.assertEqual(response.status_code, 200)
        text = '\n'.join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
        for expected in ['Literal specimen', 'Literal collection time', 'Literal receipt time', 'Text']:
            self.assertIn(expected, text)
        for i in range(21):
            self.assertIn(f'ROW_{i:02}_END', text)
