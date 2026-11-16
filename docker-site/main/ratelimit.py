"""Client address for django-ratelimit (settings.RATELIMIT_IP_META_KEY)."""


def client_ip(request):
    """The address of the client as seen by the reverse proxy.

    Apache overwrites X-Forwarded-For with the peer address and mod_proxy
    then appends that same address, so the LAST entry is always written by
    our own proxy; entries before it can be supplied by the client and are
    ignored. Without the header (runserver reached directly) REMOTE_ADDR is
    the client itself.

    The application port must stay unreachable except through the proxy
    (it is bound to loopback in docker-compose.prod.yml): a client that can
    reach it directly can choose this header.
    """
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    last = forwarded.split(',')[-1].strip()
    return last or request.META.get('REMOTE_ADDR', '')
