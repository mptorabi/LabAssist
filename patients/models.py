from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

def validate_birth_date(value):
    if value > timezone.localdate():
        raise ValidationError("Date of birth cannot be in the future.")


class Patient(models.Model):
    class SexAssignedAtBirth(models.TextChoices):
        UNKNOWN = "unknown", "Unknown / Not recorded"
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        INTERSEX = "intersex", "Intersex"

    full_name = models.CharField(max_length=200)

    sex_assigned_at_birth = models.CharField(
        max_length=10,
        choices=SexAssignedAtBirth.choices,
        default=SexAssignedAtBirth.UNKNOWN,
        verbose_name="Sex assigned at birth",
    )


    date_of_birth = models.DateField(
        null=True,
        blank=True,
        validators=[validate_birth_date],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.full_name} (#{self.pk})"