from core.corrections import correction_view
from .models import LabReport, LabResult
from django.urls import path

from . import pdf_views, report_views, views

app_name = "labs"

urlpatterns = [
    path(
        "patients/<int:patient_pk>/reports/<int:report_pk>/pdf/",
        pdf_views.lab_report_pdf,
        name="report_pdf",
    ),
    path('patients/<int:patient_pk>/reports/<int:pk>/corrections/', correction_view(
        LabReport, ('patients.view_patient', 'labs.view_labreport', 'labs.view_labresult')
    ), name='report_corrections'),
    path('patients/<int:patient_pk>/results/<int:pk>/corrections/', correction_view(
        LabResult, ('patients.view_patient', 'labs.view_labresult')
    ), name='result_corrections'),
    path(
        "patients/<int:patient_pk>/reports/",
        report_views.lab_report_list,
        name="report_list",
    ),
    path(
        "patients/<int:patient_pk>/reports/<int:report_pk>/",
        report_views.lab_report_detail,
        name="report_detail",
    ),
    path(
        "patients/<int:patient_pk>/results/new/",
        views.lab_result_create,
        name="result_create",
    ),
    path(
        "patients/<int:patient_pk>/results/<int:result_pk>/report/",
        views.lab_result_report,
        name="result_report",
    ),
    path(
        "patients/<int:patient_pk>/reports/new/",
        report_views.lab_report_create,
        name="report_create",
    ),
]