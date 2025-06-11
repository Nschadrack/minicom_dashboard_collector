from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from automation.models import BulkUploadJob
from .tasks import process_csv_icbt
from .models import ICBTRecord

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

    all_icbts = ICBTRecord.objects.filter(id__in=current_all_icbt_ids).order_by("date_period")
    export_icbts = ICBTRecord.objects.filter(id__in=current_export_icbt_ids).order_by("date_period")
    import_icbts = ICBTRecord.objects.filter(id__in=current_import_icbt_ids).order_by("date_period")

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
    
    context = {
        'range_10': range(5)
    }
    return render(request, 'trade/icbt/upload_icbt.html', context)

