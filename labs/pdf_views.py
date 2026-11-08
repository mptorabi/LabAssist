"""Permission-protected PDF downloads using in-memory snapshots."""
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import LabReport, LabResult
from .pdf_export import UnsupportedPDFText, render_report_pdf


@never_cache
@login_required
@permission_required(
    ("patients.view_patient", "labs.view_labreport", "labs.view_labresult"),
    raise_exception=True,
)
@require_GET
def lab_report_pdf(request, patient_pk, report_pk):
    # Materialize one SQLite read transaction, then release it before rendering.
    with transaction.atomic():
        report = get_object_or_404(
            LabReport.objects.select_related("patient"),
            pk=report_pk, patient_id=patient_pk,
        )
        if report.results.exclude(patient_id=patient_pk).exists():
            return HttpResponse(
                "PDF export unavailable: inconsistent patient links require review. "
                "No PDF was generated.",
                status=409, content_type="text/plain; charset=utf-8",
            )
        results = list(report.results.filter(patient_id=patient_pk).select_related(
            "lab_test"
        ).order_by("test_date", "pk"))
        earliest = {}
        for result in results:
            earliest.setdefault(result.lab_test_id, result.test_date)
        criteria = Q(pk__in=[])
        for test_id, date in earliest.items():
            criteria |= Q(lab_test_id=test_id, test_date__lt=date)
        previous = LabResult.objects.filter(
            criteria, patient_id=patient_pk,
        ).exclude(report_id=report.pk).select_related("lab_test").order_by(
            "-test_date", "-created_at", "-pk"
        )
        history_total = previous.count()
        history = list(previous[:100])
        generated_at = timezone.now()
    try:
        content = render_report_pdf(report, results, history, history_total, generated_at)
    except UnsupportedPDFText:
        response = HttpResponse(
            "PDF export unavailable: recorded text contains a character not supported "
            "by the bundled font. No PDF was generated. Do not alter clinical data "
            "to work around this; use the web report and contact the maintainer.",
            status=422, content_type="text/plain; charset=utf-8",
        )
    else:
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="lab-report-{report.pk}.pdf"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
