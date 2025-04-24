from django import template
from automation.utils import format_number

register = template.Library()

@register.filter(name='format_number')
def format_number_filter(value, places=2):
    return format_number(value, places)