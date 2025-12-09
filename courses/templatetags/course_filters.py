"""
Custom template filters for courses app.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def in_list(value, the_list):
    """
    Check if value is in list.
    Usage: {% if value|in_list:my_list %}
    """
    return value in the_list


@register.filter
def replace(value, args):
    """
    Replace occurrences of a string.
    Usage: {{ value|replace:"old,new" }}
    """
    if not value:
        return value
    try:
        old, new = args.split(',')
        return str(value).replace(old, new)
    except ValueError:
        return value


@register.filter
def multiply(value, arg):
    """
    Multiply a value by the argument.
    Usage: {{ value|multiply:10 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """Multiply the value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide the value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
