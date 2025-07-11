import json
import os
import traceback
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.db.models import Prefetch
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from system_management.models import (User, AdministrativeUnit, 
                                      EconomicSector, EconomicSubSector)
from system_management.utils import generate_random_code
from .models import (IndustryEconomicZone, PartitionedPlot, 
                    CompanyProfile, CompanySite, 
                    LandRequestInformation, IndustryProduct,
                    AllocatedPlot, IndustryAttachment, 
                    IndustryEconomicSector, ContractPaymentInstallment,
                    IndustryContract, IndustryContractPayment, 
                    PaymentInstallmentTransaction)
from automation.models import BulkUploadJob
from system_management.models import IndustrialZone, Product
from .utils import (load_countries, get_zones_and_partitioned_plots_in_park,
                    record_allocated_plot_from_request, record_industry_in_plot_from_request,
                    get_base_domain, create_payment_installment, convert_datetime_timezone,
                    record_payment_transaction)
from .tasks import process_geojson_plots
from .fixtures import (PRODUCT_QUANTITIES, PRODUCT_PACKAGING_MATERIAL,
                       PRODUCT_QUANTITIES_UNITS_MAP, PRODUCT_PRODUCTION_CAPACITY_PERIOD,
                       PRODUCT_PRODUCTION_CAPACITY_UNIT)

from  system_management.permissions import (check_role_permission_on_module_decorator, 
                                            is_user_permitted)
from trade.views import clean_csv_file
from .tasks import process_industry_profile
from .extractor_data import get_optimized_company_data


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0012", 3)
def industrial_parks_list(request):
    # paginated_data = get_optimized_company_data(page_number=1, page_size=50)
    # df = pd.DataFrame(paginated_data)
    # df.to_csv("industrial_park_test_extracted_dataset.csv", index=False)
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0012", 1):
            name = request.POST.get("name")
            category = request.POST.get("category")
            total_area = request.POST.get("total_area")
            leasable_area = request.POST.get("leasable_area")
            province = AdministrativeUnit.objects.filter(category="PROVINCE", id=request.POST.get("province").strip()).first()
            district = AdministrativeUnit.objects.filter(category="DISTRICT", id=request.POST.get("district").strip()).first()
            sector = AdministrativeUnit.objects.filter(category="SECTOR", id=request.POST.get("sector").strip()).first()
            cell = AdministrativeUnit.objects.filter(category="CELL", id=request.POST.get("cell").strip()).first()

            if IndustryEconomicZone.objects.filter(name__iexact=name, category__iexact=category).first():
                messages.info(request, message=f"{name.title()} {category.title()} already exists.")
            else:
                IndustryEconomicZone.objects.create(
                    name=name,
                    category=category,
                    total_land_size=total_area,
                    leasable_land=leasable_area,
                    province=province.name,
                    district=district.name,
                    sector=sector.name,
                    cell=cell.name
                )
                messages.success(request, message=f"{name.title()} {category.title()} added successfully!")
        else:
            messages.error(request, message="You don't have permission to register industrial park/special economic zone")
        return redirect("industry:parks-list")
    
    provinces = AdministrativeUnit.objects.filter(category="PROVINCE").order_by("name")
    districts = AdministrativeUnit.objects.filter(category="DISTRICT").order_by("name")
    sectors = AdministrativeUnit.objects.filter(category="SECTOR").order_by("name")
    cells = AdministrativeUnit.objects.filter(category="CELL").order_by("name")
    jobs = BulkUploadJob.objects.filter(category="PARTITIONED_PLOTS").order_by("-created_at")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'industrial_parks_list')
    page_number = request.GET.get('page', 1)
    ordering = ("category", "name")

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(IndustryEconomicZone.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    industrial_parks = IndustryEconomicZone.objects.filter(id__in=current_ids).order_by(*ordering)
    
    context = {
        "jobs": jobs,
        "industrial_parks": industrial_parks,
        "page": current_page,
        'tab_type': active_tab,
        "provinces": provinces,
        "districts": json.dumps(list(districts.values())),
        "sectors": json.dumps(list(sectors.values())),
        "cells": json.dumps(list(cells.values())),
    }
    return render(request, "industry/park/industrial_parks_list.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0012", 3)
def industrial_park_detail(request, park_id):
    industrial_park = IndustryEconomicZone.objects.filter(id=park_id).first()
    zones = IndustrialZone.objects.all().order_by("name")

    if industrial_park is None:
        return redirect("industry:parks-list") 
    
    plots = PartitionedPlot.objects.filter(park=industrial_park)
    available_plots = len(plots.filter(is_allocated=False))
    all_plots = len(plots)

    page_number = request.GET.get('page', 1)
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    partitioned_plots_tab_type = "partitioned_plots_tab"
    allocated_plots_tab_type = "allocated_plots_tab"
    industries_in_park_tab_type = "industries_in_park_tab"

    # Layer 1: Cache ordered ID list with versioning
    cache_key_partitioned_plots_ids = f"{partitioned_plots_tab_type}_ids"
    cache_key_allocated_plots_ids = f"{allocated_plots_tab_type}_ids"
    cache_key_industries_in_park_ids = f"{industries_in_park_tab_type}_ids"
    ordered_partitioned_plots_ids = cache.get(cache_key_partitioned_plots_ids)
    ordered_allocated_plots_ids = cache.get(cache_key_allocated_plots_ids)
    ordered_industry_in_park_ids = cache.get(cache_key_industries_in_park_ids)

    if page_number == 1 or not ordered_partitioned_plots_ids or not ordered_allocated_plots_ids or not ordered_industry_in_park_ids:
        ordered_partitioned_plots_ids = list(PartitionedPlot.objects.filter(park=industrial_park).values_list('id', flat=True))
        ordered_allocated_plots_ids = list(AllocatedPlot.objects.filter(park=industrial_park).values_list('id', flat=True))
        ordered_industry_in_park_ids = list(CompanySite.objects.filter(allocated_plot__id__in=ordered_allocated_plots_ids).values_list('id', flat=True))
        cache.set(cache_key_partitioned_plots_ids, ordered_partitioned_plots_ids, CACHE_TIMEOUT)
        cache.set(cache_key_allocated_plots_ids, ordered_allocated_plots_ids, CACHE_TIMEOUT)
        cache.set(cache_key_industries_in_park_ids, ordered_industry_in_park_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    partitioned_plot_paginator = Paginator(ordered_partitioned_plots_ids, PAGE_SIZE)
    allocated_plot_paginator = Paginator(ordered_allocated_plots_ids, PAGE_SIZE)
    industry_paginator = Paginator(ordered_industry_in_park_ids, PAGE_SIZE)

    try:
        current_partitioned_plot_page = partitioned_plot_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_partitioned_plot_page = partitioned_plot_paginator.page(1)
    
    try:
        current_allocated_plot_page = allocated_plot_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_allocated_plot_page = allocated_plot_paginator.page(1)

    try:
        current_industry_page = industry_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_industry_page = industry_paginator.page(1)

    current_partitioned_plot_ids = current_partitioned_plot_page.object_list
    current_allocated_plot_ids = current_allocated_plot_page.object_list
    current_industry_ids = current_industry_page.object_list

    park_partitioned_plots = PartitionedPlot.objects.filter(id__in=current_partitioned_plot_ids).order_by("plot_number", "zone__name", "-is_allocated")
    allocated_plots = AllocatedPlot.objects.filter(id__in=current_allocated_plot_ids).order_by("-recorded_date")
    park_industries = CompanySite.objects.filter(id__in=current_industry_ids).order_by("company__name")

    context = {
        "industrial_park": industrial_park,
        "park_partitioned_plots": park_partitioned_plots,
        "partitioned_plots_page": current_partitioned_plot_page,
        "zones": zones,
        "allocated_plots": allocated_plots,
        "allocated_plots_page": current_allocated_plot_page,
        "park_industries": park_industries,
        "industries_in_park_page": current_industry_page,
        "available_plots": available_plots,
        "all_plots": all_plots

    }

    return render(request, "industry/park/industrial_park_details.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0012", 3)
def record_partitioned_plot(request, park_id):
    
    if request.method == "POST":
        if is_user_permitted(request.user, "0012", 2):
            upi_status = request.POST.get("upi_status")
            plot_number = request.POST.get("plot_number")
            plot_upi = request.POST.get("plot_upi")
            plot_size = request.POST.get("plot_size")
            zone_id = request.POST.get("zone", " -").split("-")[0]

            park = IndustryEconomicZone.objects.filter(id=park_id).first()
            zone = IndustrialZone.objects.filter(id=zone_id).first()
            if park is not None and zone is not None:
                PartitionedPlot.objects.create(
                    plot_number=plot_number,
                    partitioned_plot_upi=plot_upi,
                    upi_status=upi_status,
                    plot_size=plot_size,
                    zone=zone,
                    park=park
                )
                messages.success(request, message="Partitioned plot added successfully!")
            if park is None:
                messages.info(request, message="The industrial park/economic zone should be recorded first!")
                return redirect("industry:parks-list")
        else:
            messages.error(request, message="You don't have permission to modify the industrial park/special economic zone")
        
        redirect_url = reverse("industry:park-details", args=(park.id, ))
        return redirect(f"{redirect_url}#partitioned-plots")
    

def clean_geojson_file(request):
    MAX_SIZE = 60 * 1024 * 1024 # 50MB
    file =  request.FILES.get('geojson_file', None)
    if not file.name.endswith('.geojson') and not file.name.endswith('.json'):
        return None, 'Only GEOJSON and JSON files are allowed'
    
    if file.size > MAX_SIZE:
        return None, f'File size exceeds {MAX_SIZE} MBs. Split the file into chuncks and upload one by one'
    
    return file, None

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0012", 3)
def partitioned_plots_upload_view(request):
    if request.method == "POST":
        file, message = clean_geojson_file(request)
        park = request.POST.get("park", -1)
        if file:
            upload_job = BulkUploadJob.objects.create(user=request.user, category="PARTITIONED_PLOTS", uploaded_file=file)
            process_geojson_plots(upload_job.id, park_id=park)
            messages.info(request, "Bulk upload has started. You can monitor the status here.")

            redirect_url = reverse('industry:parks-list')
            return redirect(f"{redirect_url}#upload-plots-in-parks")
        else:
            messages.error(request, f"Invalid form submission. Please check the file. {message}")
            return redirect("industry:parks-list")
        
    parks = IndustryEconomicZone.objects.all().order_by("name")
    context = {
        'parks': parks
    }
    return render(request, 'industry/park/upload_partitioned_plots.html', context)
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 3)
def companies_industries_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0013", 1):
            try:
                name = request.POST.get("name", "").strip()
                tin_number = request.POST.get("tin_number", "").strip()
                category = request.POST.get("category", "").strip()
                phone_contact = request.POST.get("phone_contact", "").strip()
                email_contact = request.POST.get("email_contact", "").strip().lower()
                registeration_date = request.POST.get("registeration_date", None).strip()
                investor_origin_country = request.POST.get("selected_items")
                company_size = request.POST.get("company_size", "").strip()

                first_name = request.POST.get("first_name", "").strip()
                last_name = request.POST.get("last_name", "").strip()
                managing_director_id = request.POST.get("managing_director_id", "").strip()
                headquaters_province = request.POST.get("headquaters_province", "").strip()
                headquaters_district = request.POST.get("headquaters_district", "").strip()
                headquaters_sector = request.POST.get("headquaters_sector", "").strip()
                headquaters_cell = request.POST.get("headquaters_cell", "").strip()
                headquaters_village = request.POST.get("headquaters_village", "").strip()

                headquaters_province = AdministrativeUnit.objects.filter(category="PROVINCE", id=headquaters_province).first().name
                headquaters_district = AdministrativeUnit.objects.filter(category="DISTRICT", id=headquaters_district).first().name
                headquaters_sector = AdministrativeUnit.objects.filter(category="SECTOR", id=headquaters_sector).first().name
                headquaters_cell = AdministrativeUnit.objects.filter(category="CELL", id=headquaters_cell).first().name
                headquaters_village = AdministrativeUnit.objects.filter(category="VILLAGE", id=headquaters_village).first().name


                if len(registeration_date.strip()) < 6:
                    registeration_date = None

                user = User.objects.filter(email=email_contact).first()
                if user is None:
                    password = generate_random_code()
                    user = User(
                        user_category="COMPANY",
                        change_password_required=True,
                        first_name=first_name,
                        last_name=last_name,
                        email=email_contact
                    )
                    user.set_password(password)
                    user.save()
                    profile = CompanyProfile(
                        name=name,
                        category=category,
                        tin_number=tin_number,
                        user=user,
                        phone_contact=phone_contact,
                        email_contact=email_contact,
                        registeration_date=registeration_date,
                        investor_origin_country=investor_origin_country,
                        company_size=company_size,
                        managing_director_id=managing_director_id,
                        headquaters_province=headquaters_province,
                        headquaters_district=headquaters_district,
                        headquaters_sector=headquaters_sector,
                        headquaters_cell=headquaters_cell,
                        headquaters_village=headquaters_village,
                        managing_director_name=f"{first_name} {last_name}"
                    )
                    profile.save()
                    message = f"New company profile with TIN: {tin_number} and name: {name} created successfully!"
                    messages.success(request, message=message)
                else:
                    message = f"The contact email: {email_contact} is alreay taken, provide a different email"
                    messages.info(request, message=message)
            except Exception as e:
                message = f"Error: {str(e)}"
                messages.error(request, message=message)
        else:
            messages.error(request, message="You don't have permission to register company profile")
        
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-profiles")
        
    provinces = AdministrativeUnit.objects.filter(category="PROVINCE").order_by("name")
    districts = AdministrativeUnit.objects.filter(category="DISTRICT").order_by("name")
    sectors = AdministrativeUnit.objects.filter(category="SECTOR").order_by("name")
    cells = AdministrativeUnit.objects.filter(category="CELL").order_by("name")
    villages = AdministrativeUnit.objects.filter(category="VILLAGE").order_by("name")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    industry_profiles_tab_type = "industry_profiles_tab"
    industries_tab_type = "industries_tab"

    # Layer 1: Cache ordered ID list with versioning
    cache_key_profile_ids = f"{industry_profiles_tab_type}_ids"
    cache_key_industries_ids = f"{industries_tab_type}_ids"
    ordered_profile_ids = cache.get(cache_key_profile_ids)
    ordered_industry_ids = cache.get(cache_key_industries_ids)

    if page_number == 1 or not ordered_profile_ids or not ordered_industry_ids:
        ordered_profile_ids = list(CompanyProfile.objects.values_list('id', flat=True))
        ordered_industry_ids = list(CompanySite.objects.values_list('id', flat=True))
        cache.set(cache_key_profile_ids, ordered_profile_ids, CACHE_TIMEOUT)
        cache.set(cache_key_industries_ids, ordered_industry_ids, CACHE_TIMEOUT)
    

    # Paginate IDs
    profile_paginator = Paginator(ordered_profile_ids, PAGE_SIZE)
    industry_paginator = Paginator(ordered_industry_ids, PAGE_SIZE)
    try:
        current_profile_page = profile_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_profile_page = profile_paginator.page(1)

    try:
        current_industry_page = industry_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_industry_page = industry_paginator.page(1)

    current_profile_ids = current_profile_page.object_list
    current_industry_ids = current_industry_page.object_list

    companies_industries_profiles = CompanyProfile.objects.filter(id__in=current_profile_ids).order_by("name")
    park_industries = CompanySite.objects.filter(id__in=current_industry_ids).order_by("company__name")
    jobs = BulkUploadJob.objects.filter(category="INDUSTRY_PROFILE").order_by("-created_at")

    context = {
        "companies_industries_profiles": companies_industries_profiles,
        "park_industries": park_industries,
        "industries_tab_type": industries_tab_type,
        "industry_profile_tab_type": industry_profiles_tab_type,
        "industry_page": current_industry_page,
        "industry_profile_page": current_profile_page,
        "search_items": json.dumps(load_countries()),
        "parent": "none",
        "provinces": provinces,
        "districts": json.dumps(list(districts.values())),
        "sectors": json.dumps(list(sectors.values())),
        "cells": json.dumps(list(cells.values())),
        "villages": json.dumps(list(villages.values())),
        "jobs": jobs
    }
    return render(request, "industry/industries/industries_companies.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 1)
def bulk_industry_profiles_upload(request):
    if request.method == "POST":
        file, message = clean_csv_file(request)
        if file:
            upload_job = BulkUploadJob.objects.create(user=request.user, category="INDUSTRY_PROFILE", uploaded_file=file)
            process_industry_profile(upload_job.id)
            messages.info(request, "Bulk upload has started. You can monitor the status here.")

            redirect_url = reverse('industry:companies-industries-list')
            return redirect(f"{redirect_url}#upload-inudstry-profiles")
        else:
            messages.error(request, f"Invalid form submission. Please check the file. {message}")
            return redirect("industry:companies-industries-list")
        
    return render(request, "industry/industries/upload_profiles.html")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 3)
def industry_profile_details(request, profile_id):
    industry = CompanyProfile.objects.filter(id=profile_id).first()
    branches = CompanySite.objects.filter(company=industry)
    attachments = IndustryAttachment.objects.filter(industry__in=branches).order_by("category","-uploaded_date", "name")
    context = {
        "industry": industry,
        "branches": branches,
        "attachments": attachments,
    }
    return render(request, "industry/industry_profile_detail_page/profile_detail_page.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 3)
def add_industry_not_in_park(request):
    if request.method == "POST":
        if is_user_permitted(request.user, "0013", 1):
            try:
                tin_number = request.POST.get("industry", " || ").split("||")[0]
                occupied_space = request.POST.get("occupied_space")
                longitude = request.POST.get("longitude", "")
                latitude = request.POST.get("latitude", "")
                province = AdministrativeUnit.objects.filter(category="PROVINCE", id=request.POST.get("province").strip()).first()
                district = AdministrativeUnit.objects.filter(category="DISTRICT", id=request.POST.get("district").strip()).first()
                sector = AdministrativeUnit.objects.filter(category="SECTOR", id=request.POST.get("sector").strip()).first()
                cell = AdministrativeUnit.objects.filter(category="CELL", id=request.POST.get("cell").strip()).first()

                investment_amount = request.POST.get("investment_amount")
                investment_currency = request.POST.get("investment_currency")

                industry = CompanyProfile.objects.get(tin_number=tin_number)

                if len(longitude.strip()) < 2:
                    longitude = None
                if len(latitude.strip()) < 2:
                    latitude = None
                
                if len(occupied_space.strip()) < 2:
                    occupied_space = None
                
                if len(investment_amount.strip()) < 2:
                    investment_amount = None
                    investment_currency = None

                CompanySite.objects.create(
                    company=industry,
                    longitude=longitude,
                    latitude=latitude,
                    province=province.name,
                    district=district.name,
                    sector=sector.name,
                    cell=cell.name,
                    occupied_space=occupied_space,
                    investment_amount=investment_amount,
                    investment_currency=investment_currency,
                    is_in_park=False
                )

                messages.success(request, message="New {industry.name} industry location has been recorded successfully!")
            except Exception as e:
                messages.error(request, message=f"Error: {str(e)}")
        else:
            messages.error(request, message="You don't have permission to add industry")

    redirect_url = reverse('industry:companies-industries-list')
    return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 3)
def industry_details(request, industry_id):
    industry = CompanySite.objects.filter(id=industry_id).first()
    attachments = IndustryAttachment.objects.filter(industry=industry).order_by("category","-uploaded_date", "name")
    industry_economic_sub_sectors = IndustryEconomicSector.objects.filter(industry=industry).order_by("sector__economic_sector__name", "sector__name")
    economic_sectors = EconomicSector.objects.all()
    sub_sectors = EconomicSubSector.objects.exclude(id__in=[sector.id for sector in industry_economic_sub_sectors])
    contracts = IndustryContract.objects.filter(industry=industry).order_by("signing_date")
    products = Product.objects.filter(sub_sector__in=industry_economic_sub_sectors.values_list("sector", flat=True)).order_by("name")
    search_items = []
    for sector in sub_sectors:
        search_items.append(f"{sector.id}|{sector.name.strip().replace(',', "-")}|{sector.economic_sector.id}")
    
    industry_products = IndustryProduct.objects.filter(industry=industry).select_related("industry", "product").order_by("product__name", "product_brand_name")

    context = {
        "industry": industry,
        "parent": "economic-sector",
        "industry_economic_sub_sectors": industry_economic_sub_sectors,
        "search_items": json.dumps(search_items),
        "economic_sectors": economic_sectors,
        "attachments": attachments,
        "industry_products": industry_products,
        "products": products,
        "PRODUCT_PACKAGING_MATERIAL": [ m[0] for m in PRODUCT_PACKAGING_MATERIAL],
        "PRODUCT_PRODUCTION_CAPACITY_PERIOD": [ p[0] for p in PRODUCT_PRODUCTION_CAPACITY_PERIOD],
        "PRODUCT_QUANTITIES": [m[0] for m in PRODUCT_QUANTITIES],
        "PRODUCT_PRODUCTION_CAPACITY_UNIT": [unit[0] for unit in PRODUCT_PRODUCTION_CAPACITY_UNIT],
        "PRODUCT_QUANTITIES_UNITS_MAP": json.dumps(PRODUCT_QUANTITIES_UNITS_MAP),
        "contracts": contracts
    }
    return render(request, "industry/industry_detail_page/industry_details.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 4)
def delete_industry(request, industry_id):
    try:
        industry = CompanySite.objects.get(id=industry_id)
        contracts = IndustryContract.objects.filter(industry=industry).order_by("signing_date")
        if len(contracts) > 0:
            message = "This industry cannot be deleted because it has some historical data"
            messages.info(request, message=message)
        else:
            industry.delete()
            message = "Industry deleted successfully!"
            messages.success(request, message=message)
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")
    except Exception as e:
        message = f"[ERROR] {str(e)}"
        messages.error(request, message=message)
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")



@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 2)
def add_industry_economic_sectors(request, industry_id):
    try:
        industry = CompanySite.objects.get(id=industry_id)
        if request.method == "POST":
            selected_sectors = request.POST.get("selected_items")
            sectors_splits = selected_sectors.split(",")
            for split in sectors_splits:
                sector_id = split.split("|")[0]
                sector = EconomicSubSector.objects.filter(id=sector_id).first()
                if sector is not None:
                    IndustryEconomicSector.objects.create(industry=industry, sector=sector)
                    messages.success(request, message=f"New economic sector: {sector.name} added successfully!")
                else:
                    messages.info(request, message=f"Sector with id {sector_id} not found")

            redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
            return redirect(f"{redirect_url}#industry-detail")
    except Exception as e:
        messages.error(request, message=f"Error: {str(e)}")
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 2)
def add_industry_product(request, industry_id):
    try:
        industry = CompanySite.objects.get(id=industry_id)
        if request.method == "POST":
            product = request.POST.get("product")
            brand_name = request.POST.get("brand_name")
            quantity_measure = request.POST.get("quantity_measure")
            quantity_measure_unit = request.POST.get("quantity_measure_unit")
            quantity = request.POST.get("quantity")
            packaging_material = request.POST.get("packaging_material")
            production_installed_capacity = request.POST.get("production_installed_capacity")
            production_installed_capacity_unit = request.POST.get("production_installed_capacity_unit")
            production_installed_capacity_period = request.POST.get("production_installed_capacity_period")
            production_line_tech = request.POST.get("production_line_tech")

            
            if product and len(product.strip()) > 5 and len(product.split("||")) > 1:
                product_code = product.split("||")[0].strip()
                product = Product.objects.filter(product_code=product_code).first()

                if product:
                    IndustryProduct.objects.create(
                        industry=industry,
                        product=product,
                        product_brand_name=brand_name.strip(),
                        quantity=quantity,
                        quantity_measure=quantity_measure,
                        quantity_measure_unit=quantity_measure_unit,
                        packaging_material=packaging_material,
                        production_installed_capacity=production_installed_capacity,
                        production_installed_capacity_unit=production_installed_capacity_unit,
                        production_installed_capacity_period=production_installed_capacity_period,
                        production_line_tech=production_line_tech
                    )
                    message = f"New product has been added for {industry.company.name}"
                    messages.success(request, message=message)
                else:
                    message = "Unable to add a new product, check if you have selected the product instead of typing"
                    messages.info(request, message=message)
            else:
                message = "You should select the product from the list."
                messages.info(request, message=message)

        redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
        return redirect(f"{redirect_url}#product-industry")
    except CompanySite.DoesNotExist:
        messages.error(request, message="Induststry location selected does not exist")
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")
    except Exception as e:
        messages.error(request, message=f"Error: {str(e)}")
        redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
        return redirect(f"{redirect_url}#product-industry")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 2)
def delete_industry_product(request, product_id):
    try:
        product = IndustryProduct.objects.get(id=product_id)
        industry = product.industry
        product.delete()
        messages.success(request, message="Product deleted successfully!")
        redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
        return redirect(f"{redirect_url}#product-industry")
    except Exception as e:
        messages.error(request, message=f"Error: {str(e)}")
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 2)
def record_industry_attachment(request, industry_id):
    industry = CompanySite.objects.filter(id=industry_id).first()
    if industry is not None:
        if request.method == "POST":
            base_domain = get_base_domain(request)
            category = request.POST.get("category")
            name = request.POST.get("name", None)
            document = request.FILES.get("document")
            comment = request.POST.get("comment")

            document_name = category
            if name is not None and category.lower() == "other supporting document":
                document_name = name
            else:
                category = "Main Document"

            attachment = IndustryAttachment(
                industry=industry,
                name=document_name,
                category=category,
                comment=comment,
                document=document
            )
            attachment.save()
            attachment.document_url = f"{base_domain}/{attachment.document.url.lstrip('/')}"
            attachment.save()
            messages.success(request, message="New attached added successfully")
            redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
            return redirect(f"{redirect_url}#attachment-industry")
    else:
        messages.info(request, message=f"Industry with ID={industry_id} does not exist")
    redirect_url = reverse('industry:companies-industries-list')
    return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0013", 2)
def delete_industry_attachment(request, attachment_id):
    try:
        attachment = IndustryAttachment.objects.get(id=attachment_id)
        industry = attachment.industry

        if os.path.isfile(attachment.document.path) and os.path.exists(attachment.document.path):
            os.remove(attachment.document.path)
        attachment.delete()
        messages.success(request, message="Attachment deleted successfully!")
        redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
        return redirect(f"{redirect_url}#attachment-industry")
    except Exception as e:
        messages.error(request, message=f"Error: {str(e)}")
        print(traceback.print_exc())
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0015", 3)
def land_request(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0015", 1):
            try:
                land_owner = request.POST.get("land_owner")
                request_date = request.POST.get("request_date", None)
                request_closure_date = request.POST.get("request_closure_date", None)
                requested_land_size = request.POST.get("requested_land_size").strip()
                park = request.POST.get("park")
                zone = request.POST.get("zone")

                park = IndustryEconomicZone.objects.filter(id=park).first()
                zone = IndustrialZone.objects.filter(id=zone).first()
                land_owner = CompanyProfile.objects.filter(id=land_owner).first()

                if park is None:
                    messages.info(request, message="Selected park/special economic zone does not exist")
                
                if zone is None:
                    messages.info(request, message="Selected zoning does not exist")
                
                if land_owner is None:
                    messages.info(request, message="Industry profile was not found!")

                if park and zone and land_owner:
                    if len(request_date.strip()) < 6:
                        request_date = None
                    if len(request_closure_date.strip()) < 6:
                        request_closure_date = None
                    
                    land_request_obj = LandRequestInformation(
                    land_owner=land_owner,
                    requested_land_size=requested_land_size,
                        request_date=request_date,
                        request_closure_date=request_closure_date,
                        park=park,
                        zone=zone
                    )
                    land_request_obj.save()
                    messages.success(request, message="New land information request added successfully!")
            except Exception as e:
                messages.error(request, message=f"Error: {{str(e)}}")
        else:
            messages.error(request, message="You don't have permission to add land information request")

    company_profiles = CompanyProfile.objects.all().order_by("name")
    parks = IndustryEconomicZone.objects.all()

    zones, _ = get_zones_and_partitioned_plots_in_park()

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'land_information_list')
    page_number = request.GET.get('page', 1)
    ordering = ("request_date", "recorded_date")

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(LandRequestInformation.objects.order_by(*ordering).values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)
    
    current_ids = current_page.object_list
    land_requests = LandRequestInformation.objects.filter(id__in=current_ids).order_by(*ordering)

    context = {
        "zones": json.dumps(zones),
        "parks": parks,
        "page": current_page,
        "company_profiles": company_profiles,
        "land_requests": land_requests
    }
    return render(request, "industry/land_request/land_request_list.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0015", 3)
def land_request_detail(request, land_request_id, flag=None):
    land_request = LandRequestInformation.objects.filter(id=land_request_id).first()
    if land_request is None:
        messages.info(request, message="Land information request was not found")
        return redirect("industry:land-requests")
    
    if flag and flag.upper() == "ALLOCATE_PLOT" and request.method == "POST":
        succeed = record_allocated_plot_from_request(request=request, land_request=land_request)

        if not succeed:
            messages.info(request, message="Unable to recorded allocate plot")
        else:
            messages.success(request, message="Allocated plot recorded successfully!")
    elif flag and flag.upper() == "ADD_INDUSTRY" and request.method == "POST":
        succeed = record_industry_in_plot_from_request(request=request)

        if not succeed:
            messages.info(request, message="Unable to add industry in the allocated plot!")
        else:
            messages.success(request, message=f"The industry added in the allocated plot successfully!")
    
    parks = IndustryEconomicZone.objects.all().order_by("name")
    zones, partitioned_plots = get_zones_and_partitioned_plots_in_park()
    allocated_plot = AllocatedPlot.objects.filter(land_request=land_request).first()
    park_industries = CompanySite.objects.filter(allocated_plot=allocated_plot).order_by("company__name")
    industries = CompanyProfile.objects.exclude(tin_number__in=[ comp.company.tin_number for comp in park_industries]).order_by("name")
    context = {
        "land_request": land_request,
        "allocated_plot": allocated_plot,
        "parks": parks,
        "industries": industries,
        "park_industries": park_industries,
        "zones": json.dumps(zones),
        "partitioned_plots": json.dumps(partitioned_plots)
    }
    return render(request, "industry/land_request/land_request_details.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0014", 3)
def contracts_list(request):
    if request.method == "POST":
        if is_user_permitted(request.user, "0014", 1):
            industry_id = request.POST.get("industry")
            contract_type = request.POST.get("contract_type")
            signing_date = request.POST.get("signing_date")
            contract_amount = request.POST.get("contract_amount")
            contract_currency = request.POST.get("contract_currency")
            operational_years = request.POST.get("operational_years")
            contract_document = request.FILES.get("document")

            industry = CompanySite.objects.filter(id=industry_id).first()

            if industry is not None:
                base_domain = get_base_domain(request)
                contract = IndustryContract(
                    industry=industry,
                    contract_type=contract_type,
                    signing_date=signing_date,
                    contract_amount=contract_amount,
                    contract_currency=contract_currency,
                    operational_years=operational_years,
                    contract_document=contract_document
                )

                contract.save()
                contract.contract_document_url = f"{base_domain}/{contract.contract_document.url.lstrip('/')}"
                contract.save()

                messages.success(request, message="Contract saved successfully!")
                redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
                return redirect(f"{redirect_url}#contract-detail")
            else:
                messages.info(request, message="Unable to save the contract because the industry to be added on the contract does not exists")
        else:
            messages.error(request, message="You don't have permission to add contract")
        return redirect("industry:companies-industries-list")
    
    return redirect("industry:companies-industries-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0014", 3)
def contracts_detail(request, contract_id):
    contract = IndustryContract.objects.filter(id=contract_id).prefetch_related(
        Prefetch("contract_payments", queryset=IndustryContractPayment.objects.prefetch_related("payment_installments"))
    ).first()

    if contract is None:
            messages.info(request, message="contract could not be found!")
            return redirect("industry:companies-industries-list")
        
    if request.method == "POST":
        if is_user_permitted(request.user, "0014", 2):
            payment_modality = request.POST.get("payment_modality")
            payment_start_date = request.POST.get("payment_start_date")
            irembo_application_number = request.POST.get("irembo_application_number", None)
            contract_payment = IndustryContractPayment(
                contract=contract,
                total_amount_to_pay=contract.contract_amount,
                total_amount_unpaid=contract.contract_amount,
                payment_currency=contract.contract_currency,
                payment_modality=payment_modality,
                number_of_installments=1 if payment_modality.upper() == "SINGLE FULL PAYMENT" else 6,
                irembo_application_number=irembo_application_number
            )
            contract_payment.save()
            payment_start_date = datetime.strptime(payment_start_date, "%Y-%m-%d")
            payment_start_date = convert_datetime_timezone(payment_start_date).date() # convert to timezone time

            payment_dates = []
            if payment_modality == "SINGLE FULL PAYMENT": # create one payment installment
                payment_dates.append(payment_start_date)
            elif payment_modality == "INSTALLMENTS": # create six payment installments
                payment_dates.append(payment_start_date)
                for i in range(5): # creating 6 installments dates
                    payment_dates.append(
                        payment_dates[i] + relativedelta(years=1)
                    )
            else:
                message.info(request, message="Wrong payment modality selected")
                redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
                return redirect(f"{redirect_url}#contract-detail")
            
            succeeded, total_amount, message = create_payment_installment(contract_payment=contract_payment, installments_dates=payment_dates)
            if not succeeded:
                contract_payment.delete()
                messages.info(request, "Unable to create payment installments")
            else:
                if total_amount !=  contract_payment.total_amount_to_pay:
                    contract_payment.total_amount_to_pay = total_amount
                    contract_payment.total_amount_unpaid = total_amount
                    contract_payment.contract.contract_amount = contract_payment.total_amount_to_pay  
                    contract_payment.save() 
                    contract_payment.contract.save() # update the contract as well
                messages.success(request, message="Payment isntallments created successfully!")
            
            redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
        else:
            messages.error(request, message="You don't have permission to modify contract/adding payment to the contract")
        return redirect(f"{redirect_url}#contract-payments")

    payment = contract.contract_payments.first()
    if payment is not None:
        payment_installments = payment.payment_installments.all().order_by("expected_payment_date") if payment else ContractPaymentInstallment.objects.none()
        transactions = PaymentInstallmentTransaction.objects.filter(
            installment__contract_payment=payment).select_related("installment").order_by("installment__expected_payment_date")
        installment_payment_amount = None
        unpaid_installments = None
        transaction_to_refund = PaymentInstallmentTransaction.objects.filter(id=payment.transaction_to_refund).first()
            
        unpaid_installment = payment_installments.filter(payment_status__in=("PARTIALLY PAID", "NOT PAID")).first()
        if unpaid_installment is None:
            unpaid_installments = list(payment_installments.filter(accrued_penalties__gt=0))
            for install_ in unpaid_installments:
                if install_.accrued_penalties != install_.paid_penalties:
                    unpaid_installment = install_
                    break
        
        if unpaid_installment:
            if unpaid_installment.actual_paid_amount:
                installment_payment_amount = unpaid_installment.expected_payment_amount - unpaid_installment.actual_paid_amount
            else:
                installment_payment_amount = unpaid_installment.expected_payment_amount
            
            if installment_payment_amount is None:
                if unpaid_installment.accrued_penalties and unpaid_installment.accrued_penalties > 0:
                    if unpaid_installment.paid_penalties and unpaid_installment.paid_penalties > 0:
                        installment_payment_amount = unpaid_installment.accrued_penalties - unpaid_installment.paid_penalties
                    else:
                        installment_payment_amount = unpaid_installment.accrued_penalties
                else:
                    installment_payment_amount = 0
    else:
        payment = None
        payment_installments = []
        unpaid_installment = None
        installment_payment_amount = 0
        transactions = []
        transaction_to_refund = None

    context = {
        "contract": contract,
        "payment": payment,
        "payment_installments": payment_installments,
        "unpaid_installment": unpaid_installment,
        "installment_payment_amount": installment_payment_amount,
        "transactions": transactions,
        "transaction_to_refund": transaction_to_refund
    }

    return render(request, "industry/contract/contract_details.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0014", 2)
def make_payment_transaction(request):
    if request.method == "POST":
        data = {
            "installment": request.POST.get("installment"),
            "payment_date": request.POST.get("payment_date"),
            "payment_amount": request.POST.get("payment_amount"),
            "document": request.FILES.get("document")
        }
        base_domain = get_base_domain(request=request)
        succeeded, message, contract_id = record_payment_transaction(data=data, base_domain=base_domain)
        if succeeded:
            messages.success(request, message)
        else:
            messages.info(request, message=message)
        redirect_url = reverse('industry:contracts-detail', args=(contract_id, ))
        return redirect(f"{redirect_url}#installments-transactions") 
    return redirect("industry:companies-industries-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0014", 3)
def main_indstry_contracts(request):
    page_number = request.GET.get('page', 1)
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    contract_tab_type = "main_contracts_tab"
    payments_tab_type = "main_payments_tab"
    payment_installments_tab_type = "main_payment_installments_tab"
    transactions_tab_type = "main_transactions_tab"

    # Layer 1: Cache ordered ID list with versioning
    cache_key_contract_ids = f"{contract_tab_type}_ids"
    cache_key_payment_ids = f"{payments_tab_type}_ids"
    cache_key_payment_installments_ids = f"{payment_installments_tab_type}_ids"
    cache_key_transactions_ids = f"{transactions_tab_type}_ids"

    ordered_contract_ids = cache.get(cache_key_contract_ids)
    ordered_payment_ids = cache.get(cache_key_payment_ids)
    ordered_payment_installment_ids = cache.get(cache_key_payment_installments_ids)
    ordered_transactions_ids = cache.get(cache_key_transactions_ids)

    if page_number == 1 or not ordered_contract_ids or not ordered_payment_ids or not ordered_payment_installment_ids or not ordered_transactions_ids:
        ordered_contract_ids = list(IndustryContract.objects.values_list('id', flat=True))
        ordered_payment_ids = list(IndustryContractPayment.objects.values_list('id', flat=True))
        ordered_payment_installment_ids = list(ContractPaymentInstallment.objects.values_list('id', flat=True))
        ordered_transactions_ids = list(PaymentInstallmentTransaction.objects.values_list('id', flat=True))
        cache.set(cache_key_contract_ids, ordered_contract_ids, CACHE_TIMEOUT)
        cache.set(cache_key_payment_ids, ordered_payment_ids, CACHE_TIMEOUT)
        cache.set(cache_key_payment_installments_ids, ordered_payment_installment_ids, CACHE_TIMEOUT)
        cache.set(cache_key_transactions_ids, ordered_transactions_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    contract_paginator = Paginator(ordered_contract_ids, PAGE_SIZE)
    payment_paginator = Paginator(ordered_payment_ids, PAGE_SIZE)
    payment_installment_paginator = Paginator(ordered_payment_installment_ids, PAGE_SIZE)
    transaction_paginator = Paginator(ordered_transactions_ids, PAGE_SIZE)

    try:
        current_contract_page = contract_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_contract_page = contract_paginator.page(1)

    try:
        current_payment_page = payment_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_payment_page = payment_paginator.page(1)

    try:
        current_payment_installment_page = payment_installment_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_payment_installment_page = payment_installment_paginator.page(1)

    try:
        current_transaction_page = transaction_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_transaction_page = transaction_paginator.page(1)

    current_contract_ids = current_contract_page.object_list
    current_payment_ids = current_payment_page.object_list
    current_payment_installment_ids = current_payment_installment_page.object_list
    current_transaction_ids = current_transaction_page.object_list

    contracts = IndustryContract.objects.filter(id__in=current_contract_ids).order_by("signing_date")
    payments = IndustryContractPayment.objects.filter(id__in=current_payment_ids).order_by("next_payment_date")
    payment_installments = ContractPaymentInstallment.objects.filter(id__in=current_payment_installment_ids).order_by("expected_payment_date")
    transactions = PaymentInstallmentTransaction.objects.filter(id__in=current_transaction_ids).order_by("payment_date")

    context = {
        "contracts": contracts,
        "payments": payments,
        "payment_installments": payment_installments,
        "transactions": transactions,
        "contract_page": current_contract_page,
        "contract_tab_type": contract_tab_type,
        "payment_tab_type": payments_tab_type,
        "payment_page": current_payment_page,
        "installments_tab_type": payment_installments_tab_type,
        "installments_page": current_payment_installment_page,
        "transaction_tab_type": transactions_tab_type,
        "transaction_page": current_transaction_page
    }

    return render(request, "industry/contract/main_contracts_information.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0014", 2)
def record_refund(request, transaction_id):
    if request.method == "POST":
        transaction = PaymentInstallmentTransaction.objects.filter(id=transaction_id).first()
        if transaction is not None:
            refunded_date = request.POST.get("refunded_date")
            document = request.FILES.get("document")
            transaction.refund_amount = transaction.refund_amount
            transaction.refunded_date = refunded_date
            transaction.is_refunded = True
            transaction.refund_proof = document
            transaction.recorded_by = request.user
            transaction.save()
            base_domain = get_base_domain(request=request)
            transaction.refund_proof_url = f"{base_domain}/{transaction.refund_proof.url.lstrip('/')}"
            transaction.save()

            messages.success(request, message="New transaction refund has been recorded successfully!")
            
            redirect_url = reverse('industry:contracts-detail', args=(transaction.installment.contract_payment.contract.id, ))
            return redirect(f"{redirect_url}#installments-transactions") 
        messages.info(request, message="Could not find the transaction to refund")
    return redirect("industry:companies-industries-list")



