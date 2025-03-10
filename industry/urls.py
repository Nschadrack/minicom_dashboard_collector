from django.urls import path
from .views import (industrial_parks_list, industrial_park_detail,
                    record_partitioned_plot, companies_industries_list,
                    industry_details, industry_profile_details,
                    land_request, land_request_detail,add_industry_not_in_park,
                    record_industry_attachment, add_industry_economic_sectors)


app_name = "industry"
urlpatterns = [
    path("parks/", industrial_parks_list, name="parks-list"),
    path("parks/<str:park_id>/", industrial_park_detail, name="park-details"),
    path("parks/<str:park_id>/partitioned-plot/", record_partitioned_plot, name="add-partitioned-plot"),
    path("companies-profiles/", companies_industries_list, name="companies-industries-list"),
    path("companies-profiles/<str:profile_id>/", industry_profile_details, name="industry-profile-details"),
    path("industries/<str:industry_id>/", industry_details, name="industry-info-details"),
    path("industries/<str:industry_id>/add-economic-sector/", add_industry_economic_sectors, name="add-industry-economic-sector"),
    path("industries/<str:industry_id>/upload-attachment/", record_industry_attachment, name="upload-industry-attachment"),
    path("land-requests/", land_request, name="land-requests"),
    path("land-requests/<str:land_request_id>/", land_request_detail, name="land-request-detail"),
    path("land-requests/<str:land_request_id>/<str:flag>/", land_request_detail, name="land-request-allocate-plot"),

    # register industry not in the park
    path("add-industries/not-in-park/", add_industry_not_in_park, name="add-indusrty-outof-park"),
]
