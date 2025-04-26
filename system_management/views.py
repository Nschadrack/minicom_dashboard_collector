import json
import os
from datetime import datetime, timedelta
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
from reporting.models import MonthsReportingPeriodConfig, ReportingPeriodPlan
from .utils import (generate_random_code, build_default_password_email_template,
                    bulk_saving_administrative, bulk_saving_zoning, send_mails)
from reporting.utils import generate_periods


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"].strip().lower()
        password = request.POST["password"].strip()
        user = authenticate(request, email=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard:dashboard") 
        else:
            messages.error(request, message="Invalid credentials. username or password is incorrect!")
    
    return render(request, "index.html")
    # return render(request, "index_map.html")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def logout_user(request):
    logout(request)
    return redirect("system_management:login")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def users_list(request):
    if request.method == "POST":
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
        return redirect("system_management:users-list")

    users = User.objects.all().order_by("-date_joined")
    
    context = {
        "users": users
    }
    return render(request, "systems_management/users.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
def roles_list(request):
    if request.method == "POST":
        role_name = request.POST.get("role_name", "").strip()
        role = Role.objects.filter(name__iexact=role_name).first()
        if role:
            messages.info(request, message=f"{role.name} role already exists, try a different name!")
            return redirect("system_management:roles-list")
        Role.objects.create(name=role_name)
        messages.success(request, message=f"{role_name.title()} role created successfuly!")
        return redirect("system_management:roles-list")

    roles = Role.objects.all().order_by("name")
    context = {
        "roles": roles,
    }

    return render(request, "systems_management/roles.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
def zones_list(request):
    if request.method == "POST":
        zone_name = request.POST.get("zone_name")
        zone = IndustrialZone.objects.filter(name__iexact=zone_name).first()
        if zone:
            messages.info(request, f"Industrial zoning with name:{zone_name} already exists!")
        else:
            IndustrialZone.objects.create(name=zone_name)
            messages.success(request, message="Industrial zoning added successfully!")

        return redirect("system_management:zones-list")

    zones = IndustrialZone.objects.all().order_by("name")
    context = {
        "zones": zones,
    }

    return render(request, "systems_management/zones.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def economic_sectors_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        sector = EconomicSector.objects.filter(name__iexact=name).first()
        if sector:
            messages.info(request, message=f"The economic sector with name: {name} already exists!")
        else:
            EconomicSector.objects.create(name=name)
            messages.success(request, message="Economic sector added successfully!")

        return redirect("system_management:economic-sectors-list")

    economic_sectors = EconomicSector.objects.all().order_by("name")
    context = {
        "economic_sectors": economic_sectors,
    }

    return render(request, "systems_management/economic_sectors.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
def economic_sub_sectors_list(request):
    if request.method == "POST":
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
        return redirect("system_management:economic-sub-sectors-list")

    economic_sub_sectors = EconomicSubSector.objects.all().order_by("economic_sector__name", "name")
    economic_sectors = EconomicSector.objects.all().order_by("name")
    context = {
        "economic_sub_sectors": economic_sub_sectors,
        "economic_sectors": economic_sectors
    }

    return render(request, "systems_management/economic_sub_sector.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
def products_list(request):
    if request.method == "POST":
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

        return redirect("system_management:products-list")

    economic_sub_sectors = EconomicSubSector.objects.all().order_by("economic_sector__name", "name")
    economic_sectors = EconomicSector.objects.all().order_by("name")
    products = Product.objects.all().order_by("sub_sector__economic_sector__name", "sub_sector__name", "product_code", "name")
    context = {
        "economic_sub_sectors": economic_sub_sectors,
        "economic_sectors": economic_sectors,
        "products": products
    }

    return render(request, "systems_management/products.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
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
    except MonthsReportingPeriodConfig.DoesNotExist:
        message = "Unable to activate the reporting period"
        messages.info(request, message=message)
    except Exception as e:
        message = f"Unexpected error ocurred: {str(e)}"
        messages.error(request, message=message)
    redirect_url = reverse('system_management:configurations')
    return redirect(f"{redirect_url}#add-report")


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def configurations(request):
    reporting_months = MonthsReportingPeriodConfig.objects.all().order_by("id")
    reporting_periods = list(ReportingPeriodPlan.objects.all().order_by("start_date"))
    if len(reporting_periods) > 12:
        reporting_periods = reporting_periods[-12:]
    context = {
        "reporting_months": reporting_months,
        "reporting_periods": reporting_periods
    }
    
    return render(request, "configurations/configurations.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def system_settings(request, flag=None):
    if flag == "modules":
        with open(os.path.join(os.getcwd(), "modules.json")) as f:
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
        with open(os.path.join(os.getcwd(), "reporting_months.json")) as f:
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
        
    
    modules = len(Module.objects.all())
    reporting_months = MonthsReportingPeriodConfig.objects.all()
    zones = len(IndustrialZone.objects.all())
    economic_sectors = len(EconomicSector.objects.all())
    economic_sub_sectors = len(EconomicSubSector.objects.all())
    administrative_divisions = len(AdministrativeUnit.objects.all())

    context ={
        "modules": modules,
        "zones": zones,
        "reporting_months": reporting_months,
        "economic_sectors": economic_sectors,
        "economic_sub_sectors": economic_sub_sectors,
        "administrative_divisions": administrative_divisions
    }

    return render(request, "systems_management/system_settings.html", context=context)
