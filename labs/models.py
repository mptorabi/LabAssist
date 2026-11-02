from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class LabTest(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique local code, for example: CBC_HGB.",
    )
    name = models.CharField(
        max_length=200,
        help_text="Test name, for example: Hemoglobin.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "code"]
        verbose_name = "Lab test"
        verbose_name_plural = "Lab tests"

    def __str__(self):
        return f"{self.name} ({self.code})"

class LabResult(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="lab_results",
    )
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name="results",
    )
    test_date = models.DateField(
        help_text="Date of the test as recorded on the laboratory report.",
    )
    value = models.CharField(
        max_length=255,
        help_text="Result exactly as reported, for example: 13.5, Negative, or <0.01.",
    )
    unit = models.CharField(
        max_length=100,
        blank=True,
        help_text="Unit as reported. Leave blank if not provided.",
    )
    reference_range = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reference range as reported. Leave blank if not provided.",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-test_date", "-created_at", "-pk"]
        verbose_name = "Lab result"
        verbose_name_plural = "Lab results"

    def clean(self):
        super().clean()

        if self.test_date and self.test_date > timezone.localdate():
            raise ValidationError(
                {"test_date": "Test date cannot be in the future."}
            )

    def __str__(self):
        return (
            f"{self.lab_test.code} — "
            f"Patient #{self.patient_id} — {self.test_date}"
        )

