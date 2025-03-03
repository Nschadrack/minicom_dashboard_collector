from django.urls import path
from .views import (industrial_parks_list, industrial_park_detail,
                    record_partitioned_plot, companies_industries_list,
                    land_request)


app_name = "industry"
urlpatterns = [
    path("", industrial_parks_list, name="parks-list"),
    path("parks/<str:park_id>/", industrial_park_detail, name="park-details"),
    path("parks/<str:park_id>/partitioned-plot/", record_partitioned_plot, name="add-partitioned-plot"),
    path("companies-profiles/", companies_industries_list, name="companies-industries-list"),
    path("land-requests/", land_request, name="land-requests"),
]
