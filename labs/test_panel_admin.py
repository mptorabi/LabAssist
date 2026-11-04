from django.contrib import admin
from django.test import TestCase

from .admin import LabPanelAdmin, LabPanelItemInline
from .models import LabPanel, LabPanelItem


class LabPanelAdminTests(TestCase):
    def setUp(self):
        self.panel_admin = LabPanelAdmin(LabPanel, admin.site)

    def test_panel_is_registered_with_expected_admin(self):
        self.assertTrue(admin.site.is_registered(LabPanel))
        self.assertIsInstance(
            admin.site.get_model_admin(LabPanel),
            LabPanelAdmin,
        )

    def test_panel_admin_configuration(self):
        self.assertEqual(
            self.panel_admin.list_display,
            (
                "code",
                "name",
                "version",
                "is_active",
                "updated_at",
            ),
        )
        self.assertEqual(
            self.panel_admin.search_fields,
            ("code", "name", "description"),
        )
        self.assertEqual(
            self.panel_admin.list_filter,
            ("is_active",),
        )
        self.assertEqual(
            self.panel_admin.readonly_fields,
            ("created_at", "updated_at"),
        )
        self.assertEqual(
            self.panel_admin.inlines,
            (LabPanelItemInline,),
        )

    def test_panel_item_inline_configuration(self):
        inline = LabPanelItemInline(LabPanel, admin.site)

        self.assertIs(inline.model, LabPanelItem)
        self.assertEqual(
            inline.fields,
            ("lab_test", "position"),
        )
        self.assertEqual(
            inline.autocomplete_fields,
            ("lab_test",),
        )
        self.assertEqual(
            inline.ordering,
            ("position", "pk"),
        )
        self.assertEqual(inline.extra, 0)