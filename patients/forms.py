from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "full_name",
            "date_of_birth",
            "sex_assigned_at_birth",
        ]

        labels = {
            "full_name": "Full name",
            "date_of_birth": "Date of birth",
        }
        widgets = {
            "date_of_birth": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }
        help_texts = {
            "date_of_birth": "Optional. Cannot be in the future.",
            "sex_assigned_at_birth": "Select Unknown / Not recorded if unavailable.",
        }

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"].strip()

        if not full_name:
            raise forms.ValidationError("Enter a full name.")

        return full_name
