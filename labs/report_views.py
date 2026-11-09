from django.db.models import Q
from core.search import search_query
from core.audit import create_record
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET

from patients.models import Patient

from .entry_catalog import entry_catalog
from .models import LabPanel, LabReport, LabResult, LabTest
from .report_forms import LabReportEntryForm, LabReportResultFormSet, LabReportResultRowForm


MAX_ROWS = 100
ROW_FIELDS = tuple(LabReportResultRowForm.base_fields)


def _panel_tests(panels):
    """Stable ordering; overlapping presets never duplicate a row."""
    tests = {}
    for panel in panels:
        for item in panel.items.filter(lab_test__is_active=True).select_related(
            "lab_test"
        ).order_by("position", "pk"):
            tests.setdefault(item.lab_test_id, item.lab_test)
    return list(tests.values())


def _submitted_rows(data, formset):
    """Read raw text only after validating bounded management counts."""
    management = formset.management_form
    if not management.is_valid():
        return None
    total = management.cleaned_data["TOTAL_FORMS"]
    initial = management.cleaned_data["INITIAL_FORMS"]
    if not 0 <= initial <= total <= MAX_ROWS:
        return None
    return [
        {field: data.get(f"results-{i}-{field}", "") for field in ROW_FIELDS}
        for i in range(total)
    ]


@login_required
@permission_required(
    ("patients.view_patient", "labs.view_labresult", "labs.add_labresult", "labs.add_labreport"),
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
    if set(requested_codes) != set(selected_codes):
        error = "One or more selected panels are unavailable."

    # Panels are entry presets, not an authorization boundary. Any active
    # catalog test may be explicitly added; inactive/unknown IDs remain invalid.
    allowed_tests = LabTest.objects.filter(is_active=True)
    bound_data = request.POST if request.method == "POST" else None
    initial_rows = []
    if request.method == "GET" and not error:
        tests = _panel_tests(selected_panels)
        if len(tests) > MAX_ROWS:
            error = "Select fewer panels. A report supports up to 100 rows."
        else:
            initial_rows = [{"lab_test": test.pk} for test in tests]
            if requested_codes and not tests:
                error = "The selected panels contain no active tests."

    header_form = LabReportEntryForm(bound_data, instance=LabReport(patient=patient))
    result_formset = LabReportResultFormSet(
        bound_data, prefix="results", initial=initial_rows,
        form_kwargs={"allowed_tests": allowed_tests},
    )
    review_rows = []
    reviewing = False
    entry_notice = ""

    if request.method == "POST":
        action = request.POST.get("action")
        raw_rows = _submitted_rows(request.POST, result_formset)
        if raw_rows is None:
            error = "Invalid or missing row count. A report supports up to 100 rows."
        elif not error and action in ("add_panels", "add_test", "remove_blank"):
            additions = []
            if action == "add_panels":
                codes = request.POST.getlist("add_panels")
                new_panels = list(panels.filter(code__in=codes))
                if not codes or set(codes) != {p.code for p in new_panels}:
                    error = "Choose available panels to add."
                else:
                    additions = _panel_tests(new_panels)
                    if not additions:
                        error = "The selected panels contain no active tests."
            elif action == "add_test":
                test_id = request.POST.get("add_test", "")
                # Avoid passing arbitrarily large or malformed identifiers to SQLite.
                if test_id.isascii() and test_id.isdigit() and len(test_id) <= 18:
                    test = allowed_tests.filter(pk=test_id).first()
                else:
                    test = None
                if test is None:
                    error = "Choose an available test to add."
                else:
                    additions = [test]
            else:
                # Never discard a populated row; clear it explicitly before removal.
                before = len(raw_rows)
                raw_rows = [row for row in raw_rows if any(
                    str(row[field]).strip() for field in ROW_FIELDS if field != "lab_test"
                )]
                entry_notice = f"Removed {before - len(raw_rows)} entirely blank row(s)."

            seen = {str(row["lab_test"]) for row in raw_rows}
            new_rows = [{"lab_test": test.pk} for test in additions if str(test.pk) not in seen]
            if len(raw_rows) + len(new_rows) > MAX_ROWS:
                error = "No rows added. A report supports up to 100 rows."
            elif not error:
                raw_rows.extend(new_rows)
                if action != "remove_blank":
                    entry_notice = f"Added {len(new_rows)} row(s). Existing rows were kept."

            # Adding controls must work with incomplete headers and invalid result
            # text. Re-render the raw fields, not cleaned_data (which can strip text).
            header_form = LabReportEntryForm(
                initial={field: request.POST.get(field, "") for field in header_form.fields},
                instance=LabReport(patient=patient),
            )
            result_formset = LabReportResultFormSet(
                prefix="results", initial=raw_rows,
                form_kwargs={"allowed_tests": allowed_tests},
            )
        elif not error and action in ("review", "save", "edit"):
            header_valid = header_form.is_valid()
            rows_valid = result_formset.is_valid()
            if header_valid and rows_valid:
                for row_form in result_formset:
                    data = row_form.cleaned_data
                    if not data.get("value", "").strip():
                        continue
                    review_rows.append({
                        "lab_test": data["lab_test"],
                        "test_date": data.get("test_date") or header_form.cleaned_data["default_test_date"],
                        **{field: data[field] for field in ("value", "unit", "reference_range", "notes", "result_kind")},
                    })
                if action == "save":
                    with transaction.atomic():
                        report = header_form.save(commit=False)
                        report.patient = patient
                        create_record(report, request.user)
                        for row in review_rows:
                            result = LabResult(patient=patient, report=report, **row)
                            create_record(result, request.user)
                    return redirect("patients:detail", pk=patient.pk)
                reviewing = action == "review"
        elif not error:
            error = "Choose an available action. Nothing was saved."

    catalog = entry_catalog()
    tests_by_id = {test["id"]: test for test in catalog}
    for row_form in result_formset:
        test = tests_by_id.get(str(row_form["lab_test"].value()))
        label = f'{test["name"]} ({test["code"]})' if test else "Unavailable test"
        row_form.test_label = label
        if test:
            row_form.fields["unit"].widget.attrs["list"] = f'unit-options-{test["id"]}'
        for name in ("value", "unit", "reference_range", "test_date", "notes", "result_kind"):
            row_form.fields[name].widget.attrs.update({
                "aria-label": f"{label}: {row_form.fields[name].label}",
                "autocomplete": "off",
            })

    return render(request, "labs/lab_report_entry.html", {
        "patient": patient, "panels": panels, "selected_codes": selected_codes,
        "header_form": header_form, "result_formset": result_formset,
        "review_rows": review_rows, "reviewing": reviewing,
        "entry_error": error, "entry_notice": entry_notice,
        "test_search_data": catalog,
    })


@login_required
@permission_required(
    ("patients.view_patient", "labs.view_labresult", "labs.view_labreport"),
    raise_exception=True,
)
@require_GET
def lab_report_list(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    reports = patient.lab_reports.order_by("-created_at", "-pk")
    query = search_query(request)
    if query:
        reports = reports.filter(Q(laboratory_name__icontains=query) | Q(report_number__icontains=query))
    page = Paginator(reports, 20).get_page(request.GET.get("page"))
    return render(request, "labs/lab_report_list.html", {
        "patient": patient,
        "page_obj": page,
        "query": query,
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
    results = report.results.select_related('lab_test').order_by('test_date', 'lab_test__name', 'pk')
    query = search_query(request)
    if query:
        results = results.filter(Q(lab_test__name__icontains=query) | Q(lab_test__code__icontains=query))
    page = Paginator(results, 20).get_page(request.GET.get('page'))
    return render(request, "labs/lab_report_detail.html", {
        "patient": report.patient,
        "report": report,
        "results": page,
        "page_obj": page,
        "query": query,
    })
