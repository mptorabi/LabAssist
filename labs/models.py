from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class LabTestCategory(models.Model):
    code = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Stable local category code.",
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "code"]
        verbose_name = "Lab test category"
        verbose_name_plural = "Lab test categories"

    def __str__(self):
        return self.name

class LabTest(models.Model):
    class InputType(models.TextChoices):
        TEXT = "text", "Free text"
        NUMERIC = "numeric", "Numeric or comparison value"
        QUALITATIVE = "qualitative", "Qualitative"
        STRUCTURED = "structured", "Structured (text fallback)"

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique local code, for example: CBC_HGB.",
    )
    name = models.CharField(
        max_length=200,
        help_text="Test name, for example: Hemoglobin.",
    )
    category = models.ForeignKey(
        LabTestCategory,
        on_delete=models.PROTECT,
        related_name="lab_tests",
        null=True,
        blank=True,
        help_text="Optional primary category used for browsing.",
    )
    input_type = models.CharField(
        max_length=20,
        choices=InputType.choices,
        default=InputType.TEXT,
        help_text=(
            "Suggested input format for future entry forms. "
            "Does not restrict or convert recorded result text."
        ),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "code"]
        verbose_name = "Lab test"
        verbose_name_plural = "Lab tests"

    def __str__(self):
        return f"{self.name} ({self.code})"

class LabTestAlias(models.Model):
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    name = models.CharField(
        max_length=200,
        help_text="Alternative name or abbreviation used for searching.",
    )

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Lab test alias"
        verbose_name_plural = "Lab test aliases"
        constraints = [
            models.UniqueConstraint(
                fields=["lab_test", "name"],
                name="labs_unique_test_alias",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.lab_test.code})"

class LabTestUnit(models.Model):
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="suggested_units",
    )
    symbol = models.CharField(
        max_length=100,
        help_text=(
            "Suggested unit as displayed for entry, "
            "for example: mg/dL. Not a conversion rule."
        ),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["symbol", "pk"]
        verbose_name = "Lab test unit"
        verbose_name_plural = "Lab test units"
        constraints = [
            models.UniqueConstraint(
                fields=["lab_test", "symbol"],
                name="labs_unique_test_unit",
            ),
        ]

    def __str__(self):
        return f"{self.symbol} ({self.lab_test.code})"

class LabReport(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="lab_reports",
    )
    report_date = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Issue date printed on the laboratory report. "
            "Leave blank if not provided."
        ),
    )
    laboratory_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Laboratory name as printed on the report.",
    )
    report_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "Report identifier as printed. "
            "It is not assumed to be globally unique."
        ),
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "Lab report"
        verbose_name_plural = "Lab reports"

    def clean(self):
        super().clean()

        errors = {}

        if self.report_date and self.report_date > timezone.localdate():
            errors["report_date"] = "Report date cannot be in the future."

        if self.pk and self.patient_id:
            has_results_for_other_patient = (
                self.results
                .exclude(patient_id=self.patient_id)
                .exists()
            )

            if has_results_for_other_patient:
                errors["patient"] = (
                    "The report patient must match the patient "
                    "of every linked result."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Lab report #{self.pk} — Patient #{self.patient_id}"



class LabResult(models.Model):
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="lab_results",
    )
    report = models.ForeignKey(
        LabReport,
        on_delete=models.PROTECT,
        related_name="results",
        null=True,
        blank=True,
        help_text=(
            "Optional laboratory report containing this result. "
            "The report must belong to the same patient."
        ),
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

        errors = {}

        if self.test_date and self.test_date > timezone.localdate():
            errors["test_date"] = "Test date cannot be in the future."

        if self.report_id and self.patient_id:
            report_has_different_patient = (
                LabReport.objects
                .filter(pk=self.report_id)
                .exclude(patient_id=self.patient_id)
                .exists()
            )

            if report_has_different_patient:
                errors["report"] = (
                    "The selected report must belong to the same patient "
                    "as this result."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.lab_test.code} — "
            f"Patient #{self.patient_id} — {self.test_date}"
        )

