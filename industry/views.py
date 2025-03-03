from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from system_management.models import User
from system_management.utils import generate_random_code
from .models import (IndustryEconomicZone, PartitionedPlot, CompanyProfile, 
                     CompanySite, LandOwner, LandRequestInformation,
                     AllocatedPlot)
from system_management.models import IndustrialZone
from .utils import load_countries


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industrial_parks_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category = request.POST.get("category")
        total_area = request.POST.get("total_area")
        leasable_area = request.POST.get("leasable_area")
        province = request.POST.get("province")
        district = request.POST.get("district")
        sector = request.POST.get("sector")

        IndustryEconomicZone.objects.create(
            name=name,
            category=category,
            total_land_size=total_area,
            leasable_land=leasable_area,
            province=province,
            district=district,
            sector=sector
        )
        return redirect("industry:parks-list")
    industrial_parks = IndustryEconomicZone.objects.all().order_by("category", "name")
    context = {
        "industrial_parks": industrial_parks
    }
    return render(request, "industry/industrial_parks_list.html", context)

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industrial_park_detail(request, park_id):
    industrial_park = IndustryEconomicZone.objects.filter(id=park_id).first()
    zones = IndustrialZone.objects.all().order_by("name")
    park_partitioned_plots = PartitionedPlot.objects.all().order_by("upi_status")

    if industrial_park is None:
        return redirect("industry:parks-list") 

    context = {
        "industrial_park": industrial_park,
        "park_partitioned_plots": park_partitioned_plots,
        "zones": zones,
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
                plot_upi=plot_upi,
                upi_status=upi_status,
                plot_size=plot_size,
                zone=zone,
                park=park
            )
        
        if park is None:
            return redirect("industry:parks-list")
        return redirect(reverse("industry:park-details", args=(park.id, )))
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def companies_industries_list(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name", "").strip()
            tin_number = request.POST.get("tin_number", "").strip()
            category = request.POST.get("category", "").strip()
            phone_contact = request.POST.get("phone_contact", "").strip()
            email_contact = request.POST.get("email_contact", "").strip()
            registeration_date = request.POST.get("registeration_date").strip()
            investor_origin_country = request.POST.getlist("investor_origin_country[]", [])
            company_size = request.POST.get("company_size", "").strip()

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
                investor_origin_country=",".join(investor_origin_country),
                company_size=company_size
            )
            profile.save()
        except:
            pass
        
    companies_industries_profiles = CompanyProfile.objects.all().order_by("name")
    context = {
        "companies_industries_profiles": companies_industries_profiles,
        "countries": load_countries(),
    }
    return render(request, "industry/industries_companies.html", context=context)


def land_request(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name").strip()
            phone_contact = request.POST.get("phone_contact").strip()
            email_contact = request.POST.get("email_contact", "").strip()
            request_date = request.POST.get("request_date")
            request_closure_date = request.POST.get("request_closure_date")
            requested_land_size = request.POST.get("requested_land_size").strip()
            zone = request.POST.get("zone", "01-").split("-")[0]
            zone = IndustrialZone.objects.filter(id=zone).first()

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
                land_owner = LandOwner(
                    user=user,
                    phone_number=phone_contact
                )

                land_owner.save()
            else:
                land_owner = LandOwner.objects.filter(user=user).first()
            
            land_request_obj = LandRequestInformation(
               land_owner=land_owner,
               requested_land_size=requested_land_size,
                request_date=request_date,
                request_closure_date=request_closure_date,
                zone=zone
            )
            land_request_obj.save()
        except Exception as e:
            print(f"\n\nError: {str(e)}\n\n")

    zones = IndustrialZone.objects.all().order_by("name")
    land_requests = LandRequestInformation.objects.all().order_by("request_date", "recorded_date")

    context = {
        "zones": zones,
        "land_requests": land_requests
    }
    return render(request, "industry/land_request_list.html", context)
