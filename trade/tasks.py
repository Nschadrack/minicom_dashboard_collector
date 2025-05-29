import os
from background_task import background
import pandas as pd
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import time
from django.db import transaction, IntegrityError
from automation.models import BulkUploadJob
from .models import ICBTRecord
import warnings

warnings.simplefilter("ignore")

@background(schedule=0)
def process_csv_icbt(upload_job_id):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()
    errors = []
    row_count = 0

    start_time = time.time()
    try:
        batch_size = settings.BATCH_SIZE

        for chunk in pd.read_csv(job.uploaded_file.path, chunksize=batch_size):
            chunk_start_row = row_count  # Track starting row for this chunk
            chunk_length = len(chunk)
            
            chunk.columns = [col.strip() for col in chunk.columns]
            chunk.drop_duplicates(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
                        'cross_point', 'district', 'sex', 'profession', 'trader_residence', 
                        'product_origin', 'product_destination', 'transport_mode', 
                        'product', 'unit', 'quantity', 'unit_price', 'total_price', 
                        'total_price_usd'], inplace=True)
            chunk.dropna(subset=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
                        'cross_point', 'district', 'sex', 'profession'], inplace=True)
            try:
                with transaction.atomic():
                    # Convert dataframe rows to model instances
                    objects = [
                        ICBTRecord(
                            form_code=row['form_code'],
                            start_time=timezone.make_aware(pd.to_datetime(row['start_time'], format='mixed', dayfirst=True)),
                            end_time=timezone.make_aware(pd.to_datetime(row['end_time'], format='mixed', dayfirst=True)),
                            date_period=pd.to_datetime(row['date_period'], format='mixed', dayfirst=True).date(),
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
                        ignore_conflicts=False
                    )
                    
                    job.success_count += len(objects)

            except IntegrityError as e:
                # Convert rows to dictionaries BEFORE appending
                for i, (_, row) in enumerate(chunk.iterrows()):
                    errors.append({
                        'row': chunk_start_row + i + 1,
                        'error': "data should be unique, there are already similar records in the system",
                        'data': row.to_dict()
                    })
                job.failure_count += chunk_length

            except Exception as e:
                # Convert rows to dictionaries BEFORE appending
                for i, (_, row) in enumerate(chunk.iterrows()):
                    errors.append({
                        'row': chunk_start_row + i + 1,
                        'error': str(e),
                        'data': row.to_dict()
                    })
                job.failure_count += chunk_length

            # Update row count after processing chunk
            row_count += chunk_length

        # Final status after processing all chunks
        if errors:
            job.status = 'completed_with_errors'
            job.error_log = errors
        else:
            job.status = 'completed'
            job.error_log = None

        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.processing_minutes = minutes
        print("\nBefore Saving\n")
        job.save()
        print("\nAfter saving\n")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        job.status = 'failed'
        # Create safe error structure
        job.error_log = [{
            'row': 0,
            'error': f"Global processing error: {str(e)}",
            'data': {}
        }]
        print(f"\n{errors[:10]}\n")
        total_time = time.time() - start_time
        minutes = round(total_time / 60, 2)
        job.processing_minutes = minutes
        job.save()
    
    # File cleanup in finally block
    finally:
        try:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        except Exception as e:
            # Log file removal error if needed
            print(f"Error removing file: {str(e)}")
