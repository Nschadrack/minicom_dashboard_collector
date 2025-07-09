import datetime
from datetime import datetime as datetime_obj
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.db.models import (Sum, Count, F, Q, Case, When, 
                              Value, DecimalField, Avg, Subquery, OuterRef)
from django.db.models.functions import Coalesce, TruncMonth
from django.views import View
from django.utils import timezone

from system_management.models import User, Role, UserRole, EconomicSubSector
from industry.models import (
    CompanyProfile, CompanySite, IndustryEconomicZone, 
    AllocatedPlot, PartitionedPlot, IndustryContractPayment
)
from trade.models import FormalTrade, ICBTRecord
from reporting.models import IndustryProductReport, EmploymentReport


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def dashboard(request):
    return render(request, "welcome/dashboard.html")

@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
def welcome(request):
    today = datetime_obj.now()
    hour = today.hour
    # Determine the appropriate greeting based on the time
    if 0 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    today = today.strftime("It's %A, %d %B %Y  %H:%M:%S")
    context = {
        "user": request.user,
        "title": "Welcome",
        "today": today,
        "greeting": f"{greeting}, {request.user.get_full_name()}"
    }
    return render(request, "welcome/welcome.html", context=context)

class DashboardDataView(View):
    def get(self, request, *args, **kwargs):
        filters = {k: v for k, v in request.GET.items()}
        data = {
            'industry': self.get_industry_data(filters),
            'parks': self.get_park_data(filters),
            'trade': self.get_trade_data(filters),
            'payments': self.get_payment_data(filters),
            'reporting': self.get_reporting_data(filters),
            'admin': self.get_admin_data(filters),
        }
        if not request.GET:
            data['filters'] = self.get_filter_options()
        return JsonResponse(data, safe=False)

    def get_filter_options(self):
        return {
            'sectors': list(EconomicSubSector.objects.values_list('name', flat=True).distinct()),
            'company_sizes': [size[0] for size in CompanyProfile.COMPANY_SIZES],
            'parks': list(IndustryEconomicZone.objects.values_list('name', flat=True).distinct()),
            'countries': list(FormalTrade.objects.values_list('origin_country_name', flat=True).distinct().order_by('origin_country_name')),
            'companies': list(CompanyProfile.objects.values_list('name', flat=True).distinct().order_by('name')),
        }

    def apply_filters(self, queryset, model_filters):
        for key, value in model_filters.items():
            if value and value != 'all':
                queryset = queryset.filter(**{key: value})
        return queryset

    def get_industry_data(self, filters):
        sites = CompanySite.objects.select_related('company').prefetch_related('industryeconomicsector_set__sector')
        if f_year := filters.get('industry_year', 'all'): sites = self.apply_filters(sites, {'operational_start_date__year': f_year})
        if f_sector := filters.get('industry_sector', 'all'): sites = self.apply_filters(sites, {'industryeconomicsector__sector__name': f_sector})
        if f_size := filters.get('industry_size', 'all'): sites = self.apply_filters(sites, {'company__company_size': f_size})
        
        profiles = CompanySite.objects.all().distinct()
        employment = EmploymentReport.objects.filter(industry__in=sites)
        production = IndustryProductReport.objects.filter(product__industry__in=sites)

        total_companies = profiles.count()
        agg_investment = sites.aggregate(total=Coalesce(Sum('investment_amount'), 0, output_field=DecimalField()), avg=Coalesce(Avg('investment_amount'), 0, output_field=DecimalField()))
        emp_agg = employment.aggregate(
            male=Coalesce(Sum('current_male_permanent_employees'), 0, output_field=DecimalField()) + Coalesce(Sum('current_male_casual_employees'), 0, output_field=DecimalField()),
            female=Coalesce(Sum('current_female_permanent_employees'), 0, output_field=DecimalField()) + Coalesce(Sum('current_female_casual_employees'), 0, output_field=DecimalField())
        )

        return {
            'total_companies': total_companies,
            'total_investment': agg_investment['total'],
            'avg_investment': agg_investment['avg'],
            'total_employees': emp_agg['male'] + emp_agg['female'],
            'companies_under_construction': sites.filter(construction_status="Under Construction").count(),
            'company_by_sector': {i['industryeconomicsector__sector__name']: i['count'] for i in sites.values('industryeconomicsector__sector__name').annotate(count=Count('id')) if i['industryeconomicsector__sector__name']},
            'operational_status': dict(sites.values_list('operational_status').annotate(count=Count('id'))),
            'production_by_product': dict(production.values_list('product__product__name').annotate(total=Sum('production_volume')).order_by('-total')[:5]),
            'employment_by_gender': emp_agg,
        }

    def get_park_data(self, filters):
        parks_qs = IndustryEconomicZone.objects.prefetch_related('park_allocated_plots', 'park_partitioned_plots')
        if f_park := filters.get('park', 'all'): parks_qs = self.apply_filters(parks_qs, {'name': f_park})

        occupancy_data = parks_qs.annotate(
            total_allocated_size=Coalesce(Sum('park_allocated_plots__plot_size'), 0.0, output_field=DecimalField()),
            occupancy=Case(When(leasable_land__gt=0, then=(F('total_allocated_size') * 100 / F('leasable_land'))), default=Value(0.0), output_field=DecimalField())
        )
        plot_status = {p.name: {'allocated': p.park_allocated_plots.count(), 'available': p.park_partitioned_plots.filter(is_allocated=False).count()} for p in parks_qs}
        
        return {
            'total_parks': IndustryEconomicZone.objects.count(),
            'total_land': IndustryEconomicZone.objects.aggregate(total=Coalesce(Sum('leasable_land'), 0, output_field=DecimalField()))['total'] / 10000, # to hectares
            'total_allocated_plots': AllocatedPlot.objects.count(),
            'total_available_plots': PartitionedPlot.objects.filter(is_allocated=False).count(),
            'industries_by_park': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('allocated_plot__park__name').annotate(count=Count('id'))),
            'park_occupancy': {p.name: round(p.occupancy, 2) for p in occupancy_data},
            'plot_status': plot_status,
            'investment_by_park': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('allocated_plot__park__name').annotate(total=Sum('investment_amount'))),
        }

    def get_trade_data(self, filters):
        formal = FormalTrade.objects.all()
        informal = ICBTRecord.objects.all()
        if f_year := filters.get('trade_year', 'all'):
            formal = self.apply_filters(formal, {'rra_recorded_date__year': f_year})
            informal = self.apply_filters(informal, {'date_period__year': f_year})
        if f_country := filters.get('trade_country', 'all'):
            formal = formal.filter(Q(origin_country_name=f_country) | Q(destination_country_name=f_country))
            informal = informal.filter(Q(product_origin=f_country) | Q(product_destination=f_country))

        imports_val = formal.filter(category='IMPORT').aggregate(total=Coalesce(Sum('fob_usd'), 0, output_field=DecimalField()))['total']
        exports_val = formal.filter(category='EXPORT').aggregate(total=Coalesce(Sum('fob_usd'), 0, output_field=DecimalField()))['total']
        top_partner = formal.values('origin_country_name').annotate(total=Sum('fob_usd')).order_by('-total').first()

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        imports_flow = dict(formal.filter(category='IMPORT').values_list('month').annotate(total=Sum('fob_usd')))
        exports_flow = dict(formal.filter(category='EXPORT').values_list('month').annotate(total=Sum('fob_usd')))

        return {
            'formal_total': imports_val + exports_val,
            'informal_total': informal.aggregate(total=Coalesce(Sum('total_price_usd'), 0, output_field=DecimalField()))['total'],
            'trade_balance': exports_val - imports_val,
            'top_partner': top_partner['origin_country_name'] if top_partner else '-',
            'trade_flow': {'labels': months, 'imports': [imports_flow.get(m, 0) for m in months], 'exports': [exports_flow.get(m, 0) for m in months]},
            'top_imports': dict(formal.filter(category='IMPORT').values_list('product_description').annotate(total=Sum('cif_usd')).order_by('-total')[:5]),
            'top_exports': dict(formal.filter(category='EXPORT').values_list('product_description').annotate(total=Sum('fob_usd')).order_by('-total')[:5]),
        }

    def get_payment_data(self, filters):
        payments = IndustryContractPayment.objects.select_related('contract__industry__company')
        if f_year := filters.get('payment_year', 'all'): payments = self.apply_filters(payments, {'contract__signing_date__year': f_year})
        if f_company := filters.get('payment_company', 'all'): payments = self.apply_filters(payments, {'contract__industry__company__name': f_company})
        
        kpis = payments.aggregate(paid=Coalesce(Sum('total_amount_paid'), 0, output_field=DecimalField()), 
                                  unpaid=Coalesce(Sum('total_amount_unpaid'), 0, output_field=DecimalField()), 
                                  overdue=Coalesce(Sum('amount_overdued'), 0, output_field=DecimalField()))
        trends_qs = payments.filter(payment_installments__installment_transactions__payment_date__isnull=False)
        trends = trends_qs.annotate(month=TruncMonth('payment_installments__installment_transactions__payment_date')).values('month').annotate(total=Sum('payment_installments__installment_transactions__payment_amount')).order_by('month')

        return {
            'total_paid': kpis['paid'], 'total_unpaid': kpis['unpaid'], 'total_overdue': kpis['overdue'],
            'contracts_in_arrears': payments.filter(days_in_arrears__gt=0).count(),
            'payment_status_summary': dict(payments.values_list('payment_status').annotate(count=Count('id'))),
            'payment_trends': {'labels': [t['month'].strftime('%Y-%m-%d') for t in trends], 'data': [t['total'] for t in trends]},
            'top_unpaid_companies': dict(payments.filter(total_amount_unpaid__gt=0).values_list('contract__industry__company__name').annotate(total=Sum('total_amount_unpaid')).order_by('-total')[:5]),
            'payment_modality': dict(payments.values_list('payment_modality').annotate(count=Count('id'))),
        }

    def get_reporting_data(self, filters):
        period = filters.get('reporting_period', 'last_year')
        today = timezone.now().date()
        if period == 'last_quarter':
            start_date = today - datetime.timedelta(days=90)
        elif period == 'last_6_months':
            start_date = today - datetime.timedelta(days=180)
        else: # last_year
            start_date = today - datetime.timedelta(days=365)

        active_industries = CompanySite.objects.filter(operational_status__in=["Not Operational", "Fully Operational", "Partially Operational"])
        total_industries = active_industries.count()
        
        reported_industries_subquery = EmploymentReport.objects.filter(
            industry=OuterRef('pk'),
            reported_on__gte=start_date
        ).values('industry_id')
        
        industries_with_reports = active_industries.annotate(has_report=Subquery(reported_industries_subquery)).filter(has_report__isnull=False)
        reported_count = industries_with_reports.count()

        production_reports = IndustryProductReport.objects.filter(reported_on__gte=start_date, product__industry__in=industries_with_reports).select_related('product__industry__industryeconomicsector__sector')
        production_by_sector = dict(production_reports.values_list('product__industry__industryeconomicsector__sector__name').annotate(total=Sum('production_volume')))

        return {
            'total_industries': total_industries,
            'reported_count': reported_count,
            'not_reported_count': total_industries - reported_count,
            'compliance_rate': (reported_count / total_industries * 100) if total_industries > 0 else 0,
            'production_by_sector': production_by_sector,
        }

    def get_admin_data(self, filters):
        return {
            'total_users': User.objects.count(),
            'users_by_category': dict(User.objects.values_list('user_category').annotate(count=Count('id'))),
            'total_roles': Role.objects.count(),
            'users_by_role': dict(UserRole.objects.values_list('role__name').annotate(count=Count('id'))),
        }

