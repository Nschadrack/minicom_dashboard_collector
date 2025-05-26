from django.urls import path
from .views import not_found, view_job_detail, clear_job_data, delete_upload_job

app_name = "automation"

urlpatterns = [
    path("not-found/", not_found, name="index"),
    path("job/<str:id>/", view_job_detail, name="job_detail"),
    path("job/<str:id>/clear-job/", clear_job_data, name="clear_job_data"),
    path("job/<str:id>/delete/", delete_upload_job, name="delete_job"),
]
