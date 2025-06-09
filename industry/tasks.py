import os
import re
from background_task import background
import pandas as pd
import geopandas as gpd
import time
from automation.models import BulkUploadJob
from .models import IndustryEconomicZone, PartitionedPlot
from system_management.models import IndustrialZone
import warnings

warnings.simplefilter("ignore")

def extract_coords(geom):
    if geom.geom_type == 'Polygon':
        return list(geom.exterior.coords)
    elif geom.geom_type == 'MultiPolygon':
        return [list(poly.exterior.coords) for poly in geom.geoms]
    else:
        return None

@background(schedule=0)
def process_geojson_plots(upload_job_id, park_id):
    park = IndustryEconomicZone.objects.filter(id=park_id).first()
    job = BulkUploadJob.objects.get(id=upload_job_id)
    if park is None:
        job.status = "failed"
        job.save()
        return
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0

    start_time = time.time()
    partitioned_plots = []

    try:
        gdf = gpd.read_file(job.uploaded_file.path)
        gdf['coords'] = gdf.geometry.apply(extract_coords)
        columns = [ col.strip() for col in gdf.columns]
        gdf.columns = columns

        for idx, row in gdf.iterrows():
            row_count += 1
            coords = row["coords"]
            if coords:
                coords = [[float(x), float(y)] for x, y in coords] 
                coords = [coords]
            else:
                coords = None

            area = row["Area"].strip()
            upi = row["upi"]
            zoning = row["ZONING"]
            plot_number = row["Plot_refer"].strip()

            if len(plot_number) > 0:
                plot_number = re.split(r'\s*(?:,|and|&)\s*', plot_number)
                if len(plot_number) > 0:
                    plot_number = plot_number[0]
                else:
                    plot_number = None

            area_str = re.split(r'\s*(?:ha|hectares?)\s*', row["Area"], flags=re.IGNORECASE)[0].strip()
            try:
                area_val = float(area_str)  # Convert to float (handles decimals)
            except ValueError as e:
                area_val = 0.0
                err_message = f"The plot size given is zero or not a number which is not acceptable. "
                if plot_number:
                    err_message += f"Plot number: {plot_number}. "
                if upi:
                    err_message += f"UPI: {upi}"
                errors.append({
                        'row': idx,
                        'error': err_message,
                        'data': {}
                    })

            area = area_val * 10000  # Convert hectares → sq. meters
            
            if area == 0.0 or not coords:
                continue

            zone = IndustrialZone.objects.filter(name__iexact=zoning).first()
            if not zone:
                zone = IndustrialZone.objects.create(name=zoning.lower())

            if len(upi.strip()) > 0: 
                plot = PartitionedPlot.objects.filter(partitioned_plot_upi=upi).first() 
                if plot:
                    continue
                
            if not plot_number:
                plot_number = f"{park.name[0]}{idx}"
            
            plot = PartitionedPlot.objects.filter(plot_number=plot_number).first()
            if plot:
                plot_number = f"{plot_number}_{plot.id}_{idx}"
               
            if len(upi) > 5:
                upi_status = "Issued"
            else:
                upi_status = "Not Yet Requested"

            plot = PartitionedPlot.objects.create(
                plot_number=plot_number,
                partitioned_plot_upi=upi,
                upi_status=upi_status,
                zone=zone,
                plot_size=area,
                park=park,
                coordinates=coords
            )
            partitioned_plots.append(plot)

            # print(f"Plot {idx+1}: {plot.plot_number} \tUPI: {plot.partitioned_plot_upi}")
        
        job.status = "completed"
    except Exception as e:
        errors.append({
                    'row': 0,
                    'error': str(e),
                    'data': {}
                })
        job.status = "failed"
    finally:
        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.success_count = len(partitioned_plots)
        job.failure_count = row_count - len(partitioned_plots)
        job.error_log = errors
        job.processing_minutes = minutes
        job.save()
        try:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        except Exception as e:
            print(f"Error removing file: {str(e)}")

