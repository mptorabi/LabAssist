from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    LabTest,
    LabTestAlias,
    LabTestCategory,
    LabTestUnit,
)


class LabCatalogAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username="catalog_admin",
            email="catalog@example.invalid",
            password="Synthetic-test-password-123!",
        )
        cls.category = LabTestCategory.objects.create(
            code="synthetic-category",
            name="Synthetic category",
        )
        cls.lab_test = LabTest.objects.create(
            code="SYN_A",
            name="Synthetic test A",
            category=cls.category,
            input_type=LabTest.InputType.NUMERIC,
        )
        cls.other_test = LabTest.objects.create(
            code="SYN_B",
            name="Synthetic test B",
            input_type=LabTest.InputType.TEXT,
        )
        for name in ["LookupAlias One", "LookupAlias Two"]:
            LabTestAlias.objects.create(
                lab_test=cls.lab_test,
                name=name,
            )
        LabTestUnit.objects.create(
            lab_test=cls.lab_test,
            symbol="mg/dL",
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_category_list_displays_category(self):
        response = self.client.get(
            reverse("admin:labs_labtestcategory_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Synthetic category")

    def test_test_change_page_contains_alias_and_unit_inlines(self):
        response = self.client.get(
            reverse(
                "admin:labs_labtest_change",
                args=[self.lab_test.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        inline_models = {
            inline.opts.model
            for inline in response.context["inline_admin_formsets"]
        }
        self.assertEqual(
            inline_models,
            {LabTestAlias, LabTestUnit},
        )
        self.assertContains(response, "LookupAlias One")
        self.assertContains(response, "mg/dL")

    def test_alias_search_returns_test_without_duplicates(self):
        response = self.client.get(
            reverse("admin:labs_labtest_changelist"),
            {"q": "LookupAlias"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["cl"].result_list),
            [self.lab_test],
        )

    def test_input_type_filter_returns_matching_test(self):
        response = self.client.get(
            reverse("admin:labs_labtest_changelist"),
            {"input_type__exact": "numeric"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["cl"].result_list),
            [self.lab_test],
        )

    def test_category_filter_returns_matching_test(self):
        response = self.client.get(
            reverse("admin:labs_labtest_changelist"),
            {"category__id__exact": str(self.category.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["cl"].result_list),
            [self.lab_test],
        )