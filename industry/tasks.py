import os
import re
from background_task import background
import pandas as pd
import geopandas as gpd
import time
from automation.models import BulkUploadJob
from .models import (IndustryEconomicZone, PartitionedPlot, CompanyProfile, 
                     LandRequestInformation, AllocatedPlot, CompanySite)
from system_management.models import IndustrialZone, User
from system_management.utils import generate_random_code
import warnings

warnings.simplefilter("ignore")

def extract_coords(geom):
    if geom.geom_type == 'Polygon':
        return list(geom.exterior.coords)
    elif geom.geom_type == 'MultiPolygon':
        return [list(poly.exterior.coords) for poly in geom.geoms]
    else:
        return None

def clean_tin_number(value):
    value = str(value).strip().rstrip(".00").rstrip(".0")
    if not value:
        value = "0"
    return value

def create_land_information_request(profile, tin_plots):
    if profile:
        request_size = 0.0
        plot_ = None
        for plot_key in tin_plots:
            plot = plot_key['plot']
            if not plot.is_allocated:
                request_size += plot.plot_size
                plot_ = plot
        
        if request_size > 0:
            land_request = LandRequestInformation.objects.create(
                land_owner=profile,
                requested_land_size=request_size,
                park=plot_.park,
                zone=plot_.zone
            )

            return land_request
    
    return None

def allocate_plot(land_request, request_plots):
    plot_size = 0.0
    plot_ = None
    for plot_key in request_plots:
        plot = plot_key['plot']
        plot_ = plot
        if not plot.is_allocated:
            plot_size += plot.plot_size

    if plot_size > 0:
        allocated_plot = AllocatedPlot.objects.create(
            land_owner=land_request.land_owner,
            land_request=land_request,
            zone=plot_.zone,
            plot_size=plot_size,
            park=plot_.park
        )

        for plot_key in request_plots:
            plot = plot_key['plot']
            if not plot.is_allocated:
                plot.is_allocated = True
                plot.allocated_plot = allocated_plot
                plot.save()
        
        return allocated_plot
    return None

def add_industry_in_park(allocated_plot, plots):
    status = "Not Started"
    for plot_key in plots:
        status = plot_key["status"]

    CompanySite.objects.create(company=allocated_plot.land_owner,
                               province=allocated_plot.park.province,
                               district=allocated_plot.park.district,
                               sector=allocated_plot.park.sector,
                               cell=allocated_plot.park.cell,
                               construction_status=status,
                               allocated_plot=allocated_plot
                               )



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
    allocated_plots = {}

    try:
        gdf = gpd.read_file(job.uploaded_file.path)
        gdf['coords'] = gdf.geometry.apply(extract_coords)
        gdf['TIN'] = gdf['TIN'].astype(str)
        gdf['TIN'] = gdf['TIN'].apply(clean_tin_number)
        columns = [ col.strip() for col in gdf.columns]
        gdf.columns = columns
        consider_columns = ["TIN", "Area", "upi", "ZONING", "Plot_refer", "Company_na", "Plot_Devel", "transact_1", "Company__O"]

        for idx, row in gdf.iterrows():
            row_count += 1
            coords = row["coords"]
            if coords:
                coords = [[float(x), float(y)] for x, y in coords] 
                coords = [coords]
            else:
                coords = None
                errors.append({
                        'row': idx,
                        'error': f"There are no coordinates provided: {row['Plot_refer']}",
                        'data': row[consider_columns].to_dict()
                    })

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

            # area_str = re.split(r'\s*(?:ha|hectares?)\s*', row["Area"], flags=re.IGNORECASE)[0].strip()
            area_str = re.split(r'\s*(?:sq m?)\s*', row["Area"], flags=re.IGNORECASE)[0].strip()
            try:
                area_val = float(area_str)  # Convert to float (handles decimals)
                if area_val == 0.0:
                    errors.append({
                        'row': idx,
                        'error': f"The plot size given is zero: {row['Plot_refer']}",
                        'data':  row[consider_columns].to_dict()
                    })
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
                        'data':  row[consider_columns].to_dict()
                    })

            # area = area_val * 10000  # Convert hectares → sq. meters
            area = area_val
            
            if area == 0.0 or not coords:
                continue

            zone = IndustrialZone.objects.filter(name__iexact=zoning).first()
            if not zone:
                zone = IndustrialZone.objects.create(name=zoning.lower())

            if len(upi.strip()) > 0: 
                plot = PartitionedPlot.objects.filter(partitioned_plot_upi=upi).first() 
                if plot:
                    errors.append({
                        'row': idx,
                        'error': f"Plot UPI: {upi} already exists",
                        'data':  row[consider_columns].to_dict()
                    })
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

            tin = int(row["TIN"])
            if tin:
                status = row["Plot_Devel"]
                if "not started" in status.lower():
                    status = "Not Started"
                else:
                    status = status.title()

                allocated_plots[tin] = allocated_plots.get(tin, [] ) + [{"plot": plot, "status": status}]
        
        for tin, tin_plots in allocated_plots.items():
            profile = CompanyProfile.objects.filter(tin_number=tin).first()
            land_request = create_land_information_request(profile, tin_plots)
            if land_request:
                allocated_plot = allocate_plot(land_request=land_request, request_plots=tin_plots)
                add_industry_in_park(allocated_plot=allocated_plot, plots=tin_plots)

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


def validate_phone_number(phone):
    phone = str(phone)
    if any(sub in phone for sub in ['78', '79', '72', '73']):
        if not phone.startswith('07'):
            phone = '0' + phone.lstrip('0')
    elif 'nan' in phone.lower():
        phone = ''
    return phone

@background(schedule=0)
def process_industry_profile(upload_job_id):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0
    start_time = time.time()
    current_row = None
    row_count = 0
    succeeded = 0
    failed = 0
    try:
        rows_df = pd.read_csv(job.uploaded_file.path)
        rows_df.columns = [col.strip().lower() for col in rows_df.columns]
        rows_df.drop_duplicates(subset=['tin'], inplace=True)
        rows_df['tin'] = round(rows_df['tin'], 0)
        rows_df['phone'] = rows_df['phone'].apply(validate_phone_number)
        rows_df.dropna(subset=['tin'], inplace=True)
        rows_df.dropna(subset=['email'], inplace=True)
        rows_df.fillna({
            'director_first_name': '',
            'director_last_name': '',
            'phone': '',
            'industry_size': '',
            'origin_country': ''
        }, inplace=True)

        for _, row in rows_df.iterrows():
            current_row = row
            row_count += 1

            try:
                password = generate_random_code()
                user = User.objects.create(
                    first_name=row["director_first_name"],
                    last_name=row["director_last_name"],
                    change_password_required=True,
                    user_category="COMPANY",
                    email=row["email"]
                )
                user.set_password(password)
                user.save()
                CompanyProfile.objects.create(
                    user=user,
                    name=row["name"],
                    tin_number=row["tin"],
                    category="INDUSTRY",
                    phone_contact=row["phone"],
                    email_contact=user.email,
                    investor_origin_country=row["origin_country"],
                    company_size=row["industry_size"],
                    managing_director_name=user.get_full_name(),
                    managing_director_id=row["director_id"]
                    # headquaters_province=row["headquaters_province"],
                    # headquaters_district=row["headquarters_district"],
                    # headquaters_sector=row["headquarters_sector"],
                    # headquaters_cell=row["headquarters_cell"],
                    # headquaters_village=row["headquarters_village"]
                )
                succeeded += 1

            except Exception as e:
                failed += 1
                errors.append({
                    'row': row_count,
                    'error': str(e),
                    'data': row.to_dict()
                })

    except Exception as e:
        errors.append({
            'row': row_count,
            'error': str(e),
            'data': current_row.to_dict() if current_row is not None else {}
        })
    finally:
        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.success_count = succeeded
        job.failure_count = failed
        job.error_log = errors
        job.processing_minutes = minutes

        if (succeeded > 0 and failed > 0) or (succeeded == 0 and failed > 0):
            job.status = "completed_with_errors"
        elif succeeded > 0 and failed == 0:
            job.status = "completed"
        else:
            job.status = "failed"
        
        job.save()
        try:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        except Exception as e:
            print(f"Error removing file: {str(e)}")


