from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .models import Patient
from django.contrib.auth import get_user_model
from django.urls import reverse



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
class PatientAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="testadmin",
            email="testadmin@example.com",
            password="test-only-password-482!",
        )
        self.client.force_login(self.admin_user)

    def test_patient_list_is_accessible(self):
        patient = Patient.objects.create(full_name="Admin Test Patient")

        response = self.client.get(
            reverse("admin:patients_patient_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, patient.full_name)

    def test_admin_can_create_patient(self):
        response = self.client.post(
            reverse("admin:patients_patient_add"),
            {
                "full_name": "New Test Patient",
                "date_of_birth": "",
                "_save": "Save",
            },
        )

        self.assertRedirects(
            response,
            reverse("admin:patients_patient_changelist"),
        )
        self.assertTrue(
            Patient.objects.filter(full_name="New Test Patient").exists()
        )

    def test_admin_rejects_future_birth_date(self):
        future_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse("admin:patients_patient_add"),
            {
                "full_name": "Invalid Test Patient",
                "date_of_birth": future_date.isoformat(),
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Date of birth cannot be in the future.",
        )
        self.assertFalse(
            Patient.objects.filter(full_name="Invalid Test Patient").exists()
        )

