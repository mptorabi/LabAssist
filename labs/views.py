from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from patients.models import Patient
from .forms import LabResultForm
from .models import LabResult



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

    return render(
        request,
        "labs/lab_result_form.html",
        {
            "patient": patient,
            "form": form,
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
