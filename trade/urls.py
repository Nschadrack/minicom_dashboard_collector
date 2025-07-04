from django.urls import path
# from .views import icbt_view
# from .views import icbt_upload_view
from .views import formal_trade_view, formal_trade_upload_view

app_name = "trade"

urlpatterns = [
    # path("icbt/", icbt_view, name="icbt-list"),
    # path("upload-icbt/", icbt_upload_view, name="upload-icbt")
    path("formal-trade/", formal_trade_view, name="formal-trade-list"),
    path("upload-formal-trade/", formal_trade_upload_view, name="upload-formal-trade"),
]