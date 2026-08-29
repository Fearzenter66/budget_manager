from django import template

from core.money import format_amount as format_amount_value

register = template.Library()


@register.filter
def format_amount(value):
    return format_amount_value(value)
