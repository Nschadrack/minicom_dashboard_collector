from django.core.paginator import Paginator
from django.db.models import Prefetch
from .models import (
    CompanySite,
    IndustryEconomicSector,
    # EconomicSubSector,
    IndustryProduct,
    # Product,
    IndustryContract,
    AllocatedPlot,
    IndustryEconomicZone,
    CompanyProfile,
)
from automation.utils import format_number_two

def get_optimized_company_data(page_number=1, page_size=10):
    """
    An optimized query to retrieve company site data with related information,
    including pagination.
    """
    prefetched_products = Prefetch(
        "company_products",
        queryset=IndustryProduct.objects.select_related("product"),
        to_attr="products_data",
    )

    prefetched_contracts = Prefetch(
        "industry_contracts",
        queryset=IndustryContract.objects.filter(contract_type="INITIAL"),
        to_attr="contracts_data",
    )

    # The main query
    company_sites = CompanySite.objects.select_related(
        "company",
        "allocated_plot__park",  # Using '__' to traverse relationships
        "allocated_plot__zone",
    ).prefetch_related(
        prefetched_products,
        prefetched_contracts,
    ).all()

    # Pagination
    paginator = Paginator(company_sites, page_size)
    page_obj = paginator.get_page(page_number)

    # Format the data
    results = []
    for site in page_obj:
        site_data = {
            "industry_name": site.company.name,
            "tin_number": site.company.tin_number,
            "phone_number": site.company.phone_contact,
            "email": site.company.email_contact,
            "plot_owner": site.allocated_plot.land_owner.name if site.allocated_plot else "",
            "park_size": format_number_two(site.allocated_plot.park.total_land_size) if site.allocated_plot.park else 0,
            "park_leasable_land": format_number_two(site.allocated_plot.park.leasable_land) if site.allocated_plot.park else 0,
            "park_infrastructure_size": format_number_two(site.allocated_plot.park.total_land_size - site.allocated_plot.park.leasable_land) if site.allocated_plot.park else 0,
            "industry_size": site.company.company_size,
            "construction_status": site.construction_status,
            "operational_status": site.operational_status,
            "province": site.province,
            "district": site.district,
            "sector": site.sector,
            "investment_amount": format_number_two(site.investment_amount) if site.investment_amount else 0,
            "investment_currency": site.investment_currency if site.investment_currency else "",
            "allocated_plot_upi": site.allocated_plot.allocated_plot_upi if site.allocated_plot and site.allocated_plot.allocated_plot_upi else "",
            "allocated_plot_upi_status": site.allocated_plot.upi_status if site.allocated_plot else "",
            "plot_zoning": site.allocated_plot.zone.name if site.allocated_plot and site.allocated_plot.zone else "",
            "park_name": site.allocated_plot.park.name if site.allocated_plot and site.allocated_plot.park else "",
            "park_category": site.allocated_plot.park.category if site.allocated_plot and site.allocated_plot.park else "",
            "initial_contract_amount": site.contracts_data[0].contract_amount if len(site.contracts_data) > 0 and site.contracts_data[0].contract_amount else 0,
            "initial_contract_currency": site.contracts_data[0].contract_currency if len(site.contracts_data) > 0 else "",
            "initial_contract_signing_date": site.contracts_data[0].signing_date if len(site.contracts_data) > 0 and site.contracts_data[0].signing_date else "",
            "payment_status": site.contracts_data[0].contract_payments.all().first().payment_status if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else "",
            "payment_modality": site.contracts_data[0].contract_payments.all().first().payment_modality if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else "",
            "number_of_installments": site.contracts_data[0].contract_payments.all().first().number_of_installments if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "total_amount_paid": site.contracts_data[0].contract_payments.all().first().total_amount_paid if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "total_amount_unpaid": site.contracts_data[0].contract_payments.all().first().total_amount_unpaid if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "amount_overdued": site.contracts_data[0].contract_payments.all().first().amount_overdued if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "days_in_arrears": site.contracts_data[0].contract_payments.all().first().days_in_arrears if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "accrued_penalties": site.contracts_data[0].contract_payments.all().first().accrued_penalties if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "paid_penalties": site.contracts_data[0].contract_payments.all().first().paid_penalties if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "next_payment_date": site.contracts_data[0].contract_payments.all().first().next_payment_date if len(site.contracts_data) > 0 and site.contracts_data[0].contract_payments.all().first() else 0,
            "operational_years": site.contracts_data[0].operational_years if len(site.contracts_data) > 0 and site.contracts_data[0].operational_years else 0,
            "investor_origin_country": site.company.investor_origin_country if site.company.investor_origin_country else "",
            "rdb_registeration_date": site.company.registeration_date if site.company.registeration_date else "",
            "benefited_electricity_tarrif": "Yes" if site.benefited_electricity_tarrif else "No",
            "operational_start_date": site.operational_start_date if site.operational_start_date else "",
            "construction_start_date": site.construction_start_date if site.construction_start_date else "",
            "plot_size": format_number_two(site.allocated_plot.plot_size) if site.allocated_plot and site.allocated_plot.plot_size else 0,
            "is_land_title_issued": "Yes" if site.allocated_plot and site.allocated_plot.is_land_title_issued else "No",
            "land_title_status": site.allocated_plot.land_title_status if site.allocated_plot else "",
            "economic_sector": "",
            "economic_sub_sector": "",
            "product_name": "",
            "product_brand_name": "",
            "packaging_material": "",
            "production_installed_capacity": 0,
            "production_installed_capacity_unit": "",
            "production_installed_capacity_period": "",
            "production_line_tech": "",
            "coordinates": site.allocated_plot.partitioned_plots.all().first().coordinates if site.allocated_plot and site.allocated_plot.partitioned_plots.all().first() else [[[]]],

        }
        
        if len(site.products_data) > 0:
            for p in site.products_data:
                site_data_temp = site_data.copy()
                site_data_temp["economic_sector"] = p.product.sub_sector.economic_sector.name
                site_data_temp["economic_sub_sector"] = p.product.sub_sector.name
                site_data_temp["product_name"] = p.product.name
                site_data_temp["product_brand_name"] = p.product_brand_name
                site_data_temp["packaging_material"] = p.packaging_material
                site_data_temp["production_installed_capacity"] = format_number_two(p.production_installed_capacity)
                site_data_temp["production_installed_capacity_unit"] = p.production_installed_capacity_unit
                site_data_temp["production_installed_capacity_period"] = p.production_installed_capacity_period
                site_data_temp["production_line_tech"] = p.production_line_tech
                results.append(site_data_temp)
        else:
            results.append(site_data)


    return results