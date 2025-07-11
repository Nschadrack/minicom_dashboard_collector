from django.urls import path
from .views import (industrial_parks_list, industrial_park_detail,
                    record_partitioned_plot, companies_industries_list,
                    industry_details, industry_profile_details,
                    land_request, land_request_detail,add_industry_not_in_park,
                    record_industry_attachment, add_industry_economic_sectors,
                    contracts_list, contracts_detail, make_payment_transaction,
                    main_indstry_contracts, record_refund, add_industry_product,
                    delete_industry_product, delete_industry_attachment, delete_industry,
                    partitioned_plots_upload_view, bulk_industry_profiles_upload)


app_name = "industry"
urlpatterns = [
    # parks
    path("parks/", industrial_parks_list, name="parks-list"),
    path("parks/upload-plots/", partitioned_plots_upload_view, name="upload-plots"),
    path("parks/<str:park_id>/", industrial_park_detail, name="park-details"),
    path("parks/<str:park_id>/partitioned-plot/", record_partitioned_plot, name="add-partitioned-plot"),

    # profile and industries
    path("companies-profiles/", companies_industries_list, name="companies-industries-list"),
    path("companies-profiles/<str:profile_id>/", industry_profile_details, name="industry-profile-details"),
    path("industries/<str:industry_id>/", industry_details, name="industry-info-details"),
    path("industries/<str:industry_id>/delete/", delete_industry, name="delete-industry"),
    path("industries/<str:industry_id>/add-economic-sector/", add_industry_economic_sectors, name="add-industry-economic-sector"),
    path("industries/<str:industry_id>/upload-attachment/", record_industry_attachment, name="upload-industry-attachment"),
    path("industries/attachments/<str:attachment_id>/delete/", delete_industry_attachment, name="delete-industry-attachment"),
    path("companies-profiles/bulk-upload/industry-profiles/", bulk_industry_profiles_upload, name="bulk-upload-industry-profiles"),

    # industry product
    path("industries/<str:industry_id>/add-product/", add_industry_product, name="add-industry-product"),

    # land information
    path("land-requests/", land_request, name="land-requests"),
    path("land-requests/<str:land_request_id>/", land_request_detail, name="land-request-detail"),
    path("land-requests/<str:land_request_id>/<str:flag>/", land_request_detail, name="land-request-allocate-plot"),

    # register industry not in the park
    path("add-industries/not-in-park/", add_industry_not_in_park, name="add-indusrty-outof-park"),
    path("industries/products/<str:product_id>/delete/", delete_industry_product, name="delete-industry-product"),

    # contracts
    path("contracts/", contracts_list, name="contract-list"),
    path("contracts/<str:contract_id>/", contracts_detail, name="contracts-detail"),
    path("contracts/make-transaction/payment/", make_payment_transaction, name="transaction-payment"),
    path("contracts/all/industries/", main_indstry_contracts, name="all-contracts"),
    path("contracts/payment-transaction/<str:transaction_id>/", record_refund, name="record_refund"),
]
