from django.test import SimpleTestCase
from django.urls import reverse


class HomePageTests(SimpleTestCase):
    def test_home_page_loads_successfully(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "core/base.html")
        self.assertContains(response, "<h1>LabAssist</h1>", html=True)

    def test_home_page_uses_english_and_ltr_direction(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, 'lang="en"')
        self.assertContains(response, 'dir="ltr"')

    def test_home_page_displays_clinical_disclaimer(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(
            response,
            "This application does not replace clinical judgment.",
        )
