from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse



class HomePageTests(SimpleTestCase):
    def test_home_page_loads_successfully(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "core/base.html")
        self.assertContains(
            response,
            '<h1 id="home-title">LabAssist</h1>',
            html=True,
        )

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
class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "test-only-password-482!"
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password=self.password,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Sign In")

    def test_valid_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(self.user.pk),
        )

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": self.user.username,
                "password": "incorrect-password",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_home_displays_logged_in_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Signed in as testuser")
        self.assertContains(response, "Sign Out")

    def test_logout_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

        home_response = self.client.get(reverse("core:home"))

        self.assertContains(home_response, "Sign In")
        self.assertNotContains(home_response, "Signed in as")

    def test_logout_does_not_accept_get_requests(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
