from django.db import models

class ICBTRecord(models.Model):
    form_code = models.CharField(max_length=200, null=False, blank=False)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    date_period = models.DateField(null=False, blank=False)
    month = models.CharField(null=False, blank=False, max_length=20)
    cross_point = models.CharField(max_length=50, null=False, blank=False)
    district = models.CharField(max_length=30, null=False, blank=False)
    sex = models.CharField(max_length=30, null=False, blank=False)
    profession = models.CharField(max_length=60, null=False, blank=False)
    trader_residence = models.CharField(max_length=60, null=False, blank=False)
    product_origin = models.CharField(max_length=50, null=False, blank=False)
    product_destination = models.CharField(max_length=50, null=False, blank=False)
    transport_mode = models.CharField(max_length=50, null=False, blank=False)
    product = models.CharField(max_length=100, null=False, blank=False)
    unit = models.CharField(max_length=30, null=False, blank=False)
    quantity = models.DecimalField(decimal_places=2, max_digits=7, null=False, blank=False)
    unit_price = models.DecimalField(decimal_places=2, max_digits=8, null=False, blank=False)
    total_price = models.DecimalField(decimal_places=2, max_digits=12, null=False, blank=False)
    total_price_usd = models.DecimalField(decimal_places=2, max_digits=12, null=False, blank=False)
    latitude = models.DecimalField(decimal_places=10, max_digits=13, null=False, blank=False)
    longitude = models.DecimalField(decimal_places=10, max_digits=13, null=False, blank=False)
    accuracy = models.DecimalField(decimal_places=7, max_digits=12, null=False, blank=False)


    class Meta:
        db_table = "ICBTRecords"
        indexes = [
            models.Index(fields=['start_time', 'end_time', 'date_period']),
            models.Index(fields=['cross_point']),
            models.Index(fields=['product_origin', 'product']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['form_code', 'start_time', 'end_time', 'date_period', 'month', 
                        'cross_point', 'district', 'sex', 'profession', 'trader_residence', 
                        'product_origin', 'product_destination', 'transport_mode', 
                        'product', 'unit', 'quantity', 'unit_price', 'total_price', 
                        'total_price_usd'],
                name='icbt_unique_all_fields_combined'
            )
        ]