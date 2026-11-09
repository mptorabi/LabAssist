from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.audit import create_record, correct_record, StaleRecord
from core.models import RecordAudit
from patients.forms import PatientForm
from patients.models import Patient


class PatientContextTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser('context-reviewer', password='test-only')

    def patient(self, **kwargs):
        return Patient(full_name='Synthetic patient', **kwargs)

    def test_optional_fields_preserve_old_workflow(self):
        form = PatientForm({'full_name': 'Synthetic', 'sex_assigned_at_birth': 'unknown'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_positive_measurements(self):
        p = self.patient(height_cm=Decimal('170.25'), weight_kg=Decimal('70.50'))
        p.full_clean()
        self.assertIsNone(p.height_measured_on)

    def test_nonpositive_measurements_rejected(self):
        for field in ('height_cm', 'weight_kg'):
            for value in ('0', '-1'):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    self.patient(**{field: Decimal(value)}).full_clean()

    def test_orphan_dates_rejected(self):
        for field in ('height_measured_on', 'weight_measured_on', 'medications_as_of', 'conditions_as_of'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.patient(**{field: date(2020, 1, 1)}).full_clean()

    def test_context_date_limits(self):
        for field, value in (('height_measured_on', 'height_cm'), ('weight_measured_on', 'weight_kg'),
                             ('medications_as_of', 'medications'), ('conditions_as_of', 'underlying_conditions')):
            for day in (date(1999, 1, 1), timezone.localdate() + timedelta(days=1)):
                with self.subTest(field=field, day=day), self.assertRaises(ValidationError):
                    self.patient(date_of_birth=date(2000, 1, 1), **{field: day, value: '1'}).full_clean()

    def test_text_length(self):
        for field in ('medications', 'underlying_conditions'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                self.patient(**{field: 'x' * 5001}).full_clean()

    def test_create_and_correct_audited(self):
        p = create_record(self.patient(weight_kg=Decimal('70')), self.actor)
        correct_record(Patient, p.pk, p.revision, {'weight_kg': Decimal('71')}, 'Transcription correction', self.actor)
        entry = RecordAudit.objects.filter(record_type='patients.patient', record_id=p.pk, action='correct').get()
        self.assertEqual(Decimal(entry.before['weight_kg']), Decimal('70'))
        self.assertEqual(Decimal(entry.after['weight_kg']), Decimal('71'))
        with self.assertRaises(StaleRecord):
            correct_record(Patient, p.pk, p.revision, {'weight_kg': Decimal('72')}, 'Stale edit', self.actor)

    def test_invalid_correction_rolls_back(self):
        p = create_record(self.patient(), self.actor)
        with self.assertRaises(ValidationError):
            correct_record(Patient, p.pk, p.revision, {'weight_kg': Decimal('-1')}, 'Invalid', self.actor)
        p.refresh_from_db()
        self.assertEqual(p.revision, 0)
        self.assertIsNone(p.weight_kg)

    def test_profile_escapes_text(self):
        p = create_record(self.patient(medications='<script>alert(1)</script>'), self.actor)
        self.client.force_login(self.actor)
        response = self.client.get(reverse('patients:detail', args=[p.pk]))
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'not automatically applied')

    def test_correction_form_contains_context(self):
        p = create_record(self.patient(), self.actor)
        self.client.force_login(self.actor)
        response = self.client.get(reverse('patients:corrections', args=[p.pk]))
        self.assertContains(response, 'name="weight_kg"')
        self.assertContains(response, 'name="medications_as_of"')

    def test_profile_requires_authentication(self):
        p = create_record(self.patient(), self.actor)
        self.assertEqual(self.client.get(reverse('patients:detail', args=[p.pk])).status_code, 302)
