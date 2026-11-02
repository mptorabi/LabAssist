from django.contrib import admin
from .models import LabResult, LabTest


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    ordering = ("name", "code")

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "lab_test",
        "test_date",
        "value",
        "unit",
    )
    list_filter = ("lab_test", "test_date")
    search_fields = (
        "patient__full_name",
        "lab_test__code",
        "lab_test__name",
    )
    autocomplete_fields = ("patient", "lab_test")
    list_select_related = ("patient", "lab_test")
    readonly_fields = ("created_at", "updated_at")
