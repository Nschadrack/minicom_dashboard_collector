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
    AllocatedPlot, PartitionedPlot, IndustryContractPayment,
    IndustryEconomicSector
)
from trade.models import FormalTrade, ICBTRecord
from reporting.models import IndustryProductReport, EmploymentReport
from automation.utils import format_number


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
        "greeting": f"{greeting}, <b>{request.user.get_full_name()}</b>, <br/><br/> Welcome back!"
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
        sites = CompanySite.objects.select_related('company')
        # if f_year := filters.get('industry_year', 'all'): sites = self.apply_filters(sites, {'operational_start_date__year': f_year})
        # if f_sector := filters.get('industry_sector', 'all'): sites = self.apply_filters(sites, {'industryeconomicsector__sector__name': f_sector})
        # if f_size := filters.get('industry_size', 'all'): sites = self.apply_filters(sites, {'company__company_size': f_size})
        
        profiles = CompanyProfile.objects.all().distinct()
        employment = EmploymentReport.objects.filter(industry__in=sites)
        production = IndustryProductReport.objects.filter(product__industry__in=sites)

        total_profiles = profiles.count()
        total_industries_locations = sites.distinct().count()
        industry_economic_sector = dict(IndustryEconomicSector.objects.all().values_list("sector__economic_sector__name").annotate(count=Count('industry')))

        agg_investment = sites.filter(investment_currency__iexact="rwf").aggregate(total=Coalesce(Sum('investment_amount'), 0, output_field=DecimalField()), 
                                                                                   avg=Coalesce(Avg('investment_amount'), 0, output_field=DecimalField()))
        # emp_agg = employment.aggregate(
        #     male=Coalesce(Sum('current_male_permanent_employees'), 0, output_field=DecimalField()) + Coalesce(Sum('current_male_casual_employees'), 0, output_field=DecimalField()),
        #     female=Coalesce(Sum('current_female_permanent_employees'), 0, output_field=DecimalField()) + Coalesce(Sum('current_female_casual_employees'), 0, output_field=DecimalField())
        # )

        return {
            'total_industries': total_profiles,
            "total_industries_locations": total_industries_locations,
            'total_investment': agg_investment['total'],
            'avg_investment': agg_investment['avg'],
            # 'total_employees': emp_agg['male'] + emp_agg['female'],
            'companies_under_construction': sites.filter(construction_status="Under Construction").count(),
            'company_by_sector': industry_economic_sector,
            'operational_status': dict(sites.values_list('operational_status').annotate(count=Count('id'))),
            'construction_status': dict(sites.values_list('construction_status').annotate(count=Count('id'))),
            'location': dict(sites.values_list('is_in_park').annotate(count=Count('id'))),
            'electricity_tariff': dict(sites.values_list('benefited_electricity_tarrif').annotate(count=Count('id'))),
            "industry_size": dict(profiles.values_list("company_size").annotate(count=Count('id')))
            # 'production_by_product': dict(production.values_list('product__product__name').annotate(total=Sum('production_volume')).order_by('-total')[:5]),
            # 'employment_by_gender': emp_agg,
        }

    def get_park_data(self, filters):
        parks_qs = IndustryEconomicZone.objects.prefetch_related('park_allocated_plots', 'park_partitioned_plots')
        if f_park := filters.get('park', 'all'): parks_qs = self.apply_filters(parks_qs, {'name': f_park})

        occupancy_data = parks_qs.aggregate(
            total_allocated_size=Coalesce(Sum('park_allocated_plots__plot_size'), 0.0, output_field=DecimalField()),
            park_size=Coalesce(Sum('total_land_size'), 0.0, output_field=DecimalField()),
            total_leasable_land=Coalesce(Sum('leasable_land'), 0.0, output_field=DecimalField())
        )
        plot_status = {p.name: {'allocated': p.park_allocated_plots.count(), 'available': p.park_partitioned_plots.filter(is_allocated=False).count()} for p in parks_qs}
        industry_economic_sector = dict(IndustryEconomicSector.objects.filter(industry__allocated_plot__park__in=parks_qs).values_list("sector__economic_sector__name").annotate(count=Count('industry')))

        return {
            'total_parks': IndustryEconomicZone.objects.count(),
            'total_parks_land': occupancy_data["park_size"],
            "total_parks_leasable_land": occupancy_data["total_leasable_land"],
            "total_parks_unleasable_land":  occupancy_data["park_size"] - occupancy_data["total_leasable_land"],
            "total_leased_land": occupancy_data["total_allocated_size"],
            "total_unleased_land": occupancy_data["total_leasable_land"] - occupancy_data["total_allocated_size"],
            'total_allocated_plots': AllocatedPlot.objects.count(),
            'total_available_plots': PartitionedPlot.objects.filter(is_allocated=False).count(),
            'industries_by_park': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('allocated_plot__park__name').annotate(count=Count('id'))),
            'operational_status': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('operational_status').annotate(count=Count('id'))),
            'construction_status': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('construction_status').annotate(count=Count('id'))),
            'plot_status': plot_status,
            'industry_size': dict(CompanySite.objects.filter(is_in_park=True, allocated_plot__park__in=parks_qs).values_list('company__company_size').annotate(total=Count('company'))),
            "industry_economic_sector": industry_economic_sector
        }

    def get_trade_data(self, filters):
        formal = FormalTrade.objects.all()
        informal = ICBTRecord.objects.all()
        # if f_year := filters.get('trade_year', 'all'):
        #     formal = self.apply_filters(formal, {'rra_recorded_date__year': f_year})
        #     informal = self.apply_filters(informal, {'date_period__year': f_year})
        # if f_country := filters.get('trade_country', 'all'):
        #     formal = formal.filter(Q(origin_country_name=f_country) | Q(destination_country_name=f_country))
        #     informal = informal.filter(Q(product_origin=f_country) | Q(product_destination=f_country))

        # Formal Trade
        formal_imports_val = formal.filter(category='IMPORT').aggregate(total=Coalesce(Sum('cif_usd'), 0,  output_field=DecimalField()),
                                                                        total_rw=Coalesce(Sum('cif'), 0,  output_field=DecimalField()))
        formal_exports_val = formal.filter(category='EXPORT').aggregate(total=Coalesce(Sum('fob_usd'), 0,  output_field=DecimalField()),
                                                                        total_rw=Coalesce(Sum('fob'), 0,  output_field=DecimalField()))
        
        formal_re_exports_val = formal.filter(category='RE-EXPORT').aggregate(total=Coalesce(Sum('fob_usd'), 0,  output_field=DecimalField()),
                                                                              total_rw=Coalesce(Sum('fob'), 0,  output_field=DecimalField()))

        # ICBT Imports
        icbt_imports_val = informal.filter(product_destination__iexact='RWANDA').aggregate(total=Coalesce(Sum('total_price_usd'), 0,  output_field=DecimalField()),
                                                                                           total_rw=Coalesce(Sum('total_price'), 0,  output_field=DecimalField()))
        
        icbt_exports_val = informal.filter(product_origin__iexact="RWANDA").aggregate(total=Coalesce(Sum('total_price_usd'), 0,  output_field=DecimalField()),
                                                                                      total_rw=Coalesce(Sum('total_price'), 0,  output_field=DecimalField()))

        # Partners
        formal_top_partner_import_from = dict(formal.filter(category='IMPORT').values_list('origin_country_name').annotate(total=Sum('cif_usd')).order_by('-total')[:10])
        formal_top_partner_export_to = dict(formal.filter(category='EXPORT').values_list('destination_country_name').annotate(total=Sum('fob_usd')).order_by('-total')[:10])
        formal_top_partner_re_export_to = dict(formal.filter(category='RE-EXPORT').values_list('destination_country_name').annotate(total=Sum('fob_usd')).order_by('-total')[:10])
        icbt_top_partner_import_from = dict(informal.filter(product_destination__iexact='RWANDA').values_list('product_origin').annotate(total=Sum('total_price_usd')).order_by('-total'))
        icbt_top_partner_export_to = dict(informal.filter(product_origin__iexact="RWANDA").values_list('product_destination').annotate(total=Sum('total_price_usd')).order_by('-total'))

        # Top Products
        formal_top_products_import_from = dict(formal.filter(category='IMPORT').values_list('product_description').annotate(total=Sum('cif_usd')).order_by('-total')[:10])
        formal_top_products_export_to = dict(formal.filter(category='EXPORT').values_list('product_description').annotate(total=Sum('fob_usd')).order_by('-total')[:10])
        formal_top_products_re_export_to = dict(formal.filter(category='RE-EXPORT').values_list('product_description').annotate(total=Sum('fob_usd')).order_by('-total')[:10])
        icbt_top_products_import_from = dict(informal.filter(product_destination__iexact='RWANDA').values_list('product').annotate(total=Sum('total_price_usd')).order_by('-total')[:10])
        icbt_top_products_export_to = dict(informal.filter(product_origin__iexact="RWANDA").values_list('product').annotate(total=Sum('total_price_usd')).order_by('-total')[:10])


        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        formal_imports_flow = dict(formal.filter(category='IMPORT').values_list('month').annotate(total=Coalesce(Sum('cif_usd'), 0, output_field=DecimalField())))
        formal_exports_flow = dict(formal.filter(category='EXPORT').values_list('month').annotate(total=Coalesce(Sum('fob_usd'), 0, output_field=DecimalField())))
        formal_re_exports_flow = dict(formal.filter(category='RE-EXPORT').values_list('month').annotate(total=Coalesce(Sum('fob_usd'), 0, output_field=DecimalField())))

        icbt_import_flow = dict(informal.filter(product_destination__iexact='RWANDA').values_list('month').annotate(total=Coalesce(Sum('total_price_usd'), 0, output_field=DecimalField())))
        icbt_exports_flow = dict(informal.filter(product_origin__iexact="RWANDA").values_list('month').annotate(total=Coalesce(Sum('total_price_usd'), 0, output_field=DecimalField())))
        
        return {
            'formal_imports_val': formal_imports_val['total'],
            'formal_imports_val_rw': formal_imports_val['total_rw'],
            'formal_exports_val': formal_exports_val['total'],
            'formal_exports_val_rw': formal_exports_val['total_rw'],
            "formal_re_exports_val": formal_re_exports_val['total'],
            "formal_re_exports_val_rw": formal_re_exports_val['total_rw'],
            'icbt_imports_val': icbt_imports_val['total'],
            'icbt_imports_val_rw': icbt_imports_val['total_rw'],
            "icbt_exports_val": icbt_exports_val['total'],
            "icbt_exports_val_rw": icbt_exports_val['total_rw'],
            'formal_trade_balance': formal_exports_val['total'] - formal_imports_val['total'],
            'formal_trade_balance_rw': formal_exports_val['total_rw'] - formal_imports_val['total_rw'],
            "icbt_balance": icbt_exports_val['total'] - icbt_imports_val['total'],
            "icbt_balance_rw": icbt_exports_val['total_rw'] - icbt_imports_val['total_rw'],
            'trade_flow': {'labels': month_labels, 'imports': [formal_imports_flow.get(m.title(), 0) for m in months], 
                           'exports': [formal_exports_flow.get(m.title(), 0) for m in months],
                           're_exports': [formal_re_exports_flow.get(m.title(), 0) for m in months]
                           },
            'icbt_flow': {'labels': month_labels, 'imports': [icbt_import_flow.get(m.title(), 0) for m in months], 
                           'exports': [icbt_exports_flow.get(m.title(), 0) for m in months],
                           },
            'formal_top_imports': formal_top_partner_import_from,
            'formal_top_exports': formal_top_partner_export_to,
            "formal_top_re_exports": formal_top_partner_re_export_to,
            'icbt_top_imports': icbt_top_partner_import_from,
            'icbt_top_exports': icbt_top_partner_export_to,
            'formal_top_product_imports': formal_top_products_import_from,
            'formal_top_product_exports': formal_top_products_export_to,
            "formal_top_re_product_exports": formal_top_products_re_export_to,
            'icbt_top_product_imports': icbt_top_products_import_from,
            'icbt_top_product_exports': icbt_top_products_export_to,
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

