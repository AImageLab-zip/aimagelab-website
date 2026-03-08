from django import template

register = template.Library()


@register.filter
def split(value, arg=","):
    """Split a string by the given separator and return a list."""
    return [item.strip() for item in value.split(arg) if item.strip()]
