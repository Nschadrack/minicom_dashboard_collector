import os
from background_task import background
from django.db import transaction
import pandas as pd
from decimal import Decimal
from django.db import IntegrityError
from automation.models import BulkUploadJob
from .models import ICBTRecord


@background(schedule=0)
def process_csv_icbt(upload_job_id):
    job = BulkUploadJob.objects.get(id=upload_job_id)
    job.status = 'processing'
    job.save()

    try:
        batch_size = 500
        errors = []

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
                            start_time=pd.to_datetime(row['start_time']),
                            end_time=pd.to_datetime(row['end_time']),
                            date_period=pd.to_datetime(row['date_period']).date(),
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
                    'row': index + 1,
                    'error': str(e),
                    'data': row.to_dict()
                } for index, row in chunk.iterrows())
                job.failure_count += len(chunk)
                continue

            except Exception as e:
                errors.extend({
                    'row': index + 1,
                    'error': str(e),
                    'data': row.to_dict()
                } for index, row in chunk.iterrows())
                job.failure_count += len(chunk)

        job.status = 'completed'
        job.error_log = errors
        job.save()
        
        if os.path.exists(job.uploaded_file.path):
            os.remove(job.uploaded_file.path)

    except Exception as e:
        job.status = 'failed'
        job.error_log = [{'error': str(e)}]
        job.save()
        if os.path.exists(job.uploaded_file.path):
            os.remove(job.uploaded_file.path)