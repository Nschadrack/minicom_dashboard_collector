import json
import csv
import os
import pandas as pd
from datetime import datetime, timedelta
from django.db import IntegrityError
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from .models import (User, Role, UserRole, Module, 
                     RolePermission, IndustrialZone,
                     EconomicSector, EconomicSubSector, 
                     AdministrativeUnit, Product)
from industry.models import IndustryProduct
from reporting.models import (MonthsReportingPeriodConfig, 
                              ReportingPeriodPlan)
from automation.models import (WorldCountry, BNRUSDAveragePrice,
                               ProductMeasurements, RRACustomCode)
from .utils import (generate_random_code, build_default_password_email_template,
                    bulk_saving_administrative, bulk_saving_zoning, send_mails)
from reporting.utils import generate_periods
from .permissions import check_role_permission_on_module_decorator, is_user_permitted

def index(request):
    return render(request, "index.html")

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"].strip().lower()
        password = request.POST["password"].strip()
        user = authenticate(request, email=username, password=password)
        if user is not None:
            if user.change_password_required:
                messages.info(request, message="This is your first time to login, you need to change password!")
                return redirect(reverse("system_management:change_password", args=(user.email,)))
            login(request, user)
            return redirect("dashboard:dashboard") 
        else:
            messages.error(request, message="Invalid credentials. username or password is incorrect!")
    
    return render(request, "systems_management/login.html")
    # return render(request, "index_map.html")

def change_password(request, username=None):
    user = None
    if username:
        user = User.objects.filter(email=username).first()
    
    if request.method == "POST":
        password1 = request.POST.get("password1", None)
        password2 = request.POST.get("password2", None)
        email = request.POST.get("email", None)

        if password1 and password2 and email and (password1 == password2):
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(password1)
                user.change_password_required = False
                user.save()
                messages.success(request, message="Password changed successfully!")
                return redirect("system_management:login")
            else:
                messages.error(request, message=f"user account with email: {email} does not exist")
        else:
            messages.error(request, message="Check your email/username and passwords entered. Password fields must match!")
            return redirect("system_management:login")

    context = {
        "user": user
    }
    return render(request, "systems_management/change_password.html", context)

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def logout_user(request):
    logout(request)
    return redirect("system_management:login")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0002", 3)
def users_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0002", 1):
            user_category = request.POST.get("user_category").strip()
            first_name = request.POST.get("first_name").strip()
            last_name = request.POST.get("last_name").strip()
            email = request.POST.get("email").strip().lower()
            password = generate_random_code()

            user = User.objects.filter(email=email).first()
            if user:
                messages.info(request, message="user with email: {user.email} already exists!")
                return redirect("system_management:users-list")

            user = User(
                user_category=user_category,
                change_password_required=True,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            user.set_password(password)
            user.save()
            email_body = build_default_password_email_template(user, password)
            send_mails(user.email, "Account Creation", email_body)
            messages.success(request, message="user account with email: {user.email} created successfully! and email containing first time login has been sent to the email.")
        else:
            messages.error(request, message="You don't have permission to create user")
        return redirect("system_management:users-list")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'users_list')
    ordering = ("-date_joined", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(User.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    users = User.objects.filter(id__in=current_ids).order_by(*ordering)
    
    context = {
        "users": users,
        "page": current_page,
        'tab_type': active_tab,
    }
    return render(request, "systems_management/users.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0002", 3)
def user_detail(request, user_id):
    user = User.objects.filter(id=user_id).first()
    user_roles = UserRole.objects.filter(user=user).order_by("role__name")
    existing_roles = [ role.role.id for role in user_roles]
    roles = Role.objects.exclude(id__in=existing_roles).order_by("name")
    if user is not None:
        context = {
            "user": user,
            "roles": roles,
            "user_roles": user_roles
        }
        return render(request, "systems_management/user-details.html", context=context)
    return redirect("system_management:users-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0003", 3)
def roles_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0003", 1):
            role_name = request.POST.get("role_name", "").strip()
            role = Role.objects.filter(name__iexact=role_name).first()
            if role:
                messages.info(request, message=f"{role.name} role already exists, try a different name!")
                return redirect("system_management:roles-list")
            Role.objects.create(name=role_name)
            messages.success(request, message=f"{role_name.title()} role created successfuly!")
        else:
            messages.error(request, message="You don't have permission to create the system role")
        return redirect("system_management:roles-list")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'roles_list')
    ordering = ("name", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(Role.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    roles = Role.objects.filter(id__in=current_ids).order_by(*ordering)

    context = {
        "roles": roles,
        "page": current_page,
        'tab_type': active_tab,
    }

    return render(request, "systems_management/roles.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0003", 3)
def role_details(request, role_id):
    role = Role.objects.filter(id=role_id).first()
    role_users = []
    if role is not None:
        role_users = UserRole.objects.filter(role=role).order_by("user__first_name")
    else:
        return redirect("system_management:roles-list")
    
    permissions = []
    with open(os.path.join(os.getcwd(), "modules_permissions.json")) as f:
        permissions = json.load(f)
    
    role_permissions = RolePermission.objects.filter(role=role)
    for existing_permission in role_permissions:
        for permission in permissions:
            if permission["module_id"] == existing_permission.module.module_id and permission["action_value"] == existing_permission.action_value:
                permissions.remove(permission)
    
    context = {
        "role": role,
        "role_users": role_users,
        "role_permissions": role_permissions,
        "permissions": permissions
    }

    return render(request, "systems_management/role_details.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0003", 6)
def assign_roles(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user is not None and request.method == "POST":
        roles_to_add_ids = [int(v[0]) for v in dict(request.POST).values() if v[0].isdigit()]
        roles_to_add = Role.objects.filter(pk__in=roles_to_add_ids)
        message = f"Roles: "
        role_names = []
        for role in roles_to_add:
            UserRole.objects.create(role=role, user=user, assigned_by=request.user)
            role_names.append(role.name)
        message += f"{', '.join(role_names)} assigned to {user.get_full_name()} successfully!"
        messages.success(request, message=message)
        return redirect(reverse("system_management:user-details", args=(user_id, )))
    else:
        return redirect("system_management:users-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0003", 6)
def assign_role_permissions(request, role_id):
    role = Role.objects.filter(id=role_id).first()
    if role is not None and request.method == "POST":
        permissions = []
        with open(os.path.join(os.getcwd(), "modules_permissions.json")) as f:
            permissions = json.load(f)

        permissions_to_add_ids = [int(v[0]) for v in dict(request.POST).values() if v[0].isdigit()]
        for permission_id in permissions_to_add_ids:
            if permission_id < len(permissions):
                permision_module = permissions[permission_id]
                if permission_id == permision_module.get("permission_id", -1):
                    module = Module.objects.filter(module_id=permision_module.get("module_id", None)).first()
                    if module is not None:
                        RolePermission.objects.create(role=role,
                                                      module=module,
                                                      action=permision_module.get("action", "do nothing"),
                                                      action_value=permision_module.get("action_value", 0))
        messages.success(request, message=f"Permissions added to the role: {role.name}")
        
        return redirect(reverse("system_management:role-details", args=(role_id, )))
    else:
        return redirect("system_management:roles-list")
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0004", 3)
def zones_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0004", 1):
            zone_name = request.POST.get("zone_name")
            zone = IndustrialZone.objects.filter(name__iexact=zone_name).first()
            if zone:
                messages.info(request, f"Industrial zoning with name:{zone_name} already exists!")
            else:
                IndustrialZone.objects.create(name=zone_name)
                messages.success(request, message="Industrial zoning added successfully!")
        else:
            messages.error(request, message="You don't have permission to record zoning")

        return redirect("system_management:zones-list")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'industrial_zonings_list')
    ordering = ("name", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(IndustrialZone.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    zones = IndustrialZone.objects.filter(id__in=current_ids).order_by(*ordering)
    context = {
        "zones": zones,
        "page": current_page,
        'tab_type': active_tab,
    }

    return render(request, "systems_management/zones.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0005", 3)
def economic_sectors_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0005", 1):
            name = request.POST.get("name")
            sector = EconomicSector.objects.filter(name__iexact=name).first()
            if sector:
                messages.info(request, message=f"The economic sector with name: {name} already exists!")
            else:
                EconomicSector.objects.create(name=name)
                messages.success(request, message="Economic sector added successfully!")
        else:
            messages.error(request, message="You don't have permission to record economic sector")

        return redirect("system_management:economic-sectors-list")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'economic_sectors_list')
    ordering = ("name", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(EconomicSector.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    economic_sectors = EconomicSector.objects.filter(id__in=current_ids).order_by(*ordering)
    context = {
        "economic_sectors": economic_sectors,
        "page": current_page,
        'tab_type': active_tab,
    }

    return render(request, "systems_management/economic_sectors.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0005", 4)
def delete_economic_sector(request, id):
    sector = EconomicSector.objects.filter(id=id).first()
    if sector:
        sub_sector = EconomicSubSector.objects.filter(economic_sector=sector).first()
        if sub_sector:
            message = "You cannot delete this economic sector because it has sub economic sectors linked to it."
            messages.info(request, message=message)
        else:
            sector.delete()
            message = f"Economic sector: {sector.name} deleted successfully!"
            messages.success(request, message=message)
    else:
        message = f"Unable to delete economic sector with ID: {id} because it does not exist."
        messages.error(request, message=message)
    return redirect("system_management:economic-sectors-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0006", 3)
def economic_sub_sectors_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0006", 1):
            name = request.POST.get("name")
            isic_code = request.POST.get("isic_code")
            economic_sector = request.POST.get("economic_sector", "-1||").split("||")[0]
            economic_sector = EconomicSector.objects.filter(id=economic_sector.strip()).first()
            if EconomicSubSector.objects.filter(isic_code=isic_code).first():
                messages.info(request, message=f"Sub economic sector with ISIC code: {isic_code} already exists!")
            else:
                if economic_sector:
                    EconomicSubSector.objects.create(isic_code=isic_code, name=name, economic_sector=economic_sector)
                    messages.success(request, message="Economic sub sector added successfully!")
                else:
                    messages.error(request, message="You should select an economic sector")
        else:
            messages.error(request, message="You don't have permission to record sub economic sector")
        return redirect("system_management:economic-sub-sectors-list")

    economic_sectors = EconomicSector.objects.all().order_by("name")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'economic_sub_sectors_list')
    ordering = ("economic_sector__name", "name")

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(EconomicSubSector.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    economic_sub_sectors = EconomicSubSector.objects.filter(id__in=current_ids).order_by(*ordering)

    context = {
        "economic_sub_sectors": economic_sub_sectors,
        "economic_sectors": economic_sectors,
        "page": current_page,
        'tab_type': active_tab,
    }

    return render(request, "systems_management/economic_sub_sector.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0006", 4)
def delete_sub_economic_sector(request, id):
    try:
        sub_sector = EconomicSubSector.objects.get(id=id)
        product = Product.objects.filter(sub_sector=sub_sector).first()
        if product:
            message = "You cannot delete this sub economic sector because it has products linked to it."
            messages.info(request, message=message)
        else:
            message = "Sub economic sector deleted successfully!"
            messages.success(request, message=message)
            sub_sector.delete()
    except EconomicSubSector.DoesNotExist:
        message = f"Unable to delete sub economic sector with ID={id} because it does not exist."
        messages.error(request, message=message)
    return redirect("system_management:economic-sub-sectors-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0016", 3)
def products_list(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        if is_user_permitted(request.user, "0016", 1):
            name = request.POST.get("name")
            economic_sector = request.POST.get("economic_sector", "-1||").split("||")[0]
            economic_sub_sector = request.POST.get("economic_sub_sector", "-1||").split("||")[0]
            economic_sector = EconomicSector.objects.filter(id=economic_sector.strip()).first()
            economic_sub_sector = EconomicSubSector.objects.filter(id=economic_sub_sector.strip()).first()

            if economic_sector is None:
                messages.error(request, message="You should select the economic sector")
            
            if economic_sub_sector is None:
                messages.error(request, message="You should select sub economic sector!")

            if economic_sub_sector and economic_sector:
                last_product = Product.objects.filter(sub_sector=economic_sub_sector).order_by("id").last()
                product_code = "0001"
                if last_product:
                    product_code = last_product.product_code[-4:] # ignoring sub-sector code 202340002
                    code_len = len(product_code)
                    product_code = int(product_code) + 1
                    len_diff = code_len - len(str(product_code))
                    product_code = "0" * len_diff + str(product_code)

                Product.objects.create(
                    sub_sector=economic_sub_sector,
                    product_code=f"{economic_sub_sector.isic_code}{product_code}",
                    name=name
                )
            messages.success(request, message="New product added successfully!")
        else:
            messages.error(request, message="You don't have permission to record a product")

        return redirect("system_management:products-list")

    economic_sub_sectors = EconomicSubSector.objects.all().order_by("economic_sector__name", "name")
    economic_sectors = EconomicSector.objects.all().order_by("name")

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'economic_sub_sectors_list')
    ordering = ("sub_sector__economic_sector__name", "sub_sector__name", "product_code", "name")

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(Product.objects.values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    products = Product.objects.filter(id__in=current_ids).order_by(*ordering)

    context = {
        "economic_sub_sectors": economic_sub_sectors,
        "economic_sectors": economic_sectors,
        "products": products,
        "page": current_page,
        'tab_type': active_tab
    }

    return render(request, "systems_management/products.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0016", 4)
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        industry_product = IndustryProduct.objects.filter(product=product).first()
        if industry_product:
            message = "You cannot delete this product because it has other industry products linked to it"
            messages.info(request, message=message)
        else:
            product.delete()
            message = "Product deleted successfully!"
            messages.success(request, message=message)
    except Product.DoesNotExist:
        message = "Unable to delete the product because it does not exist"
        messages.error(request, message=message)
    return redirect("systems_management:products-list")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0017", 2)
def activate_months_reporting_period(request, month_id):
    try:
        month = MonthsReportingPeriodConfig.objects.get(id=month_id)
        today = datetime.today().date()
        existing_plans = list(ReportingPeriodPlan.objects.filter(end_date__gt=today).order_by("end_date"))
        start_date = None
        if len(existing_plans) > 0:
            end_date = existing_plans[0].end_date
            # Add one day to start from the next day of this date
            start_date = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")

        months = month.months
        periods = generate_periods(months, start_date)

        for existing_plan in existing_plans[1:]:
            existing_plan.delete()
        
        for period in periods:
            ReportingPeriodPlan.objects.create(
                start_date=period[0],
                end_date=period[1],
                period_config=month
            )
        active_months = MonthsReportingPeriodConfig.objects.filter(is_active=True).exclude(id=month.id)
        for active_month in active_months:
            active_month.is_active = False
            active_month.save()
        month.is_active = True
        month.save()
        
        if not start_date:
            start_date = f"01-01-{today.year}"

        message = f"Reporting period plan has been modified to restart from {start_date} with {months} month(s) range"
        messages.success(request, message=message)
        redirect_url = reverse('system_management:configurations')
        return redirect(f"{redirect_url}#reporting-periods")
    except MonthsReportingPeriodConfig.DoesNotExist:
        message = "Unable to activate the reporting period"
        messages.info(request, message=message)
    except Exception as e:
        message = f"Unexpected error ocurred: {str(e)}"
        messages.error(request, message=message)
    redirect_url = reverse('system_management:configurations')
    return redirect(f"{redirect_url}#reporting-months")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0017", 3)
def configurations(request):
    reporting_months = MonthsReportingPeriodConfig.objects.all().order_by("id")
    reporting_periods = list(ReportingPeriodPlan.objects.all().order_by("start_date"))
    usd_rates = list(BNRUSDAveragePrice.objects.all().order_by("-id"))
    rra_customs = list(RRACustomCode.objects.all().order_by("code"))
    countries = list(WorldCountry.objects.all().order_by("country_name"))
    measurments = list(ProductMeasurements.objects.all().order_by("short_abbr"))

    if len(reporting_periods) > 12:
        reporting_periods = reporting_periods[-12:]
    context = {
        "reporting_months": reporting_months,
        "reporting_periods": reporting_periods,
        "usd_rates": usd_rates,
        "rra_customs": rra_customs,
        "countries": countries,
        "measurments": measurments

    }
    
    return render(request, "configurations/configurations.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0007", 3)
def system_settings(request, flag=None):
    if request.user.is_staff and flag:
        if flag == "modules":
            with open(os.path.join(os.getcwd(), "fixtures", "modules.json")) as f:
                modules = json.load(f)
                for module in modules:
                    exiting_module = Module.objects.filter(module_id=module["module_id"]).first()
                    if exiting_module is None:
                        parent = Module.objects.filter(module_id=module["parent_id"]).first()
                        Module.objects.create(
                            module_id=module["module_id"],
                            name=module["name"],
                            parent_id=parent
                        )
            messages.success(request, message="Modules have been seeded successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "reporting_months":
            with open(os.path.join(os.getcwd(), "fixtures", "reporting_months.json")) as f:
                months = json.load(f)
                for month in months:
                    MonthsReportingPeriodConfig.objects.create(
                        id=month["id"],
                        months=month["months"]
                    )
            messages.success(request, message="Report months have been seeded successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "administrative_divisions":
            sectors = AdministrativeUnit.objects.filter(category="SECTOR")
            if len(sectors) != 416:
                print(f"Going into background task")
                bulk_saving_administrative() # execute the background task
                print("background task started")
                messages.success(request, message="Administrative dvisions background task has started successfully. You can check later if all administrative divisions are seeded.")
            else:
                messages.info(request, message="Administrative divisions already seeded!")
            return redirect("systems_management:system-settings")
        elif flag == "zoning":
            print(f"\nGoing to start background task\n")
            bulk_saving_zoning() # execute the background task
            print("\nStarted backgound task\n")
            messages.info(request, message="Industrial zoning background task has started successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "countries":
            reader = pd.read_csv(os.path.join(os.getcwd(), "fixtures", "countries_with_code.csv"))
            reader.columns = ["code", "name"] 
            for _, row in reader.iterrows():
                try:
                    WorldCountry.objects.create(
                        country_code=row["code"],
                        country_name=row["name"]
                    )
                except IntegrityError as e:
                    messages.error(request, f"error: {str(e)}")
                    return redirect("systems_management:system-settings")
            messages.success(request, message="Countries have been seeded successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "product_measurements":
            reader = pd.read_csv(os.path.join(os.getcwd(), "fixtures", "unit_measurements_rra.csv"))
            reader.columns = ["short_abbr", "full_abbr", "full_form", "description"]
            for _, row in reader.iterrows():
                try:
                    ProductMeasurements.objects.create(
                        short_abbr=row["short_abbr"],
                        long_abbr=row["full_abbr"],
                        full_form=row["full_form"],
                        description=row["description"]
                    )
                except IntegrityError as e:
                    messages.error(request, f"error: {str(e)}")
                    return redirect("systems_management:system-settings")
            messages.success(request, message="Product measurements have been seeded successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "rra_customs":
            reader = pd.read_csv(os.path.join(os.getcwd(), "fixtures", "rra_customs_codes.csv"))
            reader.columns = ["code", "name"]
            for _, row in reader.iterrows():
                try:
                    RRACustomCode.objects.create(
                        code=row["code"],
                        custom_name=row["name"]
                    )
                except IntegrityError as e:
                    messages.error(request, f"error: {str(e)}")
                    return redirect("systems_management:system-settings")
            messages.success(request, message="RRA customs have been seeded successfully!")
            return redirect("systems_management:system-settings")
        elif flag == "bnr_usd_rates":
            reader = pd.read_csv(os.path.join(os.getcwd(), "fixtures", "bnr_usd_rates.csv"))
            reader = reader[["year", "month", "rate"]]
            print(reader.head())
            for _, row in reader.iterrows():
                try:
                    BNRUSDAveragePrice.objects.create(
                        month=row["month"],
                        year=row["year"],
                        rate=row["rate"]
                    )
                except IntegrityError as e:
                    messages.error(request, f"error: {str(e)}")
                    return redirect("systems_management:system-settings")
            messages.success(request, message="BNR USD Average rates have been seeded successfully!")
            return redirect("systems_management:system-settings")
    elif not request.user.is_staff and flag:
        messages.error(request, message=f"You have permission for seeding data({flag.lower().replace('_', ' ')}) in the system")
        
    modules = len(Module.objects.all())
    reporting_months = MonthsReportingPeriodConfig.objects.all()
    zones = len(IndustrialZone.objects.all())
    economic_sectors = len(EconomicSector.objects.all())
    economic_sub_sectors = len(EconomicSubSector.objects.all())
    administrative_divisions = len(AdministrativeUnit.objects.all())
    countries = len(WorldCountry.objects.all())
    usd_rates = len(BNRUSDAveragePrice.objects.all())

    context ={
        "modules": modules,
        "zones": zones,
        "reporting_months": reporting_months,
        "economic_sectors": economic_sectors,
        "economic_sub_sectors": economic_sub_sectors,
        "administrative_divisions": administrative_divisions,
        "countries": countries,
        "usd_rates": usd_rates
    }

    return render(request, "systems_management/system_settings.html", context=context)
