from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Dashboard


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def industry_dashboards(request):
    if request.method == "POST":
        name = request.POST.get("name")
        dashboard_link = request.POST.get("dashboard_link")
        category = "INDUSTRY"
        Dashboard.objects.create(
            name=name,
            category=category,
            dashboard_link=dashboard_link,
            created_by=request.user
        )

    dashboards = Dashboard.objects.filter(category="INDUSTRY").order_by("name")
    context = {
        "dashboards": dashboards
    }
    return render(request, "dashboards/industry.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def trade_dashboards(request):
    if request.method == "POST":
        name = request.POST.get("name")
        dashboard_link = request.POST.get("dashboard_link")
        category = "TRADE"
        Dashboard.objects.create(
            name=name,
            category=category,
            dashboard_link=dashboard_link,
            created_by=request.user
        )
        
    dashboards = Dashboard.objects.filter(category="TRADE").order_by("name")
    context = {
        "dashboards": dashboards
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
