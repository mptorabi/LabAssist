from django.db import IntegrityError, transaction
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import (
    LabReport,
    LabResult,
    LabTest,
    LabTestAlias,
    LabTestCategory,
    LabTestUnit
)
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

class LabResultFormTests(TestCase):
    def setUp(self):
        from labs.models import LabTest

        self.lab_test = LabTest.objects.create(
            code="SYNTHETIC_FORM_TEST",
            name="Synthetic Form Test",
        )

    def make_data(self, **changes):
        from django.utils import timezone

        data = {
            "lab_test": str(self.lab_test.pk),
            "test_date": timezone.localdate().isoformat(),
            "value": "13.5",
            "unit": "",
            "reference_range": "",
            "notes": "",
        }
        data.update(changes)
        return data

    def test_valid_form_allows_blank_optional_fields(self):
        from labs.forms import LabResultForm

        form = LabResultForm(data=self.make_data())

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["unit"], "")
        self.assertEqual(form.cleaned_data["reference_range"], "")
        self.assertEqual(form.cleaned_data["notes"], "")

    def test_reported_values_remain_text(self):
        from labs.forms import LabResultForm

        for value in ("13.5", "Negative", "<0.01"):
            with self.subTest(value=value):
                form = LabResultForm(data=self.make_data(value=value))

                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["value"], value)
                self.assertIsInstance(form.cleaned_data["value"], str)

    def test_future_test_date_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        from labs.forms import LabResultForm

        tomorrow = timezone.localdate() + timedelta(days=1)
        form = LabResultForm(
            data=self.make_data(test_date=tomorrow.isoformat())
        )

        self.assertFalse(form.is_valid())
        self.assertIn("test_date", form.errors)

    def test_required_fields_cannot_be_blank(self):
        from labs.forms import LabResultForm

        for field in ("lab_test", "test_date", "value"):
            with self.subTest(field=field):
                form = LabResultForm(
                    data=self.make_data(**{field: ""})
                )

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_whitespace_only_value_is_rejected(self):
        from labs.forms import LabResultForm

        form = LabResultForm(data=self.make_data(value="   "))

        self.assertFalse(form.is_valid())
        self.assertIn("value", form.errors)

    def test_patient_is_not_an_editable_form_field(self):
        from labs.forms import LabResultForm

        form = LabResultForm()

        self.assertNotIn("patient", form.fields)

class LabResultCreateViewTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        from django.urls import reverse
        from django.utils import timezone
        from patients.models import Patient
        from labs.models import LabTest

        self.user = get_user_model().objects.create_user(
            username="syntheticresultcreator",
        )

        for app_label, model, codename in (
            ("patients", "patient", "view_patient"),
            ("labs", "labresult", "view_labresult"),
            ("labs", "labresult", "add_labresult"),
        ):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    content_type__model=model,
                    codename=codename,
                )
            )

        self.patient = Patient.objects.create(
            full_name="Synthetic Form Patient",
        )
        self.other_patient = Patient.objects.create(
            full_name="Synthetic Other Patient",
        )
        self.lab_test = LabTest.objects.create(
            code="SYNTHETIC_CREATE_TEST",
            name="Synthetic Create Test",
        )
        self.url = reverse(
            "labs:result_create",
            kwargs={"patient_pk": self.patient.pk},
        )
        self.data = {
            "lab_test": str(self.lab_test.pk),
            "test_date": timezone.localdate().isoformat(),
            "value": "<0.01",
            "unit": "",
            "reference_range": "",
            "notes": "Synthetic view test",
        }

    def test_authorized_user_can_open_form(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "labs/lab_result_form.html",
        )
        self.assertContains(response, "Reported value")
        self.assertEqual(response.context["patient"], self.patient)

    def test_valid_result_is_saved_for_patient_in_url(self):
        from django.urls import reverse
        from labs.models import LabResult

        self.client.force_login(self.user)

        # A submitted patient ID must not override the URL's patient.
        self.data["patient"] = str(self.other_patient.pk)

        response = self.client.post(self.url, self.data)

        self.assertRedirects(
            response,
            reverse("patients:detail", kwargs={"pk": self.patient.pk}),
        )
        self.assertEqual(LabResult.objects.count(), 1)

        result = LabResult.objects.get()
        self.assertEqual(result.patient_id, self.patient.pk)
        self.assertEqual(result.lab_test_id, self.lab_test.pk)
        self.assertEqual(result.value, "<0.01")
        self.assertEqual(result.unit, "")
        self.assertEqual(result.reference_range, "")
        self.assertEqual(result.notes, "Synthetic view test")

    def test_future_date_does_not_save_result(self):
        from datetime import timedelta
        from django.utils import timezone
        from labs.models import LabResult

        self.client.force_login(self.user)
        tomorrow = timezone.localdate() + timedelta(days=1)
        self.data["test_date"] = tomorrow.isoformat()

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "labs/lab_result_form.html",
        )
        self.assertIn("test_date", response.context["form"].errors)
        self.assertEqual(LabResult.objects.count(), 0)

    def test_anonymous_user_cannot_open_or_submit_form(self):
        from django.urls import reverse
        from labs.models import LabResult

        for method in ("get", "post"):
            with self.subTest(method=method):
                if method == "get":
                    response = self.client.get(self.url)
                else:
                    response = self.client.post(self.url, self.data)

                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={self.url}",
                )
                self.assertEqual(LabResult.objects.count(), 0)

    def test_each_required_permission_is_enforced(self):
        from django.contrib.auth.models import Permission
        from labs.models import LabResult

        self.client.force_login(self.user)

        for app_label, model, codename in (
            ("patients", "patient", "view_patient"),
            ("labs", "labresult", "view_labresult"),
            ("labs", "labresult", "add_labresult"),
        ):
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                content_type__model=model,
                codename=codename,
            )
            self.user.user_permissions.remove(permission)

            try:
                for method in ("get", "post"):
                    with self.subTest(
                        missing_permission=codename,
                        method=method,
                    ):
                        if method == "get":
                            response = self.client.get(self.url)
                        else:
                            response = self.client.post(
                                self.url,
                                self.data,
                            )

                        self.assertEqual(response.status_code, 403)
                        self.assertNotContains(
                            response,
                            self.patient.full_name,
                            status_code=403,
                        )
                        self.assertEqual(LabResult.objects.count(), 0)
            finally:
                self.user.user_permissions.add(permission)

    def test_missing_patient_returns_404_without_saving(self):
        from labs.models import LabResult

        self.client.force_login(self.user)
        self.patient.delete()

        for method in ("get", "post"):
            with self.subTest(method=method):
                if method == "get":
                    response = self.client.get(self.url)
                else:
                    response = self.client.post(self.url, self.data)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(LabResult.objects.count(), 0)

class LabResultReportViewTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        from django.urls import reverse
        from django.utils import timezone
        from patients.models import Patient
        from labs.models import LabTest, LabResult

        self.user = get_user_model().objects.create_user(
            username="syntheticreportviewer",
        )

        for app_label, model, codename in (
            ("patients", "patient", "view_patient"),
            ("labs", "labresult", "view_labresult"),
        ):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    content_type__model=model,
                    codename=codename,
                )
            )

        self.patient = Patient.objects.create(
            full_name="Synthetic Report Patient",
        )
        self.other_patient = Patient.objects.create(
            full_name="Synthetic Other Report Patient",
        )
        self.lab_test = LabTest.objects.create(
            code="SYNTH_REPORT",
            name="Synthetic Report Test",
        )
        self.result = LabResult.objects.create(
            patient=self.patient,
            lab_test=self.lab_test,
            test_date=timezone.localdate(),
            value="<0.01",
            unit="synthetic-unit",
            reference_range="synthetic-range",
            notes="Synthetic first line.\nSynthetic second line.",
        )

        self.url = reverse(
            "labs:result_report",
            kwargs={
                "patient_pk": self.patient.pk,
                "result_pk": self.result.pk,
            },
        )
        self.client.force_login(self.user)

    def test_authorized_user_can_view_recorded_result_report(self):
        from django.urls import reverse

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "labs/lab_result_report.html",
        )
        self.assertEqual(response.context["patient"], self.patient)
        self.assertEqual(response.context["result"], self.result)

        for text in (
            self.patient.full_name,
            self.lab_test.name,
            self.lab_test.code,
            self.result.test_date.isoformat(),
            "&lt;0.01",
            "synthetic-unit",
            "synthetic-range",
            "Synthetic first line.<br>Synthetic second line.",
            "No automated clinical interpretation has been performed.",
        ):
            with self.subTest(text=text):
                self.assertContains(response, text)

        self.assertNotContains(
            response,
            "No unit is recorded for this result.",
        )
        self.assertNotContains(
            response,
            "No reference range is recorded for this result.",
        )

        history_url = reverse(
            "patients:lab_history",
            kwargs={
                "pk": self.patient.pk,
                "lab_test_pk": self.lab_test.pk,
            },
        )
        patient_url = reverse(
            "patients:detail",
            kwargs={"pk": self.patient.pk},
        )
        self.assertContains(response, f'href="{history_url}"')
        self.assertContains(response, f'href="{patient_url}"')

    def test_missing_optional_data_is_explicitly_reported(self):
        self.result.unit = ""
        self.result.reference_range = ""
        self.result.notes = ""
        self.result.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not recorded")
        self.assertContains(
            response,
            "No unit is recorded for this result.",
        )
        self.assertContains(
            response,
            "No reference range is recorded for this result.",
        )
        self.assertEqual(response.context["result"].unit, "")
        self.assertEqual(response.context["result"].reference_range, "")

    def test_result_under_another_patient_url_returns_404(self):
        from django.urls import reverse

        wrong_patient_url = reverse(
            "labs:result_report",
            kwargs={
                "patient_pk": self.other_patient.pk,
                "result_pk": self.result.pk,
            },
        )

        response = self.client.get(wrong_patient_url)

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(
            response,
            self.patient.full_name,
            status_code=404,
        )
        self.assertNotContains(
            response,
            "Synthetic first line.",
            status_code=404,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        from django.urls import reverse

        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.url}",
        )

    def test_each_required_permission_is_enforced(self):
        from django.contrib.auth.models import Permission

        for app_label, model, codename in (
            ("patients", "patient", "view_patient"),
            ("labs", "labresult", "view_labresult"),
        ):
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                content_type__model=model,
                codename=codename,
            )
            self.user.user_permissions.remove(permission)

            try:
                with self.subTest(missing_permission=codename):
                    response = self.client.get(self.url)

                    self.assertEqual(response.status_code, 403)
                    self.assertNotContains(
                        response,
                        self.patient.full_name,
                        status_code=403,
                    )
                    self.assertNotContains(
                        response,
                        self.lab_test.name,
                        status_code=403,
                    )
                    self.assertNotContains(
                        response,
                        "Synthetic first line.",
                        status_code=403,
                    )
            finally:
                self.user.user_permissions.add(permission)

    def test_missing_result_returns_404(self):
        self.result.delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_report_escapes_html_in_notes(self):
        self.result.notes = (
            "Synthetic note.\n"
            "<script>alert('synthetic')</script>"
        )
        self.result.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Synthetic note.<br>")
        self.assertContains(response, "&lt;script&gt;")
        self.assertContains(response, "&lt;/script&gt;")
        self.assertNotContains(response, "<script>")

class LabReportModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            full_name="Synthetic Report Patient",
        )
        self.other_patient = Patient.objects.create(
            full_name="Synthetic Other Report Patient",
        )
        self.lab_test = LabTest.objects.create(
            code="SYNTHETIC_REPORT_TEST",
            name="Synthetic Report Test",
        )

    def make_result(self, report=None):
        return LabResult(
            patient=self.patient,
            report=report,
            lab_test=self.lab_test,
            test_date=timezone.localdate(),
            value="<0.01",
        )

    def test_report_allows_blank_optional_fields(self):
        report = LabReport(patient=self.patient)

        report.full_clean()
        report.save()
        report.refresh_from_db()

        self.assertEqual(report.patient_id, self.patient.pk)
        self.assertIsNone(report.report_date)
        self.assertEqual(report.laboratory_name, "")
        self.assertEqual(report.report_number, "")
        self.assertEqual(report.notes, "")

    def test_future_report_date_is_rejected(self):
        report = LabReport(
            patient=self.patient,
            report_date=timezone.localdate() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as context:
            report.full_clean()

        self.assertIn("report_date", context.exception.message_dict)

    def test_today_and_past_report_dates_are_allowed(self):
        today = timezone.localdate()

        for report_date in (today, today - timedelta(days=1)):
            with self.subTest(report_date=report_date):
                report = LabReport(
                    patient=self.patient,
                    report_date=report_date,
                )

                report.full_clean()
                report.save()
                report.refresh_from_db()

                self.assertEqual(report.report_date, report_date)

    def test_result_can_be_saved_without_report(self):
        result = self.make_result()

        result.full_clean()
        result.save()
        result.refresh_from_db()

        self.assertIsNone(result.report_id)
        self.assertEqual(result.patient_id, self.patient.pk)
        self.assertEqual(result.value, "<0.01")

    def test_result_accepts_report_for_same_patient(self):
        report = LabReport.objects.create(patient=self.patient)
        result = self.make_result(report=report)

        result.full_clean()
        result.save()
        result.refresh_from_db()

        self.assertEqual(result.report_id, report.pk)
        self.assertEqual(list(report.results.all()), [result])

    def test_result_rejects_report_for_different_patient(self):
        report = LabReport.objects.create(patient=self.other_patient)
        result = self.make_result(report=report)

        with self.assertRaises(ValidationError) as context:
            result.full_clean()

        self.assertIn("report", context.exception.message_dict)

    def test_report_with_result_cannot_be_deleted(self):
        report = LabReport.objects.create(patient=self.patient)
        result = self.make_result(report=report)
        result.full_clean()
        result.save()
        report_pk = report.pk

        with self.assertRaises(ProtectedError):
            report.delete()

        self.assertTrue(
            LabReport.objects.filter(pk=report_pk).exists()
        )
        result.refresh_from_db()
        self.assertEqual(result.report_id, report_pk)
    def test_report_patient_change_is_rejected_when_results_exist(self):
        report = LabReport.objects.create(patient=self.patient)
        result = self.make_result(report=report)
        result.full_clean()
        result.save()

        report.patient = self.other_patient

        with self.assertRaises(ValidationError) as context:
            report.full_clean()

        self.assertIn("patient", context.exception.message_dict)

        report.refresh_from_db()
        result.refresh_from_db()
        self.assertEqual(report.patient_id, self.patient.pk)
        self.assertEqual(result.patient_id, self.patient.pk)

    def test_report_patient_can_change_when_no_results_exist(self):
        report = LabReport.objects.create(patient=self.patient)
        report.patient = self.other_patient

        report.full_clean()
        report.save()
        report.refresh_from_db()

        self.assertEqual(report.patient_id, self.other_patient.pk)

    def test_report_notes_can_change_when_results_exist(self):
        report = LabReport.objects.create(patient=self.patient)
        result = self.make_result(report=report)
        result.full_clean()
        result.save()

        report.notes = "Updated synthetic report notes."
        report.full_clean()
        report.save()
        report.refresh_from_db()

        self.assertEqual(
            report.notes,
            "Updated synthetic report notes.",
        )
        self.assertEqual(report.patient_id, self.patient.pk)
class LabTestCategoryModelTests(TestCase):
    def setUp(self):
        self.category = LabTestCategory.objects.create(
            code="synthetic-category",
            name="Synthetic Category",
        )

    def test_category_string_and_active_default(self):
        self.assertEqual(str(self.category), "Synthetic Category")
        self.assertTrue(self.category.is_active)

    def test_category_code_must_be_unique(self):
        duplicate = LabTestCategory(
            code=self.category.code,
            name="Another Synthetic Category",
        )

        with self.assertRaises(ValidationError) as context:
            duplicate.full_clean()

        self.assertIn("code", context.exception.message_dict)

    def test_lab_test_can_be_saved_without_category(self):
        lab_test = LabTest(
            code="SYNTHETIC_UNCATEGORIZED",
            name="Synthetic Uncategorized Test",
        )

        lab_test.full_clean()
        lab_test.save()
        lab_test.refresh_from_db()

        self.assertIsNone(lab_test.category_id)

    def test_lab_test_can_belong_to_category(self):
        lab_test = LabTest(
            code="SYNTHETIC_CATEGORIZED",
            name="Synthetic Categorized Test",
            category=self.category,
        )

        lab_test.full_clean()
        lab_test.save()
        lab_test.refresh_from_db()

        self.assertEqual(lab_test.category_id, self.category.pk)
        self.assertEqual(
            list(self.category.lab_tests.all()),
            [lab_test],
        )

    def test_category_with_lab_test_cannot_be_deleted(self):
        lab_test = LabTest.objects.create(
            code="SYNTHETIC_PROTECTED_CATEGORY",
            name="Synthetic Protected Category Test",
            category=self.category,
        )
        category_pk = self.category.pk

        with self.assertRaises(ProtectedError):
            self.category.delete()

        self.assertTrue(
            LabTestCategory.objects.filter(pk=category_pk).exists()
        )
        lab_test.refresh_from_db()
        self.assertEqual(lab_test.category_id, category_pk)


class LabTestAliasModelTests(TestCase):
    def setUp(self):
        self.lab_test = LabTest.objects.create(
            code="SYNTHETIC_ALIAS_TEST",
            name="Synthetic Alias Test",
        )

    def test_alias_is_saved_for_lab_test(self):
        alias = LabTestAlias(
            lab_test=self.lab_test,
            name="Synthetic alternative name",
        )

        alias.full_clean()
        alias.save()
        alias.refresh_from_db()

        self.assertEqual(alias.lab_test_id, self.lab_test.pk)
        self.assertEqual(
            list(self.lab_test.aliases.all()),
            [alias],
        )
        self.assertEqual(
            str(alias),
            "Synthetic alternative name (SYNTHETIC_ALIAS_TEST)",
        )

    def test_alias_name_is_required(self):
        alias = LabTestAlias(
            lab_test=self.lab_test,
            name="",
        )

        with self.assertRaises(ValidationError) as context:
            alias.full_clean()

        self.assertIn("name", context.exception.message_dict)

    def test_duplicate_alias_for_same_test_fails_validation(self):
        LabTestAlias.objects.create(
            lab_test=self.lab_test,
            name="Synthetic shared alias",
        )
        duplicate = LabTestAlias(
            lab_test=self.lab_test,
            name="Synthetic shared alias",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_duplicate_alias_for_same_test_is_blocked_by_database(self):
        LabTestAlias.objects.create(
            lab_test=self.lab_test,
            name="Synthetic shared alias",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LabTestAlias.objects.create(
                    lab_test=self.lab_test,
                    name="Synthetic shared alias",
                )

        self.assertEqual(self.lab_test.aliases.count(), 1)

    def test_same_alias_can_belong_to_different_tests(self):
        other_test = LabTest.objects.create(
            code="SYNTHETIC_OTHER_ALIAS_TEST",
            name="Synthetic Other Alias Test",
        )
        LabTestAlias.objects.create(
            lab_test=self.lab_test,
            name="Synthetic shared alias",
        )
        other_alias = LabTestAlias(
            lab_test=other_test,
            name="Synthetic shared alias",
        )

        other_alias.full_clean()
        other_alias.save()

        self.assertEqual(
            LabTestAlias.objects.filter(
                name="Synthetic shared alias",
            ).count(),
            2,
        )

    def test_deleting_unused_lab_test_deletes_its_aliases(self):
        alias = LabTestAlias.objects.create(
            lab_test=self.lab_test,
            name="Synthetic alternative name",
        )
        alias_pk = alias.pk

        self.lab_test.delete()

        self.assertFalse(
            LabTestAlias.objects.filter(pk=alias_pk).exists()
        )
class LabTestInputTypeModelTests(TestCase):
    def test_default_input_type_is_text(self):
        lab_test = LabTest(
            code="INPUT_DEFAULT",
            name="Synthetic default test",
        )

        self.assertEqual(lab_test.input_type, LabTest.InputType.TEXT)

    def test_default_input_type_is_saved(self):
        lab_test = LabTest.objects.create(
            code="INPUT_SAVED",
            name="Synthetic saved test",
        )

        lab_test.refresh_from_db()

        self.assertEqual(lab_test.input_type, "text")

    def test_all_supported_input_types_validate_and_save(self):
        for input_type in LabTest.InputType.values:
            with self.subTest(input_type=input_type):
                lab_test = LabTest(
                    code=f"INPUT_{input_type.upper()}",
                    name=f"Synthetic {input_type} test",
                    input_type=input_type,
                )

                lab_test.full_clean()
                lab_test.save()
                lab_test.refresh_from_db()

                self.assertEqual(lab_test.input_type, input_type)

    def test_unknown_input_type_is_rejected_by_validation(self):
        lab_test = LabTest(
            code="INPUT_INVALID",
            name="Synthetic invalid test",
            input_type="unsupported",
        )

        with self.assertRaises(ValidationError) as context:
            lab_test.full_clean()

        self.assertIn("input_type", context.exception.message_dict)

    def test_blank_input_type_is_rejected_by_validation(self):
        lab_test = LabTest(
            code="INPUT_BLANK",
            name="Synthetic blank test",
            input_type="",
        )

        with self.assertRaises(ValidationError) as context:
            lab_test.full_clean()

        self.assertIn("input_type", context.exception.message_dict)

class LabTestUnitModelTests(TestCase):
    def setUp(self):
        self.lab_test = LabTest.objects.create(
            code="UNIT_TEST_A",
            name="Synthetic unit test A",
        )

    def test_unit_validates_and_saves(self):
        unit = LabTestUnit(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        unit.full_clean()
        unit.save()
        unit.refresh_from_db()

        self.assertEqual(unit.symbol, "mg/dL")
        self.assertEqual(unit.lab_test_id, self.lab_test.pk)

    def test_unit_is_active_by_default(self):
        unit = LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        unit.refresh_from_db()

        self.assertTrue(unit.is_active)

    def test_string_representation(self):
        unit = LabTestUnit(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        self.assertEqual(str(unit), "mg/dL (UNIT_TEST_A)")

    def test_multiple_units_are_allowed_for_one_test(self):
        for symbol in ["mg/dL", "mmol/L"]:
            LabTestUnit.objects.create(
                lab_test=self.lab_test,
                symbol=symbol,
            )

        self.assertEqual(self.lab_test.suggested_units.count(), 2)

    def test_same_symbol_is_allowed_for_different_tests(self):
        other_test = LabTest.objects.create(
            code="UNIT_TEST_B",
            name="Synthetic unit test B",
        )
        LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )
        other_unit = LabTestUnit(
            lab_test=other_test,
            symbol="mg/dL",
        )

        other_unit.full_clean()
        other_unit.save()

        self.assertEqual(LabTestUnit.objects.count(), 2)

    def test_duplicate_unit_is_rejected_by_validation(self):
        LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )
        duplicate = LabTestUnit(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_duplicate_unit_is_rejected_by_database(self):
        LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LabTestUnit.objects.create(
                    lab_test=self.lab_test,
                    symbol="mg/dL",
                )

        self.assertEqual(self.lab_test.suggested_units.count(), 1)

    def test_blank_symbol_is_rejected_by_validation(self):
        unit = LabTestUnit(
            lab_test=self.lab_test,
            symbol="",
        )

        with self.assertRaises(ValidationError) as context:
            unit.full_clean()

        self.assertIn("symbol", context.exception.message_dict)

    def test_unit_can_be_deactivated(self):
        unit = LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )

        unit.is_active = False
        unit.full_clean()
        unit.save()
        unit.refresh_from_db()

        self.assertFalse(unit.is_active)
        self.assertEqual(self.lab_test.suggested_units.count(), 1)

    def test_deleting_unused_test_deletes_its_suggested_units(self):
        unit = LabTestUnit.objects.create(
            lab_test=self.lab_test,
            symbol="mg/dL",
        )
        unit_pk = unit.pk

        self.lab_test.delete()

        self.assertFalse(
            LabTestUnit.objects.filter(pk=unit_pk).exists()
        )
