from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfReader

from patients.models import Patient
from .models import LabReport, LabResult, LabTest


class PDFExportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="reader")
        self.permissions = list(Permission.objects.filter(
            codename__in=["view_patient", "view_labreport", "view_labresult"]
        ))
        self.user.user_permissions.set(self.permissions)
        self.client.force_login(self.user)
        self.patient = Patient.objects.create(full_name="Synthetic Patient")
        self.report = LabReport.objects.create(patient=self.patient, notes="Recorded <only> & unchanged")
        self.test = LabTest.objects.create(code="SYNTHETIC", name="Synthetic test")
        self.result = self.make_result(value="<0.01", report=self.report)
        self.url = reverse("labs:report_pdf", args=[self.patient.pk, self.report.pk])

    def make_result(self, **kwargs):
        defaults = dict(patient=self.patient, lab_test=self.test, test_date=date(2025, 1, 2), value="Synthetic")
        defaults.update(kwargs)
        return LabResult.objects.create(**defaults)

    def extract(self, response):
        return "\n".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)

    def test_download_recorded_data_and_privacy_headers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("attachment;", response["Content-Disposition"])
        self.assertNotIn(self.patient.full_name, response["Content-Disposition"])
        text = self.extract(response)
        for expected in ["<0.01", "Recorded <only> & unchanged", "Not recorded", "not independently", "Synthetic Patient"]:
            self.assertIn(expected, text)

    def test_anonymous_redirect(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_each_permission_required(self):
        for permission in self.permissions:
            with self.subTest(permission=permission.codename):
                self.user.user_permissions.set([p for p in self.permissions if p != permission])
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_wrong_patient_and_missing_report(self):
        other = Patient.objects.create(full_name="Other")
        self.assertEqual(self.client.get(reverse("labs:report_pdf", args=[other.pk, self.report.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("labs:report_pdf", args=[self.patient.pk, 99999])).status_code, 404)

    def test_post_disallowed(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_history_scope_and_same_day_exclusion(self):
        self.make_result(value="INCLUDED", test_date=date(2025, 1, 1))
        self.make_result(value="SAME_DAY")
        self.make_result(value="LATER", test_date=date(2025, 1, 3))
        other = Patient.objects.create(full_name="Other")
        self.make_result(value="OTHER_PATIENT", patient=other, test_date=date(2025, 1, 1))
        other_test = LabTest.objects.create(code="OTHER", name="Other test")
        self.make_result(value="OTHER_TEST", lab_test=other_test, test_date=date(2025, 1, 1))
        text = self.extract(self.client.get(self.url))
        self.assertIn("INCLUDED", text)
        for excluded in ["SAME_DAY", "LATER", "OTHER_PATIENT", "OTHER_TEST"]:
            self.assertNotIn(excluded, text)

    def test_history_limit_disclosed(self):
        for _ in range(101):
            self.make_result(test_date=date(2025, 1, 1))
        self.assertIn("Showing 100 of 101", self.extract(self.client.get(self.url)))

    def test_inconsistent_link_does_not_leak(self):
        other = Patient.objects.create(full_name="Other")
        self.make_result(patient=other, report=self.report, value="WRONG_PATIENT_SECRET")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertNotIn(b"WRONG_PATIENT_SECRET", response.content)
        self.assertIn("no-store", response["Cache-Control"])

    def test_empty_report(self):
        self.result.delete()
        self.assertIn("No linked results.", self.extract(self.client.get(self.url)))

    def test_long_multiline_notes_paginate(self):
        self.report.notes = ("Long recorded note <literal> & preserved.\n" * 180) + "END_OF_NOTES"
        self.report.save()
        response = self.client.get(self.url)
        reader = PdfReader(BytesIO(response.content))
        self.assertGreater(len(reader.pages), 2)
        self.assertIn("END_OF_NOTES", self.extract(response))
        self.assertIn("Page 2", reader.pages[1].extract_text())
        self.assertIn(f"Report ID {self.report.pk}", reader.pages[1].extract_text())

    def test_unbroken_long_value_and_notes(self):
        self.result.value = "X" * 255
        self.result.notes = "Y" * 2000 + "END_LONG_TOKEN"
        self.result.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("END_LONG_TOKEN", self.extract(response).replace("\n", ""))

    def test_history_uses_earliest_date_per_test(self):
        self.make_result(report=self.report, test_date=date(2025, 1, 4))
        self.make_result(value="BETWEEN_REPORT_DATES", test_date=date(2025, 1, 3))
        self.make_result(value="BEFORE_EARLIEST", test_date=date(2025, 1, 1))
        text = self.extract(self.client.get(self.url))
        self.assertIn("BEFORE_EARLIEST", text)
        self.assertNotIn("BETWEEN_REPORT_DATES", text)

    def test_persian_and_unit_symbols_render(self):
        self.patient.full_name = "بیمار آزمایشی"
        self.patient.save()
        self.result.unit = "µmol/L ×10⁹/L"
        self.result.save()
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_unsupported_glyph_fails_explicitly(self):
        self.result.value = "\U0001f9ec"
        self.result.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 422)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotIn("Content-Disposition", response)

    def test_export_does_not_write_or_use_network(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with patch("socket.socket", side_effect=AssertionError("Network forbidden")):
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        writes = [q["sql"] for q in queries if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))]
        self.assertEqual(writes, [])

    def test_report_page_links_to_pdf(self):
        response = self.client.get(reverse("labs:report_detail", args=[self.patient.pk, self.report.pk]))
        self.assertContains(response, self.url)
