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
    created_at = models.DateTimeField(auto_now_add=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    processing_minutes = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "BulkUploadJobs"
    
    def __str__(self):
        return f"{self.status.title()}: {self.category}"