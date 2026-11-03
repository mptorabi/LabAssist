from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from patients.models import Patient

from .forms import LabResultForm
from .models import LabResult, LabTest


class LabResultFormTestSelectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active_test = LabTest.objects.create(
            code="FORM_ACTIVE",
            name="Synthetic active test",
            is_active=True,
        )
        cls.inactive_test = LabTest.objects.create(
            code="FORM_INACTIVE",
            name="Synthetic inactive test",
            is_active=False,
        )

    def test_new_result_lists_only_active_tests(self):
        form = LabResultForm()

        self.assertEqual(
            list(form.fields["lab_test"].queryset),
            [self.active_test],
        )

    def test_active_test_is_accepted_by_field(self):
        form = LabResultForm()

        selected_test = form.fields["lab_test"].clean(
            str(self.active_test.pk)
        )

        self.assertEqual(selected_test, self.active_test)

    def test_inactive_test_is_rejected_by_field(self):
        form = LabResultForm()

        with self.assertRaises(ValidationError) as context:
            form.fields["lab_test"].clean(
                str(self.inactive_test.pk)
            )

        self.assertEqual(
            context.exception.code,
            "invalid_choice",
        )

class LabResultFormEditTestSelectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patient = Patient.objects.create(
            full_name="Synthetic Patient",
        )
        cls.recorded_test = LabTest.objects.create(
            code="EDIT_RECORDED",
            name="Synthetic recorded test",
            is_active=True,
        )
        cls.result = LabResult.objects.create(
            patient=cls.patient,
            lab_test=cls.recorded_test,
            test_date=timezone.localdate(),
            value="Example result",
        )

        # Simulate deactivation after a result was recorded.
        cls.recorded_test.is_active = False
        cls.recorded_test.save(update_fields=["is_active"])

        cls.other_inactive_test = LabTest.objects.create(
            code="EDIT_OTHER_INACTIVE",
            name="Synthetic other inactive test",
            is_active=False,
        )
        cls.active_test = LabTest.objects.create(
            code="EDIT_ACTIVE",
            name="Synthetic active test",
            is_active=True,
        )

    def test_edit_keeps_recorded_inactive_test_available(self):
        form = LabResultForm(instance=self.result)
        field = form.fields["lab_test"]

        self.assertSetEqual(
            set(field.queryset.values_list("pk", flat=True)),
            {self.recorded_test.pk, self.active_test.pk},
        )
        self.assertEqual(
            field.clean(str(self.recorded_test.pk)),
            self.recorded_test,
        )

    def test_edit_rejects_other_inactive_test(self):
        form = LabResultForm(instance=self.result)

        with self.assertRaises(ValidationError) as context:
            form.fields["lab_test"].clean(
                str(self.other_inactive_test.pk)
            )

        self.assertEqual(
            context.exception.code,
            "invalid_choice",
        )