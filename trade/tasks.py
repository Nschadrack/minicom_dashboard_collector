import os
from background_task import background
import pandas as pd
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from automation.models import BulkUploadJob
from .models import ICBTRecord


@background(schedule=0)
def process_csv_icbt(upload_job_id):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0

    try:
        batch_size = settings.BATCH_SIZE

        for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):
            chunk.columns = [col.strip() for col in chunk.columns]
            chunk.drop_duplicates(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
                        'cross_point', 'district', 'sex', 'profession', 'trader_residence', 
                        'product_origin', 'product_destination', 'transport_mode', 
                        'product', 'unit', 'quantity', 'unit_price', 'total_price', 
                        'total_price_usd'], inplace=True)
            try:
                with transaction.atomic():
                    # Convert dataframe rows to model instances
                    objects = [
                        ICBTRecord(
                            form_code=row['form_code'],
                            start_time=pd.to_datetime(row['start_time'], dayfirst=False),
                            end_time=pd.to_datetime(row['end_time'], dayfirst=False),
                            date_period=pd.to_datetime(row['date_period'], dayfirst=False).date(),
                            month=row['month'],
                            cross_point=row['cross_point'],
                            district=row['district'],
                            sex=row['sex'],
                            profession=row['profession'],
                            trader_residence=row['trader_residence'],
                            product_origin=row['product_origin'],
                            product_destination=row['product_destination'],
                            transport_mode=row['transport_mode'],
                            product=row['product'],
                            unit=row['unit'],
                            quantity=Decimal(str(row['quantity'])),
                            unit_price=Decimal(str(row['unit_price'])),
                            total_price=Decimal(str(row['total_price'])),
                            total_price_usd=Decimal(str(row['total_price_usd'])),
                            latitude=Decimal(str(row['latitude'])),
                            longitude=Decimal(str(row['longitude'])),
                            accuracy=Decimal(str(row['accuracy']))
                        )
                        for _, row in chunk.iterrows()
                    ]
                    
                    # Bulk create with conflict handling
                    ICBTRecord.objects.bulk_create(
                        objects,
                        batch_size=batch_size,
                        ignore_conflicts=False  # Set to True if you want to skip duplicates
                    )
                    
                    job.success_count += len(objects)

            except IntegrityError as e:
                errors.extend({
                    'row': 1 + row_count,
                    'error': str(e),
                    'data': row.to_dict()
                } for index, row in chunk.iterrows())
                job.failure_count += len(chunk)
                row_count += len(chunk)
                continue

            except Exception as e:
                errors.extend({
                    'row': 1 + row_count,
                    'error': str(e),
                    'data': row.to_dict()
                } for index, row in chunk.iterrows())
                job.failure_count += len(chunk)
                row_count += len(chunk)


        if len(errors) > 0:
            job.status = 'completed_with_errors'
        else:
            job.status = 'completed'
            errors = None
        job.error_log = errors
        job.save()
        
        if os.path.exists(job.uploaded_file.path):
            os.remove(job.uploaded_file.path)

    except Exception as e:
        if len(errors) > 0:
            job.status = 'failed'
        else:
            job.status = 'completed_with_errors'
            errors = None
        job.error_log = errors
        job.save()
        if os.path.exists(job.uploaded_file.path):
            os.remove(job.uploaded_file.path)


# Assuming your models are defined something like this:
# from your_app.models import BulkUploadJob, ICBTRecord

# @background(schedule=0)
# def process_csv_icbt(upload_job_id):
#     job = BulkUploadJob.objects.get(id=upload_job_id)
#     job.status = 'processing'
#     job.save()

#     errors_log = []
#     total_rows_processed = 0
#     successful_inserts = 0
#     failed_rows = 0
#     # To keep track of the original row number in the CSV
#     current_row_number = 0

#     try:
#         batch_size = batch_size = settings.BATCH_SIZE # This is for pd.read_csv, actual DB batch can be different or same

#         for chunk_number, chunk in enumerate(pd.read_csv(job.uploaded_file.path, chunksize=batch_size, keep_default_na=False, na_values=[''])):
#             chunk.columns = [col.strip() for col in chunk.columns]
            
#             chunk.drop_duplicates(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month',
#                                           'cross_point', 'district', 'sex', 'profession', 'trader_residence',
#                                           'product_origin', 'product_destination', 'transport_mode',
#                                           'product', 'unit', 'quantity', 'unit_price', 'total_price',
#                                           'total_price_usd'], inplace=True)

#             valid_objects_for_bulk_create = []
            
#             for index, row in chunk.iterrows():
#                 # Calculate original row number (approximate, depends on header and previous chunks)
#                 # Add 1 for header row, and 1 because iterrows is 0-indexed
#                 original_row_index = (chunk_number * batch_size) + index + 2 
                
#                 try:
#                     # Attempt to clean and convert data for a single row
#                     # Handle potential empty strings or invalid formats for each field
                    
#                     # --- Start Time ---
#                     start_time_val = row.get('start_time')
#                     if pd.isna(start_time_val) or str(start_time_val).strip() == '':
#                         raise ValueError("start_time cannot be empty.")
#                     start_time = pd.to_datetime(start_time_val, dayfirst=True)
#                     start_time = timezone.make_aware(start_time)

#                     # --- End Time ---
#                     end_time_val = row.get('end_time')
#                     if pd.isna(end_time_val) or str(end_time_val).strip() == '':
#                         raise ValueError("end_time cannot be empty.")
#                     end_time = pd.to_datetime(end_time_val, dayfirst=True)
#                     end_time = timezone.make_aware(end_time)

#                     # --- Date Period ---
#                     date_period_val = row.get('date_period')
#                     if pd.isna(date_period_val) or str(date_period_val).strip() == '':
#                         raise ValueError("date_period cannot be empty.")
#                     date_period = pd.to_datetime(date_period_val, dayfirst=False).date()
                    
#                     # --- Quantity ---
#                     quantity_val = str(row.get('quantity', '0')).strip()
#                     if not quantity_val: quantity_val = '0' # Default to 0 if empty after strip
#                     quantity = round(float(quantity_val), 2)

#                     # --- Unit Price ---
#                     unit_price_val = str(row.get('unit_price', '0')).strip()
#                     if not unit_price_val: unit_price_val = '0'
#                     unit_price = round(float(unit_price_val), 2)

#                     # --- Total Price ---
#                     total_price_val = str(row.get('total_price', '0')).strip()
#                     if not total_price_val: total_price_val = '0'
#                     total_price = round(float(total_price_val), 2)
                    
#                     # --- Total Price USD ---
#                     total_price_usd_val = str(row.get('total_price_usd', '0')).strip()
#                     if not total_price_usd_val: total_price_usd_val = '0'
#                     total_price_usd = round(float(total_price_usd_val), 2)

#                     # --- Latitude ---
#                     latitude_val = str(row.get('latitude', '0')).strip() # Assuming 0 is a valid default if missing
#                     if not latitude_val: latitude_val = '0'
#                     latitude = round(float(latitude_val), 10)
                    
#                     # --- Longitude ---
#                     longitude_val = str(row.get('longitude', '0')).strip() # Assuming 0 is a valid default if missing
#                     if not longitude_val: longitude_val = '0'
#                     longitude = round(float(longitude_val), 10)

#                     # --- Accuracy ---
#                     accuracy_val = str(row.get('accuracy', '0')).strip() # Assuming 0 is a valid default if missing
#                     if not accuracy_val: accuracy_val = '0'
#                     accuracy = round(float(accuracy_val), 7)

#                     # Create model instance (without saving yet)
#                     record = ICBTRecord(
#                         form_code=row.get('form_code'),
#                         start_time=start_time,
#                         end_time=end_time,
#                         date_period=date_period,
#                         month=row.get('month'),
#                         cross_point=row.get('cross_point'),
#                         district=row.get('district'),
#                         sex=row.get('sex'),
#                         profession=row.get('profession'),
#                         trader_residence=row.get('trader_residence'),
#                         product_origin=row.get('product_origin'),
#                         product_destination=row.get('product_destination'),
#                         transport_mode=row.get('transport_mode'),
#                         product=row.get('product'),
#                         unit=row.get('unit'),
#                         quantity=quantity,
#                         unit_price=unit_price,
#                         total_price=total_price,
#                         total_price_usd=total_price_usd,
#                         latitude=latitude,
#                         longitude=longitude,
#                         accuracy=accuracy
#                     )
#                     # You might want to call record.full_clean() here to catch Django model validation errors
#                     # before adding to the bulk_create list.
#                     # try:
#                     #     record.full_clean()
#                     # except ValidationError as ve:
#                     #     errors_log.append({
#                     #     'row': original_row_index,
#                     #     'error': f"Validation Error: {ve.message_dict}",
#                     #     'data': row.to_dict()
#                     #     })
#                     #     failed_rows += 1
#                     #     continue # Skip this record

#                     valid_objects_for_bulk_create.append(record)

#                 except (ValueError, TypeError, AttributeError) as e: # Catch data conversion/type errors
#                     errors_log.append({
#                         'row': original_row_index, # More accurate row number
#                         'error': f"Data Clean/Conversion Error: {str(e)}",
#                         'data': row.to_dict()
#                     })
#                     failed_rows += 1
#                 except Exception as e: # Catch any other unexpected error for this row
#                     errors_log.append({
#                         'row': original_row_index,
#                         'error': f"Unexpected error processing row: {str(e)}",
#                         'data': row.to_dict()
#                     })
#                     failed_rows += 1
            
#             # Now, attempt to bulk_create the valid objects for this chunk
#             if valid_objects_for_bulk_create:
#                 try:
#                     with transaction.atomic():
#                         # Using ignore_conflicts=True will skip rows that violate unique constraints.
#                         # If False, an IntegrityError for the whole batch can occur.
#                         # To handle IntegrityError per row with ignore_conflicts=False,
#                         # you'd have to insert one by one, which is slow.
#                         # A common strategy is ignore_conflicts=True for initial bulk load,
#                         # or handle conflicts based on specific fields if your DB supports `ON CONFLICT DO UPDATE`.
                        
#                         ICBTRecord.objects.bulk_create(
#                             valid_objects_for_bulk_create,
#                             batch_size=len(valid_objects_for_bulk_create), # process all valid ones from this chunk
#                             ignore_conflicts=False 
#                         )
#                         successful_inserts += len(valid_objects_for_bulk_create)

#                 except IntegrityError as ie:
#                     # This block will only be hit if ignore_conflicts=False and an integrity error occurs
#                     # for the *whole batch*. The row-level error handling above is preferred.
#                     # If you reach here, it means the entire batch failed.
#                     job.failure_count += len(valid_objects_for_bulk_create)
                    
#                     for i, record in enumerate(valid_objects_for_bulk_create): 
#                         data = {}  
#                         for field in record._meta.get_fields():
#                             field_name = field.name
#                             field_value = getattr(record, field_name)
#                             data[field_name] = field_value
#                         errors_log.append({
#                             'row': f"Chunk starting at approx row { (chunk_number * batch_size) + 2 + i}",
#                             'error': f"Batch IntegrityError: {str(ie)}.",
#                             'data': data
#                         })
#                     failed_rows += len(valid_objects_for_bulk_create)
#                 except Exception as e_batch:
#                     # Other batch-level errors
#                     job.failure_count += len(valid_objects_for_bulk_create)

#                     for i, record in enumerate(valid_objects_for_bulk_create): 
#                         data = {}  
#                         for field in record._meta.get_fields():
#                             field_name = field.name
#                             field_value = getattr(record, field_name)
#                             data[field_name] = field_value
#                         errors_log.append({
#                             'row': f"Chunk starting at approx row { (chunk_number * batch_size) + 2 }",
#                             'error': f"Batch processing error: {str(e_batch)}",
#                             'data': data
#                         })

#                     failed_rows += len(valid_objects_for_bulk_create)
        
#         job.success_count = successful_inserts # Update with actual successful inserts
#         job.failure_count = failed_rows
#         job.error_log = errors_log
#         job.status = 'completed' if not errors_log else 'completed_with_errors'
#         job.save()

#     except pd.errors.EmptyDataError:
#         job.status = 'failed'
#         job.error_log = [{'row': 0, 'error': 'The uploaded CSV file is empty or unreadable.', 'data': {}}]
#         job.save()
#     except Exception as e: # Catch errors like file not found, major pandas parsing errors, etc.
#         job.status = 'failed'
#         # Ensure error_log is a list of dicts
#         if isinstance(job.error_log, list):
#             job.error_log.append({'row': 'N/A', 'error': f"Critical error during processing: {str(e)}", 'data': {}})
#         else: # If error_log was not initialized as a list (e.g., previous string error)
#             job.error_log = [{'row': 'N/A', 'error': f"Critical error during processing: {str(e)}", 'data': {}}]
#         job.save()
#     finally:
#         if job.uploaded_file and hasattr(job.uploaded_file, 'path') and os.path.exists(job.uploaded_file.path):
#             os.remove(job.uploaded_file.path)