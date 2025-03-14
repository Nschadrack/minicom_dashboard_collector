from django.db import models
from django.utils.translation import gettext_lazy as _
from system_management.models import IndustrialZone, User, EconomicSubSector


class IndustryEconomicZone(models.Model):
    CATEGORIES = (
        ("Special Economic Zone", "Special Economic Zone"),
        ("Industrial Park", "Industrial Park"),
        ("Light Industrial Zone", "Light Industrial Zone"),
    )
    name = models.CharField(max_length=150, null=False, blank=False)
    category = models.CharField(max_length=60, null=False, blank=False, choices=CATEGORIES)
    total_land_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    leasable_land = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    province = models.CharField(max_length=60, null=False, blank=False)
    district = models.CharField(max_length=60, null=False, blank=False)
    sector = models.CharField(max_length=60, null=False, blank=False)
    cell = models.CharField(max_length=60, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    park_plots_map = models.FileField(upload_to="Industrial_parks_plots_maps/", null=True, blank=True)

    class Meta:
        db_table = "IndustryEconomicZones"
    
    def __str__(self):
        return f"{self.name} {self.category.lower()}"

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
    land_owner = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, null=True, blank=True)
    request_date = models.DateField(null=True, blank=True)
    request_closure_date = models.DateField(null=True, blank=True)
    requested_land_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_land_requests", blank=False, null=False)
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
    land_owner = models.ForeignKey(CompanyProfile, on_delete=models.SET_NULL, null=True, blank=True)
    land_request = models.OneToOneField(LandRequestInformation, on_delete=models.SET_NULL, null=True, blank=True, related_name="land_request_plot")
    allocated_plot_upi = models.CharField(max_length=50, null=True, blank=True)
    upi_status = models.CharField(max_length=30, null=False, blank=False, choices=UPI_STATUSES, default="Not Yet Requested")
    zone = models.ForeignKey(IndustrialZone, on_delete=models.CASCADE, related_name="zone_allocated_plots")
    plot_size = models.DecimalField(decimal_places=5, max_digits=13, null=True, blank=True)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_allocated_plots", blank=True, null=True)
    is_in_park = models.BooleanField(default=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    is_land_title_issued = models.BooleanField(default=False)
    land_title_status = models.CharField(max_length=20, choices=LAND_TITLE_STATUSES, default="Not Yet Requested")
    date_of_letter_addressed_to_nla = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "AllocatedPlots"

class PartitionedPlot(models.Model):
    STATUSES = (
        ("Not Yet Requested", "Not Requested"),
        ("Pending To Land Institution", "Pending To Land Institution"),
        ("Issued", "Issued"),
    )
    plot_number = models.CharField(max_length=30, null=False, blank=False)
    partitioned_plot_upi = models.CharField(max_length=50, null=True, blank=True)
    upi_status = models.CharField(max_length=30, null=False, blank=False, choices=STATUSES)
    zone = models.ForeignKey(IndustrialZone, on_delete=models.CASCADE, related_name="zone_partitioned_plots")
    plot_size = models.DecimalField(decimal_places=5, max_digits=13, null=False, blank=False)
    park = models.ForeignKey(IndustryEconomicZone, on_delete=models.CASCADE, related_name="park_partitioned_plots")
    allocated_plot = models.ForeignKey(AllocatedPlot, on_delete=models.CASCADE, related_name="partitioned_plots", null=True, blank=True)
    is_allocated = models.BooleanField(default=False)
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
    CURRENCIES = (
        ("USD", "USD"),
        ("RWF", "RWF"),
    )
    
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name="company_profile_sites")
    benefited_electricity_tarrif = models.BooleanField(blank=True, null=True)
    longitude = models.DecimalField(decimal_places=8, max_digits=12, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=12, null=True, blank=True)
    province = models.CharField(max_length=60, null=False, blank=False)
    district = models.CharField(max_length=60, null=False, blank=False)
    sector = models.CharField(max_length=60, null=False, blank=False)
    cell = models.CharField(max_length=60, null=True, blank=True)
    construction_status = models.CharField(max_length=20, choices=CONSTRUCTION_STATUSES, default="Not Started")
    operational_status = models.CharField(max_length=30, choices=OPERATIONAL_STATUSES, default="Not Operational")
    construction_start_date = models.DateField(null=True, blank=True)
    operational_start_date = models.DateField(null=True, blank=True)
    allocated_plot = models.ForeignKey(AllocatedPlot, on_delete=models.SET_NULL, blank=True, null=True)
    is_in_park = models.BooleanField(default=True)
    occupied_space = models.DecimalField(decimal_places=5, max_digits=13, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    investment_amount = models.DecimalField(decimal_places=2, max_digits=15, null=True, blank=True)
    investment_currency = models.CharField(max_length=10, null=True, blank=True, choices=CURRENCIES)

    class Meta:
        db_table = "CompanySites"

class IndustryAttachment(models.Model):
    CATEGORIES = (
        ("Main Document", "Main Document"),
        ("Other Supporting Document", "Other Supporting Document"),
    )
    industry = models.ForeignKey(CompanySite, on_delete=models.CASCADE, related_name="industry_attachments")
    name = models.CharField(max_length=100, null=False, blank=False)
    category = models.CharField(max_length=40, choices=CATEGORIES)
    comment = models.CharField(max_length=200, null=True, blank=True)
    uploaded_date = models.DateTimeField(auto_now_add=True)
    document = models.FileField(upload_to="Industry_attachments/", null=False, blank=False)
    document_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "IndustryAttachments"

class IndustryEconomicSector(models.Model):
    industry = models.ForeignKey(CompanySite, on_delete=models.CASCADE)
    sector = models.ForeignKey(EconomicSubSector, on_delete=models.CASCADE)

    class Meta:
        db_table = "IndustryEconomicSectors"


