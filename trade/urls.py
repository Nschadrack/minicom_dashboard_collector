from django.urls import path
from .views import icbt_view
from .views import icbt_upload_view

app_name = "trade"

urlpatterns = [
    path("", icbt_view, name="icbt-list"),
    path("upload-icbt/", icbt_upload_view, name="upload-icbt")
]