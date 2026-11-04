from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from patients.models import Patient

from .models import LabResult, LabTest, LabTestAlias


class LabResultCatalogSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="catalog_entry_user",
            password="Synthetic-test-password-123!",
        )

        for app_label, codename in [
            ("patients", "view_patient"),
            ("labs", "view_labresult"),
            ("labs", "add_labresult"),
        ]:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            cls.user.user_permissions.add(permission)

        cls.patient = Patient.objects.create(
            full_name="Synthetic Search Patient",
        )
        cls.active_test = LabTest.objects.create(
            code="SEARCH_ACTIVE",
            name="Synthetic active search test",
            is_active=True,
        )
        cls.inactive_test = LabTest.objects.create(
            code="SEARCH_INACTIVE",
            name="Synthetic inactive search test",
            is_active=False,
        )

        LabTestAlias.objects.create(
            lab_test=cls.active_test,
            name="SyntheticLookup",
        )
        LabTestAlias.objects.create(
            lab_test=cls.inactive_test,
            name="InactiveLookup",
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse(
            "labs:result_create",
            kwargs={"patient_pk": self.patient.pk},
        )

    def test_search_data_contains_active_test_and_alias(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["test_search_data"],
            [
                {
                    "id": str(self.active_test.pk),
                    "code": "SEARCH_ACTIVE",
                    "name": "Synthetic active search test",
                    "aliases": ["SyntheticLookup"],
                },
            ],
        )
        self.assertContains(
            response,
            'id="lab-test-search-data"',
        )
        self.assertContains(
            response,
            "labs/js/lab_test_search.js",
        )

    def test_search_data_excludes_inactive_tests(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        test_ids = {
            item["id"]
            for item in response.context["test_search_data"]
        }

        self.assertNotIn(str(self.inactive_test.pk), test_ids)
        self.assertNotContains(response, "InactiveLookup")

    def test_invalid_post_keeps_search_data_and_entered_values(self):
        response = self.client.post(
            self.url,
            {
                "lab_test": str(self.active_test.pk),
                "test_date": "",
                "value": "<0.01",
                "unit": "example-unit",
                "reference_range": "",
                "notes": "Synthetic note",
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form"]

        self.assertIn("test_date", form.errors)
        self.assertEqual(
            form["lab_test"].value(),
            str(self.active_test.pk),
        )
        self.assertEqual(form["value"].value(), "<0.01")
        self.assertEqual(form["unit"].value(), "example-unit")

        self.assertEqual(
            [item["id"] for item in response.context["test_search_data"]],
            [str(self.active_test.pk)],
        )
        self.assertEqual(LabResult.objects.count(), 0)
