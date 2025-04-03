from django.db import models
from system_management.models import User

class Dashboard(models.Model):
    CATEGORIES = (
        ("INDUSTRY", "INDUSTRY"),
        ("TRADE", "TRADE"),
    )
    name = models.CharField(max_length=255, null=False, blank=False)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    created_at = models.DateTimeField(auto_now_add=True)
    dashboard_link = models.TextField(null=False, blank=False)
    created_by = models.ForeignKey(User, related_name="user_dashboards_created", on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name="user_dashboards_updated", on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "Dashboards"
    
    def __str__(self):
        return self.name
