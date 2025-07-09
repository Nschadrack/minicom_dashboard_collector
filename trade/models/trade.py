from django.db import models


class ICBTRecord(models.Model):
    row_key = models.TextField(unique=True, null=False, blank=False)
    date_period = models.DateField(null=False, blank=False)
    date_period_time = models.TimeField(null=True, blank=True)
    month = models.CharField(null=False, blank=False, max_length=20)
    cross_point = models.CharField(max_length=50, null=False, blank=False)
    enumerator_code = models.CharField(max_length=20, null=True, blank=True)
    enumerator_name = models.CharField(max_length=160, null=True, blank=True)
    cross_point_code = models.CharField(max_length=20, null=True, blank=True)
    cross_point_code = models.CharField(max_length=20, null=True, blank=True)
    district = models.CharField(max_length=30, null=False, blank=False)
    sex = models.CharField(max_length=30, null=False, blank=False)
    age_range = models.CharField(max_length=60, null=True, blank=True)
    profession = models.CharField(max_length=60, null=False, blank=False)
    trader_residence_country = models.CharField(max_length=80, null=False, blank=False)
    product_origin = models.CharField(max_length=50, null=False, blank=False)
    product_destination = models.CharField(max_length=50, null=False, blank=False)
    transport_mode = models.CharField(max_length=50, null=False, blank=False)
    product = models.CharField(max_length=100, null=False, blank=False)
    product_hscode = models.CharField(max_length=25, null=True, blank=True)
    main_category = models.IntegerField(null=True, blank=True)
    sub_category = models.IntegerField(null=True, blank=True)
    unit = models.CharField(max_length=30, null=False, blank=False)
    quantity = models.DecimalField(decimal_places=2, max_digits=10, null=False, blank=False)
    unit_price = models.DecimalField(decimal_places=2, max_digits=15, null=False, blank=False)
    total_price = models.DecimalField(decimal_places=2, max_digits=16, null=False, blank=False)
    total_price_usd = models.DecimalField(decimal_places=2, max_digits=12, null=False, blank=False)
    altitude = models.DecimalField(decimal_places=10, max_digits=15, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=10, max_digits=15, null=False, blank=False)
    longitude = models.DecimalField(decimal_places=10, max_digits=15, null=False, blank=False)
    accuracy = models.DecimalField(decimal_places=7, max_digits=12, null=False, blank=False)


    class Meta:
        db_table = "ICBTRecords"
        indexes = [
            models.Index(fields=['date_period']),
            models.Index(fields=['date_period', 'date_period_time']),
            models.Index(fields=['cross_point']),
            models.Index(fields=['product_origin', 'product']),
        ]
        

class FormalTrade(models.Model):
   CATEGORIES = (
       ("IMPORT", "IMPORT"),
       ("EXPORT", "EXPORT"),
       ("RE-EXPORT", "RE-EXPORT"),
   )
   row_key = models.TextField(unique=True, null=False, blank=False)
   tin_number = models.PositiveIntegerField(null=True, blank=True)
   tax_payer_name = models.CharField(max_length=100, null=True, blank=True)
   supplier_name = models.CharField(max_length=100, null=True, blank=True)
   rra_custom_office_code = models.CharField(max_length=10, null=True, blank=True)
   rra_custom_office_name = models.CharField(max_length=100, blank=True, null=True)
   rra_recorded_date = models.DateField(null=False, blank=False)
   month = models.CharField(max_length=40, null=True, blank=True)
   regime =models.CharField(max_length=30, null=True, blank=True)
   nbr_sad = models.IntegerField(null=True, blank=True)
   item_nbr = models.IntegerField(blank=True, null=True)
   hs_code = models.CharField(max_length=20, null=True, blank=True)
   hs2_code = models.CharField(max_length=10, null=True, blank=True)
   hs4_code = models.CharField(max_length=14, null=True, blank=True)
   hs6_code = models.CharField(max_length=20, null=True, blank=True)
   product_description = models.CharField(max_length=250, null=True, blank=True)
   local_product_description = models.CharField(max_length=250, null=True, blank=True)
   custom_border_post_code = models.CharField(max_length=10, null=True, blank=True)
   custom_border_post_name = models.CharField(max_length=100, null=True, blank=True)
   origin_country_code = models.CharField(max_length=10, null=True, blank=True)
   origin_country_name = models.CharField(max_length=100, null=True, blank=True)
   destination_country_code = models.CharField(max_length=10, null=True, blank=True)
   destination_country_name = models.CharField(max_length=100, null=True, blank=True)
   provenance_country_code = models.CharField(max_length=10, null=True, blank=True)
   provenance_country_name = models.CharField(max_length=100, null=True, blank=True)
   stat_unit_rra = models.CharField(max_length=10, null=True, blank=True)
   stat_unit_common = models.CharField(max_length=10, null=True, blank=True)
   quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
   net_weight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
   fob = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   fob_usd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   freight = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   insurance = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   other_costs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   cif = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   cif_usd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
   category = models.CharField(choices=CATEGORIES, max_length=20)

   class Meta:
       db_table = "FormalTrade"
       indexes = [
            models.Index(fields=['tin_number']),
            models.Index(fields=['origin_country_name', 'destination_country_name']),
            models.Index(fields=['rra_recorded_date']),
            models.Index(fields=['month']),
        ]

       

