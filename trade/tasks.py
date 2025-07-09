import os
import hashlib
from background_task import background
import pandas as pd
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import time
from django.db import IntegrityError
from automation.models import (BulkUploadJob, BNRUSDAveragePrice, 
                               WorldCountry, ProductMeasurements, RRACustomCode)
from .models import ICBTRecord, FormalTrade
import warnings
import numpy as np

warnings.simplefilter("ignore")


def create_row_hash(row):
    values = [str(v) for v in list(row.values())]
    combined_string = '|'.join(values)
    combined_string = combined_string.lower().replace(" ", "")
    return combined_string


def add_month(row, column):
    if pd.notna(row[column]):
        value = row[column].strftime('%B')
    else:
        value = "month not found in date. defaulted 1998"
    if value:
        value = value.title()
    row["month"] = value
    return row

def add_usd(row, date_col, amount_col, target_col, rates):
    if row[date_col]:
        if pd.notna(row[date_col]):
            month = row[date_col].strftime('%B')
            year = row[date_col].year
        else:
            year = 1998
            month = "month not found in date. defaulted 1998"
    else:
        year = 1998
        month = "month not found in date. defaulted 1998"

    rate = rates.get(f"{month.upper()}_{year}", 0)
    if rate == 0:
        raise ValueError(f"Could not find USD exchange rate for {month.upper()} {year}, record it into the system under administration module under configuration module. Ask admin if you don't have permission.")
    row[target_col] = row[amount_col] / float(rate)
    return row

def add_more_columns(row, date_col, amount_rw_fob_col, amount_rw_cif_col, target_fob_usd_col, target_cif_usd_col, hs_code_col, rates, countries, measurements, customs):
    if row[date_col]:
        if pd.notna(row[date_col]):
            month = row[date_col].strftime('%B').title()
            year = row[date_col].year
        else:
            year = 1998
            month = "month not found in date. defaulted 1998"
    else:
        year = 1998
        month = "month not found in date. defaulted 1998"

    rate = rates.get(f"{month.upper()}_{year}", 0)

    row["MONTH"] = month
    row["HS2"] = row[hs_code_col][:2]
    row["HS4"] = row[hs_code_col][:4]
    row["HS6"] = row[hs_code_col][:6]

    origine = countries.get(row["ORIG"].upper(), row["ORIG"].upper())
    dest = countries.get(row["DEST"].upper(), row["DEST"].upper())
    prov = countries.get(row["PROV"].upper(), row["PROV"].upper())
    rra_office = customs.get(row["OFFICE"].upper(), row["OFFICE"].upper())
    rra_custom_post = customs.get(row["CUSTOMS BORDER POST"].upper(), row["CUSTOMS BORDER POST"].upper())
    measurement = measurements.get(row["STAT UNIT"], row["STAT UNIT"])

    row["ORIGINE"] = origine
    row["DESTINATION"] = dest
    row["PROVENANCE"] = prov
    row["OFFICE NAME"] = rra_office
    row["CUSTOM POST NAME"] = rra_custom_post
    row["STAT UNIT NEW"] = measurement

    if rate == 0:
        raise ValueError(f"Could not find USD exchange rate for {month.upper()} {year}, record it into the system under administration module under configuration module. Ask admin if you don't have permission.")
   
    row[target_fob_usd_col] = row[amount_rw_fob_col] / float(rate)
    row[target_cif_usd_col] = row[amount_rw_cif_col] / float(rate)

    return row


def clean_icbt_data(df, rates):
    columns = list(df.columns)
    for col in columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].fillna('')
        else:
            df[col] = df[col].fillna(0)
        df[col] = df[col].astype(str)

    df["date"] = pd.to_datetime(df["date"], format='mixed', dayfirst=True, errors='coerce')
    df['time'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce').dt.time
    df["month"] = [""] * len(df)
    df['price_usd'] = [0.0] * len(df)

    df['quantity'] = pd.to_numeric(df['quantity'].str.replace(',', ''), errors='coerce')
    df['unit_price'] = pd.to_numeric(df['unit_price'].str.replace(',', ''), errors='coerce')
    df['price'] = pd.to_numeric(df['price'].str.replace(',', ''), errors='coerce')

    df['quantity'] = df['quantity'].astype(np.float64)
    df['unit_price'] = df['unit_price'].astype(np.float64)
    df['price'] = df['price'].astype(np.float64)
    df['price_usd'] = df['price_usd'].astype(np.float64)

    df['quantity'] = np.abs(df['quantity'])
    df['unit_price'] = np.abs(df['unit_price'])
    df['price'] = np.abs(df['price'])

    infinity = [np.inf, -np.inf]

    df['quantity'] = df['quantity'].replace(infinity, 0)
    df['unit_price'] = df['unit_price'].replace(infinity, 0)
    df['price'] = df['price'].replace(infinity, 0)

    # adding months
    df = df.apply(add_month, column="date", axis=1)

    # adding usd
    df = df.apply(add_usd, date_col="date", amount_col="price", target_col="price_usd", rates=rates, axis=1)
    
    return df

def build_icbt_object(row):
    trade = ICBTRecord(
        row_key=create_row_hash(row),
        date_period=row["date"],
        date_period_time=row["time"],
        month=row['month'],
        enumerator_code=row["enumerator_code"],
        enumerator_name=row["enumerator_name"],
        cross_point_code=row["crossing_point_code"],
        cross_point=row['crosspoint_name'],
        district=row['district_name'],
        sex=row['gender'],
        age_range=row["age"],
        profession=row['profession'],
        trader_residence_country=row['residence_country'],
        product_origin=row['origin_country'],
        product_destination=row['destination_country'],
        transport_mode=row['mode_transport'],
        product=row['product_name'],
        product_hscode=row["hscode"],
        main_category=row["main_category"],
        sub_category=row["sub_category"],
        unit=row['unit'],
        quantity=Decimal(str(row['quantity'])),
        unit_price=Decimal(str(row['unit_price'])),
        total_price=Decimal(str(row['price'])),
        total_price_usd=Decimal(str(row['price_usd'])),
        altitude=Decimal(str(row['latitude'])),
        longitude=Decimal(str(row['longitude'])),
        latitude=Decimal(str(row['latitude'])),
        accuracy=Decimal(str(row['gps_accuracy'])))
    
    return trade

@background(schedule=0)
def process_csv_icbt(upload_job_id):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0
    row_to_consider = None
    required_columns = [
            "date",	"Time",	"enumerator_code", "enumerator_name", "crossing_point_code", 
            "crosspoint_name",	"district_name","gender","age",	"profession",
            "residence_country","origin_country", "flow", "destination_country",
            "mode_transport","product_name","unit",	"quantity",	"price","unit_price", 
            "main_category","sub_category",	"HSCode","latitude","longitude","altitude",	"gps_accuracy"
        ]
    check_cols = required_columns.copy()

    start_time = time.time()
    try:
        batch_size = settings.BATCH_SIZE
        rates_dict = {}
        rates = BNRUSDAveragePrice.objects.all()
        for rate in rates:
            rates_dict[f"{rate.month.upper()}_{rate.year}"] = rate.rate

        required_columns = sorted([col.lower() for col in required_columns])

        for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):            
            chunk_columns= [col.strip().lower() for col in chunk.columns]
            chunk.columns = chunk_columns

            diff = list(set(required_columns).symmetric_difference(set(chunk_columns)))
            diff = list(set(diff) - set(required_columns))
            chunk = chunk.drop(columns=diff)  # remove unwanted columns

            chunk_columns=  list(chunk.columns)
            diff = list(set(required_columns).symmetric_difference(set(chunk_columns)))
            if len(diff) > 0:
                raise Exception(f"Only allowed columns are: {', '.join(required_columns).lower()}.")

            row_to_consider = chunk
            chunk = clean_icbt_data(df=chunk, rates=rates_dict)
            check_cols = list(chunk.columns)

            for _, row in chunk.iterrows():
                row_count += 1
                job.processed_count += 1
                cleaned_row = {k: None if pd.isna(v) else v for k, v in row.to_dict().items()}
                try:
                    if cleaned_row["flow"].lower() not in ["import", "export"]:
                        errors.append({
                            'row': row_count,
                            'error': f"invalid value for flow:{cleaned_row["flow"].lower()}. Accepted values are import and export",
                            'data': cleaned_row
                        })
                        job.failure_count += 1
                        continue
                    else:
                        if cleaned_row["flow"].lower() == "import":
                            cleaned_row["destination_country"] = "Rwanda"
                        else:
                            cleaned_row["origin_country"] = "Rwanda"

                    trade = build_icbt_object(cleaned_row)
                    trade.save()
                    job.success_count += 1
                except IntegrityError as e:
                    errors.append({
                        'row': row_count,
                        'error': f"This record cannot be inserted, there is already same record in the system:{str(e)}",
                        'data': cleaned_row
                    })
                    job.failure_count += 1
                except ValueError as e:
                    errors.append({
                        'row': row_count,
                        'error': f"Same values in this record have errors:{str(e)}",
                        'data': cleaned_row
                    })
                    job.failure_count += 1
                except Exception as e:
                    errors.append({
                        'row': row_count,
                        'error': f"Error while processing this record: {str(e)}",
                        'data': cleaned_row
                    })
                    job.failure_count += 1
            job.error_log = errors
            job.save()
        
        if len(errors) > 0:
            job.status = "completed_with_errors"
        else:
            job.status = "completed"
        
        job.global_message = "All records processed successfully!"
    except Exception as exc:
            job.status = "failed"
            if row_to_consider is not None and len(row_to_consider) > 0:
                for _, row in row_to_consider.iterrows():
                    row_count +=1
                    cleaned_row = {k: None if pd.isna(v) else v for k, v in row.to_dict().items()}
                    errors.append({
                        'row': row_count,
                        'error': str(exc),
                        'data': cleaned_row
                    })
                    job.failure_count += 1
                    job.processed_count += 1
            else:
                errors = [{
                    'row': row_count,
                    'error': f"Global processing error: {str(exc)}",
                    'data': {col: "" for col in check_cols}
                }]
            
            job.global_message = f"Processing encountered error: {str(exc)}"
    finally:
        job.error_log = errors
        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.processing_minutes = minutes
        job.save()
        try:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        except Exception as e:
            # Log file removal error if needed
            print(f"Error removing file: {str(e)}")    


def clean_tin(tin):
    tin = str(tin).strip()
    if len(tin) > 0:
        if tin.isnumeric():
            tin = (int(tin))
        else:
            tin = None
    else:
        tin = None
    return tin    
        
def clean_formal_trade_data(df, rates, countries, measurements, customs, category):
    columns = df.columns
    for col in columns:
        if col == "NAME OF SUPPLIER":
            df[col] = df[col].fillna('')
            continue

        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].fillna('')
        else:
            df[col] = df[col].fillna(0)
        df[col] = df[col].astype(str)

    df["DATE"] = pd.to_datetime(df["DATE"], format='mixed', dayfirst=True)
    df["MONTH"] = [""] * len(df)
    df["TIN"] = df["TIN"].astype(str)
    df["TIN"] = df["TIN"].apply(clean_tin)

    df['ITEM NBR'] = df['ITEM NBR'].fillna(0)
    df['ITEM NBR'] = df['ITEM NBR'].astype(np.int64)
    df['NBR SAD'] = df['NBR SAD'].astype(int)

    df['HS2'] = [""] * len(df)
    df['HS4'] = [""] * len(df)
    df['HS6'] = [""] * len(df)

    df['QUANTITY'] = df['QUANTITY'].astype(np.float64)
    df['NET WEIGHT'] = df['NET WEIGHT'].astype(np.float64)
    df['FOB'] = df['FOB'].astype(np.float64)
    df["FOB_USD"] = [0.0] * len(df)
    df["CIF_USD"] = [0.0] * len(df)

    if category.upper() == "IMPORT":
        df['FREIGHT'] = df['FREIGHT'].astype(np.float64)
        df['INSURANCE'] = df['INSURANCE'].astype(np.float64)
        df['OTHER COSTS'] = df['OTHER COSTS'].astype(np.float64)
        df['CIF'] = df['CIF'].astype(np.float64)
        df['DEST'] = ["RW"] * len(df)
    elif category.upper() == "EXPORT":
        df['ORIG'] = ["RW"] * len(df)
        df['PROV'] = [""] * len(df)
        df['CIF'] = [0.0] * len(df)
        df['CIF'] = df['CIF'].astype(np.float64)
        df['FREIGHT'] = [0.0] * len(df)
        df['FREIGHT'] = df['FREIGHT'].astype(np.float64)
        df['INSURANCE'] = [0.0] * len(df)
        df['INSURANCE'] = df['INSURANCE'].astype(np.float64)
        df['OTHER COSTS'] = [0.0] * len(df)
        df['OTHER COSTS'] = df['OTHER COSTS'].astype(np.float64)
    elif category.upper() == "RE-EXPORT":
        df['PROV'] = [""] * len(df)
        df['CIF'] = [0.0] * len(df)
        df['CIF'] = df['CIF'].astype(np.float64)
        df['FREIGHT'] = [0.0] * len(df)
        df['FREIGHT'] = df['FREIGHT'].astype(np.float64)
        df['INSURANCE'] = [0.0] * len(df)
        df['INSURANCE'] = df['INSURANCE'].astype(np.float64)
        df['OTHER COSTS'] = [0.0] * len(df)
        df['OTHER COSTS'] = df['OTHER COSTS'].astype(np.float64)
    
    df["ORIGINE"] = [""] * len(df)
    df["DESTINATION"] = [""] * len(df)
    df["PROVENANCE"] = [""] * len(df)
    df["OFFICE NAME"] = [""] * len(df)
    df["CUSTOM POST NAME"] = [""] * len(df)
    df["STAT UNIT NEW"] = [""] * len(df)
    
    df = df.apply(add_more_columns, date_col="DATE", amount_rw_fob_col="FOB", 
                  target_fob_usd_col="FOB_USD", hs_code_col="HS CODE", 
                  amount_rw_cif_col="CIF", target_cif_usd_col="CIF_USD",
                  rates=rates, countries=countries, measurements=measurements,
                  customs=customs, axis=1)
    df["CATEGORY"] = [category] * len(df)

    return df

def build_formal_trade(row):
    trade = FormalTrade(
        row_key=create_row_hash(row),
        tin_number=row["TIN"],
        tax_payer_name=row["NAME OF TAXPAYER"],
        supplier_name=row["NAME OF SUPPLIER"],
        rra_custom_office_code=row["OFFICE"],
        rra_custom_office_name=row["OFFICE NAME"],
        rra_recorded_date=row["DATE"],
        month=row["MONTH"],
        regime=row["REGIME"],
        nbr_sad=row["NBR SAD"],
        item_nbr=row["ITEM NBR"],
        hs_code=row["HS CODE"],
        hs2_code=row["HS2"],
        hs4_code=row["HS4"],
        hs6_code=row["HS6"],
        product_description=row["DESCRIPTION OF GOODS"],
        local_product_description=row["MARK"],
        custom_border_post_code=row["CUSTOMS BORDER POST"],
        custom_border_post_name=row["CUSTOM POST NAME"],
        origin_country_code=row["ORIG"],
        origin_country_name=row["ORIGINE"],
        destination_country_code=row["DEST"],
        destination_country_name=row["DESTINATION"],
        provenance_country_code=row["PROV"],
        provenance_country_name=row["PROVENANCE"],
        stat_unit_rra=row["STAT UNIT"],
        stat_unit_common=row["STAT UNIT NEW"],
        quantity=row["QUANTITY"],
        net_weight=row["NET WEIGHT"],
        fob=row["FOB"],
        fob_usd=row["FOB_USD"],
        freight=row["FREIGHT"],
        insurance=row["INSURANCE"],
        other_costs=row["OTHER COSTS"],
        cif=row["CIF"],
        cif_usd=row["CIF_USD"],
        category=row["CATEGORY"]
    )
    return trade

@background(schedule=0)
def process_csv_formal_trade(upload_job_id, category):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0
    row_to_consider = None
    start_time = time.time()

    columns = ["TIN", "NAME OF TAXPAYER", "NAME OF SUPPLIER", "OFFICE",	"DATE", "REGIME", "NBR SAD", 
                "HS CODE", "DESCRIPTION OF GOODS", "MARK", "CUSTOMS BORDER POST",
                "ITEM NBR", "STAT UNIT", "QUANTITY", "NET WEIGHT", "FOB"]
        
    import_columns = sorted(columns + ["PROV", "ORIG", "FREIGHT", "INSURANCE", "OTHER COSTS", "CIF"])
    export_columns = sorted(columns + ["DEST"])
    re_export_columns = sorted(columns + ["ORIG", "DEST"])

    if category.upper() == "IMPORT":
        check_cols = import_columns.copy()
    elif category.upper() == "EXPORT":
        check_cols = export_columns.copy()
    elif category.upper() == "RE-EXPORT":
         check_cols = re_export_columns.copy()
    
    check_cols += ["ORIGINE", "DESTINATION", "PROVENANCE", "OFFICE NAME", 
                   "CUSTOM POST NAME", "STAT UNIT NEW", "CATEGORY", "HS2", "HS4", "HS6"]
    try:
        batch_size = settings.BATCH_SIZE
        rates = BNRUSDAveragePrice.objects.all()
        countries = WorldCountry.objects.all()
        measurements = ProductMeasurements.objects.all()
        customs = RRACustomCode.objects.all()

        customs_dict = {}
        countries_dict = {}
        rates_dict = {}
        measurements_dict = {}

        for rate in rates:
            rates_dict[f"{rate.month.upper()}_{rate.year}"] = rate.rate
        
        for country in countries:
            countries_dict[country.country_code.upper()] = country.country_name.title()
        
        for measurement in measurements:
            measurements_dict[measurement.long_abbr] = measurement.short_abbr
        
        for custom in customs:
            customs_dict[custom.code.upper()] = custom.custom_name.title()

        try:
            for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):
                chunk_columns = chunk.columns
                chunk_columns = [ col.upper() for col in chunk_columns]
                chunk.columns = chunk_columns
                row_to_consider = chunk
                check_cols = chunk_columns
                if category.upper() == "IMPORT":
                    diff = list(set(import_columns).symmetric_difference(set(chunk_columns)))
                    diff = list(set(diff) - set(import_columns))
                    chunk = chunk.drop(columns=diff)  # remove unwanted columns

                    chunk_columns=  list(chunk.columns)
                    diff = list(set(import_columns).symmetric_difference(set(chunk_columns)))
                    if len(diff) > 0:
                        raise Exception(f"For import, allowed columns are: {', '.join(import_columns).lower()}. Difference in columns to check: {', '.join(diff).lower()}")
                    
                elif category.upper() == "EXPORT":
                    diff = list(set(export_columns).symmetric_difference(set(chunk_columns)))
                    diff = list(set(diff) - set(export_columns))
                    chunk = chunk.drop(columns=diff)  # remove unwanted columns

                    chunk_columns=  list(chunk.columns)
                    diff = list(set(export_columns).symmetric_difference(set(chunk_columns)))
                    if len(diff) > 0:
                         raise Exception(f"For export, allowed columns are: {', '.join(export_columns).lower()}. Difference in columns to check: {', '.join(diff).lower()}")
                    
                elif category.upper() == "RE-EXPORT":
                    diff = list(set(re_export_columns).symmetric_difference(set(chunk_columns)))
                    diff = list(set(diff) - set(re_export_columns))
                    chunk = chunk.drop(columns=diff)  # remove unwanted columns

                    chunk_columns=  list(chunk.columns)
                    diff = list(set(re_export_columns).symmetric_difference(set(chunk_columns)))
                    if len(diff) > 0:
                        raise Exception(f"For re-export, allowed columns are: {', '.join(re_export_columns).lower()}. Difference in columns to check: {', '.join(diff).lower()}")
                else:
                    raise Exception("Invalid category selected. Accepted categories are: IMPORT, EXPORT and RE-EXPORT")
                
                chunk = clean_formal_trade_data(df=chunk, countries=countries_dict,
                                                measurements=measurements_dict,
                                                customs=customs_dict,
                                                rates=rates_dict,
                                                category=category)
                
                for _, row in chunk.iterrows():
                    row_count += 1
                    job.processed_count += 1
                    cleaned_row = {k: None if pd.isna(v) else v for k, v in row.to_dict().items()}
                    try:
                        trade = build_formal_trade(cleaned_row)
                        trade.save()
                        job.success_count += 1
                    except IntegrityError as e:

                        errors.append({
                            'row': row_count,
                            'error': f"This record cannot be inserted, there is already same record in the system:{str(e)}",
                            'data': cleaned_row
                        })
                        job.failure_count += 1
                    except ValueError as e:

                        errors.append({
                            'row': row_count,
                            'error': f"Same values in this record have errors:{str(e)}",
                            'data': cleaned_row
                        })
                        job.failure_count += 1
                    except Exception as e:
                        errors.append({
                            'row': row_count,
                            'error': f"Error while processing this record: {str(e)}",
                            'data': cleaned_row
                        })
                        job.failure_count += 1

                job.error_log = errors
                job.save() # save the job after each chunck

            if len(errors) > 0:
                job.status = "completed_with_errors"
            else:
                job.status = "completed"
            
            job.global_message = "All records processed successfully!"
        except Exception as exc:
            job.status = "failed"
            if row_to_consider is not None and len(row_to_consider) > 0:
                for _, row in row_to_consider.iterrows():
                    row_count +=1
                    cleaned_row = {k: None if pd.isna(v) else v for k, v in row.to_dict().items()}
                    errors.append({
                        'row': row_count,
                        'error': str(exc),
                        'data': cleaned_row
                    })
                    job.failure_count += 1
                    job.processed_count += 1
            else:
                errors = [{
                    'row': row_count,
                    'error': f"Global processing error: {str(exc)}",
                    'data': {col: "" for col in check_cols}
                }]
            
            job.global_message = f"Processing encountered error: {str(exc)}"
    except Exception as gexc:
        job.failure_count = 0
        job.processed_count = 0
        job.success_count = 0
        errors = [{
                    'row': 0,
                    'error': f"Processing error: {str(gexc)}",
                    'data': {col: "" for col in check_cols}
                }]
        job.global_message = str(gexc)
    finally:
        job.error_log = errors
        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.processing_minutes = minutes
        job.save()
        try:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        except Exception as e:
            # Log file removal error if needed
            print(f"Error removing file: {str(e)}")    