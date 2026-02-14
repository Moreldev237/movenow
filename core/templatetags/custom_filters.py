from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide two values"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0


@register.filter
def sub(value, arg):
    """Subtract two values"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def add(value, arg):
    """Add two values"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total) * 100) if float(total) != 0 else 0
    except (ValueError, TypeError):
        return 0


@register.filter
def floatformat_zero(value):
    """Format number without decimal places"""
    try:
        return f"{float(value):.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
@stringfilter
def truncatechars_nospaces(value, length):
    """Truncate string without counting spaces"""
    if not value:
        return ''
    # Remove extra spaces
    value = ' '.join(value.split())
    if len(value) > length:
        return value[:length] + '...'
    return value

