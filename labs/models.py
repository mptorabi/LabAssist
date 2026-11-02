from django.db import models


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
