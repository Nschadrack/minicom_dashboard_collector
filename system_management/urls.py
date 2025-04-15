from django.urls import path
from .views import (users_list, user_detail, login_user, 
                    logout_user, roles_list, role_details,
                    zones_list, economic_sub_sectors_list, 
                    economic_sectors_list, assign_roles, 
                    system_settings, assign_role_permissions,
                    delete_sub_economic_sector, products_list)

app_name = "systems_management"

urlpatterns = [
    # Users routers
    path("users/", users_list, name="users-list"),
    path("users/<str:user_id>/", user_detail, name="user-details"),
    path("users/<str:user_id>/assign-role/", assign_roles, name="assign-role"),

    # Login routers
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),

    # Roles routers
    path("roles/", roles_list, name="roles-list"),
    path("roles/<str:role_id>/", role_details, name="role-details"),
    path("role/<str:role_id>/assign-permissions/", assign_role_permissions, name="assign-role-permission"),

    # Zones routers
    path("industrial-zoning/", zones_list, name="zones-list"),

    # economic sector routers 
    path("economic-sector/", economic_sectors_list, name="economic-sectors-list"),
    path("economic/sub-sector/", economic_sub_sectors_list, name="economic-sub-sectors-list"),
    path("economic/sub-sector/<str:id>/", delete_sub_economic_sector, name="delete-sub-economic-sector"),
    path("economic/products-list/", products_list, name="products-list"),

    # System settings routers
    path("system-settings/", system_settings, name="system-settings"),
    path("system-settings/feed-<str:flag>/", system_settings, name="feed-data"),

]
