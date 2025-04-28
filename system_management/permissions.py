from django.shortcuts import redirect
from django.contrib import messages
from .models import Module, UserRole, RolePermission, Role


def user_module_permissions(user, module_id):
    """
        Function which checks user access permissions on a certain module
    """
    try:
        module = Module.objects.get(module_id=module_id)
        return list(
            RolePermission.objects.filter(
                module=module,
                role_id__in=UserRole.objects.filter(user=user).values("role_id")
            ).values_list("action_value", flat=True).distinct()
        )
    except Module.DoesNotExist:
        return []


def is_user_permitted(user, module_id, permission_value):
    permissions = user_module_permissions(user, module_id)

    return permission_value in permissions or user.is_staff


def permission_exist_on_module_role(role, module, permission_value):
    return RolePermission.objects.filter(role=role, module=module, permission_value=permission_value).first()


def check_role_permission_on_module_decorator(module_id, permission_value):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            current_user = request.user
            if is_user_permitted(current_user, module_id, permission_value):
                return view_func(request, *args, **kwargs)
            
            module = Module.objects.filter(module_id=module_id).first()
            permission = RolePermission.objects.filter(action_value=permission_value).first()

            if module and permission:
                message = f"You don't have {permission.action.lower()} permission for the module {module.name}"
            else:
                message = "You don't have required module access"
            messages.error(request, message)
            return redirect("dashboard:welcome")
        return wrapper
    return decorator

