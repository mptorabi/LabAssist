from django.contrib import admin
from core.admin_safety import ClinicalReadOnlyAdminMixin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(ClinicalReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "date_of_birth",
        "created_at",
    )
    search_fields = ("full_name",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at", "-pk")
