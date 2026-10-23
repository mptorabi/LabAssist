from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Patient


class PatientModelTests(TestCase):
    def test_patient_can_be_created_without_birth_date(self):
        patient = Patient(full_name="Test Patient")

        patient.full_clean()
        patient.save()
        patient.refresh_from_db()

        self.assertIsNotNone(patient.pk)
        self.assertEqual(patient.full_name, "Test Patient")
        self.assertIsNone(patient.date_of_birth)
        self.assertIsNotNone(patient.created_at)
        self.assertIsNotNone(patient.updated_at)

    def test_future_birth_date_is_rejected(self):
        patient = Patient(
            full_name="Test Patient",
            date_of_birth=timezone.localdate() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as context:
            patient.full_clean()

        self.assertIn("date_of_birth", context.exception.message_dict)

    def test_today_is_allowed_as_birth_date(self):
        patient = Patient(
            full_name="Newborn Patient",
            date_of_birth=timezone.localdate(),
        )

        patient.full_clean()
        patient.save()

        self.assertEqual(patient.date_of_birth, timezone.localdate())

    def test_empty_name_is_rejected(self):
        patient = Patient(full_name="")

        with self.assertRaises(ValidationError) as context:
            patient.full_clean()

        self.assertIn("full_name", context.exception.message_dict)

    def test_patients_can_have_identical_names(self):
        first = Patient.objects.create(full_name="Test Patient")
        second = Patient.objects.create(full_name="Test Patient")

        self.assertNotEqual(first.pk, second.pk)

    def test_string_representation_contains_name_and_id(self):
        patient = Patient.objects.create(full_name="Test Patient")

        self.assertEqual(
            str(patient),
            f"Test Patient (#{patient.pk})",
        )
from django.test import TestCase

# Create your tests here.
