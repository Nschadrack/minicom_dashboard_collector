# views.py (optimized)
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

CACHE_TIMEOUT = 60 * 5  # 5 minutes
PAGE_SIZE = 20

def industry_list(request):
    active_tab = request.GET.get('tab', TAB_PROFILES)
    page_number = request.GET.get('page', 1)
    
    # Layer 1: Cache entire paginator
    cache_key = f"paginator_{active_tab}"
    paginator = cache.get(cache_key)
    
    if not paginator:
        # Layer 2: Cache object data
        if active_tab == TAB_PROFILES:
            ids = cache.get(f"ids_{TAB_PROFILES}")
            if not ids:
                ids = list(CompanyIndustryProfile.objects.values_list('id', flat=True)
                cache.set(f"ids_{TAB_PROFILES}", ids, CACHE_TIMEOUT)
            
            objects = cache.get_many([f"profile_{id}" for id in ids])
            missing_ids = [id for id in ids if f"profile_{id}" not in objects]
            
            if missing_ids:
                fresh_objects = CompanyIndustryProfile.objects.in_bulk(missing_ids)
                cache.set_many({f"profile_{id}": obj for id, obj in fresh_objects.items()}, CACHE_TIMEOUT)
                objects.update(fresh_objects)
            
            object_list = [objects[f"profile_{id}"] for id in ids]
            
        elif active_tab == TAB_PARKS:
            # Similar logic for ParkIndustry
            pass
        
        # Create and cache paginator
        paginator = Paginator(object_list, PAGE_SIZE)
        cache.set(cache_key, paginator, CACHE_TIMEOUT)
    
    try:
        page = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page = paginator.page(1)
    
    context = {
        'active_tab': active_tab,
        'page': page,
        'tab_type': active_tab
    }
    
    return render(request, 'industry/full_template.html', context)