from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        db_table = 'users'

class Role(models.Model):
    name = models.CharField(max_length=120, null=False, blank=False, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Roles'

    def __str__(self):
        return f"Role: {self.name}"

class Module(models.Model):
    module_id = models.CharField(max_length=10, null=False, blank=False, unique=True, primary_key=True)
    name = models.CharField(max_length=40, null=False, blank=False, unique=True)
    created_date = models.CharField(auto_now_add=True)

    class Meta:
        db_table = 'Modules'

    def __str__(self):
        return f"Module: {self.name}"
    
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="all_user_roles")
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="all_users_assigned")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="all_role_users")
    assignment_reason = models.CharField(max_length=200, null=True, blank=True)
    assigned_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'UserRoles'

    def __str__(self):
        return f"{self.user.get_full_name()} has {self.role.name} role"
    
class RolePermission(models.Model):
    ACTIONS = (
        ("Create", "Create"),
        ("Edit", "Edit"),
        ("View", "View"),
        ("Delete", "Delete"),
        ("Approve", "Approve"),
        ("Grant", "Grant"),
        ("Revoke", "Revoke"),
    )
    ACTIONS_VALUES = {
        "Create": 1,
        "Edit": 2,
        "View": 3,
        "Delete": 4,
        "Approve": 5,
        "Grant": 6,
        "Revoke": 7
    }

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="all_module_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="all_role_modules")
    action = models.CharField(max_length=10, null=False, blank=False, choices=ACTIONS)
    action_value = models.PositiveSmallIntegerField(null=False, blank=False)

    class Meta:
        db_table = 'RolePermissions'

    def __str__(self):
        return f"{self.role.name} is permitted to {self.action.lower()} on {self.module.name}"
    
class EconomicSector(models.Model):
    name = models.CharField(max_length=150, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'EconomicSectors'

    def __str__(self):
        return f"Economic sector: {self.name}"

class EconomicSubSector(EconomicSector):
    economic_sector = models.ForeignKey(EconomicSector, on_delete=models.CASCADE, related_name="sub_sectors")

    class Meta:
        db_table = 'EconomicSubSectors'

    def __str__(self):
        return f"Economic sub-sector: {self.name}"
    
class AdministrativeUnit(models.Model):
    CATEGORIES = (
        ("PROVINCE", "PROVINCE"),
        ("DISTRICT", "DISTRICT"),
        ("SECTOR", "SECTOR"),
        ("CELL", "CELL"),
        ("VILLAGE", "VILLAGE"),
    )
    name = models.CharField(max_length=50, null=False, blank=False)
    category = models.CharField(max_length=30, null=False, blank=False)
    parent = models.ForeignKey("self", on_delete=models.CASCADE)

    class Meta:
        db_table = 'AdministrativeUnits'
    
    def __str__(self):
        return f"{self.name} {self.category.lower()}"

