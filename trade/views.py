from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from automation.models import BulkUploadJob
from .tasks import process_csv_icbt, process_csv_formal_trade
# from .tasks import process_csv_formal_trade
from .models import ICBTRecord, FormalTrade

from  system_management.permissions import check_role_permission_on_module_decorator


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0020", 3)
def icbt_view(request):
    icbt_jobs = BulkUploadJob.objects.filter(category="ICBT").order_by("-created_at")
    page_number = request.GET.get('page', 1)
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    all_icbts_tab_type = "all_icbts_tab"
    export_icbt_tab_type = "export_icbts_tab"
    import_icbt_tab_type = "import_icbs_tab"

    # Layer 1: Cache ordered ID list with versioning
    cache_key_all_icbts_ids = f"{all_icbts_tab_type}_ids"
    cache_key_export_icbt_ids = f"{export_icbt_tab_type}_ids"
    cache_key_import_icbt_ids = f"{import_icbt_tab_type}_ids"
    ordered_all_icbts_ids = cache.get(cache_key_all_icbts_ids)
    ordered_export_icbt_ids = cache.get(cache_key_export_icbt_ids)
    ordered_import_icbt_ids = cache.get(cache_key_import_icbt_ids)

    if page_number == 1 or not ordered_all_icbts_ids or not ordered_export_icbt_ids or not ordered_import_icbt_ids:
        ordered_all_icbts_ids = list(ICBTRecord.objects.values_list('id', flat=True))
        ordered_export_icbt_ids = list(ICBTRecord.objects.filter(product_origin__iexact="rwanda").values_list('id', flat=True))
        ordered_import_icbt_ids = list(ICBTRecord.objects.filter(product_destination__iexact="rwanda").values_list('id', flat=True))
        cache.set(cache_key_all_icbts_ids, ordered_all_icbts_ids, CACHE_TIMEOUT)
        cache.set(cache_key_export_icbt_ids, ordered_export_icbt_ids, CACHE_TIMEOUT)
        cache.set(cache_key_import_icbt_ids, ordered_import_icbt_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    all_icbts_paginator = Paginator(ordered_all_icbts_ids, PAGE_SIZE)
    export_icbt_paginator = Paginator(ordered_export_icbt_ids, PAGE_SIZE)
    import_icbt_paginator = Paginator(ordered_import_icbt_ids, PAGE_SIZE)

    try:
        current_all_icbt_page = all_icbts_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_all_icbt_page = all_icbts_paginator.page(1)
    
    try:
        current_export_icbt_page = export_icbt_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_export_icbt_page = export_icbt_paginator.page(1)

    try:
        current_import_icbt_page = import_icbt_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_import_icbt_page = import_icbt_paginator.page(1)
    
    current_all_icbt_ids = current_all_icbt_page.object_list
    current_export_icbt_ids = current_export_icbt_page.object_list
    current_import_icbt_ids = current_import_icbt_page.object_list

    all_icbts = ICBTRecord.objects.filter(id__in=current_all_icbt_ids).order_by("-date_period")
    export_icbts = ICBTRecord.objects.filter(id__in=current_export_icbt_ids).order_by("-date_period")
    import_icbts = ICBTRecord.objects.filter(id__in=current_import_icbt_ids).order_by("-date_period")

    context = {
        "all_icbts": all_icbts,
        "all_icbts_page": current_all_icbt_page,
        "export_icbts": export_icbts,
        "export_icbts_page": current_export_icbt_page,
        "import_icbts": import_icbts,
        "import_icbts_page": current_import_icbt_page,
        "icbt_jobs": icbt_jobs
    }

    return render(request, "trade/icbt/trade.html", context=context)


def clean_csv_file(request):
    MAX_SIZE = 60 * 1024 * 1024 # 50MB
    file =  request.FILES.get('csv_file', None)
    if not file.name.endswith('.csv'):
        return None, 'Only CSV files are allowed'
    
    if file.size > MAX_SIZE:
        return None, f'File size exceeds {MAX_SIZE} MBs. Split the file into chuncks and upload one by one'
    
    return file, None


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0020", 1)
def icbt_upload_view(request):
    if request.method == "POST":
        file, message = clean_csv_file(request)
        if file:
            upload_job = BulkUploadJob.objects.create(user=request.user, category="ICBT", uploaded_file=file)
            process_csv_icbt(upload_job.id)
            messages.info(request, "Bulk upload has started. You can monitor the status here.")

            redirect_url = reverse('trade:icbt-list')
            return redirect(f"{redirect_url}#icbt-upload-job")
        else:
            messages.error(request, f"Invalid form submission. Please check the file. {message}")
            return redirect("trade:upload-icbt")
    
    required_columns = [
            "date",	"Time",	"enumerator_code", "enumerator_name", "crossing_point_code",
            "crosspoint_name",	"district_name", "gender",	"age",	"profession",	
            "residence_country",	"origin_country", "flow", "destination_country",	
            "mode_transport",	"product_name",	"unit",	"quantity",	"price",	
            "unit_price", 	"main_category",	"sub_category",	
            "HSCode",	"latitude",	"longitude",	"altitude",	"gps_accuracy"
        ]

    required_columns = sorted([col.lower() for col in required_columns])
    context = {
        'required_columns': required_columns
    }
    return render(request, 'trade/icbt/upload_icbt.html', context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0021", 3)
def formal_trade_view(request):
    formal_trade_jobs = BulkUploadJob.objects.filter(category="FORMAL_TRADE").order_by("-created_at")
    page_number = request.GET.get('page', 1)
    CACHE_TIMEOUT = settings.CACHE_TIMEOUT
    PAGE_SIZE = settings.PAGE_SIZE
    import_formal_tab_type = "import_formal_tab"
    export_formal_tab_type = "export_formal_tab"
    re_export_formal_tab_type = "re_export_tab"

    # Layer 1: Cache ordered ID list with versioning
    cache_key_import_formal_tab_ids = f"{import_formal_tab_type}_ids"
    cache_key_export_formal_tab_ids = f"{export_formal_tab_type}_ids"
    cache_key_re_export_formal_tab_ids = f"{re_export_formal_tab_type}_ids"
    ordered_import_formal_ids = cache.get(cache_key_import_formal_tab_ids)
    ordered_export_formal_ids = cache.get(cache_key_export_formal_tab_ids)
    ordered_re_export_formal_ids = cache.get(cache_key_re_export_formal_tab_ids)

    if page_number == 1 or not ordered_import_formal_ids or not ordered_export_formal_ids or not ordered_re_export_formal_ids:
        ordered_import_formal_ids = list(FormalTrade.objects.filter(category__iexact="IMPORT").values_list('id', flat=True))
        ordered_export_formal_ids = list(FormalTrade.objects.filter(category__iexact="EXPORT").values_list('id', flat=True))
        ordered_re_export_formal_ids = list(FormalTrade.objects.filter(category__iexact="RE-EXPORT").values_list('id', flat=True))
        cache.set(cache_key_import_formal_tab_ids, ordered_import_formal_ids, CACHE_TIMEOUT)
        cache.set(cache_key_export_formal_tab_ids, ordered_export_formal_ids, CACHE_TIMEOUT)
        cache.set(cache_key_re_export_formal_tab_ids, ordered_re_export_formal_ids, CACHE_TIMEOUT)
    
    # Paginate IDs
    imports_paginator = Paginator(ordered_import_formal_ids, PAGE_SIZE)
    exports_paginator = Paginator(ordered_export_formal_ids, PAGE_SIZE)
    re_exports_paginator = Paginator(ordered_re_export_formal_ids, PAGE_SIZE)

    try:
        current_imports_page = imports_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_imports_page = imports_paginator.page(1)
    
    try:
        current_exports_page = exports_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_exports_page = exports_paginator.page(1)

    try:
        current_re_exports_page = re_exports_paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        current_re_exports_page = re_exports_paginator.page(1)
    
    current_imports_ids = current_imports_page.object_list
    current_exports_ids = current_exports_page.object_list
    current_re_exports_ids = current_re_exports_page.object_list

    imports_formal = FormalTrade.objects.filter(id__in=current_imports_ids).order_by("-rra_recorded_date")
    exports_formal = FormalTrade.objects.filter(id__in=current_exports_ids).order_by("-rra_recorded_date")
    re_exports_formal = FormalTrade.objects.filter(id__in=current_re_exports_ids).order_by("-rra_recorded_date")

    context = {
        "formal_trade_jobs": formal_trade_jobs,
        "imports_formal": imports_formal,
        "imports_page": current_imports_page,
        "exports_formal": exports_formal,
        "exports_page": current_exports_page,
        "re_exports_formal": re_exports_formal,
        "re_exports_page": current_re_exports_page,
        "import_formal_tab_type": import_formal_tab_type,
        "export_formal_tab_type": export_formal_tab_type,
        "re_export_formal_tab_type": re_export_formal_tab_type
    }

    return render(request, "trade/formal/trade.html", context=context)


@login_required(login_url="system_management:login", redirect_field_name="redirect_to")
@check_role_permission_on_module_decorator("0021", 1)
def formal_trade_upload_view(request):
    if request.method == "POST":
        file, message = clean_csv_file(request)
        category = request.POST.get("category", "NONE")

        if category.upper() not in ("IMPORT", "EXPORT", "RE-EXPORT"):
            messages.error(request, f"invalid category: {category.upper()}. Valid categories: IMPORT, EXPORT, RE-EXPORT")
            redirect_url = reverse('trade:formal-trade-list')
            return redirect(f"{redirect_url}#formal-upload-job")
        else:
            category = category.upper()

        if file:
            upload_job = BulkUploadJob.objects.create(user=request.user, category="FORMAL_TRADE", uploaded_file=file)
            process_csv_formal_trade(upload_job.id, category=category)
            messages.info(request, "Bulk upload has started. You can monitor the status here.")

            redirect_url = reverse('trade:formal-trade-list')
            return redirect(f"{redirect_url}#formal-upload-job")
        else:
            messages.error(request, f"Invalid form submission. Please check the file. {message}")
            return redirect("trade:formal-trade-list")
    
    columns = ["TIN", "NAME OF TAXPAYER", "NAME OF SUPPLIER", "OFFICE",	"DATE", "REGIME", "NBR SAD", 
                "HS CODE", "DESCRIPTION OF GOODS", "MARK", "CUSTOMS BORDER POST",
                "ITEM NBR", "STAT UNIT", "QUANTITY", "NET WEIGHT", "FOB"]
        
    import_columns = sorted(columns + ["PROV", "ORIG", "FREIGHT", "INSURANCE", "OTHER COSTS", "CIF"])
    export_columns = sorted(columns + ["DEST"])
    re_export_columns = sorted(columns + ["ORIG", "DEST"])
    
    context = {
        "import_columns": import_columns,
        "export_columns": export_columns,
        "re_export_columns": re_export_columns
    }
    return render(request, 'trade/formal/upload_formal_trade.html', context)


