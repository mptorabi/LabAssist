from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_birth_date(value):
    if value > timezone.localdate():
        raise ValidationError("Date of birth cannot be in the future.")


class Patient(models.Model):
    full_name = models.CharField(max_length=200)

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
from django.db import models

# Create your models here.
