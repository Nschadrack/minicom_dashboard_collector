import os
from background_task import background
import pandas as pd
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import time
from django.db import transaction, IntegrityError
from automation.models import (BulkUploadJob, BNRUSDAveragePrice, 
                               WorldCountry, ProductMeasurements, RRACustomCode)
from .models import ICBTRecord, FormalTrade
import warnings
import numpy as np

warnings.simplefilter("ignore")


def add_month(row, column):
    value = row[column].dt.strftime('%B')
    if value:
        value = value.title()
    row["MONTH"] = value
    return row

def add_usd(row, date_col, amount_col, target_col, rates):
    if row[date_col]:
        year = row[date_col].dat.year
        month = row[date_col].dt.strftime('%B')
    else:
        year = 1998
        month = ""

    rate = rates.get(f"{month.upper()}_{year}", 0)
    row[target_col] = row[amount_col] / rate
    return row

def add_more_columns(row, date_col, amount_rw_col, amount_rw_cif_col, target_usd_col, target_cif_usd_col, hs_code_col, rates, countries, measurements, customs):
    if row[date_col]:
        year = row[date_col].dat.year
        month = row[date_col].dt.strftime('%B')
        month = month.title()
    else:
        year = 1998
        month = ""

    year = row[date_col].dat.year
    rate = rates.get(f"{month.upper()}_{year}", 0)
    row[target_usd_col] = row[amount_rw_col] / rate
    row[target_cif_usd_col] = row[amount_rw_cif_col] / rate

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

    return row


# def clean_data(df):
#     df["month"] = df["month"].str.strip()
#     df['quantity'] = df['quantity'].astype(str)
#     df['unit_price'] = df['unit_price'].astype(str)
#     df['total_price'] = df['total_price'].astype(str)
#     df['total_price_usd'] = df['total_price_usd'].astype(str)

#     df['quantity'] = pd.to_numeric(df['quantity'].str.replace(',', ''))
#     df['unit_price'] = pd.to_numeric(df['unit_price'].str.replace(',', ''))
#     df['total_price'] = pd.to_numeric(df['total_price'].str.replace(',', ''))
#     df['total_price_usd'] = pd.to_numeric(df['total_price_usd'].str.replace(',', ''))

#     df['quantity'] = df['quantity'].astype(np.float64)
#     df['unit_price'] = df['unit_price'].astype(np.float64)
#     df['total_price'] = df['total_price'].astype(np.float64)
#     df['total_price_usd'] = df['total_price_usd'].astype(np.float64)

#     df['quantity'] = np.abs(df['quantity'])
#     df['unit_price'] = np.abs(df['unit_price'])
#     df['total_price'] = np.abs(df['total_price'])
#     df['total_price_usd'] = np.abs(df['total_price_usd'])

#     infinity = [np.inf, -np.inf]

#     df['quantity'] = df['quantity'].replace(infinity, 0)
#     df['unit_price'] = df['unit_price'].replace(infinity, 0)
#     df['total_price'] = df['total_price'].replace(infinity, 0)
#     df['total_price_usd'] = df['total_price_usd'].replace(infinity, 0)
    
#     return df

# @background(schedule=0)
# def process_csv_icbt(upload_job_id):
#     job = BulkUploadJob.objects.get(id=upload_job_id)
#     job.status = 'processing'
#     job.save()
#     errors = []
#     row_count = 0
#     row_to_consider = None

#     start_time = time.time()
#     try:
#         batch_size = settings.BATCH_SIZE

#         for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):
#             chunk_start_row = row_count  # Track starting row for this chunk
#             chunk_length = len(chunk)
            
#             chunk.columns = [col.strip() for col in chunk.columns]
#             chunk.drop_duplicates(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
#                         'cross_point', 'district', 'sex', 'profession', 'trader_residence', 
#                         'product_origin', 'product_destination', 'transport_mode', 
#                         'product', 'unit', 'quantity', 'unit_price', 'total_price', 
#                         'total_price_usd'], inplace=True)
#             chunk.dropna(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
#                         'cross_point', 'district', 'sex', 'profession'], inplace=True)
            
#             row_to_consider = chunk
#             chunk = clean_data(chunk)
#             try:
#                 with transaction.atomic():
#                     # Convert dataframe rows to model instances
#                     objects = [
#                         ICBTRecord(
#                             form_code=row['form_code'],
#                             start_time=timezone.make_aware(pd.to_datetime(row['start_time'], format='mixed', dayfirst=True)),
#                             end_time=timezone.make_aware(pd.to_datetime(row['end_time'], format='mixed', dayfirst=True)),
#                             date_period=pd.to_datetime(row['date_period'], format='mixed', dayfirst=True).date(),
#                             month=row['month'],
#                             cross_point=row['cross_point'],
#                             district=row['district'],
#                             sex=row['sex'],
#                             profession=row['profession'],
#                             trader_residence=row['trader_residence'],
#                             product_origin=row['product_origin'],
#                             product_destination=row['product_destination'],
#                             transport_mode=row['transport_mode'],
#                             product=row['product'],
#                             unit=row['unit'],
#                             quantity=Decimal(str(row['quantity'])),
#                             unit_price=Decimal(str(row['unit_price'])),
#                             total_price=Decimal(str(row['total_price'])),
#                             total_price_usd=Decimal(str(row['total_price_usd'])),
#                             latitude=Decimal(str(row['latitude'])),
#                             longitude=Decimal(str(row['longitude'])),
#                             accuracy=Decimal(str(row['accuracy']))
#                         )
#                         for _, row in chunk.iterrows()
#                     ]
                    
#                     # Bulk create with conflict handling
#                     ICBTRecord.objects.bulk_create(
#                         objects,
#                         batch_size=batch_size,
#                         ignore_conflicts=False
#                     )
                    
#                     job.success_count += len(objects)

#             except IntegrityError as e:
#                 # Convert rows to dictionaries BEFORE appending
#                 for i, (_, row) in enumerate(chunk.iterrows()):
#                     errors.append({
#                         'row': chunk_start_row + i + 1,
#                         'error': "data should be unique, there are already similar records in the system",
#                         'data': row.to_dict()
#                     })
#                 job.failure_count += chunk_length

#             except Exception as e:
#                 # Convert rows to dictionaries BEFORE appending
#                 for i, (_, row) in enumerate(chunk.iterrows()):
#                     errors.append({
#                         'row': chunk_start_row + i + 1,
#                         'error': str(e),
#                         'data': row.to_dict()
#                     })
#                 job.failure_count += chunk_length

#             # Update row count after processing chunk
#             row_count += chunk_length

#         # Final status after processing all chunks
#         if errors:
#             job.status = 'completed_with_errors'
#             job.error_log = errors
#         else:
#             job.status = 'completed'
#             job.error_log = None

#         total_time = time.time() - start_time
#         minutes = round(total_time / 60, 2)
#         job.processing_minutes = minutes
#         job.save()
        
#     except Exception as e:
#         print(f"ERROR: {str(e)}")
#         job.status = 'failed'
#         if row_to_consider is not None and len(row_to_consider) > 0:
#             for i, (_, row) in enumerate(row_to_consider.iterrows()):
#                     errors.append({
#                         'row': row_count + i + 1,
#                         'error': str(e),
#                         'data': row.to_dict()
#                     })
#             job.failure_count += len(row_to_consider)
#         else:
#             job.error_log = [{
#                 'row': 0,
#                 'error': f"Global processing error: {str(e)}",
#                 'data': {}
#             }]
#         total_time = time.time() - start_time
#         minutes = round(total_time / 60, 2)
#         job.processing_minutes = minutes
#         job.save()
    
#     # File cleanup in finally block
#     finally:
#         try:
#             pass
#             if os.path.exists(job.uploaded_file.path):
#                 os.remove(job.uploaded_file.path)
#         except Exception as e:
#             # Log file removal error if needed
#             print(f"Error removing file: {str(e)}")

def clean_tin(tin):
    tin = str(tin).strip()
    if len(tin) > 0:
        if tin.isnumeric():
            tin = (int(tin))
        else:
            tin = ""
    else:
        tin = ""
    return tin
        
def clean_formal_trade_data(df, rates, countries, measurements, customs, category):
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["MONTH"] = [""] * len(df)
    df["TIN"] = df["TIN"].astype(str)
    df["TIN"] = df["TIN"].apply(clean_tin)

    df['NAME OF TAXPAYER'] = df['NAME OF TAXPAYER'].astype(str)
    df['NAME OF SUPPLIER'] = df['NAME OF SUPPLIER'].astype(str)
    df['ITEM NBR'] = df['ITEM NBR'].astype(np.float64)
    df['OFFICE'] = df['OFFICE'].astype(str)
    df['REGIME'] = df['REGIME'].astype(str)
    df['NBR SAD'] = df['NBR SAD'].astype(int)

    df['HS CODE'] = df['HS CODE'].astype(str)
    df['HS2'] = [""] * len(df)
    df['HS4'] = [""] * len(df)
    df['HS6'] = [""] * len(df)

    df['DESCRIPTION OF GOODS'] = df['DESCRIPTION OF GOODS'].astype(str)
    df['MARK'] = df['MARK'].astype(str)
    df['CUSTOMS BORDER POST'] = df['CUSTOMS BORDER POST'].astype(str)

    df['STAT UNIT'] = df['STAT UNIT'].astype(str)
    df['QUANTITY'] = df['QUANTITY'].astype(np.float64)
    df['NET WEIGHT'] = df['NET WEIGHT'].astype(np.float64)
    df['FOB'] = df['FOB'].astype(np.float64)
    df['CIF'] = df['CIF'].astype(np.float64)
    df["FOB_USD"] = [0.0] * len(df)
    df["CIF_USD"] = [0.0] * len(df)

    if category.upper() == "IMPORT":
        df['PROV'] = df['PROV'].astype(str)
        df['ORIG'] = df['ORIG'].astype(str)
        df['FREIGHT'] = df['FREIGHT'].astype(np.float64)
        df['INSURANCE'] = df['INSURANCE'].astype(np.float64)
        df['OTHER COSTS'] = df['OTHER COSTS'].astype(np.float64)
        df['CIF'] = df['CIF'].astype(np.float64)
        df['DEST'] = ["RW"] * len(df)
    elif category.upper() == "EXPORT":
        df['DEST'] = df['DEST'].astype(str)
        df['ORIG'] = ["RW"] * len(df)
        df['PROV'] = [""] * len(df)
    elif category.upper() == "RE-EXPORT":
        df['ORIG'] = df['ORIG'].astype(str)
        df['DEST'] = df['DEST'].astype(str)
        df['PROV'] = [""] * len(df)
    
    df["ORIGINE"] = [""] * len(df)
    df["DESTINATION"] = [""] * len(df)
    df["PROVENANCE"] = [""] * len(df)
    df["OFFICE NAME"] = [""] * len(df)
    df["CUSTOM POST NAME"] = [""] * len(df)
    df["STAT UNIT NEW"] = [""] * len(df)
    
    df = df.apply(add_more_columns, date_col="DATE", amount_col="FOB", 
                  target_col="FOB_USD", hs_code_col="HS CODE", 
                  amount_rw_cif_col="CIF", target_cif_usd_col="CIF_USD",
                  rates=rates, countries=countries, measurements=measurements,
                  customs=customs, axis=1)
    df["CATEGORY"] = [category] * len(df)

    return df

def build_formal_trade(row):
    trade = FormalTrade(
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

    try:
        rates = BNRUSDAveragePrice.objects.all()
        countries = WorldCountry.objects.all()
        measurements = ProductMeasurements.objects.all()
        customs = RRACustomCode.objects.all()

        customs_dict = {}
        countries_dict = {}
        rates_dict = {}
        measurements_dict = {}

        columns = ["TIN", "NAME OF TAXPAYER", "NAME OF SUPPLIER", "OFFICE",	"DATE", "REGIME", "NBR SAD", 
                "HS CODE", "DESCRIPTION OF GOODS", "MARK", "CUSTOMS BORDER POST",
                "ITEM NBR", "STAT UNIT", "QUANTITY", "NET WEIGHT", "FOB"]
        
        import_columns = sorted(columns + ["PROV", "ORIG", "FREIGHT", "INSURANCE", "OTHER COSTS", "CIF"])
        export_columns = sorted(columns + ["DEST"])
        re_export_columns = sorted(columns + ["ORIG", "DEST"])

        for rate in rates:
            rates_dict[f"{rate.month.upper()}_{rate.year}"] = rate.rate
        
        for country in countries:
            countries_dict[country.country_code.upper()] = country.country_name.title()
        
        for measurement in measurements:
            measurements_dict[measurement.long_abbr] = measurement.short_abbr
        
        for custom in customs:
            customs_dict[custom.code.upper()] = custom.custom_name.title()

        try:
            batch_size = settings.BATCH_SIZE
            for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):
                chunk_start_row = row_count  # Track starting row for this chunk
                chunk_length = len(chunk)
                
                row_to_consider = chunk
                chunk = clean_formal_trade_data(df=chunk, countries=countries_dict,
                                                measurements=measurements_dict,
                                                customs=customs_dict,
                                                category=category)
                chunck_columns = chunk.columns
                chunck_columns = sorted([ col.upper() for col in chunck_columns])

                if category.upper() == "IMPORT":
                    if import_columns != chunck_columns:
                        raise Exception(f"For import, allowed columns are: {','.join(import_columns).lower()}")
                elif category.upper() == "EXPORT":
                    if export_columns != chunck_columns:
                        raise Exception(f"For export, allowed columns are: {','.join(export_columns).lower()}")
                elif category.upper() == "RE-EXPORT":
                    if re_export_columns != chunck_columns:
                        raise Exception(f"For re-export, allowed columns are: {','.join(re_export_columns).lower()}")
                else:
                    raise Exception("Invalid category selected. Accepted categories are: IMPORT, EXPORT and RE-EXPORT")
                
                for _, row in chunk.iterrows():
                    row_count += 1
                    job.processed_count += 1
                    try:
                        trade = build_formal_trade(row)
                        trade.save()
                        job.success_count += 1
                    except IntegrityError as e:
                        errors.append({
                            'row': row_count,
                            'error': f"This record cannot be inserted, there is already same record in the system:{str(e)}",
                            'data': row.to_dict()
                        })
                        job.failure_count += 1
                    except ValueError as e:
                        errors.append({
                            'row': row_count,
                            'error': f"Same values in this record have errors:{str(e)}",
                            'data': row.to_dict()
                        })
                        job.failure_count += 1
                    except Exception as e:
                        errors.append({
                            'row': row_count,
                            'error': f"Error while processing this record: {str(e)}",
                            'data': row.to_dict()
                        })
                        job.failure_count += 1

                job.save() # save the job after each chunck

            if len(errors) > 0:
                job.status = "completed_with_errors"
            else:
                job.status = "completed"
            
            job.global_message = "All records processed successfully!"
        except Exception as exc:
            job.status = "failed"
            if row_to_consider:
                for _, row in row_to_consider.iterrows():
                    row_count +=1
                    errors.append({
                        'row': row_count,
                        'error': str(exc),
                        'data': row.to_dict()
                    })
                    job.failure_count += 1
                    job.processed_count += 1
            else:
                errors = [{
                    'row': row_count,
                    'error': f"Global processing error: {str(exc)}",
                    'data': {}
                }]
            
            job.global_message = f"Processing encountered error: {str(exc)}"
    except Exception as gexc:
        job.failure_count = 0
        job.processed_count = 0
        job.success_count = 0
        errors = [{
                    'row': 0,
                    'error': f"Processing error: {str(gexc)}",
                    'data': {}
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