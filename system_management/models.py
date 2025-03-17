from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.model(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save()
        return user
    
class User(AbstractUser):
    USER_CATEGORIES = (
        ("MINICOM STAFF", "MINICOM STAFF"),
        ("COMPANY", "COMPANY"),
        ("VISITOR", "VISITOR"),
    )

    first_name = models.CharField(max_length=250, null=False, blank=False)
    username = None
    change_password_required = models.BooleanField(default=False)
    user_category = models.CharField(max_length=20, choices=USER_CATEGORIES, null=False, blank=False)
    email = models.EmailField(unique=True, max_length=250)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
        db_table = 'Users'


class Role(models.Model):
    name = models.CharField(max_length=120, null=False, blank=False, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Roles'

    def __str__(self):
        return f"Role: {self.name}"
    

class Module(models.Model):
    module_id = models.CharField(max_length=10, null=False, blank=False, unique=True, primary_key=True)
    parent_id = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=40, null=False, blank=False, unique=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Modules'

    def __str__(self):
        return f"Module: {self.name}"
    
    
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="all_user_roles")
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="all_users_assigned")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="all_role_users")
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
    name = models.CharField(max_length=200, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'EconomicSectors'

    def __str__(self):
        return f"Economic sector: {self.name}"
      

class EconomicSubSector(models.Model):
    isic_code = models.CharField(max_length=10, null=False, blank=False)
    economic_sector = models.ForeignKey(EconomicSector, on_delete=models.CASCADE, related_name="sub_sectors")
    name = models.CharField(max_length=200, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'EconomicSubSectors'

    def __str__(self):
        return f"Economic sub-sector: {self.name}"
    

class IndustrialZone(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    recorded_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'IndustrialZones'

    def __str__(self):
        return f"Industrial zone: {self.name}"
    
    
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
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'AdministrativeUnits'
    
    def __str__(self):
        return f"{self.name} {self.category.lower()}"

