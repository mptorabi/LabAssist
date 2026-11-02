from django import forms

from .models import LabResult


class LabResultForm(forms.ModelForm):
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
