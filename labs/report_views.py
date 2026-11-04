from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_http_methods, require_GET

from patients.models import Patient

from .models import LabPanel, LabReport, LabResult, LabTest
from .report_forms import LabReportEntryForm, LabReportResultFormSet


@login_required
@permission_required(
    (
        "patients.view_patient",
        "labs.view_labresult",
        "labs.add_labresult",
        "labs.add_labreport",
    ),
    raise_exception=True,
)
@require_http_methods(["GET", "POST"])
def lab_report_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    panels = LabPanel.objects.filter(is_active=True).order_by("name", "code")

    source = request.POST if request.method == "POST" else request.GET
    requested_codes = source.getlist("panels")

    selected_panels = list(panels.filter(code__in=requested_codes))
    selected_codes = [panel.code for panel in selected_panels]

    error = None
    header_form = None
    result_formset = None
    review_rows = []
    reviewing = False

    if set(requested_codes) != set(selected_codes):
        error = "One or more selected panels are unavailable."
    elif requested_codes:
        # Preserve panel item ordering and remove overlapping tests.
        ordered_tests = []
        seen_ids = set()

        for panel in selected_panels:
            items = (
                panel.items
                .filter(lab_test__is_active=True)
                .select_related("lab_test")
                .order_by("position", "pk")
            )
            for item in items:
                if item.lab_test_id not in seen_ids:
                    seen_ids.add(item.lab_test_id)
                    ordered_tests.append(item.lab_test)

        if not ordered_tests:
            error = "The selected panels contain no active tests."
        elif len(ordered_tests) > 200:
            error = "Select fewer panels. A report supports up to 200 rows."
        else:
            allowed_tests = LabTest.objects.filter(
                pk__in=seen_ids,
                is_active=True,
            )
            initial_rows = [
                {"lab_test": test.pk}
                for test in ordered_tests
            ]
            bound_data = request.POST if request.method == "POST" else None

            header_form = LabReportEntryForm(
                bound_data,
                instance=LabReport(patient=patient),
            )
            result_formset = LabReportResultFormSet(
                bound_data,
                prefix="results",
                initial=initial_rows,
                form_kwargs={"allowed_tests": allowed_tests},
            )

            tests_by_id = {
                str(test.pk): test
                for test in ordered_tests
            }

            for row_form in result_formset:
                test = tests_by_id.get(
                    str(row_form["lab_test"].value())
                )
                row_form.test_label = (
                    str(test) if test else "Unavailable test"
                )

            if request.method == "POST":
                header_valid = header_form.is_valid()
                rows_valid = result_formset.is_valid()

                if header_valid and rows_valid:
                    submitted_ids = {
                        form.cleaned_data["lab_test"].pk
                        for form in result_formset
                    }

                    if submitted_ids != seen_ids:
                        error = (
                            "The panel contents changed or rows are missing. "
                            "Select the panels again to reload the form."
                        )
                    else:
                        for row_form in result_formset:
                            data = row_form.cleaned_data

                            if not data.get("value", "").strip():
                                continue

                            review_rows.append({
                                "lab_test": data["lab_test"],
                                "test_date": (
                                    data.get("test_date")
                                    or header_form.cleaned_data[
                                        "default_test_date"
                                    ]
                                ),
                                "value": data["value"],
                                "unit": data["unit"],
                                "reference_range": data["reference_range"],
                                "notes": data["notes"],
                            })

                        action = request.POST.get("action")

                        if action == "save":
                            with transaction.atomic():
                                report = header_form.save(commit=False)
                                report.patient = patient
                                report.full_clean()
                                report.save()

                                for row in review_rows:
                                    result = LabResult(
                                        patient=patient,
                                        report=report,
                                        **row,
                                    )
                                    result.full_clean()
                                    result.save()

                            return redirect(
                                "patients:detail",
                                pk=patient.pk,
                            )

                        reviewing = action == "review"

    elif request.method == "POST":
        error = "Select at least one panel."

    return render(
        request,
        "labs/lab_report_entry.html",
        {
            "patient": patient,
            "panels": panels,
            "selected_codes": selected_codes,
            "header_form": header_form,
            "result_formset": result_formset,
            "review_rows": review_rows,
            "reviewing": reviewing,
            "entry_error": error,
        },
    )


@login_required
@permission_required(
    ("patients.view_patient", "labs.view_labresult", "labs.view_labreport"),
    raise_exception=True,
)
@require_GET
def lab_report_list(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    reports = patient.lab_reports.order_by("-created_at", "-pk")
    page = Paginator(reports, 20).get_page(request.GET.get("page"))
    return render(request, "labs/lab_report_list.html", {
        "patient": patient,
        "page_obj": page,
    })


@login_required
@permission_required(
    ("patients.view_patient", "labs.view_labresult", "labs.view_labreport"),
    raise_exception=True,
)
@require_GET
def lab_report_detail(request, patient_pk, report_pk):
    report = get_object_or_404(
        LabReport.objects.select_related("patient"),
        pk=report_pk,
        patient_id=patient_pk,
    )
    return render(request, "labs/lab_report_detail.html", {
        "patient": report.patient,
        "report": report,
        "results": report.results.select_related("lab_test").order_by(
            "test_date", "lab_test__name", "pk",
        ),
    })