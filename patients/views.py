from django.core.paginator import Paginator
from django.db.models import Q
from core.search import search_query
from core.audit import create_record
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PatientForm
from labs.models import LabTest
from labs.history import build_history
from .models import Patient


@login_required
@permission_required("patients.view_patient", raise_exception=True)
@permission_required("labs.view_labresult", raise_exception=True)
def patient_lab_history(request, pk, lab_test_pk):
    patient = get_object_or_404(Patient, pk=pk)
    lab_test = get_object_or_404(LabTest, pk=lab_test_pk)

    lab_results = (
        patient.lab_results
        .filter(lab_test=lab_test)
        .select_related("lab_test")
        .order_by("-test_date", "-created_at", "-pk")
    )

    return render(
        request,
        "patients/patient_lab_history.html",
        {
            "patient": patient,
            "lab_test": lab_test,
            "lab_results": lab_results,
            **build_history(lab_results),
        },
    )

@login_required
@permission_required("patients.view_patient", raise_exception=True)
def patient_list(request):
    query = search_query(request)
    patients = Patient.objects.all().order_by('full_name', 'pk')
    if query:
        filters = Q(full_name__icontains=query)
        if query.isascii() and query.isdecimal() and len(query) < 19:
            filters |= Q(pk=int(query))
        patients = patients.filter(filters)
    page = Paginator(patients, 20).get_page(request.GET.get('page'))

    return render(
        request,
        "patients/patient_list.html",
        {"patients": page, "page_obj": page, "query": query},
    )

@login_required
@permission_required("patients.view_patient", raise_exception=True)
@permission_required("patients.add_patient", raise_exception=True)
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            create_record(form.save(commit=False), request.user)
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

    can_view_lab_results = request.user.has_perm("labs.view_labresult")
    lab_results = None
    page = None
    query = search_query(request)

    if can_view_lab_results:
        lab_results = (
            patient.lab_results
            .select_related("lab_test")
            .order_by("-test_date", "-created_at", "-pk")
        )
        if query:
            lab_results = lab_results.filter(
                Q(lab_test__name__icontains=query) | Q(lab_test__code__icontains=query))
        page = Paginator(lab_results, 20).get_page(request.GET.get('page'))
        lab_results = page

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "can_view_lab_results": can_view_lab_results,
            "lab_results": lab_results,
            "page_obj": page,
            "query": query,
        },
    )
