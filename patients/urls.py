from core.corrections import correction_view
from .models import Patient
from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path('<int:pk>/corrections/', correction_view(Patient, ('patients.view_patient',)), name='corrections'),
    path("", views.patient_list, name="list"),
    path("new/", views.patient_create, name="create"),
    path("<int:pk>/", views.patient_detail, name="detail"),
    path(
        "<int:pk>/labs/<int:lab_test_pk>/history/",
        views.patient_lab_history,
        name="lab_history",
    ),
]
