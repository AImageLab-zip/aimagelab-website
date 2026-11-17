"""
Service layer for the mailing list app.

Handles:
- Fetching mail from Gmail via IMAP
- Resolving recipients based on subject-role routing
- Progressive sending via SMTP
"""
import os
import re
import email
import imaplib
import logging
import smtplib
from email import policy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, getaddresses, parseaddr

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import (
    BlacklistedSender,
    ExternalRecipient,
    IncomingEmail,
    IncomingEmailAttachment,
    MailingListPreference,
    OutgoingEmail,
    SubjectRoleRoute,
    UserExtraEmail,
    WhitelistedSender,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMAP fetching
# ---------------------------------------------------------------------------

def fetch_new_emails():
    """Connect to Gmail IMAP, fetch unseen messages, persist them."""
    host = settings.MAILINGLIST_IMAP_HOST
    port = settings.MAILINGLIST_IMAP_PORT
    user = settings.MAILINGLIST_EMAIL_ADDRESS
    password = settings.MAILINGLIST_EMAIL_PASSWORD

    created_ids = []
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select('INBOX')

        status, data = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.warning("IMAP search returned status %s", status)
            return created_ids

        for num in data[0].split():
            status, msg_data = mail.fetch(num, '(RFC822)')
            if status != 'OK':
                continue
            # One message at a time: a single unparsable message used to
            # raise out of the loop, which skipped every message after it
            # in this run and never queued the ones already stored.
            try:
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw, policy=policy.default)
                incoming = _persist_email(msg, raw)
            except Exception:
                logger.exception("Could not process inbound message %s", num)
                continue
            if incoming:
                created_ids.append(incoming.id)
        mail.logout()
    except Exception:
        logger.exception("Error fetching emails via IMAP")
    return created_ids


def _is_direct_recipient(msg):
    """Check if the configured list address is a direct recipient (To or Cc).
    
    Returns True if the list address appears in To or Cc headers,
    False otherwise (e.g., BCC or mailing list forwarding).
    """
    list_address = getattr(settings, 'MAILINGLIST_LIST_ADDRESS', 'aimagelab@unimore.it')
    list_local, list_domain = list_address.rsplit('@', 1)
    list_address_lower = list_address.lower()
    list_local_lower = list_local.lower()
    list_domain_lower = list_domain.lower()
    
    # Parse To and Cc headers
    raw_to = msg.get('To', '') or ''
    raw_cc = msg.get('Cc', '') or ''
    all_recipients = getaddresses([raw_to, raw_cc])
    
    # Check if list address (or plus-addressed variant) is in recipients
    for _, addr in all_recipients:
        addr_lower = addr.lower().strip()
        if '@' not in addr_lower:
            continue
        addr_local, addr_domain = addr_lower.rsplit('@', 1)
        
        # Match exact address or plus-addressed variants (aimagelab+tag@unimore.it)
        if addr_domain == list_domain_lower:
            if addr_local == list_local_lower or addr_local.startswith(list_local_lower + '+'):
                return True
    
    return False


_MESSAGE_ID = re.compile(r'<[^<>\s]+>')


def _is_reply_to_list_mail(msg):
    """True if msg answers a message this list has already distributed.

    Every copy we send carries the original Message-ID in References (see
    _build_outgoing_message), and mail clients copy References into a reply,
    so the original's id shows up in the reply's References/In-Reply-To.
    """
    ids = set(_MESSAGE_ID.findall(
        f"{msg.get('In-Reply-To', '') or ''} {msg.get('References', '') or ''}"
    ))
    if not ids:
        return False
    return IncomingEmail.objects.filter(
        message_id__in=ids, status__in=('approved', 'auto_approved')
    ).exists()


_AR_COMMENT = re.compile(r'\([^()]*\)')


def _aligned(domain, sender_domain):
    """Same domain, or one is a subdomain of the other (relaxed alignment)."""
    domain = (domain or '').lower().strip('.')
    if not domain or not sender_domain:
        return False
    return (domain == sender_domain
            or domain.endswith('.' + sender_domain)
            or sender_domain.endswith('.' + domain))


def sender_auth_verdict(msg, sender_domain):
    """What the receiving mail server says about the From: domain.

    Returns 'pass', 'fail' or 'none' (no usable Authentication-Results).

    Only the topmost Authentication-Results header is read: each server
    prepends its own, so the first one is written by the server that
    delivered into our mailbox, while any header further down may have been
    put there by the sender. If MAILINGLIST_AUTHSERV_ID is set, the header
    must also name that server.

    'pass' needs one of (RFC 8601 / RFC 7489):
      dmarc=pass  for a header.from aligned with the From: domain
      dkim=pass   with a signing domain (header.d / header.i) aligned
      spf=pass    with an envelope sender (smtp.mailfrom) aligned
    A DKIM or SPF pass for some unrelated domain proves nothing about
    From:, hence the alignment test.
    """
    headers = msg.get_all('Authentication-Results') or []
    if not headers:
        return 'none'
    value = ' '.join(str(headers[0]).split())
    # Comments may nest one level: strip until stable.
    previous = None
    while previous != value:
        previous, value = value, _AR_COMMENT.sub(' ', value)

    parts = [p.strip() for p in value.split(';')]
    authserv_id = parts[0].split()[0].lower() if parts and parts[0].split() else ''
    wanted = (getattr(settings, 'MAILINGLIST_AUTHSERV_ID', '') or '').lower()
    if wanted and authserv_id != wanted:
        return 'none'

    seen_method = False
    for part in parts[1:]:
        tokens = part.split()
        if not tokens or '=' not in tokens[0]:
            continue
        method, _, result = tokens[0].partition('=')
        method, result = method.lower(), result.lower()
        if method not in ('dmarc', 'dkim', 'spf'):
            continue
        seen_method = True
        if result != 'pass':
            continue
        props = {}
        for token in tokens[1:]:
            key, sep, val = token.partition('=')
            if sep:
                props[key.lower()] = val.strip('"<>').lower()
        if method == 'dmarc':
            candidates = [props.get('header.from', '')]
        elif method == 'dkim':
            candidates = [props.get('header.d', ''), props.get('header.i', '')]
        else:
            candidates = [props.get('smtp.mailfrom', '')]
        for candidate in candidates:
            if _aligned(candidate.rsplit('@', 1)[-1], sender_domain):
                return 'pass'
    return 'fail' if seen_method else 'none'


def _sender_is_verified(msg, sender_domain):
    """May this message be auto-approved on the strength of its From:?

    See MAILINGLIST_SENDER_AUTH in settings.py.
    """
    mode = getattr(settings, 'MAILINGLIST_SENDER_AUTH', 'lenient')
    if mode == 'off':
        return True
    verdict = sender_auth_verdict(msg, sender_domain)
    if verdict == 'pass':
        return True
    if verdict == 'none':
        return mode != 'strict'
    return False


def _safe_attachment_name(filename):
    """A storable file name from one chosen by the sender of an e-mail."""
    name = os.path.basename(str(filename or '').replace('\\', '/')).strip().lstrip('.')
    name = re.sub(r'[\x00-\x1f\x7f]', '', name) or 'unnamed'
    if len(name) > 100:
        stem, ext = os.path.splitext(name)
        name = stem[:100 - len(ext[:20])] + ext[:20]
    return name


def _part_text(part):
    """Decoded text of a MIME part; '' if it cannot be decoded."""
    try:
        content = part.get_content()
    except Exception:
        try:
            payload = part.get_payload(decode=True) or b''
            content = payload.decode('utf-8', errors='replace')
        except Exception:
            return ''
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')
    return content if isinstance(content, str) else ''


def _persist_email(msg, raw_bytes):
    """Parse an email.message.Message and save as IncomingEmail."""
    # Column limits are enforced here: MySQL runs in strict mode, so an
    # over-long Message-ID or sender name was an error and the mail was lost.
    message_id = str(msg.get('Message-ID', '') or '').strip()[:255]
    if not message_id:
        message_id = f"no-id-{timezone.now().timestamp()}"

    if IncomingEmail.objects.filter(message_id=message_id).exists():
        return None

    # parseaddr, not a split on '<': "a <x@unimore.it> <evil@example.com>"
    # and similar no longer yield an address different from the one mail
    # clients show.
    sender_name, sender = parseaddr(str(msg.get('From', '') or ''))
    sender = sender.strip()[:254]
    sender_name = sender_name.strip()[:255]

    subject = str(msg.get('Subject', '') or '(no subject)')[:998]

    # Parse email body content
    body_text = ''
    body_html = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart() or part.get_content_disposition() == 'attachment':
                continue
            ct = part.get_content_type()
            if ct == 'text/plain' and not body_text:
                body_text = _part_text(part)
            elif ct == 'text/html' and not body_html:
                body_html = _part_text(part)
    else:
        ct = msg.get_content_type()
        if ct == 'text/html':
            body_html = _part_text(msg)
        else:
            body_text = _part_text(msg)

    # Check if the configured list address is a direct recipient (To/Cc)
    # Reject emails where we're not directly addressed (e.g., from mailing lists)
    if not _is_direct_recipient(msg):
        logger.info("Rejecting email not directly addressed to list: %s from %s", 
                    subject, sender)
        incoming = IncomingEmail.objects.create(
            message_id=message_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            clean_subject=subject,
            body_text=body_text,
            body_html=body_html,
            raw_headers=str(msg.items()),
            status='not_direct_recipient',
        )
        return incoming

    # Determine auto-approval: check blacklist, then whitelist, then trusted domains
    sender_lower = sender.lower()
    if BlacklistedSender.objects.filter(email__iexact=sender_lower).exists():
        logger.info("Rejecting email from blacklisted sender %s", sender)
        routes = _match_routes(msg)
        incoming = IncomingEmail.objects.create(
            message_id=message_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            clean_subject=subject,
            body_text=body_text,
            body_html=body_html,
            raw_headers=str(msg.items()),
            status='blacklisted',
        )
        incoming.matched_routes.set(routes)
        return incoming

    sender_domain = sender_lower.split('@')[-1] if '@' in sender_lower else ''
    is_trusted = (
        WhitelistedSender.objects.filter(email__iexact=sender_lower).exists()
        or any(
            sender_domain == d or sender_domain.endswith('.' + d)
            for d in getattr(settings, 'MAILINGLIST_TRUSTED_DOMAINS', ['unimore.it'])
        )
    )
    # From: is written by the sender. Before it earns an automatic
    # distribution to every subscriber, the receiving server's SPF/DKIM/DMARC
    # verdict has to agree that the message really comes from that domain;
    # otherwise anyone could post to the whole list by typing a unimore.it
    # address into From:. A message that fails goes to moderation.
    if is_trusted and not _sender_is_verified(msg, sender_domain):
        logger.warning(
            "Sender %s is trusted by address but failed SPF/DKIM/DMARC; holding for moderation",
            sender)
        is_trusted = False

    # Match route via plus-addressing in To/Cc headers
    routes = _match_routes(msg)

    # A reply to list mail is not redistributed on the sender's trust alone:
    # one careless Reply All would reach every subscriber (issue #29). It
    # waits for a moderator unless the policy says otherwise.
    is_reply = _is_reply_to_list_mail(msg)
    if is_reply and getattr(settings, 'MAILINGLIST_REPLY_POLICY', 'moderate') != 'allow':
        if is_trusted:
            logger.info("Holding reply to list mail for moderation: %s from %s", subject, sender)
        is_trusted = False

    incoming = IncomingEmail.objects.create(
        message_id=message_id,
        sender=sender,
        sender_name=sender_name,
        subject=subject,
        clean_subject=subject,
        body_text=body_text,
        body_html=body_html,
        raw_headers=str(msg.items()),
        status='auto_approved' if is_trusted else 'pending',
        is_reply=is_reply,
    )
    incoming.matched_routes.set(routes)

    # Save attachments
    if msg.is_multipart():
        for part in msg.walk():
            disposition = part.get('Content-Disposition', '')
            if 'attachment' in disposition or 'inline' in disposition:
                # The file name is chosen by the sender. '../x' made the
                # storage layer raise, which aborted the whole fetch after
                # the message had been stored: an auto-approved message was
                # then never queued for delivery.
                filename = _safe_attachment_name(part.get_filename())
                try:
                    content = part.get_payload(decode=True)
                    if content:
                        att = IncomingEmailAttachment(
                            email=incoming,
                            filename=filename,
                            content_type=part.get_content_type()[:100],
                        )
                        att.file.save(filename, ContentFile(content), save=False)
                        att.save()
                except Exception:
                    logger.exception("Could not store attachment %r of message %s",
                                     filename, incoming.pk)

    return incoming


def _match_routes(msg):
    """Find routes by parsing To/Cc for aimagelab+<suffix>@domain addresses.

    Returns a list of matched SubjectRoleRoute objects.
    """
    list_address = getattr(settings, 'MAILINGLIST_LIST_ADDRESS', 'aimagelab@unimore.it')
    local_part, domain = list_address.rsplit('@', 1)
    local_lower = local_part.lower()
    domain_lower = domain.lower()

    raw_to = msg.get('To', '') or ''
    raw_cc = msg.get('Cc', '') or ''
    all_addrs = getaddresses([raw_to, raw_cc])

    suffixes = set()
    for _, addr in all_addrs:
        addr_lower = addr.lower().strip()
        if '@' not in addr_lower:
            continue
        addr_local, addr_domain = addr_lower.rsplit('@', 1)
        if addr_domain == domain_lower and addr_local.startswith(local_lower + '+'):
            suffix = addr_local[len(local_lower) + 1:]
            if suffix:
                suffixes.add(suffix)

    if not suffixes:
        return []

    return list(SubjectRoleRoute.objects.filter(tag__in=suffixes))


# ---------------------------------------------------------------------------
# Recipient resolution
# ---------------------------------------------------------------------------

def resolve_recipients_for_routes(routes):
    """Return a deduplicated set of email addresses for a given list of routes.

    Shared by resolve_recipients() and the tag-recipients API view.
    """
    addresses = set()

    if routes:
        target_roles = set()
        send_external = False
        send_to_admins = False
        for route in routes:
            for role in (route.roles or []):
                if role == '__admin__':
                    send_to_admins = True
                else:
                    target_roles.add(role)
            if route.send_to_external:
                send_external = True

        qs = User.objects.none()
        if target_roles:
            qs = qs | User.objects.filter(
                is_active=True,
                profile__role__in=target_roles,
                mailing_preference__subscribed=True,
            )
        if send_to_admins:
            qs = qs | User.objects.filter(
                is_active=True,
                is_staff=True,
                mailing_preference__subscribed=True,
            )
        users = qs.distinct().select_related('profile', 'mailing_preference')
    else:
        # No route → all active members (equivalent to the 'default' tag), no external
        send_external = False
        active_roles = [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
            'postdoc', 'secretariat_staff', 'research_fellow',
            'collaborator', 'phd', 'intern',
        ]
        users = User.objects.filter(
            is_active=True,
            profile__role__in=active_roles,
            mailing_preference__subscribed=True,
        ).select_related('profile', 'mailing_preference')

    for user in users:
        if user.email:
            addresses.add(user.email.lower())
        extras = UserExtraEmail.objects.filter(preference__user=user)
        for extra in extras:
            addresses.add(extra.email.lower())

    if send_external:
        for ext in ExternalRecipient.objects.filter(subscribed=True):
            addresses.add(ext.email.lower())

    list_addr = getattr(settings, 'MAILINGLIST_EMAIL_ADDRESS', '').lower()
    addresses.discard(list_addr)

    return addresses


def resolve_recipients(incoming_email):
    """Return a deduplicated set of email addresses for delivery.

    Rules:
    - If routes matched, send to the union of users matching any route's roles
      (plus external recipients if any route allows it).
    - If no routes matched, send to all subscribed active users + external.
    - Respect per-user subscription preferences.
    """
    routes = list(incoming_email.matched_routes.all())
    return resolve_recipients_for_routes(routes)


# ---------------------------------------------------------------------------
# Queue outgoing deliveries
# ---------------------------------------------------------------------------

def queue_deliveries(incoming_email):
    """Create OutgoingEmail records for each recipient."""
    addresses = resolve_recipients(incoming_email)
    objs = [
        OutgoingEmail(incoming=incoming_email, recipient_email=addr)
        for addr in addresses
    ]
    OutgoingEmail.objects.bulk_create(objs, ignore_conflicts=True)
    return len(objs)


# ---------------------------------------------------------------------------
# SMTP sending (progressive / batched)
# ---------------------------------------------------------------------------

def send_batch(batch_size=None):
    """Send a batch of queued outgoing emails via SMTP.

    Returns the number of emails successfully sent.
    """
    if batch_size is None:
        batch_size = getattr(settings, 'MAILINGLIST_BATCH_SIZE', 20)

    # Read candidate IDs first (slicing is not allowed with select_for_update).
    candidate_ids = list(
        OutgoingEmail.objects.filter(status='queued')
        .order_by('created_at')
        .values_list('id', flat=True)[:batch_size]
    )
    if not candidate_ids:
        return 0

    # Atomically claim this batch by transitioning queued → sending.
    # The WHERE status='queued' guard acts as a mutex: if two tasks race on
    # the same candidates, the second UPDATE finds 0 matching rows (PostgreSQL
    # locks the row on UPDATE, so it sees the already-changed status from the
    # first task) and does nothing, preventing double-delivery.
    claimed = OutgoingEmail.objects.filter(
        id__in=candidate_ids, status='queued'
    ).update(status='sending')
    if claimed == 0:
        return 0

    queued = list(
        OutgoingEmail.objects.filter(id__in=candidate_ids, status='sending')
        .select_related('incoming')
    )

    smtp_host = settings.MAILINGLIST_SMTP_HOST
    smtp_port = settings.MAILINGLIST_SMTP_PORT
    smtp_user = settings.MAILINGLIST_EMAIL_ADDRESS
    smtp_pass = settings.MAILINGLIST_EMAIL_PASSWORD
    list_addr = settings.MAILINGLIST_EMAIL_ADDRESS
    list_name = getattr(settings, 'MAILINGLIST_FROM_NAME', 'AImageLab Mailing List')

    sent_count = 0
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)

        for delivery in queued:
            try:
                msg = _build_outgoing_message(delivery, list_addr, list_name)
                server.sendmail(list_addr, [delivery.recipient_email], msg.as_string())
                delivery.status = 'sent'
                delivery.sent_at = timezone.now()
                delivery.save(update_fields=['status', 'sent_at'])
                sent_count += 1
            except Exception as exc:
                logger.exception("Failed to send to %s", delivery.recipient_email)
                delivery.status = 'failed'
                delivery.error_message = str(exc)[:1000]
                delivery.save(update_fields=['status', 'error_message'])

        server.quit()
    except Exception:
        logger.exception("SMTP connection error")
        # Reset any still-claimed deliveries back to queued so they can be retried.
        OutgoingEmail.objects.filter(id__in=candidate_ids, status='sending').update(status='queued')

    return sent_count


def _build_outgoing_message(delivery, list_addr, list_name):
    """Build a MIME message for a single outgoing delivery."""
    incoming = delivery.incoming

    # Show original sender's name in From, but send via the list address.
    # This satisfies Gmail SMTP (must send as authenticated address) while
    # making the sender identity clear in email clients.
    sender_display = incoming.sender_name or incoming.sender
    msg = MIMEMultipart('mixed')
    msg['From'] = formataddr((f"{sender_display} via {list_name}", list_addr))
    msg['To'] = delivery.recipient_email
    # Use clean_subject (identical to subject now that tags are no longer in subject)
    msg['Subject'] = incoming.clean_subject or incoming.subject
    # Reply-To points to the original sender so replies go back to them,
    # not to the mailing list inbox.
    msg['Reply-To'] = formataddr((sender_display, incoming.sender))
    if incoming.message_id:
        msg['References'] = incoming.message_id

    # The route addresses are NOT added as Cc. They used to be, "so Reply All
    # sends back to the list": the reply then arrived directly addressed, from
    # a trusted domain, was auto-approved and went out to every subscriber
    # (issue #29). Reply and Reply All now both go to the original sender
    # only, via Reply-To above.
    #
    # RFC 2369 List-Post / List-Id stay, so clients still offer an explicit
    # "Reply to list" and filters keep working; the footer names the list
    # the message was sent to.
    routes = list(incoming.matched_routes.all())
    list_addrs = _route_addresses(routes)
    if list_addrs:
        primary = list_addrs[0]
        msg['List-Post'] = f'<mailto:{primary}>'
        msg['List-Id'] = f'{list_name} <{primary.replace("@", ".")}>'

    # Unsubscribe header (RFC 8058)
    unsubscribe_token = _get_unsubscribe_token(delivery.recipient_email)
    if unsubscribe_token:
        base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        msg['List-Unsubscribe'] = f"<{unsub_url}>"
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

    # Body — wrap text+html in multipart/alternative so clients pick one,
    # not render both.
    footer_html = _build_footer_html(unsubscribe_token, list_addrs)
    footer_text = _build_footer_text(unsubscribe_token, list_addrs)

    if incoming.body_html or incoming.body_text:
        alt = MIMEMultipart('alternative')
        # plain text first (lowest preference)
        plain = incoming.body_text + footer_text if incoming.body_text else ''
        alt.attach(MIMEText(plain, 'plain'))
        # html second (highest preference — clients pick this when supported)
        if incoming.body_html:
            html_content = incoming.body_html
            # Case-insensitive, last occurrence: with '</BODY>' the test
            # matched but the case-sensitive replace did nothing, and the
            # message went out without its unsubscribe footer.
            close = html_content.lower().rfind('</body>')
            if close != -1:
                html_content = html_content[:close] + footer_html + html_content[close:]
            else:
                html_content += footer_html
            alt.attach(MIMEText(html_content, 'html'))
        msg.attach(alt)
    else:
        msg.attach(MIMEText('', 'plain'))

    # Attachments
    for att in incoming.attachments.all():
        try:
            part = MIMEBase(*att.content_type.split('/', 1))
            att.file.open('rb')
            part.set_payload(att.file.read())
            att.file.close()
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=att.filename)
            msg.attach(part)
        except Exception:
            logger.warning("Could not attach file %s", att.filename)

    return msg


def _get_unsubscribe_token(email_addr):
    """Return the unsubscribe token for a given email address."""
    email_lower = email_addr.lower()

    # Check user extra emails
    extra = UserExtraEmail.objects.filter(email__iexact=email_lower).first()
    if extra:
        return str(extra.unsubscribe_token)

    # Check external recipients
    ext = ExternalRecipient.objects.filter(email__iexact=email_lower).first()
    if ext:
        return str(ext.unsubscribe_token)

    # Check user primary email → use preference UUID token
    user = User.objects.filter(email__iexact=email_lower).first()
    if user:
        pref, _ = MailingListPreference.objects.get_or_create(user=user)
        return str(pref.unsubscribe_token)

    return None


def _route_addresses(routes):
    """Plus-addressed list addresses for the given routes."""
    ml_list_address = getattr(settings, 'MAILINGLIST_LIST_ADDRESS', 'aimagelab@unimore.it')
    ml_local, ml_domain = ml_list_address.rsplit('@', 1)
    return [f"{ml_local}+{r.tag}@{ml_domain}" for r in routes]


def _footer_sentence(list_addrs):
    if list_addrs:
        return f"This email was sent via the AImageLab mailing list to {', '.join(list_addrs)}."
    return "This email was sent via the AImageLab mailing list."


def _build_footer_html(unsubscribe_token, list_addrs=()):
    base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
    if unsubscribe_token:
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        return (
            '<hr style="margin-top:30px;border:none;border-top:1px solid #ddd;">'
            '<p style="font-size:11px;color:#888;margin-top:10px;">'
            f'{_footer_sentence(list_addrs)} '
            'Replies go to the sender only. '
            f'<a href="{unsub_url}">Unsubscribe</a>'
            '</p>'
        )
    return ''


def _build_footer_text(unsubscribe_token, list_addrs=()):
    base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
    if unsubscribe_token:
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        return (
            f"\n\n---\n{_footer_sentence(list_addrs)}\n"
            f"Replies go to the sender only.\n"
            f"Unsubscribe: {unsub_url}\n"
        )
    return ''


# ---------------------------------------------------------------------------
# Moderator notification
# ---------------------------------------------------------------------------

def notify_moderators(incoming_email):
    """Send an email to all moderators about a pending message."""
    from django.contrib.auth.models import User

    moderators = User.objects.filter(is_staff=True, is_active=True)
    if not moderators.exists():
        logger.warning("No moderators found to notify about email %s", incoming_email.pk)
        return

    base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
    review_url = f"{base_url}/mailinglist/moderation/"

    smtp_host = settings.MAILINGLIST_SMTP_HOST
    smtp_port = settings.MAILINGLIST_SMTP_PORT
    smtp_user = settings.MAILINGLIST_EMAIL_ADDRESS
    smtp_pass = settings.MAILINGLIST_EMAIL_PASSWORD
    list_name = getattr(settings, 'MAILINGLIST_FROM_NAME', 'AImageLab Mailing List')

    subject = f"[Moderation Required] {incoming_email.subject}"
    body = (
        f"A new email to the mailing list requires moderation.\n\n"
        f"From: {incoming_email.sender_name} <{incoming_email.sender}>\n"
        f"Subject: {incoming_email.subject}\n"
        f"Received: {incoming_email.received_at}\n\n"
        f"Review it here: {review_url}\n"
    )

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)

        for mod in moderators:
            if not mod.email:
                continue
            msg = MIMEText(body, 'plain')
            msg['From'] = formataddr((list_name, smtp_user))
            msg['To'] = mod.email
            msg['Subject'] = subject
            try:
                server.sendmail(smtp_user, [mod.email], msg.as_string())
            except Exception:
                logger.exception("Failed to notify moderator %s", mod.email)

        server.quit()
    except Exception:
        logger.exception("SMTP error while notifying moderators")
