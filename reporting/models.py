from django.db import models
from industry.models import IndustryProduct, CompanySite
from system_management.models import User
from industry.fixtures import CURRENCIES


class MonthsReportingPeriodConfig(models.Model):
    months = models.PositiveIntegerField(null=False, blank=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "MonthsReportingPeriodConfigs"


class ReportingPeriodPlan(models.Model):
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    period_config = models.ForeignKey(MonthsReportingPeriodConfig, on_delete=models.SET_NULL, blank=True, null=True)


class IndustryProductReport(models.Model):
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    product = models.ForeignKey(IndustryProduct, on_delete=models.CASCADE)
    production_volume = models.DecimalField(decimal_places=2, max_digits=12,  null=False, blank=False)
    current_installed_production = models.DecimalField(decimal_places=2, max_digits=12)
    reported_on = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    justification_production_capacity = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "IndustryProductReports"


class EmploymentReport(models.Model):
    start_date = models.DateField(null=False, blank=False)
    end_date = models.DateField(null=False, blank=False)
    industry = models.ForeignKey(CompanySite, on_delete=models.CASCADE)
    current_male_permanent_employees = models.PositiveIntegerField(blank=False, null=False)
    current_male_casual_employees = models.PositiveIntegerField(blank=False, null=False)
    current_female_permanent_employees = models.PositiveIntegerField(blank=False, null=False)
    current_female_casual_employees = models.PositiveIntegerField(blank=False, null=False)
    new_male_permanent_employees = models.PositiveIntegerField(blank=False, null=False)
    new_male_casual_employees = models.PositiveIntegerField(blank=False, null=False)
    new_female_permanent_employees = models.PositiveIntegerField(blank=False, null=False)
    new_female_casual_employees = models.PositiveIntegerField(blank=False, null=False)
    job_loss = models.PositiveIntegerField(blank=False, null=False)
    current_male_youth_employees = models.PositiveIntegerField(blank=False, null=False)
    current_female_youth_employees = models.PositiveIntegerField(blank=False, null=False)
    improvement_suggestion = models.TextField(blank=True, null=True)
    challenges_faced = models.TextField(blank=True, null=True)
    support_needed = models.TextField(blank=True, null=True)
    reported_on = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "EmploymentReports"



    


