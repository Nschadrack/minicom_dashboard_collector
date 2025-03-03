from django.urls import path
from .views import (users_list, user_detail, login_user, 
                    logout_user, roles_list, role_details,
                    zones_list,
                    assign_roles, system_settings, assign_role_permissions)

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

    # System settings routers
    path("system-settings/", system_settings, name="system-settings"),
    path("system-settings/feed-<str:flag>/", system_settings, name="feed-modules"),

]
