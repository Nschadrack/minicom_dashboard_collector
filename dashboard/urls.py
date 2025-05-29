from django.urls import path
from .views import dashboard, welcome

app_name = "dashboard"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("welcome/", welcome, name="welcome"),
]