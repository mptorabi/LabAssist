"""Read-only small-multiple charts; no clinical or unit equivalence inference."""
from collections import defaultdict

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render

from labs.history import build_history
from labs.models import LabTest
from .models import Patient


class ComparisonForm(forms.Form):
    tests = forms.ModelMultipleChoiceField(
        queryset=LabTest.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        help_text='Select up to four tests. Each has its own value scale.',
    )
    start = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, patient, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tests'].queryset = LabTest.objects.filter(
            results__patient=patient).distinct().order_by('name', 'pk')

    def clean(self):
        data = super().clean()
        if len(data.get('tests', [])) > 4:
            self.add_error('tests', 'Select no more than four tests.')
        if data.get('start') and data.get('end') and data['start'] > data['end']:
            self.add_error('end', 'End date must not precede start date.')
        return data


def comparison_sections(results):
    """Partition by recorded context, isolating observations with unknown context."""
    results = list(results)
    if len({r.patient_id for r in results}) > 1:
        raise ValueError('Comparison must contain one patient.')
    groups = defaultdict(list)
    for result in results:
        report = result.report
        specimen = report.specimen if report else ''
        laboratory = report.laboratory_name if report else ''
        # Missing context does not establish compatibility with another observation.
        unknown = result.pk if not specimen.strip() or not laboratory.strip() else None
        key = (result.lab_test_id, result.unit, specimen, laboratory,
               result.reference_range, result.result_kind, unknown)
        groups[key].append(result)
    sections = []
    for observations in groups.values():
        first = observations[0]
        sections.append({
            'lab_test': first.lab_test,
            'specimen': first.report.specimen if first.report else '',
            'laboratory': first.report.laboratory_name if first.report else '',
            'reference_range': first.reference_range,
            'result_kind': first.result_kind,
            **build_history(observations),
        })
    return sections


@login_required
@permission_required('patients.view_patient', raise_exception=True)
@permission_required('labs.view_labresult', raise_exception=True)
def patient_comparison(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = ComparisonForm(request.GET if request.GET else None, patient=patient)
    sections = []
    if form.is_bound and form.is_valid():
        results = patient.lab_results.filter(lab_test__in=form.cleaned_data['tests'])
        if form.cleaned_data.get('start'):
            results = results.filter(test_date__gte=form.cleaned_data['start'])
        if form.cleaned_data.get('end'):
            results = results.filter(test_date__lte=form.cleaned_data['end'])
        results = results.select_related('lab_test', 'report').order_by(
            'lab_test__name', 'lab_test_id', '-test_date', '-pk')
        sections = comparison_sections(results)
    return render(request, 'patients/patient_comparison.html', {
        'patient': patient, 'form': form, 'sections': sections,
    })
