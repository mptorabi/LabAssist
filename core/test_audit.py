"""Synthetic-only regression tests for attributed creation and corrections."""
from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.audit import StaleRecord, correct_record, create_record, snapshot
from core.models import RecordAudit
from labs.models import LabReport, LabResult, LabTest
from patients.models import Patient


class AuditCorrectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(username='synthetic-editor')
        cls.patient = Patient.objects.create(full_name='Synthetic patient')
        cls.other = Patient.objects.create(full_name='Other synthetic patient')
        cls.test = LabTest.objects.create(code='SYN', name='Synthetic test')
        cls.report = LabReport.objects.create(patient=cls.patient, report_number='SYN-1')
        cls.result = LabResult.objects.create(patient=cls.patient, report=cls.report,
            lab_test=cls.test, test_date=timezone.localdate(), value='12', unit='')

    def setUp(self):
        self.client.force_login(self.user)
        self.urls = {
            'patient': reverse('patients:corrections', args=[self.patient.pk]),
            'report': reverse('labs:report_corrections', args=[self.patient.pk, self.report.pk]),
            'result': reverse('labs:result_corrections', args=[self.patient.pk, self.result.pk]),
        }

    def payload(self, kind, **extra):
        data = {
            'patient': {'full_name': 'Corrected synthetic patient', 'date_of_birth': '',
                        'sex_assigned_at_birth': 'unknown'},
            'report': {'laboratory_name': 'Synthetic lab', 'report_number': 'SYN-2',
                       'report_date': '', 'notes': ''},
            'result': {'test_date': timezone.localdate().isoformat(), 'value': ' 13.00 ',
                       'unit': '', 'reference_range': '', 'notes': ''},
        }[kind]
        data.update(revision='0', reason='Compared with synthetic source')
        data.update(extra)
        return data

    def test_creation_attributed_for_each_model(self):
        records = [Patient(full_name='New synthetic'),
                   LabReport(patient=self.patient),
                   LabResult(patient=self.patient, lab_test=self.test,
                             test_date=timezone.localdate(), value=' 1.00 ')]
        for record in records:
            create_record(record, self.user)
            record.refresh_from_db()
            event = RecordAudit.objects.get(record_type=record._meta.label_lower, record_id=record.pk)
            self.assertEqual(record.created_by, self.user)
            self.assertEqual(record.revision, 0)
            self.assertEqual(event.actor, self.user)
            self.assertEqual(event.actor_name, self.user.username)
            self.assertEqual(event.action, 'create')
            self.assertEqual(event.before, {})
            self.assertEqual(event.after, snapshot(record))

    def test_each_correction_is_atomic_and_attributed(self):
        for kind in self.urls:
            record = getattr(self, kind)
            before = snapshot(record)
            created_at = record.created_at
            response = self.client.post(self.urls[kind], self.payload(kind))
            self.assertEqual(response.status_code, 302)
            record.refresh_from_db()
            event = RecordAudit.objects.get(record_type=record._meta.label_lower)
            self.assertEqual(record.revision, 1)
            self.assertIsNone(record.created_by)  # no invented legacy creator
            self.assertEqual(record.created_at, created_at)
            self.assertEqual(event.before, before)
            self.assertEqual(event.after, snapshot(record))
            self.assertEqual(event.action, 'correct')
            self.assertEqual(event.actor, self.user)
            self.assertEqual(event.reason, 'Compared with synthetic source')
            self.assertEqual(event.revision, 1)

    def test_original_creator_survives_correction_by_other_user(self):
        patient = create_record(Patient(full_name='Synthetic new'), self.user)
        other_editor = get_user_model().objects.create_superuser(username='second-editor')
        correct_record(Patient, patient.pk, 0, {'full_name': 'Synthetic corrected'}, 'Source', other_editor)
        patient.refresh_from_db()
        self.assertEqual(patient.created_by, self.user)
        self.assertEqual(RecordAudit.objects.first().actor, other_editor)

    def test_exact_result_text_and_missing_metadata_preserved(self):
        self.client.post(self.urls['result'], self.payload('result', reference_range=' < 20 ', notes='  source  '))
        self.result.refresh_from_db()
        self.assertEqual(self.result.value, ' 13.00 ')
        self.assertEqual(self.result.unit, '')
        self.assertEqual(self.result.reference_range, ' < 20 ')
        self.assertEqual(self.result.notes, '  source  ')
        self.assertEqual(self.result.lab_test, self.test)
        self.assertEqual(self.result.report, self.report)

    def test_get_does_not_write(self):
        for url in self.urls.values():
            self.assertContains(self.client.get(url), 'Unknown / legacy or external record')
        self.assertFalse(RecordAudit.objects.exists())

    def test_anonymous_redirected(self):
        self.client.logout()
        for kind, url in self.urls.items():
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url, self.payload(kind)).status_code, 302)
        self.assertFalse(RecordAudit.objects.exists())

    def test_no_permissions_forbidden(self):
        user = get_user_model().objects.create_user(username='no-permissions')
        self.client.force_login(user)
        for kind, url in self.urls.items():
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload(kind)).status_code, 403)

    def test_view_only_can_read_but_cannot_correct(self):
        user = get_user_model().objects.create_user(username='reader')
        user.user_permissions.add(*Permission.objects.filter(codename__in=[
            'view_patient', 'view_labreport', 'view_labresult']))
        self.client.force_login(user)
        for kind, url in self.urls.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'Save correction and reason')
            self.assertEqual(self.client.post(url, self.payload(kind)).status_code, 403)
        self.assertFalse(RecordAudit.objects.exists())

    def test_each_required_view_permission_enforced(self):
        required = {'patient': ['view_patient'],
                    'report': ['view_patient', 'view_labreport', 'view_labresult'],
                    'result': ['view_patient', 'view_labresult']}
        user = get_user_model().objects.create_user(username='limited')
        for kind, permissions in required.items():
            for missing in permissions:
                user.user_permissions.set(Permission.objects.filter(codename__in=[
                    code for code in permissions if code != missing] + ['change_patient', 'change_labreport', 'change_labresult']))
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.urls[kind]).status_code, 403)
                self.assertEqual(self.client.post(self.urls[kind], self.payload(kind)).status_code, 403)

    def test_wrong_patient_scope_returns_404(self):
        for name, record in [('report_corrections', self.report), ('result_corrections', self.result)]:
            url = reverse('labs:' + name, args=[self.other.pk, record.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_missing_record_returns_404(self):
        self.assertEqual(self.client.get(reverse('patients:corrections', args=[999999])).status_code, 404)

    def test_unsupported_methods_rejected(self):
        for url in self.urls.values():
            self.assertEqual(self.client.delete(url).status_code, 405)
            self.assertEqual(self.client.put(url).status_code, 405)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for kind, url in self.urls.items():
            self.assertEqual(client.post(url, self.payload(kind)).status_code, 403)
        self.assertFalse(RecordAudit.objects.exists())

    def test_reason_required_and_bounded(self):
        for reason in ['', '   ', 'x' * 1001]:
            for kind in self.urls:
                self.assertEqual(self.client.post(self.urls[kind], self.payload(kind, reason=reason)).status_code, 200)
        self.assertFalse(RecordAudit.objects.exists())
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.revision, 0)

    def test_revision_required_and_valid(self):
        for revision in ['', '-1', 'not-a-number']:
            for kind in self.urls:
                self.assertEqual(self.client.post(self.urls[kind], self.payload(kind, revision=revision)).status_code, 200)
        self.assertFalse(RecordAudit.objects.exists())

    def test_stale_form_cannot_overwrite_newer_correction(self):
        for kind in self.urls:
            self.assertEqual(self.client.post(self.urls[kind], self.payload(kind)).status_code, 302)
            response = self.client.post(self.urls[kind], self.payload(kind, reason='Stale second submission'))
            self.assertEqual(response.status_code, 409)
            self.assertContains(response, 'Reload and compare', status_code=409)
            record = getattr(self, kind)
            record.refresh_from_db()
            self.assertEqual(record.revision, 1)
        self.assertEqual(RecordAudit.objects.count(), 3)

    def test_noop_does_not_increment_or_log(self):
        with self.assertRaises(ValidationError):
            correct_record(Patient, self.patient.pk, 0, {'full_name': self.patient.full_name}, 'Source', self.user)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.revision, 0)
        self.assertFalse(RecordAudit.objects.exists())

    def test_future_dates_and_blank_names_or_values_rejected(self):
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        for kind, field, value in [('patient', 'date_of_birth', tomorrow),
                                   ('report', 'report_date', tomorrow),
                                   ('result', 'test_date', tomorrow),
                                   ('patient', 'full_name', '   '),
                                   ('result', 'value', '   ')]:
            response = self.client.post(self.urls[kind], self.payload(kind, **{field: value}))
            self.assertEqual(response.status_code, 200)
        self.assertFalse(RecordAudit.objects.exists())

    def test_invalid_service_data_rolls_back_revision(self):
        with self.assertRaises(ValidationError):
            correct_record(Patient, self.patient.pk, 0, {'full_name': ''}, 'Source', self.user)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.revision, 0)
        self.assertEqual(self.patient.full_name, 'Synthetic patient')

    def test_hidden_identity_fields_cannot_be_reassigned(self):
        self.client.post(self.urls['result'], self.payload('result', patient=self.other.pk,
            report='', lab_test='999999', created_by='999999', id='999999'))
        self.result.refresh_from_db()
        self.assertEqual(self.result.patient, self.patient)
        self.assertEqual(self.result.report, self.report)
        self.assertEqual(self.result.lab_test, self.test)
        self.assertIsNone(self.result.created_by)
        self.client.post(self.urls['report'], self.payload('report', patient=self.other.pk))
        self.report.refresh_from_db()
        self.assertEqual(self.report.patient, self.patient)

    def test_service_rejects_identity_changes(self):
        for field in ['patient_id', 'report_id', 'lab_test_id', 'created_by_id', 'revision', 'id']:
            with self.assertRaises(ValidationError):
                correct_record(LabResult, self.result.pk, 0, {field: 99}, 'Source', self.user)
        self.assertFalse(RecordAudit.objects.exists())

    def test_service_requires_change_permission(self):
        user = get_user_model().objects.create_user(username='service-reader')
        with self.assertRaises(PermissionDenied):
            correct_record(Patient, self.patient.pk, 0, {'full_name': 'No'}, 'Source', user)
        with self.assertRaises(PermissionDenied):
            create_record(Patient(full_name='No'), user)

    def test_correction_audit_failure_rolls_back_record(self):
        with patch('core.audit.log', side_effect=RuntimeError('synthetic audit failure')):
            with self.assertRaises(RuntimeError):
                correct_record(Patient, self.patient.pk, 0, {'full_name': 'Changed'}, 'Source', self.user)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.revision, 0)
        self.assertEqual(self.patient.full_name, 'Synthetic patient')
        self.assertFalse(RecordAudit.objects.exists())

    def test_creation_audit_failure_rolls_back_record(self):
        with patch('core.audit.log', side_effect=RuntimeError('synthetic audit failure')):
            with self.assertRaises(RuntimeError):
                create_record(Patient(full_name='Must roll back'), self.user)
        self.assertFalse(Patient.objects.filter(full_name='Must roll back').exists())

    def test_database_busy_returns_retry_message(self):
        with patch('core.corrections.correct_record', side_effect=OperationalError('locked')):
            response = self.client.post(self.urls['patient'], self.payload('patient'))
        self.assertContains(response, 'reload before retrying', status_code=503)
        self.assertFalse(RecordAudit.objects.exists())

    def test_history_escapes_stored_html(self):
        self.client.post(self.urls['patient'], self.payload('patient',
            full_name='<script>synthetic</script>', reason='<script>reason</script>'))
        response = self.client.get(self.urls['patient'])
        self.assertNotContains(response, '<script>synthetic</script>')
        self.assertContains(response, '&lt;script&gt;reason&lt;/script&gt;')

    def test_actor_deletion_protected_and_name_snapshot_retained(self):
        create_record(Patient(full_name='Attributed synthetic'), self.user)
        name = self.user.username
        self.user.username = 'renamed-synthetic-editor'
        self.user.save()
        self.assertEqual(RecordAudit.objects.get().actor_name, name)
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_admin_records_are_view_only_even_for_superuser(self):
        for app, model, record in [('patients', 'patient', self.patient), ('labs', 'labresult', self.result)]:
            self.assertEqual(self.client.get(reverse(f'admin:{app}_{model}_change', args=[record.pk])).status_code, 200)
            self.assertEqual(self.client.post(reverse(f'admin:{app}_{model}_change', args=[record.pk]), {}).status_code, 403)
            self.assertEqual(self.client.post(reverse(f'admin:{app}_{model}_delete', args=[record.pk]), {'post': 'yes'}).status_code, 403)
            self.assertEqual(self.client.post(reverse(f'admin:{app}_{model}_add'), {}).status_code, 403)
            self.client.post(reverse(f'admin:{app}_{model}_changelist'),
                             {'action': 'delete_selected', '_selected_action': [record.pk], 'post': 'yes'})
            self.assertTrue(type(record).objects.filter(pk=record.pk).exists())
        self.assertNotIn(RecordAudit, admin.site._registry)
        self.assertNotIn(LabReport, admin.site._registry)

    def test_patient_web_creation_audited(self):
        response = self.client.post(reverse('patients:create'), {'full_name': 'Synthetic web',
            'date_of_birth': '', 'sex_assigned_at_birth': 'unknown'})
        self.assertEqual(response.status_code, 302)
        record = Patient.objects.get(full_name='Synthetic web')
        self.assertEqual(record.created_by, self.user)
        self.assertEqual(RecordAudit.objects.get().record_id, record.pk)

    def test_result_web_creation_audited(self):
        response = self.client.post(reverse('labs:result_create', args=[self.patient.pk]),
            {'lab_test': self.test.pk, 'test_date': timezone.localdate().isoformat(),
             'value': '14', 'unit': '', 'reference_range': '', 'notes': ''})
        self.assertEqual(response.status_code, 302)
        record = LabResult.objects.exclude(pk=self.result.pk).get()
        self.assertEqual(record.created_by, self.user)
        self.assertEqual(RecordAudit.objects.get().record_id, record.pk)

    def report_payload(self):
        return {'action': 'save', 'default_test_date': timezone.localdate().isoformat(),
                'results-TOTAL_FORMS': '1', 'results-INITIAL_FORMS': '0',
                'results-0-lab_test': self.test.pk, 'results-0-value': '15',
                'results-0-test_date': '', 'results-0-unit': '',
                'results-0-reference_range': '', 'results-0-notes': ''}

    def test_report_web_creation_audits_header_and_results(self):
        response = self.client.post(reverse('labs:report_create', args=[self.patient.pk]), self.report_payload())
        self.assertEqual(response.status_code, 302)
        report = LabReport.objects.exclude(pk=self.report.pk).get()
        self.assertEqual(report.created_by, self.user)
        self.assertEqual(report.results.get().created_by, self.user)
        self.assertEqual(RecordAudit.objects.count(), 2)
        self.assertEqual(set(RecordAudit.objects.values_list('record_type', flat=True)),
                         {'labs.labreport', 'labs.labresult'})

    def test_report_audit_failure_rolls_back_entire_submission(self):
        from core.audit import log
        def fail_result(record, *args):
            if isinstance(record, LabResult):
                raise RuntimeError('synthetic result audit failure')
            return log(record, *args)
        with patch('core.audit.log', side_effect=fail_result):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('labs:report_create', args=[self.patient.pk]), self.report_payload())
        self.assertEqual(LabReport.objects.count(), 1)
        self.assertEqual(LabResult.objects.count(), 1)
        self.assertFalse(RecordAudit.objects.exists())

    def test_correction_does_not_update_sibling_results(self):
        before = snapshot(self.result)
        self.client.post(self.urls['report'], self.payload('report'))
        self.result.refresh_from_db()
        self.assertEqual(snapshot(self.result), before)
        self.assertEqual(self.result.revision, 0)

    def test_history_paginated_and_scoped(self):
        for number in range(26):
            correct_record(Patient, self.patient.pk, number,
                           {'full_name': f'Synthetic {number}'}, 'Source', self.user)
        response = self.client.get(self.urls['patient'])
        self.assertEqual(len(response.context['history']), 25)
        response = self.client.get(self.urls['patient'], {'page': 2})
        self.assertEqual(len(response.context['history']), 1)
        response = self.client.get(reverse('patients:corrections', args=[self.other.pk]))
        self.assertEqual(len(response.context['history']), 0)

    def test_navigation_links_render(self):
        for url, target in [(reverse('patients:detail', args=[self.patient.pk]), self.urls['patient']),
                            (reverse('labs:report_detail', args=[self.patient.pk, self.report.pk]), self.urls['report']),
                            (reverse('labs:result_report', args=[self.patient.pk, self.result.pk]), self.urls['result'])]:
            self.assertContains(self.client.get(url), target)
