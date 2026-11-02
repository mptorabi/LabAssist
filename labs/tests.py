from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import LabResult, LabTest
from django.contrib import admin
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from patients.models import Patient



class LabTestModelTests(TestCase):
    def test_string_representation(self):
        lab_test = LabTest(
            code="CBC_HGB",
            name="Hemoglobin",
        )

        self.assertEqual(
            str(lab_test),
            "Hemoglobin (CBC_HGB)",
        )

    def test_is_active_defaults_to_true(self):
        lab_test = LabTest.objects.create(
            code="CBC_HGB",
            name="Hemoglobin",
        )

        lab_test.refresh_from_db()

        self.assertTrue(lab_test.is_active)

    def test_code_is_required(self):
        lab_test = LabTest(code="", name="Hemoglobin")

        with self.assertRaises(ValidationError) as context:
            lab_test.full_clean()

        self.assertIn("code", context.exception.message_dict)

    def test_name_is_required(self):
        lab_test = LabTest(code="CBC_HGB", name="")

        with self.assertRaises(ValidationError) as context:
            lab_test.full_clean()

        self.assertIn("name", context.exception.message_dict)

    def test_duplicate_code_is_rejected_by_validation(self):
        LabTest.objects.create(
            code="CBC_HGB",
            name="Hemoglobin",
        )
        duplicate = LabTest(
            code="CBC_HGB",
            name="Another test",
        )

        with self.assertRaises(ValidationError) as context:
            duplicate.full_clean()

        self.assertIn("code", context.exception.message_dict)

    def test_tests_are_ordered_by_name_then_code(self):
        second = LabTest.objects.create(
            code="HGB_B",
            name="Hemoglobin",
        )
        first = LabTest.objects.create(
            code="HGB_A",
            name="Hemoglobin",
        )
        third = LabTest.objects.create(
            code="WBC",
            name="White blood cell count",
        )

        self.assertEqual(
            list(LabTest.objects.all()),
            [first, second, third],
        )

class LabTestAdminTests(TestCase):
    def test_lab_test_is_registered_in_admin(self):
        self.assertTrue(admin.site.is_registered(LabTest))
class LabResultDateValidationTests(TestCase):
    def setUp(self):
        from patients.models import Patient

        self.patient = Patient.objects.create(
            full_name="Synthetic Result Patient",
        )
        self.lab_test = LabTest.objects.create(
            code="CBC_HGB",
            name="Hemoglobin",
        )

    def make_result(self, test_date):
        from .models import LabResult

        return LabResult(
            patient=self.patient,
            lab_test=self.lab_test,
            test_date=test_date,
            value="13.5",
            unit="g/dL",
        )

    def test_today_is_allowed(self):
        from django.utils import timezone

        result = self.make_result(timezone.localdate())

        result.full_clean()

    def test_past_date_is_allowed(self):
        from datetime import timedelta
        from django.utils import timezone

        result = self.make_result(
            timezone.localdate() - timedelta(days=1)
        )

        result.full_clean()

    def test_future_date_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone

        result = self.make_result(
            timezone.localdate() + timedelta(days=1)
        )

        with self.assertRaises(ValidationError) as context:
            result.full_clean()

        self.assertIn("test_date", context.exception.message_dict)

class LabResultModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            full_name="Synthetic Result Patient",
        )
        self.lab_test = LabTest.objects.create(
            code="CBC_HGB",
            name="Hemoglobin",
        )

    def create_result(self, **overrides):
        data = {
            "patient": self.patient,
            "lab_test": self.lab_test,
            "test_date": timezone.localdate(),
            "value": "13.5",
            "unit": "g/dL",
            "reference_range": "Example range from synthetic report",
        }
        data.update(overrides)

        result = LabResult(**data)
        result.full_clean()
        result.save()
        return result

    def test_result_is_saved_with_patient_and_test(self):
        result = self.create_result()
        result.refresh_from_db()

        self.assertEqual(result.patient, self.patient)
        self.assertEqual(result.lab_test, self.lab_test)
        self.assertEqual(result.value, "13.5")
        self.assertEqual(result.unit, "g/dL")
        self.assertEqual(
            result.reference_range,
            "Example range from synthetic report",
        )
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)

    def test_reported_value_is_preserved(self):
        for value in ("13.5", "Negative", "<0.01"):
            with self.subTest(value=value):
                result = self.create_result(value=value)
                result.refresh_from_db()

                self.assertEqual(result.value, value)

    def test_unit_and_reference_range_can_be_blank(self):
        result = self.create_result(
            unit="",
            reference_range="",
        )
        result.refresh_from_db()

        self.assertEqual(result.unit, "")
        self.assertEqual(result.reference_range, "")

    def test_value_is_required(self):
        with self.assertRaises(ValidationError) as context:
            self.create_result(value="")

        self.assertIn("value", context.exception.message_dict)

    def test_patient_with_result_cannot_be_deleted(self):
        result = self.create_result()

        with self.assertRaises(ProtectedError):
            self.patient.delete()

        self.assertTrue(
            Patient.objects.filter(pk=self.patient.pk).exists()
        )
        self.assertTrue(
            LabResult.objects.filter(pk=result.pk).exists()
        )

    def test_lab_test_with_result_cannot_be_deleted(self):
        result = self.create_result()

        with self.assertRaises(ProtectedError):
            self.lab_test.delete()

        self.assertTrue(
            LabTest.objects.filter(pk=self.lab_test.pk).exists()
        )
        self.assertTrue(
            LabResult.objects.filter(pk=result.pk).exists()
        )

class LabResultAdminTests(TestCase):
    def test_lab_result_is_registered_in_admin(self):
        self.assertTrue(admin.site.is_registered(LabResult))
