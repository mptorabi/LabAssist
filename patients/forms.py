from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "full_name",
            "date_of_birth",
            "sex_assigned_at_birth",
            "height_cm", "height_measured_on", "weight_kg", "weight_measured_on",
            "medications", "medications_as_of", "underlying_conditions", "conditions_as_of",
        ]

        labels = {
            "full_name": "Full name",
            "date_of_birth": "Date of birth",
        }
        widgets = {
            **{name: forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
               for name in ('height_measured_on', 'weight_measured_on',
                            'medications_as_of', 'conditions_as_of')},
            "medications": forms.Textarea(attrs={'rows': 3}),
            "underlying_conditions": forms.Textarea(attrs={'rows': 3}),
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
