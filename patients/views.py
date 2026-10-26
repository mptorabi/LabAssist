from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

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


from django.shortcuts import render

# Create your views here.
