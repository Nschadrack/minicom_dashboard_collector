from django import template
from automation.utils import format_number
from system_management.permissions import is_user_permitted

register = template.Library()

@register.filter(name='format_number')
def format_number_filter(value, places=2):
    return format_number(value, places)

@register.filter(name="is_user_permitted")
def is_user_allowed_access(user, args):
    module_id, permission_value = args.split(",")
    permission_value = int(permission_value)
    return is_user_permitted(user, module_id, permission_value)

@register.filter(name="is_not_company_user")
def is_not_company_user(user):
    return user.user_category.upper() != "COMPANY"

@register.filter(name="list_loop")
def loop_list(sequence, position):
    try:
        return sequence[position]
    except:
        return None