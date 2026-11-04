from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render

from patients.models import Patient

from .forms import LabResultForm
from .models import LabResult, LabTest


@login_required
@permission_required(
    (
        "patients.view_patient",
        "labs.view_labresult",
        "labs.add_labresult",
    ),
    raise_exception=True,
)
def lab_result_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)

    if request.method == "POST":
        form = LabResultForm(request.POST)

        if form.is_valid():
            result = form.save(commit=False)
            result.patient = patient
            result.save()

            return redirect("patients:detail", pk=patient.pk)
    else:
        form = LabResultForm()

    catalog_tests = (
        LabTest.objects
        .filter(is_active=True)
        .prefetch_related("aliases", "suggested_units")
        .order_by("name", "code")
    )

    test_search_data = [
        {
            "id": str(test.pk),
            "code": test.code,
            "name": test.name,
            "aliases": [
                alias.name
                for alias in test.aliases.all()
            ],
            "units": [
                unit.symbol
                for unit in test.suggested_units.all()
                if unit.is_active
            ],
        }
        for test in catalog_tests
    ]

    return render(
        request,
        "labs/lab_result_form.html",
        {
            "patient": patient,
            "form": form,
            "test_search_data": test_search_data,
        },
    )


@login_required
@permission_required(
    (
        "patients.view_patient",
        "labs.view_labresult",
    ),
    raise_exception=True,
)
def lab_result_report(request, patient_pk, result_pk):
    result = get_object_or_404(
        LabResult.objects.select_related("patient", "lab_test"),
        pk=result_pk,
        patient_id=patient_pk,
    )

    return render(
        request,
        "labs/lab_result_report.html",
        {
            "patient": result.patient,
            "result": result,
        },
    )
