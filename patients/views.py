from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
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


# Create your views here.
