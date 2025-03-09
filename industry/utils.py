import csv
import os
from .models import (IndustrialZone, PartitionedPlot, 
                     IndustryEconomicZone, AllocatedPlot,
                     CompanyProfile, CompanySite)


def get_base_domain(request):
    scheme = 'https' if request.is_secure() else 'http'
    host = request.META.get('HTTP_HOST', request.get_host())
    base_domain = f"{scheme}://{host}"
    return base_domain

def load_countries():
    DATA_PATH_FILE = os.path.join(os.getcwd(), "all_countries.csv")
    with open(DATA_PATH_FILE, mode='r', newline='', encoding='utf-8') as file_reader:
        csv_reader = csv.reader(file_reader)
        countries = []
        for row in csv_reader:
            countries.append(row[0])
    return countries[1:]


def get_zones_and_partitioned_plots_in_park(park_id=None):
    """
    Get all zones and partitioned plots for particular park when park_id is given else all zones in the park
    """
    zones = []
    partitioned_plots = []
    if park_id is not None:
        park = IndustryEconomicZone.objects.filter(id=park_id).first()
        if park is not None:
            partitioned_plots_ = PartitionedPlot.objects.filter(park=park).order_by("zone__name")
        else:
            partitioned_plots_ = []
    else:
        partitioned_plots_ = PartitionedPlot.objects.all().order_by("zone__name")
    
    found_zones = []
    for plot in partitioned_plots_:
            if f"{plot.zone.name}_{plot.park.id}_{plot.park.name}" not in found_zones:
                found_zones.append(f"{plot.zone.name}_{plot.park.id}_{plot.park.name}")
                zones.append({
                    "id": plot.zone.id,
                    "name": plot.zone.name,
                    "park_id": plot.park.id,
                    "park_name": f"{plot.park.name} {plot.park.category}"
                })

            if plot.is_allocated == False:
                partitioned_plots.append({
                        "id": plot.id,
                        "plot_number": plot.plot_number,
                        "plot_upi": plot.partitioned_plot_upi,
                        "upi_status": plot.upi_status,
                        "zone_id": plot.zone.id,
                        "zone_name": plot.zone.name,
                        "plot_size": round(float(plot.plot_size), 5),
                        "park_id": plot.park.id,
                        "park_name": f"{plot.park.name} {plot.park.category}"
                    })
    
    return zones, partitioned_plots

def record_allocated_plot_from_request(request, land_request):
    try:
        plot_upi = request.POST.get("plot_upi", "")
        upi_status = request.POST.get("upi_status")
        land_title_status = request.POST.get("land_title_status")
        date_of_letter_addressed_to_nla = request.POST.get("date_of_letter_addressed_to_nla", None)
        park_id = request.POST.get("park", -1)
        zoning_id = request.POST.get("zone", -1)
        plots_ids = request.POST.getlist("partitioned_plots[]", [])

        park = IndustryEconomicZone.objects.get(id=park_id)
        zoning = IndustrialZone.objects.get(id=zoning_id)
        partition_plots = PartitionedPlot.objects.filter(id__in=plots_ids)

        if not len(date_of_letter_addressed_to_nla.strip()) > 2:
            date_of_letter_addressed_to_nla = None

        if len(partition_plots) > 0:
            allocated_plot = AllocatedPlot(
                allocated_plot_upi=plot_upi,
                upi_status=upi_status,
                land_title_status=land_title_status,
                date_of_letter_addressed_to_nla=date_of_letter_addressed_to_nla,
                park=park,
                zone=zoning,
                land_request=land_request,
                land_owner=land_request.land_owner
            )

            allocated_plot.save()
            allocated_size = 0
            for plot in partition_plots:
                plot.allocated_plot= allocated_plot
                plot.is_allocated = True
                plot.save()
                allocated_size += plot.plot_size
            allocated_plot.plot_size=allocated_size
            allocated_plot.save()

            CompanySite.objects.create(
                company=land_request.land_owner,
                province=park.province,
                district=park.district,
                sector=park.sector,
                cell=park.cell,
                allocated_plot=allocated_plot
            )
        else:
            return False

        return True
    except Exception as e: 
        print(f"\n[ERROR]: {str(e)}\n")
        return False

def record_industry_in_plot_from_request(request):
    try:
        tin_number = request.POST.get("industry", " || ").split("||")[0]
        occupied_space = request.POST.get("occupied_space")
        longitude = request.POST.get("longitude", "")
        latitude = request.POST.get("latitude", "")
        province = request.POST.get("province")
        district = request.POST.get("district")
        sector = request.POST.get("sector")
        cell = request.POST.get("cell")
        investment_amount = request.POST.get("investment_amount")
        investment_currency = request.POST.get("investment_currency")
        allocated_plot = request.POST.get("allocated_plot")

        industry = CompanyProfile.objects.get(tin_number=tin_number)
        allocated_plot = AllocatedPlot.objects.get(id=allocated_plot)

        if len(longitude.strip()) < 2:
            longitude = None
        if len(latitude.strip()) < 2:
            latitude = None
        
        if len(occupied_space.strip()) < 2:
            occupied_space = None
        
        if len(investment_amount.strip()) < 2:
            investment_amount = None
            investment_currency = None

        CompanySite.objects.create(
            company=industry,
            longitude=longitude,
            latitude=latitude,
            province=province,
            district=district,
            sector=sector,
            cell=cell,
            occupied_space=occupied_space,
            investment_amount=investment_amount,
            investment_currency=investment_currency,
            allocated_plot=allocated_plot
        )

        return True
    except Exception as e: 
        print(f"\n[ERROR]: {str(e)}\n")
        return False



    

