import json
import os
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from .models import (User, Role, UserRole, Module, RolePermission, IndustrialZone,
                     EconomicSector, EconomicSubSector, AdministrativeUnit)
from .utils import (generate_random_code, build_default_password_email_template,
                    bulk_saving_administrative, bulk_saving_zoning, send_mails)


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"].strip().lower()
        password = request.POST["password"].strip()
        user = authenticate(request, email=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard:dashboard") 
        else:
            print(f"\n\n:username: {username}\nINVALID CREDENTIALS\n\n")
    
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
        role_name = request.POST.get("role_name")
        Role.objects.create(name=role_name)

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
        for role in roles_to_add:
            UserRole.objects.create(role=role, user=user, assigned_by=request.user)
        
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
        
        return redirect(reverse("system_management:role-details", args=(role_id, )))
    else:
        return redirect("system_management:roles-list")
    

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def zones_list(request):
    if request.method == "POST":
        zone_name = request.POST.get("zone_name")
        IndustrialZone.objects.create(name=zone_name)

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
        EconomicSector.objects.create(name=name)

        return redirect("system_management:economic-sectors-list")

    economic_sectors = EconomicSector.objects.all().order_by("name")
    context = {
        "economic_sectors": economic_sectors,
    }

    return render(request, "systems_management/economic_sectors.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def economic_sub_sectors_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        economic_sector = request.POST.get("economic_sector", "-1||").split("||")[0]
        economic_sector = EconomicSector.objects.filter(id=economic_sector.strip()).first()
        EconomicSubSector.objects.create(name=name, economic_sector=economic_sector)

        return redirect("system_management:economic-sub-sectors-list")

    economic_sub_sectors = EconomicSubSector.objects.all().order_by("economic_sector__name", "name")
    economic_sectors = EconomicSector.objects.all().order_by("name")
    context = {
        "economic_sub_sectors": economic_sub_sectors,
        "economic_sectors": economic_sectors
    }

    return render(request, "systems_management/economic_sub_sector.html", context)


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
    elif flag == "administrative_divisions":
        print(f"Going into background task")
        bulk_saving_administrative() # execute the background task
        print("background task started")
    elif flag == "zoning":
        print(f"\nGoing to start background task\n")
        bulk_saving_zoning() # execute the background task
        print("\nStarted backgound task\n")
        
    
    modules = len(Module.objects.all())
    zones = len(IndustrialZone.objects.all())
    economic_sectors = len(EconomicSector.objects.all())
    economic_sub_sectors = len(EconomicSubSector.objects.all())
    administrative_divisions = len(AdministrativeUnit.objects.all())

    context ={
        "modules": modules,
        "zones": zones,
        "economic_sectors": economic_sectors,
        "economic_sub_sectors": economic_sub_sectors,
        "administrative_divisions": administrative_divisions
    }

    return render(request, "systems_management/system_settings.html", context=context)
