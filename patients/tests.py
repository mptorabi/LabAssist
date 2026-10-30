from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from .models import Patient
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.models import Permission
from .forms import PatientForm





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
                "sex_assigned_at_birth": "unknown",
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

class PatientListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("patients:list")
        self.user = get_user_model().objects.create_user(
            username="patientviewer",
            password="test-only-password-482!",
        )

    def grant_view_permission(self):
        permission = Permission.objects.get(
            content_type__app_label="patients",
            content_type__model="patient",
            codename="view_patient",
        )
        self.user.user_permissions.add(permission)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        expected_url = f"{reverse('login')}?next={self.url}"
        self.assertRedirects(response, expected_url)

    def test_user_without_permission_is_denied(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_with_permission_can_view_empty_list(self):
        self.grant_view_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_list.html")
        self.assertContains(response, "No patients have been added yet.")

    def test_user_with_permission_can_view_patient(self):
        from .models import Patient

        Patient.objects.create(full_name="Synthetic Patient")
        self.grant_view_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Synthetic Patient")
        self.assertContains(response, "Not recorded")
        self.assertNotContains(
            response,
            "No patients have been added yet.",
        )
class PatientFormTests(TestCase):
    def test_valid_form_saves_patient(self):
        form = PatientForm(
            data={
                "full_name": "  Synthetic Patient  ",
                "date_of_birth": "",
                "sex_assigned_at_birth": "unknown",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        patient = form.save()

        self.assertEqual(patient.full_name, "Synthetic Patient")
        self.assertIsNone(patient.date_of_birth)
        self.assertEqual(patient.sex_assigned_at_birth, "unknown")

    def test_whitespace_only_name_is_rejected(self):
        form = PatientForm(
            data={
                "full_name": "   ",
                "date_of_birth": "",
                "sex_assigned_at_birth": "unknown",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("full_name", form.errors)

    def test_future_date_of_birth_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone

        tomorrow = timezone.localdate() + timedelta(days=1)

        form = PatientForm(
            data={
                "full_name": "Synthetic Patient",
                "date_of_birth": tomorrow.isoformat(),
                "sex_assigned_at_birth": "unknown",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)

    def test_invalid_sex_value_is_rejected(self):
        form = PatientForm(
            data={
                "full_name": "Synthetic Patient",
                "date_of_birth": "",
                "sex_assigned_at_birth": "invalid",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("sex_assigned_at_birth", form.errors)

class PatientCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("patients:create")
        self.user = get_user_model().objects.create_user(
            username="patientcreator",
            password="test-only-password-482!",
        )
        self.data = {
            "full_name": "Synthetic New Patient",
            "date_of_birth": "",
            "sex_assigned_at_birth": "unknown",
        }

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="patients",
            content_type__model="patient",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_anonymous_user_cannot_create_patient(self):
        response = self.client.post(self.url, self.data)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )
        self.assertEqual(Patient.objects.count(), 0)

    def test_view_permission_alone_cannot_create_patient(self):
        self.grant_permissions("view_patient")
        self.client.force_login(self.user)

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Patient.objects.count(), 0)

    def test_add_permission_alone_cannot_create_patient(self):
        self.grant_permissions("add_patient")
        self.client.force_login(self.user)

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Patient.objects.count(), 0)

    def test_authorized_user_can_open_form(self):
        self.grant_permissions("view_patient", "add_patient")
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_form.html")
        self.assertContains(response, "Save Patient")
        self.assertEqual(Patient.objects.count(), 0)

    def test_authorized_user_can_create_patient(self):
        self.grant_permissions("view_patient", "add_patient")
        self.client.force_login(self.user)

        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("patients:list"))
        self.assertEqual(Patient.objects.count(), 1)

        patient = Patient.objects.get()
        self.assertEqual(patient.full_name, "Synthetic New Patient")
        self.assertIsNone(patient.date_of_birth)
        self.assertEqual(patient.sex_assigned_at_birth, "unknown")

    def test_invalid_form_does_not_create_patient(self):
        self.grant_permissions("view_patient", "add_patient")
        self.client.force_login(self.user)
        self.data["full_name"] = ""

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "patients/patient_form.html")
        self.assertIn("full_name", response.context["form"].errors)
        self.assertEqual(Patient.objects.count(), 0)
class PatientDetailViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="patientviewer",
            password="test-only-password-482!",
        )
        self.patient = Patient.objects.create(
            full_name="Synthetic Detail Patient",
        )
        self.url = reverse(
            "patients:detail",
            kwargs={"pk": self.patient.pk},
        )

    def grant_view_permission(self):
        permission = Permission.objects.get(
            content_type__app_label="patients",
            content_type__model="patient",
            codename="view_patient",
        )
        self.user.user_permissions.add(permission)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_user_without_permission_is_denied(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(
            response,
            self.patient.full_name,
            status_code=403,
        )

    def test_authorized_user_can_view_patient(self):
        self.grant_view_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "patients/patient_detail.html",
        )
        self.assertEqual(response.context["patient"], self.patient)
        self.assertContains(response, self.patient.full_name)
        self.assertContains(response, "Not recorded")
        self.assertContains(response, "Unknown / Not recorded")

    def test_recorded_date_and_sex_are_displayed(self):
        from datetime import date

        self.patient.date_of_birth = date(1990, 5, 12)
        self.patient.sex_assigned_at_birth = "female"
        self.patient.save()

        self.grant_view_permission()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, "1990-05-12")
        self.assertContains(response, "Female")

    def test_missing_patient_returns_404(self):
        self.grant_view_permission()
        self.client.force_login(self.user)
        self.patient.delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_patient_list_links_to_details(self):
        self.grant_view_permission()
        self.client.force_login(self.user)

        response = self.client.get(reverse("patients:list"))

        self.assertContains(response, f'href="{self.url}"')
