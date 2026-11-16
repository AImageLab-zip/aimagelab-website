from django import template

register = template.Library()


@register.filter
def initials(name):
    """First letter of the first and last word of a name: "Maria De Luca" -> "ML".

    Used for the placeholder shown when a profile has no photo.
    """
    words = str(name or "").split()
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][0].upper()
    return (words[0][0] + words[-1][0]).upper()
