from django.db import models
from django.utils.translation import gettext_lazy as _


class IndustryEconomicZone(models.Model):
    CATEGORIES = (
        ("Special Economic Zone", "Special Economic Zone"),
        ("Industrial Park", "Industrial Park"),
        ("Light Industrial Zone", "Light Industrial Zone"),
        ("Industrial Zone", "Industrial Zone"),
    )
    name = models.CharField(max_length=60, null=False, blank=False)
    category = models.CharField(max_length=60, null=False, blank=False, choices=CATEGORIES)
    total_land_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    leasable_land = models.PositiveIntegerField(null=False, blank=False)
    province = models.CharField(max_length=60, null=False, blank=False)
    district = models.CharField(max_length=60, null=False, blank=False)
    sector = models.CharField(max_length=60, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "IndustryEconomicZones"
    
    def __str__(self):
        return f"{self.name} {self.category.lower()}"

class Zone(models.Model):
    name = models.CharField(max_length=60, null=False, blank=False)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_zones")
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Zones"
    
    def __str__(self):
        return f"{self.name} zone in {self.park.__str__()}"
    
class Plot(models.Model):
    STATUSES = (
        ("Not Yet Requested", "Not Requested"),
        ("Pending To Land Institution", "Pending To Land Institution"),
        ("Issued", "Issued"),
    )

    plot_number = models.CharField(max_length=30, unique=True, null=False, blank=False)
    upi = models.CharField(max_length=50, null=True, blank=True)
    upi_status = models.CharField(max_length=30, null=False, blank=False, choices=STATUSES)
    owner = models.CharField(max_length=100, null=False, blank=False)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="zone_plots")
    plot_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)

    class Meta:
        db_table = "Plots"
    
class PlotObservation(models.Model):
    name = models.TextField(null=False, blank=False)
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PlotObservations"
