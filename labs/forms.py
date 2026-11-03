from django.db.models import Q
from .models import LabResult, LabTest
from django import forms
from .models import LabResult


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

        self.fields["lab_test"].queryset = available_tests.order_by(
            "name", "code"
        )
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
