from django.db.models import Q
from .models import LabResult, LabTest
from django import forms


class LabResultForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        available_tests = LabTest.objects.filter(is_active=True)

        # Keep the recorded test available when editing an existing result.
        if self.instance.pk and self.instance.lab_test_id:
            available_tests = LabTest.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.lab_test_id)
            )

        self.fields["lab_test"].queryset = available_tests.order_by(
            "name", "code"
        )

        # Store report text verbatim; whitespace-only values are still invalid.
        for name in ("value", "unit", "reference_range", "notes"):
            self.fields[name].strip = False

    def clean_value(self):
        value = self.cleaned_data["value"]
        if not value.strip():
            raise forms.ValidationError("Enter the reported result.")
        return value

    class Meta:
        model = LabResult
        fields = [
            "lab_test",
            "test_date",
            "value",
            "unit",
            "reference_range",
            "notes",
        ]
        labels = {
            "lab_test": "Lab test",
            "test_date": "Test date",
            "value": "Reported value",
            "unit": "Unit",
            "reference_range": "Reference range",
            "notes": "Notes",
        }
        widgets = {
            "test_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
