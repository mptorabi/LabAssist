from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from patients.models import Patient
from .models import LabPanel, LabPanelItem, LabReport, LabResult, LabTest


class ReportWorkflowTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(full_name="Synthetic Patient")
        self.other = Patient.objects.create(full_name="Other Synthetic Patient")
        self.user = get_user_model().objects.create_user(username="report-test")
        for app, code in (
            ("patients", "view_patient"),
            ("labs", "view_labresult"),
            ("labs", "view_labreport"),
            ("labs", "add_labresult"),
            ("labs", "add_labreport"),
        ):
            self.user.user_permissions.add(Permission.objects.get(
                content_type__app_label=app, codename=code,
            ))
        self.client.force_login(self.user)
        self.panel = LabPanel.objects.create(code="test-entry", name="Synthetic panel")
        self.a = LabTest.objects.create(code="TEST_A", name="Synthetic A")
        self.b = LabTest.objects.create(code="TEST_B", name="Synthetic B")
        for i, test in enumerate((self.a, self.b)):
            LabPanelItem.objects.create(panel=self.panel, lab_test=test, position=i)
        self.url = reverse("labs:report_create", args=[self.patient.pk])
        self.list_url = reverse("labs:report_list", args=[self.patient.pk])
        self.day = timezone.localdate() - timedelta(days=2)

    def payload(self, action="save"):
        return {
            "panels": self.panel.code,
            "action": action,
            "laboratory_name": "Synthetic Laboratory",
            "report_number": "SYN-001",
            "report_date": "",
            "notes": "Synthetic report only",
            "default_test_date": self.day.isoformat(),
            "results-TOTAL_FORMS": "2",
            "results-INITIAL_FORMS": "2",
            "results-0-lab_test": str(self.a.pk),
            "results-0-value": " 12.50 ",
            "results-0-unit": "",
            "results-0-reference_range": "",
            "results-0-test_date": "",
            "results-0-notes": "",
            "results-1-lab_test": str(self.b.pk),
            "results-1-value": "",
            "results-1-unit": "",
            "results-1-reference_range": "",
            "results-1-test_date": "",
            "results-1-notes": "",
        }

    def assert_not_saved(self):
        self.assertEqual(LabReport.objects.count(), 0)
        self.assertEqual(LabResult.objects.count(), 0)

    def saved_report(self):
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 302)
        return LabReport.objects.get()

    def test_anonymous_redirect(self):
        self.client.logout()
        for url in (self.url, self.list_url):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_each_create_permission_required(self):
        permissions = list(self.user.user_permissions.exclude(codename="view_labreport"))
        for permission in permissions:
            with self.subTest(permission=permission.codename):
                self.user.user_permissions.remove(permission)
                self.assertEqual(self.client.post(self.url, self.payload()).status_code, 403)
                self.user.user_permissions.add(permission)
        self.assert_not_saved()

    def test_get_does_not_save(self):
        response = self.client.get(self.url, {"panels": self.panel.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["result_formset"]), 2)
        self.assert_not_saved()

    def test_overlapping_panels_deduplicate_tests(self):
        other = LabPanel.objects.create(code="overlap", name="Overlap")
        LabPanelItem.objects.create(panel=other, lab_test=self.a)
        response = self.client.get(self.url, {"panels": [self.panel.code, other.code]})
        self.assertEqual(len(response.context["result_formset"]), 2)

    def test_review_does_not_save(self):
        response = self.client.post(self.url, self.payload("review"))
        self.assertTrue(response.context["reviewing"])
        self.assertEqual(len(response.context["review_rows"]), 1)
        self.assert_not_saved()

    def test_edit_preserves_values_without_save(self):
        response = self.client.post(self.url, self.payload("edit"))
        self.assertFalse(response.context["reviewing"])
        self.assertEqual(response.context["result_formset"][0]["value"].value(), " 12.50 ")
        self.assert_not_saved()

    def test_save_links_patient_and_preserves_text_and_missing_metadata(self):
        report = self.saved_report()
        result = report.results.get()
        self.assertEqual(report.patient, self.patient)
        self.assertEqual(result.patient, self.patient)
        self.assertEqual(result.lab_test, self.a)
        self.assertEqual(result.value, " 12.50 ")
        self.assertEqual(result.unit, "")
        self.assertEqual(result.reference_range, "")
        self.assertEqual(result.test_date, self.day)
        self.assertIsNone(report.report_date)

    def test_row_date_override(self):
        data = self.payload()
        date = self.day - timedelta(days=1)
        data["results-0-test_date"] = date.isoformat()
        self.client.post(self.url, data)
        self.assertEqual(LabResult.objects.get().test_date, date)

    def test_multiple_reports_preserve_history(self):
        self.client.post(self.url, self.payload())
        self.client.post(self.url, self.payload())
        self.assertEqual(self.patient.lab_reports.count(), 2)
        self.assertEqual(self.patient.lab_results.count(), 2)

    def test_two_completed_rows(self):
        data = self.payload()
        data["results-1-value"] = "Negative"
        self.client.post(self.url, data)
        self.assertEqual(LabReport.objects.get().results.count(), 2)

    def test_empty_results_rejected(self):
        data = self.payload()
        data["results-0-value"] = " "
        self.assertEqual(self.client.post(self.url, data).status_code, 200)
        self.assert_not_saved()

    def test_partial_row_rejected(self):
        data = self.payload()
        data["results-1-unit"] = "demo"
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_future_dates_rejected(self):
        for field in ("default_test_date", "report_date", "results-0-test_date"):
            with self.subTest(field=field):
                data = self.payload()
                data[field] = (timezone.localdate() + timedelta(days=1)).isoformat()
                self.client.post(self.url, data)
                self.assert_not_saved()

    def test_unknown_panel_rejected(self):
        data = self.payload()
        data["panels"] = "unknown"
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_inactive_panel_rejected(self):
        self.panel.is_active = False
        self.panel.save()
        self.client.post(self.url, self.payload())
        self.assert_not_saved()

    def test_no_panel_rejected(self):
        data = self.payload()
        del data["panels"]
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_outside_test_rejected(self):
        outside = LabTest.objects.create(code="OUTSIDE", name="Outside")
        data = self.payload()
        data["results-0-lab_test"] = str(outside.pk)
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_inactive_test_rejected(self):
        self.a.is_active = False
        self.a.save()
        self.client.post(self.url, self.payload())
        self.assert_not_saved()

    def test_duplicate_test_rejected(self):
        data = self.payload()
        data["results-1-lab_test"] = str(self.a.pk)
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_missing_row_rejected(self):
        data = self.payload()
        data["results-TOTAL_FORMS"] = "1"
        data["results-INITIAL_FORMS"] = "1"
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_missing_management_form_rejected(self):
        data = self.payload()
        del data["results-TOTAL_FORMS"]
        self.client.post(self.url, data)
        self.assert_not_saved()

    def test_excessive_row_count_rejected(self):
        data = self.payload()
        data["results-TOTAL_FORMS"] = "100000"
        response = self.client.post(self.url, data)
        self.assertEqual(len(response.context["result_formset"].forms), 200)
        self.assert_not_saved()

    def test_invalid_action_does_not_save(self):
        self.client.post(self.url, self.payload("unexpected"))
        self.assert_not_saved()

    def test_atomic_rollback_if_second_result_fails(self):
        data = self.payload()
        data["results-1-value"] = "10"
        original_save = LabResult.save

        def fail_second(instance, *args, **kwargs):
            if instance.lab_test_id == self.b.pk:
                raise ValidationError("Synthetic failure")
            return original_save(instance, *args, **kwargs)

        with patch.object(LabResult, "save", fail_second):
            with self.assertRaises(ValidationError):
                self.client.post(self.url, data)
        self.assert_not_saved()

    def test_unsupported_create_method(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assert_not_saved()

    def test_unknown_patient(self):
        url = reverse("labs:report_create", args=[999999])
        self.assertEqual(self.client.post(url, self.payload()).status_code, 404)

    def test_list_scoped_to_patient(self):
        report = self.saved_report()
        LabReport.objects.create(patient=self.other, report_number="OTHER-PRIVATE")
        response = self.client.get(self.list_url)
        self.assertContains(response, "SYN-001")
        self.assertNotContains(response, "OTHER-PRIVATE")
        self.assertEqual(list(response.context["page_obj"]), [report])

    def test_list_pagination(self):
        for _ in range(21):
            LabReport.objects.create(patient=self.patient)
        response = self.client.get(self.list_url)
        self.assertEqual(len(response.context["page_obj"]), 20)
        response = self.client.get(self.list_url, {"page": 2})
        self.assertEqual(len(response.context["page_obj"]), 1)

    def test_detail_renders_and_escapes_input(self):
        report = self.saved_report()
        report.notes = "<script>alert(1)</script>"
        report.save()
        response = self.client.get(reverse("labs:report_detail", args=[self.patient.pk, report.pk]))
        self.assertContains(response, "12.50")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_detail_patient_mismatch_404(self):
        report = self.saved_report()
        url = reverse("labs:report_detail", args=[self.other.pk, report.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_read_permissions_required(self):
        report = self.saved_report()
        detail = reverse("labs:report_detail", args=[self.patient.pk, report.pk])
        permissions = list(self.user.user_permissions.filter(codename__startswith="view_"))
        for permission in permissions:
            with self.subTest(permission=permission.codename):
                self.user.user_permissions.remove(permission)
                for url in (self.list_url, detail):
                    self.assertEqual(self.client.get(url).status_code, 403)
                self.user.user_permissions.add(permission)

    def test_read_only_user_can_browse_not_create(self):
        report = self.saved_report()
        self.user.user_permissions.remove(*self.user.user_permissions.filter(codename__startswith="add_"))
        detail = reverse("labs:report_detail", args=[self.patient.pk, report.pk])
        self.assertEqual(self.client.get(detail).status_code, 200)
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_report_pages_reject_post(self):
        report = self.saved_report()
        detail = reverse("labs:report_detail", args=[self.patient.pk, report.pk])
        for url in (self.list_url, detail):
            self.assertEqual(self.client.post(url).status_code, 405)