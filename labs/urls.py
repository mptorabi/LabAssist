from django.urls import path

from . import views

app_name = "labs"

urlpatterns = [
    path(
        "patients/<int:patient_pk>/results/new/",
        views.lab_result_create,
        name="result_create",
    ),
]
