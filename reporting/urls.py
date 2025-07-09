from django.urls import path
from .views import (reporting, add_product_report, add_employment_report,
                    admin_report, admin_report_details)

app_name = "reporting"

urlpatterns = [
    path("", reporting, name="reporting"),
    path("admin/", admin_report, name="admin-reporting"),
    path("admin/industry/<str:company_site_id>/<str:period_id>/", admin_report_details, name="admin-reporting-detail"),
    path("product/<str:product_id>/<str:start_date>/<str:end_date>/", add_product_report, name="add-product-report"),
    path("employment/industry/<str:industry_id>/<str:start_date>/<str:end_date>/", add_employment_report, name="add-employment-report"),
]
