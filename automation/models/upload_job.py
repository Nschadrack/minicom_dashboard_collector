from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from system_management.models import User

class BulkUploadJob(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    uploaded_file = models.FileField(upload_to='bulk_uploads/')
    category = models.CharField(max_length=40)
    error_log = models.JSONField(blank=True, null=True, encoder=DjangoJSONEncoder)
    processed_count = models.IntegerField(default=0)
    global_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    processing_minutes = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "BulkUploadJobs"
    
    def __str__(self):
        return f"{self.status.title()}: {self.category}"

class WorldCountry(models.Model):
    country_code = models.CharField(max_length=6, unique=True)
    country_name = models.CharField(max_length=100, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "WorldCountries"

class BNRUSDAveragePrice(models.Model):
    month = models.CharField(max_length=30, null=False, blank=False)
    year = models.IntegerField(null=False, blank=False)
    rate = models.DecimalField(max_digits=12, decimal_places=6, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "BNRUSDAveragePrices"
        constraints = [
            models.UniqueConstraint(
                fields=["month", "year"],
                name='USDRateUniqueConstraint'
            )
        ]

class ProductMeasurements(models.Model):
    short_abbr = models.CharField(max_length=5, null=False, blank=False, unique=True)
    long_abbr = models.CharField(max_length=10, null=False, blank=False)
    full_form = models.CharField(max_length=50, null=False, blank=False)
    description = models.CharField(max_length=200, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ProductMeasurements"

class RRACustomCode(models.Model):
    code = models.CharField(max_length=10, null=False, blank=False, unique=True)
    custom_name = models.CharField(max_length=100, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "RRACustomCodes"