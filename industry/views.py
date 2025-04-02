import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import all_timezones
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from system_management.models import User, AdministrativeUnit, EconomicSector, EconomicSubSector
from system_management.utils import generate_random_code
from .models import (IndustryEconomicZone, PartitionedPlot, CompanyProfile, 
                     CompanySite, LandRequestInformation,
                     AllocatedPlot, IndustryAttachment, IndustryEconomicSector, ContractPaymentInstallment,
                     IndustryContract, IndustryContractPayment, PaymentInstallmentTransaction)
from system_management.models import IndustrialZone
from .utils import (load_countries, get_zones_and_partitioned_plots_in_park,
                    record_allocated_plot_from_request, record_industry_in_plot_from_request,
                    get_base_domain, create_payment_installment, convert_datetime_timezone,
                    record_payment_transaction)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industrial_parks_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        total_area = request.POST.get("total_area")
        leasable_area = request.POST.get("leasable_area")
        province = AdministrativeUnit.objects.filter(category="PROVINCE", id=request.POST.get("province").strip()).first()
        district = AdministrativeUnit.objects.filter(category="DISTRICT", id=request.POST.get("district").strip()).first()
        sector = AdministrativeUnit.objects.filter(category="SECTOR", id=request.POST.get("sector").strip()).first()
        cell = AdministrativeUnit.objects.filter(category="CELL", id=request.POST.get("cell").strip()).first()

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
        return redirect("industry:parks-list")
    industrial_parks = IndustryEconomicZone.objects.all().order_by("category", "name")
    provinces = AdministrativeUnit.objects.filter(category="PROVINCE").order_by("name")
    districts = AdministrativeUnit.objects.filter(category="DISTRICT").order_by("name")
    sectors = AdministrativeUnit.objects.filter(category="SECTOR").order_by("name")
    cells = AdministrativeUnit.objects.filter(category="CELL").order_by("name")
    context = {
        "industrial_parks": industrial_parks,
        "provinces": provinces,
        "districts": json.dumps(list(districts.values())),
        "sectors": json.dumps(list(sectors.values())),
        "cells": json.dumps(list(cells.values())),
    }
    return render(request, "industry/industrial_parks_list.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industrial_park_detail(request, park_id):
    industrial_park = IndustryEconomicZone.objects.filter(id=park_id).first()
    zones = IndustrialZone.objects.all().order_by("name")
    park_partitioned_plots = PartitionedPlot.objects.filter(park=industrial_park).order_by("plot_number", "zone__name", "-is_allocated")

    if industrial_park is None:
        return redirect("industry:parks-list") 
    
    allocated_plots = AllocatedPlot.objects.filter(park=industrial_park).order_by("-recorded_date")
    park_industries = CompanySite.objects.filter(allocated_plot__in=allocated_plots).order_by("company__name")

    context = {
        "industrial_park": industrial_park,
        "park_partitioned_plots": park_partitioned_plots,
        "zones": zones,
        "allocated_plots": allocated_plots,
        "park_industries": park_industries,

    }

    return render(request, "industry/industrial_park_details.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def record_partitioned_plot(request, park_id):
    if request.method == "POST":
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
        
        if park is None:
            return redirect("industry:parks-list")
        
        redirect_url = reverse("industry:park-details", args=(park.id, ))
        return redirect(f"{redirect_url}#partitioned-plots")
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def companies_industries_list(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            tin_number = request.POST.get("tin_number", "").strip()
            category = request.POST.get("category", "").strip()
            phone_contact = request.POST.get("phone_contact", "").strip()
            email_contact = request.POST.get("email_contact", "").strip().lower()
            registeration_date = request.POST.get("registeration_date", None).strip()
            investor_origin_country = request.POST.get("selected_items")
            company_size = request.POST.get("company_size", "").strip()

            if len(registeration_date.strip()) < 6:
                registeration_date = None

            user = User.objects.filter(email=email_contact).first()
            if user is None:
                password = generate_random_code()
                user = User(
                    user_category="COMPANY",
                    change_password_required=True,
                    first_name=name[:250],
                    last_name="",
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
                company_size=company_size
            )
            profile.save()
        except:
            pass
        
    companies_industries_profiles = CompanyProfile.objects.all().order_by("name")
    park_industries = CompanySite.objects.all().order_by("company__name")
    provinces = AdministrativeUnit.objects.filter(category="PROVINCE").order_by("name")
    districts = AdministrativeUnit.objects.filter(category="DISTRICT").order_by("name")
    sectors = AdministrativeUnit.objects.filter(category="SECTOR").order_by("name")
    cells = AdministrativeUnit.objects.filter(category="CELL").order_by("name")
    context = {
        "companies_industries_profiles": companies_industries_profiles,
        "park_industries": park_industries,
        "search_items": json.dumps(load_countries()),
        "parent": "none",
        "provinces": provinces,
        "districts": json.dumps(list(districts.values())),
        "sectors": json.dumps(list(sectors.values())),
        "cells": json.dumps(list(cells.values())),
    }
    return render(request, "industry/industries_companies.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
def add_industry_not_in_park(request):
    if request.method == "POST":
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
        except Exception as e:
            print(f"\n[ERROR]: {str(e)}\n")

    redirect_url = reverse('industry:companies-industries-list')
    return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industry_details(request, industry_id):
    industry = CompanySite.objects.filter(id=industry_id).first()
    attachments = IndustryAttachment.objects.filter(industry=industry).order_by("category","-uploaded_date", "name")
    industry_economic_sub_sectors = IndustryEconomicSector.objects.filter(industry=industry).order_by("sector__economic_sector__name", "sector__name")
    economic_sectors = EconomicSector.objects.all()
    sub_sectors = EconomicSubSector.objects.exclude(id__in=[sector.id for sector in industry_economic_sub_sectors])
    contracts = IndustryContract.objects.filter(industry=industry).order_by("signing_date")
    search_items = []
    for sector in sub_sectors:
        search_items.append(f"{sector.id}|{sector.name.strip().replace(',', "-")}|{sector.economic_sector.id}")

    context = {
        "industry": industry,
        "parent": "economic-sector",
        "industry_economic_sub_sectors": industry_economic_sub_sectors,
        "search_items": json.dumps(search_items),
        "economic_sectors": economic_sectors,
        "attachments": attachments,
        "contracts": contracts
    }
    return render(request, "industry/industry_detail_page/industry_details.html", context)

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
                else:
                    print("Sector with id {sector_id} not found\n")

            redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
            return redirect(f"{redirect_url}#industry-detail")
    except:
        redirect_url = reverse('industry:companies-industries-list')
        return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
            attachment.document_url = f"{base_domain}/{attachment.document.url}"
            attachment.save()
            redirect_url = reverse('industry:industry-info-details', args=(industry.id, ))
            return redirect(f"{redirect_url}#attachment-industry")

    redirect_url = reverse('industry:companies-industries-list')
    return redirect(f"{redirect_url}#companies-industries-in-parks")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def land_request(request):
    if request.method == "POST":
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
        except Exception as e:
            print(f"\n\nError: {str(e)}\n\n")

    land_requests = LandRequestInformation.objects.all().order_by("request_date", "recorded_date")
    company_profiles = CompanyProfile.objects.all().order_by("name")
    parks = IndustryEconomicZone.objects.all()

    zones, _ = get_zones_and_partitioned_plots_in_park()

    context = {
        "zones": json.dumps(zones),
        "parks": parks,
        "company_profiles": company_profiles,
        "land_requests": land_requests
    }
    return render(request, "industry/land_request_list.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def land_request_detail(request, land_request_id, flag=None):
    land_request = LandRequestInformation.objects.filter(id=land_request_id).first()
    if land_request is None:
        return redirect("industry:land-requests")
    
    if flag and flag.upper() == "ALLOCATE_PLOT" and request.method == "POST":
        succeed = record_allocated_plot_from_request(request=request, land_request=land_request)

        if not succeed:
            # failure message message
            pass
    elif flag and flag.upper() == "ADD_INDUSTRY" and request.method == "POST":
        succeed = record_industry_in_plot_from_request(request=request)

        if not succeed:
            # failure message message
            pass
    
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
    return render(request, "industry/land_request_details.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def contracts_list(request):
    if request.method == "POST":
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
            contract.contract_document_url = f"{base_domain}/{contract.contract_document.url}"
            contract.save()

            redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
            return redirect(f"{redirect_url}#contract-detail")
        return redirect("industry:companies-industries-list")
    
    return redirect("industry:companies-industries-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def contracts_detail(request, contract_id):
    contract = IndustryContract.objects.filter(id=contract_id).prefetch_related(
        Prefetch("contract_payments", queryset=IndustryContractPayment.objects.prefetch_related("payment_installments"))
    ).first()

    payment = contract.contract_payments.first()
    payment_installments = payment.payment_installments.all().order_by("expected_payment_date") if payment else ContractPaymentInstallment.objects.none()
    transactions = PaymentInstallmentTransaction.objects.filter(
        installment__contract_payment=payment).select_related("installment").order_by("installment__expected_payment_date")
    installment_payment_amount = None
    unpaid_installments = None
    transaction_to_refund = PaymentInstallmentTransaction.objects.filter(id=payment.transaction_to_refund).first()

    if contract is None:
        return redirect("industry:companies-industries-list")
    
    if request.method == "POST":
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
            redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
            return redirect(f"{redirect_url}#contract-detail")
        
        succeeded, total_amount, message = create_payment_installment(contract_payment=contract_payment, installments_dates=payment_dates)
        if not succeeded:
            contract_payment.delete()
        else:
            if total_amount !=  contract_payment.total_amount_to_pay:
                contract_payment.total_amount_to_pay = total_amount
                contract_payment.total_amount_unpaid = total_amount
                contract_payment.contract.contract_amount = contract_payment.total_amount_to_pay  
                contract_payment.save() 
                contract_payment.contract.save() # update the contract as well
        
        redirect_url = reverse('industry:contracts-detail', args=(contract.id, ))
        return redirect(f"{redirect_url}#contract-payments")
        
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
        redirect_url = reverse('industry:contracts-detail', args=(contract_id, ))
        return redirect(f"{redirect_url}#installments-transactions") 
    return redirect("industry:companies-industries-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def main_indstry_contracts(request):
    contracts = list(IndustryContract.objects.all().order_by("signing_date"))
    payments = list(IndustryContractPayment.objects.all().order_by("next_payment_date"))
    payment_installments = list(ContractPaymentInstallment.objects.all().order_by("expected_payment_date"))
    transactions = list(PaymentInstallmentTransaction.objects.all().order_by("payment_date"))

    context = {
        "contracts": contracts,
        "payments": payments,
        "payment_installments": payment_installments,
        "transactions": transactions
    }

    return render(request, "industry/contract/main_contracts_information.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
            transaction.refund_proof_url = f"{base_domain}/{transaction.refund_proof.url}"
            transaction.save()
            
            redirect_url = reverse('industry:contracts-detail', args=(transaction.installment.contract_payment.contract.id, ))
            return redirect(f"{redirect_url}#installments-transactions") 
    return redirect("industry:companies-industries-list")



