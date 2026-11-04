from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone

from .models import LabReport, LabTest


class LabReportEntryForm(forms.ModelForm):
    default_test_date = forms.DateField(
        label="Default test date",
        help_text=(
            "Test date recorded on the laboratory report. "
            "Individual rows may use a different date."
        ),
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    class Meta:
        model = LabReport
        fields = (
            "laboratory_name",
            "report_number",
            "report_date",
            "notes",
        )
        labels = {
            "laboratory_name": "Laboratory name",
            "report_number": "Report number",
            "report_date": "Report issue date",
            "notes": "Report notes",
        }
        widgets = {
            "report_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_default_test_date(self):
        value = self.cleaned_data["default_test_date"]

        if value > timezone.localdate():
            raise forms.ValidationError(
                "Test date cannot be in the future."
            )

        return value


class LabReportResultRowForm(forms.Form):
    lab_test = forms.ModelChoiceField(
        queryset=LabTest.objects.none(),
        widget=forms.HiddenInput(),
    )
    value = forms.CharField(
        label="Reported value",
        max_length=255,
        required=False,
        strip=False,
    )
    unit = forms.CharField(
        label="Unit",
        max_length=100,
        required=False,
        strip=False,
    )
    reference_range = forms.CharField(
        label="Reported reference range",
        max_length=255,
        required=False,
        strip=False,
    )
    test_date = forms.DateField(
        label="Different test date",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
        help_text="Leave blank to use the default test date.",
    )
    notes = forms.CharField(
        label="Result notes",
        required=False,
        strip=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, allowed_tests, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lab_test"].queryset = allowed_tests.filter(
            is_active=True,
        )

        # Validate the hidden test identifier even for an empty row.
        self.empty_permitted = False

    def clean_test_date(self):
        value = self.cleaned_data.get("test_date")

        if value and value > timezone.localdate():
            raise forms.ValidationError(
                "Test date cannot be in the future."
            )

        return value

    def clean(self):
        cleaned_data = super().clean()

        value = cleaned_data.get("value", "")
        has_value = bool(value.strip())

        has_other_data = any(
            bool(cleaned_data.get(field, "").strip())
            for field in ("unit", "reference_range", "notes")
        ) or cleaned_data.get("test_date") is not None

        if not has_value and has_other_data:
            self.add_error(
                "value",
                "Enter the reported result, or clear this entire row.",
            )

        return cleaned_data


class BaseLabReportResultFormSet(BaseFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        seen_test_ids = set()
        completed_rows = 0

        for form in self.forms:
            data = form.cleaned_data
            lab_test = data.get("lab_test")

            if lab_test is None:
                continue

            if lab_test.pk in seen_test_ids:
                raise forms.ValidationError(
                    "A test appears more than once. "
                    "Duplicate rows are not supported in this entry form."
                )

            seen_test_ids.add(lab_test.pk)

            if data.get("value", "").strip():
                completed_rows += 1

        if completed_rows == 0:
            raise forms.ValidationError(
                "Enter at least one laboratory result."
            )


LabReportResultFormSet = formset_factory(
    LabReportResultRowForm,
    formset=BaseLabReportResultFormSet,
    extra=0,
    max_num=200,
    validate_max=True,
    absolute_max=200,
)