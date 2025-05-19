from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Dashboard


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industry_dashboards(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number == 1
        name = request.POST.get("name")
        dashboard_link = request.POST.get("dashboard_link")
        category = "INDUSTRY"
        Dashboard.objects.create(
            name=name,
            category=category,
            dashboard_link=dashboard_link,
            created_by=request.user
        )

    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'industrial_dashboards_list')
    ordering = ("name", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(Dashboard.objects.filter(category="INDUSTRY").values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    dashboards = Dashboard.objects.filter(id__in=current_ids, category="INDUSTRY").order_by(*ordering)

    context = {
        "dashboards": dashboards,
        "page": current_page,
        'tab_type': active_tab,
    }
    return render(request, "dashboards/industry.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def trade_dashboards(request):
    page_number = request.GET.get('page', 1)
    if request.method == "POST":
        page_number = 1
        name = request.POST.get("name")
        dashboard_link = request.POST.get("dashboard_link")
        category = "TRADE"
        Dashboard.objects.create(
            name=name,
            category=category,
            dashboard_link=dashboard_link,
            created_by=request.user
        )
        
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    active_tab = request.GET.get('tab', 'trade_dashboards_list')
    ordering = ("name", )

    # Layer 1: Cache ordered ID list with versioning
    cache_key_ids = f"{active_tab}_ids"
    ordered_ids = cache.get(cache_key_ids)
    
    if not ordered_ids or page_number == 1:
        # Fetch IDs with proper ordering
        ordered_ids = list(Dashboard.objects.filter(category="TRADE").values_list('id', flat=True))
        cache.set(cache_key_ids, ordered_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    paginator = Paginator(ordered_ids, PAGE_SIZE)
    try:
        current_page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_page = paginator.page(1)

    current_ids = current_page.object_list
    dashboards = Dashboard.objects.filter(id__in=current_ids, category="TRADE").order_by(*ordering)

    context = {
        "dashboards": dashboards,
        "page": current_page,
        'tab_type': active_tab,
    }
    return render(request, "dashboards/trade.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def dashboard_detail(request, dashboard_id):
    dashboard = Dashboard.objects.filter(id=dashboard_id).first()
    if request.method == "POST":
        name = request.POST.get("name", dashboard.name)
        dashboard_link = request.POST.get("dashboard_link", dashboard.dashboard_link)
        dashboard.name = name
        dashboard.dashboard_link = dashboard_link
        dashboard.updated_at = timezone.now()
        dashboard.updated_by = request.user
        dashboard.save()

        if dashboard.category == "INDUSTRY":
            return redirect("minicom_dashboards:industry-dashboards")
        else:
            return redirect("minicom_dashboards:trade-dashboards")
        
    context = {
        "dashboard": dashboard
    }
    return render(request, "dashboards/dashboard_details.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def edit_dashboard_detail(request, dashboard_id):
    dashboard = Dashboard.objects.filter(id=dashboard_id).first()
    context = {
        "dashboard": dashboard
    }
    return render(request, "dashboards/edit_form.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def delete_dashboard(request, dashboard_id):
    dashboard = Dashboard.objects.filter(id=dashboard_id).first()
    category = dashboard.category 

    if dashboard:
        dashboard.delete()
        if category == "INDUSTRY":
                return redirect("minicom_dashboards:industry-dashboards")
    return redirect("minicom_dashboards:trade-dashboards")
