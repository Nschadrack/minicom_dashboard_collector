from django.db import models
from django.utils.translation import gettext_lazy as _
from system_management.models import IndustrialZone, User


class IndustryEconomicZone(models.Model):
    CATEGORIES = (
        ("Special Economic Zone", "Special Economic Zone"),
        ("Industrial Park", "Industrial Park"),
        ("Light Industrial Zone", "Light Industrial Zone"),
        ("Industrial Zone", "Industrial Zone"),
    )
    name = models.CharField(max_length=150, null=False, blank=False)
    category = models.CharField(max_length=60, null=False, blank=False, choices=CATEGORIES)
    total_land_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    leasable_land = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    province = models.CharField(max_length=60, null=False, blank=False)
    district = models.CharField(max_length=60, null=False, blank=False)
    sector = models.CharField(max_length=60, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "IndustryEconomicZones"
    
    def __str__(self):
        return f"{self.name} {self.category.lower()}"

class LandOwner(models.Model):
    phone_number = models.CharField(max_length=20, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "LandOwners"

class CompanyProfile(models.Model):
    CATEGORIES = (
        ("INDUSTRY", "INDUSTRY"),
        ("NOT INDUSTRY", "NOT INDUSTRY"),
    )
    COMPANY_SIZES = (
        ("Large", "Large"),
        ("Medium", "Medium"),
        ("Small", "Small"),
        ("Micro", "Micro"),
    )
    name = models.CharField(max_length=200, null=False, blank=False)
    tin_number = models.PositiveIntegerField(null=False, blank=False, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORIES, null=False, blank=False)
    phone_contact = models.CharField(max_length=20, null=False, blank=False)
    email_contact = models.EmailField(max_length=200, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    registeration_date = models.DateField(null=True, blank=True)
    investor_origin_country = models.TextField(null=False, blank=False)
    company_size = models.CharField(max_length=15, choices=COMPANY_SIZES, null=False, blank=False)
    profile_created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "CompanyProfiles"

class LandRequestInformation(models.Model):
    land_owner = models.ForeignKey(LandOwner, on_delete=models.SET_NULL, null=True, blank=True)
    request_date = models.DateField(null=False, blank=False)
    request_closure_date = models.DateField(null=False, blank=False)
    requested_land_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    zone = models.ForeignKey(IndustrialZone, on_delete=models.CASCADE, related_name="zone_land_requets")
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "LandRequestInformations"

class AllocatedPlot(models.Model):
    UPI_STATUSES = (
        ("Not Yet Requested", "Not Requested"),
        ("Pending To Land Institution", "Pending To Land Institution"),
        ("Issued", "Issued"),
    )
    LAND_TITLE_STATUSES = (
        ("Issued", "Issued"),
        ("Not Yet Requested", "Not Yet Requested"),
        ("Pending", "Pending"),
    )
    land_owner = models.ForeignKey(LandOwner, on_delete=models.SET_NULL, null=True, blank=True)
    land_request = models.OneToOneField(LandRequestInformation, on_delete=models.SET_NULL, null=True, blank=True, related_name="land_request_plot")
    plot_upi = models.CharField(max_length=50, null=True, blank=True)
    upi_status = models.CharField(max_length=30, null=False, blank=False, choices=UPI_STATUSES)
    zone = models.ForeignKey(IndustrialZone, on_delete=models.CASCADE, related_name="zone_allocated_plots")
    plot_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_allocated_plots")
    recorded_date = models.DateTimeField(auto_now_add=True)
    is_land_title_issued = models.BooleanField(default=False)
    land_title_status = models.CharField(max_length=20, choices=LAND_TITLE_STATUSES, default="Not Yet Requested")
    date_of_letter_addressed_to_nla = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "AllocatedPlots"
    
    def save(self, *args, **kwargs):
        self.plot_size = sum(plot.plot_size for plot in self.partitioned_plots.all())
        super().save(*args, **kwargs)

class PartitionedPlot(models.Model):
    STATUSES = (
        ("Not Yet Requested", "Not Requested"),
        ("Pending To Land Institution", "Pending To Land Institution"),
        ("Issued", "Issued"),
    )
    plot_number = models.CharField(max_length=30, null=False, blank=False)
    plot_upi = models.CharField(max_length=50, null=True, blank=True)
    upi_status = models.CharField(max_length=30, null=False, blank=False, choices=STATUSES)
    zone = models.ForeignKey(IndustrialZone, on_delete=models.CASCADE, related_name="zone_partitioned_plots")
    plot_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_partitioned_plots")
    allocated_plot = models.ForeignKey(AllocatedPlot, on_delete=models.CASCADE, related_name="partitioned_plots", null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PartitionedPlots"

class CompanySite(models.Model):
    CONSTRUCTION_STATUSES = (
        ("Not Started", "Not Started"),
        ("Under Construction", "Under Construction"),
        ("Completed", "Completed"),
        ("Stopped", "Stopped"),
    )
  
    OPERATIONAL_STATUSES = (
        ("Not Operational", "Not Operational"),
        ("Partially Operational", "Partially Operational"),
        ("Fully Operational", "Fully Operational"),
    )
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name="company_profile_sites")
    benefited_electricity_tarrif = models.BooleanField(default=False)
    longitude = models.DecimalField(decimal_places=8, max_digits=12, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=12, null=True, blank=True)
    province = models.CharField(max_length=40, null=False, blank=False)
    district = models.CharField(max_length=40, null=False, blank=False)
    sector = models.CharField(max_length=40, null=False, blank=False)
    construction_status = models.CharField(max_length=20, choices=CONSTRUCTION_STATUSES, default="Not Started")
    operational_status = models.CharField(max_length=30, choices=OPERATIONAL_STATUSES, default="Not Operational")
    construction_start_date = models.DateField(null=True, blank=True)
    operational_start_date = models.DateField(null=True, blank=True)
    allocated_plot = models.ForeignKey(AllocatedPlot, on_delete=models.CASCADE)
    occupied_space = models.DecimalField(decimal_places=5, max_digits=13, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    investment_amount = models.DecimalField(decimal_places=2, max_digits=15, null=True, blank=True)

    class Meta:
        db_table = "CompanySites"


