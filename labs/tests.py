from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import LabTest
from django.contrib import admin


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
