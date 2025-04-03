from django.urls import path
from .views import (industry_dashboards, dashboard_detail, trade_dashboards, 
                    edit_dashboard_detail, delete_dashboard)

app_name = "minicom_dashboards"
urlpatterns = [
    path("industry/", industry_dashboards, name="industry-dashboards"),
    path("trade/", trade_dashboards, name="trade-dashboards"),
    path("<str:dashboard_id>/", dashboard_detail, name="dashboard-detail"),
    path("<str:dashboard_id>/edit/", edit_dashboard_detail, name="edit-dashboard-detail"),
    path("<str:dashboard_id>/delete/", delete_dashboard, name="delete-dashboard"),
]
