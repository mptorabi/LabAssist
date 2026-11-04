from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import LabPanel, LabPanelItem, LabTest


class LabPanelModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.panel = LabPanel.objects.create(
            code="synthetic-panel",
            name="Synthetic Panel",
        )
        cls.first_test = LabTest.objects.create(
            code="SYN_PANEL_A",
            name="Synthetic test A",
        )
        cls.second_test = LabTest.objects.create(
            code="SYN_PANEL_B",
            name="Synthetic test B",
        )

    def test_panel_defaults(self):
        self.assertEqual(self.panel.version, 1)
        self.assertTrue(self.panel.is_active)
        self.assertEqual(self.panel.description, "")
        self.assertIsNotNone(self.panel.created_at)
        self.assertIsNotNone(self.panel.updated_at)

    def test_panel_string_representation(self):
        self.assertEqual(
            str(self.panel),
            "Synthetic Panel (synthetic-panel)",
        )

    def test_panel_code_must_be_unique(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LabPanel.objects.create(
                    code=self.panel.code,
                    name="Another panel",
                )

    def test_panel_version_zero_fails_validation(self):
        self.panel.version = 0

        with self.assertRaises(ValidationError):
            self.panel.full_clean()

    def test_panel_version_zero_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LabPanel.objects.filter(pk=self.panel.pk).update(
                    version=0,
                )

    def test_item_string_representation(self):
        item = LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
            position=10,
        )

        self.assertEqual(
            str(item),
            "synthetic-panel: SYN_PANEL_A",
        )

    def test_items_are_ordered_by_position(self):
        later_item = LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
            position=20,
        )
        earlier_item = LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.second_test,
            position=10,
        )

        self.assertEqual(
            list(self.panel.items.all()),
            [earlier_item, later_item],
        )

    def test_duplicate_test_in_same_panel_fails_validation(self):
        LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )
        duplicate = LabPanelItem(
            panel=self.panel,
            lab_test=self.first_test,
            position=30,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_duplicate_test_in_same_panel_is_rejected_by_database(self):
        LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                LabPanelItem.objects.create(
                    panel=self.panel,
                    lab_test=self.first_test,
                    position=30,
                )

    def test_same_test_can_belong_to_different_panels(self):
        other_panel = LabPanel.objects.create(
            code="synthetic-other",
            name="Synthetic Other Panel",
        )

        LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )
        other_item = LabPanelItem(
            panel=other_panel,
            lab_test=self.first_test,
        )
        other_item.full_clean()
        other_item.save()

        self.assertEqual(
            LabPanelItem.objects.filter(
                lab_test=self.first_test,
            ).count(),
            2,
        )

    def test_deleting_panel_removes_items_but_keeps_tests(self):
        item = LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )
        item_pk = item.pk
        test_pk = self.first_test.pk

        self.panel.delete()

        self.assertFalse(
            LabPanelItem.objects.filter(pk=item_pk).exists()
        )
        self.assertTrue(
            LabTest.objects.filter(pk=test_pk).exists()
        )

    def test_test_used_in_panel_is_protected_from_deletion(self):
        LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )

        with self.assertRaises(ProtectedError):
            self.first_test.delete()

    def test_deactivating_panel_keeps_its_items(self):
        item = LabPanelItem.objects.create(
            panel=self.panel,
            lab_test=self.first_test,
        )

        self.panel.is_active = False
        self.panel.save(update_fields=["is_active"])

        self.assertTrue(
            self.panel.items.filter(pk=item.pk).exists()
        )
