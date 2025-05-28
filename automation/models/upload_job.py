# models.py
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_file = models.FileField(upload_to='bulk_uploads/')
    category = models.CharField(max_length=40)
    error_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)

    class Meta:
        db_table = "BulkUploadJobs"
    
    def __str__(self):
        return f"{self.status.title()}: {self.category}"