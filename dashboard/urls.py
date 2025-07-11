from django.urls import path
from .views import dashboard, welcome, DashboardDataView

app_name = "dashboard"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("welcome/", welcome, name="welcome"),
    path("api/dashboard-data/", DashboardDataView.as_view(), name="dashboard-data"),
]