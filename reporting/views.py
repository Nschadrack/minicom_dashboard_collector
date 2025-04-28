from datetime import datetime, date
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import ReportingPeriodPlan, IndustryProductReport, EmploymentReport
from industry.models import IndustryProduct, CompanySite
from automation.utils import format_number


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def reporting(request):
    # Fetch industry IDs efficiently
    industries = CompanySite.objects.all()
    industry_ids = list(industries.values_list('id', flat=True))
    industry_products= list(IndustryProduct.objects.filter(industry__id__in=industry_ids))
    today = datetime.now().date()

    # Get the next reporting period plan
    next_report_plan = ReportingPeriodPlan.objects.filter(end_date__gte=today).order_by('end_date').first()

    # Determine the most recent report
    already_reported = IndustryProductReport.objects.filter(product__industry__id__in=industry_ids).order_by('-end_date').first()
    already_reported_employment = EmploymentReport.objects.filter(industry__id__in=industry_ids).order_by("-end_date").first()

    # Establish recent report date
    recent_report_date = already_reported.end_date if already_reported else date(today.year, 1, 1)
    recent_employment_report_date = already_reported_employment.end_date if already_reported_employment else date(today.year, 1, 1)

    # Find the next plan from the most recent report date
    next_calculated_plan = ReportingPeriodPlan.objects.filter(end_date__gt=recent_report_date).order_by('end_date').first()
    next_calculated_employment_plan = ReportingPeriodPlan.objects.filter(end_date__gt=recent_employment_report_date).order_by('end_date').first()

    # Determine if there are pending reports and the applicable plan
    has_pending_products_report = False
    has_pending_employment_report = False
    considered_next_plan = next_report_plan
    considered_next_employment_plan = next_report_plan

    if next_calculated_plan and next_report_plan:
        if next_calculated_plan.end_date < next_report_plan.end_date:
            has_pending_products_report = True
            considered_next_plan = next_calculated_plan
    
    if next_calculated_employment_plan and next_report_plan:
        if next_calculated_employment_plan.end_date < next_report_plan.end_date:
            has_pending_employment_report = True
            considered_next_employment_plan = next_calculated_employment_plan
        

    # Identify products already reported
    all_reported = []
    all_reported_industries = []
    considered_start_date = next_report_plan.start_date if next_report_plan else datetime.now()
    considered_end_date = next_report_plan.end_date  if next_report_plan else datetime.now()
    considered_start_date_employment = next_report_plan.start_date if next_report_plan else datetime.now()
    considered_end_date_employment = next_report_plan.end_date if next_report_plan else datetime.now()

    if already_reported:
        # Collect product IDs from existing reports
        reported_product_ids = IndustryProductReport.objects.filter(product__industry__id__in=industry_ids,
                                                                    start_date=already_reported.start_date, 
                                                                    end_date=already_reported.end_date).values_list('product_id', flat=True)
        all_reported = list(reported_product_ids)
        # exclude already reported products
        industry_products = [ prod for prod in industry_products if prod.id not in all_reported ]

    if already_reported_employment:
        # collect industries already report on employment
        reported_industry_ids = EmploymentReport.objects.filter(industry__id__in=industry_ids,
                                                                start_date=already_reported_employment.start_date,
                                                                end_date=already_reported_employment.end_date).values_list("industry_id", flat=True)
        all_reported_industries = list(reported_industry_ids)
        # exclude already reported industries
        industries = [ industry for industry in industries if industry.id not in all_reported_industries]

   

    if len(industries) > 0 and already_reported_employment:
        considered_start_date_employment = already_reported_employment.start_date
        considered_end_date_employment = already_reported_employment.end_date
        has_pending_employment_report = True
    else:
        if considered_next_employment_plan:
            # Use considered next employment plan dates if no existing industry employment reports
            considered_start_date_employment = considered_next_employment_plan.start_date
            considered_end_date_employment = considered_next_employment_plan.end_date

            # Check for unreported industries using current considered plan
            reported_industry_ids = EmploymentReport.objects.filter(industry__id__in=industry_ids,
                                                                start_date=considered_next_employment_plan.start_date,
                                                                end_date=considered_next_employment_plan.end_date).values_list("industry_id", flat=True)
            
            all_reported_industries = list(reported_industry_ids)
        
        # Getting industries that need to report
        industries = CompanySite.objects.exclude(id__in=all_reported_industries)


    if len(industry_products) > 0 and already_reported:
        considered_start_date = already_reported.start_date
        considered_end_date = already_reported.end_date
        has_pending_products_report = True
    else:
        if considered_next_plan:
            # Use considered plan dates if no existing reports
            considered_start_date = considered_next_plan.start_date
            considered_end_date = considered_next_plan.end_date

            # Check for unreported products using current considered plan
            reported_product_ids = IndustryProductReport.objects.filter(product__industry__id__in=industry_ids,
                                                                        start_date=considered_next_plan.start_date,
                                                                        end_date=considered_next_plan.end_date).values_list('product_id', flat=True)
            all_reported = list(reported_product_ids)

        # Get products needing reports
        industry_products = IndustryProduct.objects.exclude(id__in=all_reported)

    # Build user messages
    add_new_report_message = "No upcoming reporting periods available."
    if next_report_plan:
        base_message = (
            f"The next reporting period starts on <b>{next_report_plan.end_date.strftime('%d-%m-%Y')}</b> "
            f"covering the period <b>from {next_report_plan.start_date.strftime('%d-%m-%Y')} To "
            f"{next_report_plan.end_date.strftime('%d-%m-%Y')}.</b>"
        )
        if has_pending_products_report and considered_start_date and considered_end_date:
            base_message += (
                f"<br/>You have pending reports from <b>{considered_start_date.strftime('%d-%m-%Y')} "
                f"to {next_report_plan.end_date.strftime('%d-%m-%Y')}.</b>"
            )
        add_new_report_message = base_message

    # Create header with appropriate dates
    header_add_new_product_report = "List of Products to Report On During the Period of "
    if considered_start_date and considered_end_date:
        header_add_new_product_report += (
            f"{considered_start_date.strftime('%d-%m-%Y')} To "
            f"{considered_end_date.strftime('%d-%m-%Y')}"
        )

    context = {
        "add_new_report_message": add_new_report_message,
        "header_add_new_product_report": header_add_new_product_report,
        "has_pending_products_report": has_pending_products_report,
        "industry_products_to_report_on": industry_products,
        "next_report_plan": next_report_plan,
        "considered_start_date": considered_start_date.strftime('%d-%m-%Y'),
        "considered_end_date": considered_end_date.strftime('%d-%m-%Y'),
        "has_pending_employment_report": has_pending_employment_report,
        "considered_start_date_employment": considered_start_date_employment.strftime("%d-%m-%Y"),
        "considered_end_date_employment": considered_end_date_employment.strftime("%d-%m-%Y"),
        "industries": industries
    }

    return render(request, "reporting/reporting.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def add_product_report(request, product_id, start_date, end_date):
    product = None
    enable_justification = False
    reported_capacity = None
    try:
        product = IndustryProduct.objects.get(id=product_id)
    except IndustryProduct.DoesNotExist:
        message = "Unable to load the product reporting form"
        messages.error(request, message=message)
        redirect_url = reverse('reporting:reporting')
        return redirect(f"{redirect_url}#add-report")
    
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        production_volume = request.POST.get("production_volume")
        justification_production_capacity = request.POST.get("justification_production_capacity", "")

        if float(production_volume) > float(product.production_installed_capacity) and len(justification_production_capacity.strip()) < 10:
            enable_justification = True
            message = f"You reported production = {format_number(production_volume)} {product.production_installed_capacity_unit} "
            message += f"which is greated than installed production capacity = {format_number(product.production_installed_capacity)} {product.production_installed_capacity_unit}/{product.production_installed_capacity_period}."
            message += "You can provide more information why you exceeded the installed production capacity or if you have extended your production line, please edit the production installed capacity under products module"
            message += " and resume the report on this product."
            reported_capacity = production_volume
            messages.error(request, message=message)
        else:
            try:
                start_date = datetime.strptime(start_date, "%d-%m-%Y")
                end_date = datetime.strptime(end_date, "%d-%m-%Y")
                IndustryProductReport.objects.create(
                    start_date=start_date,
                    end_date=end_date,
                    product=product,
                    production_volume=production_volume,
                    current_installed_production=product.production_installed_capacity,
                    reported_by=request.user,
                    justification_production_capacity=justification_production_capacity
                )
                message = f"Report for the period from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')} on the product: {product.product.product_code} - {product.product.name} - {product.product_brand_name} added successfully"
                messages.success(request, message=message)
            except Exception as e:
                message = f"Unable to add report. error: {str(e)}"
                messages.error(request, message=message)        
            redirect_url = reverse('reporting:reporting')
            return redirect(f"{redirect_url}#add-report")

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "product": product,
        "reported_capacity": reported_capacity,
        "enable_justification": enable_justification,
    }
    return render(request, "reporting/product_report_form.html", context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def add_employment_report(request, industry_id, start_date, end_date):
    industry = None
    try:
        industry = CompanySite.objects.get(id=industry_id)
    except CompanySite.DoesNotExist:
        message = "Unable to load the employment reporting form"
        messages.error(request, message)
        redirect_url = reverse('reporting:reporting')
        return redirect(f"{redirect_url}#add-report")
    
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        current_female_permanent_employees = request.POST.get("current_female_permanent_employees")
        current_male_permanent_employees = request.POST.get("current_male_permanent_employees")
        current_female_casual_employees = request.POST.get("current_female_casual_employees")
        current_male_casual_employees = request.POST.get("current_male_casual_employees")
        new_female_permanent_employees = request.POST.get("new_female_permanent_employees")
        new_male_permanent_employees = request.POST.get("new_male_permanent_employees")
        new_female_casual_employees = request.POST.get("new_female_casual_employees")
        new_male_casual_employees = request.POST.get("new_male_casual_employees")
        job_loss = request.POST.get("job_loss")
        current_female_youth_employees = request.POST.get("current_female_youth_employees")
        current_male_youth_employees = request.POST.get("current_male_youth_employees")
        improvement_suggestion = request.POST.get("improvement_suggestion")
        challenges_faced = request.POST.get("challenges_faced")
        support_needed = request.POST.get("support_needed")

        error = False
        message = ""
        if int(current_female_permanent_employees) + int(current_female_casual_employees) < int(current_female_youth_employees):
            error = True
            message = f"current female employees(permanent + casual) = {int(current_female_permanent_employees) + int(current_female_casual_employees)} and cannot be less than the current female youth employees = {current_female_youth_employees}"
        
        if int(current_male_permanent_employees) + int(current_male_casual_employees) < int(current_male_youth_employees):
            error = True
            message += f"current male employees(permanent + casual) = {int(current_male_permanent_employees) + int(current_male_casual_employees)} and cannot be less than the current male youth employees = {int(current_male_youth_employees)}"
        
        if error:
           messages.error(request, message)
           redirect_url = reverse('reporting:reporting')
           return redirect(f"{redirect_url}#add-report") 


        try:
            start_date = datetime.strptime(start_date, "%d-%m-%Y")
            end_date = datetime.strptime(end_date, "%d-%m-%Y")

            EmploymentReport.objects.create(
                start_date=start_date,
                end_date=end_date,
                industry=industry,
                current_female_casual_employees=current_female_casual_employees,
                current_male_casual_employees=current_male_casual_employees,
                current_female_permanent_employees=current_female_permanent_employees,
                current_male_permanent_employees=current_male_permanent_employees,
                new_female_casual_employees=new_female_casual_employees,
                new_male_casual_employees=new_male_casual_employees,
                new_female_permanent_employees=new_female_permanent_employees,
                new_male_permanent_employees=new_male_permanent_employees,
                job_loss=job_loss,
                current_female_youth_employees=current_female_youth_employees,
                current_male_youth_employees=current_male_youth_employees,
                improvement_suggestion=improvement_suggestion,
                challenges_faced=challenges_faced,
                support_needed=support_needed,
                 reported_by=request.user
            )
            message = f"The employment report for the period from {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')} for the industry: {industry.company.tin_number} - {industry.company.name}: Located in "

            if industry.is_in_park:
                message += f"{industry.allocated_plot.park.name.title()} {industry.allocated_plot.park.category.title()}"
            else:
                message += f"{industry.province.title()} - {industry.district.title()} - {industry.sector.title()} - {industry.cell.title()}"

            message += " added successfully"
            messages.success(request, message)
        except Exception as e:
            message = f"Unable to add report. error: {str(e)}"
            messages.error(request, message)
    
        redirect_url = reverse('reporting:reporting')
        return redirect(f"{redirect_url}#add-report")

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "industry": industry
    }
    return render(request, "reporting/employment_form.html", context)