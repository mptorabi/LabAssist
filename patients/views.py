from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PatientForm


from .models import Patient


@login_required
@permission_required("patients.view_patient", raise_exception=True)
def patient_list(request):
    patients = Patient.objects.all()

    return render(
        request,
        "patients/patient_list.html",
        {"patients": patients},
    )

@login_required
@permission_required("patients.view_patient", raise_exception=True)
@permission_required("patients.add_patient", raise_exception=True)
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("patients:list")
    else:
        form = PatientForm()

    return render(
        request,
        "patients/patient_form.html",
        {"form": form},
    )

@login_required
@permission_required("patients.view_patient", raise_exception=True)
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    return render(
        request,
        "patients/patient_detail.html",
        {"patient": patient},
    )

# Create your views here.
