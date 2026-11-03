from django.contrib import admin

from .models import (
    LabResult,
    LabTest,
    LabTestAlias,
    LabTestCategory,
    LabTestUnit,
)


@admin.register(LabTestCategory)
class LabTestCategoryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    ordering = ("name", "code")


class LabTestAliasInline(admin.TabularInline):
    model = LabTestAlias
    fields = ("name",)
    extra = 0


class LabTestUnitInline(admin.TabularInline):
    model = LabTestUnit
    fields = ("symbol", "is_active")
    extra = 0


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "category",
        "input_type",
        "is_active",
    )
    search_fields = ("code", "name", "aliases__name")
    list_filter = ("category", "input_type", "is_active")
    ordering = ("name", "code")
    autocomplete_fields = ("category",)
    list_select_related = ("category",)
    inlines = (LabTestAliasInline, LabTestUnitInline)


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
