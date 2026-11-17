import logging

from django import template

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def derivative_url(instance, spec_name, source_name):
    """URL of an image derivative, or of the original if that fails.

        {% derivative_url profile 'avatar_192' 'avatar' as src %}

    Generating a derivative reads the source file. A database row can point
    at a file that is no longer on disk; that used to show as one broken
    image and must not become a 500 for the whole page.
    """
    try:
        return getattr(instance, spec_name).url
    except Exception as exc:
        # One line, no traceback: this runs on every render of the page.
        logger.warning('No %s derivative for %r (%s: %s), using the original',
                       spec_name, instance, type(exc).__name__, exc)
    try:
        source = getattr(instance, source_name)
        return source.url if source else ''
    except Exception:
        return ''
