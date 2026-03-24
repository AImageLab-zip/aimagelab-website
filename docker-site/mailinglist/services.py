"""
Service layer for the mailing list app.

Handles:
- Fetching mail from Gmail via IMAP
- Resolving recipients based on subject-role routing
- Progressive sending via SMTP
"""
import email
import imaplib
import logging
import re
import smtplib
from email import policy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr

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
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw, policy=policy.default)
            incoming = _persist_email(msg, raw)
            if incoming:
                created_ids.append(incoming.id)
        mail.logout()
    except Exception:
        logger.exception("Error fetching emails via IMAP")
    return created_ids


def _persist_email(msg, raw_bytes):
    """Parse an email.message.Message and save as IncomingEmail."""
    message_id = msg.get('Message-ID', '')
    if not message_id:
        message_id = f"no-id-{timezone.now().timestamp()}"

    if IncomingEmail.objects.filter(message_id=message_id).exists():
        return None

    sender = msg.get('From', '')
    sender_name = ''
    # Extract name and email from "Name <email>" format
    if '<' in sender:
        sender_name = sender.split('<')[0].strip().strip('"')
        sender = sender.split('<')[1].rstrip('>')

    subject = msg.get('Subject', '(no subject)')

    body_text = ''
    body_html = ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/plain' and not body_text:
                body_text = part.get_content()
            elif ct == 'text/html' and not body_html:
                body_html = part.get_content()
    else:
        ct = msg.get_content_type()
        if ct == 'text/html':
            body_html = msg.get_content()
        else:
            body_text = msg.get_content()

    # Determine auto-approval: check blacklist, then whitelist, then trusted domains
    sender_lower = sender.lower()
    if BlacklistedSender.objects.filter(email__iexact=sender_lower).exists():
        logger.info("Rejecting email from blacklisted sender %s", sender)
        routes, clean_subject = _match_routes(subject)
        incoming = IncomingEmail.objects.create(
            message_id=message_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            clean_subject=clean_subject,
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

    # Match route
    routes, clean_subject = _match_routes(subject)

    incoming = IncomingEmail.objects.create(
        message_id=message_id,
        sender=sender,
        sender_name=sender_name,
        subject=subject,
        clean_subject=clean_subject,
        body_text=body_text,
        body_html=body_html,
        raw_headers=str(msg.items()),
        status='auto_approved' if is_trusted else 'pending',
    )
    incoming.matched_routes.set(routes)

    # Save attachments
    if msg.is_multipart():
        for part in msg.walk():
            disposition = part.get('Content-Disposition', '')
            if 'attachment' in disposition or 'inline' in disposition:
                filename = part.get_filename() or 'unnamed'
                content = part.get_payload(decode=True)
                if content:
                    att = IncomingEmailAttachment(
                        email=incoming,
                        filename=filename,
                        content_type=part.get_content_type(),
                    )
                    att.file.save(filename, ContentFile(content), save=False)
                    att.save()

    return incoming


def _match_routes(subject):
    """Find all SubjectRoleRoutes whose @ailb-<tag> appears in the subject.

    Tags are matched case-insensitively anywhere in the subject.
    Returns (routes queryset, clean_subject) where clean_subject has all
    matched tags stripped and extra whitespace collapsed.
    """
    import re
    all_routes = list(SubjectRoleRoute.objects.all())
    matched = []
    clean = subject
    for route in all_routes:
        # Escape the tag and match it as a whole word preceded by @
        pattern = re.compile(re.escape(route.tag), re.IGNORECASE)
        if pattern.search(subject):
            matched.append(route)
            clean = pattern.sub('', clean)
    # Collapse multiple spaces left by removed tags
    clean = re.sub(r'\s{2,}', ' ', clean).strip()
    return matched, clean


# ---------------------------------------------------------------------------
# Recipient resolution
# ---------------------------------------------------------------------------

def resolve_recipients(incoming_email):
    """Return a deduplicated set of email addresses for delivery.

    Rules:
    - If routes matched, send to the union of users matching any route's roles
      (plus external recipients if any route allows it).
    - If no routes matched, send to all subscribed active users + external.
    - Respect per-user subscription preferences.
    """
    addresses = set()
    routes = list(incoming_email.matched_routes.all())

    if routes:
        # Union of all roles across matched routes
        target_roles = set()
        send_external = False
        for route in routes:
            target_roles.update(route.roles or [])
            if route.send_to_external:
                send_external = True

        users = User.objects.filter(
            is_active=True,
            profile__role__in=target_roles,
            mailing_preference__subscribed=True,
        ).select_related('profile', 'mailing_preference')
    else:
        # No route → behave like @ailb-active: all active members, no external
        send_external = False
        active_roles = [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
            'postdoc', 'secretariat_staff', 'research_fellow',
            'collaborator', 'phd', 'intern', 'guest',
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

    # Never send back to the list address itself
    list_addr = getattr(settings, 'MAILINGLIST_EMAIL_ADDRESS', '').lower()
    addresses.discard(list_addr)

    return addresses


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

    queued = OutgoingEmail.objects.filter(status='queued').select_related(
        'incoming'
    ).order_by('created_at')[:batch_size]

    if not queued:
        return 0

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
    # Use clean_subject (tags stripped) for the forwarded email
    msg['Subject'] = incoming.clean_subject or incoming.subject
    # Reply-To points to the original sender so replies go back to them,
    # not to the mailing list inbox.
    msg['Reply-To'] = formataddr((sender_display, incoming.sender))
    if incoming.message_id:
        msg['References'] = incoming.message_id

    # Unsubscribe header (RFC 8058)
    unsubscribe_token = _get_unsubscribe_token(delivery.recipient_email)
    if unsubscribe_token:
        base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        msg['List-Unsubscribe'] = f"<{unsub_url}>"
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

    # Body — wrap text+html in multipart/alternative so clients pick one,
    # not render both.
    footer_html = _build_footer_html(unsubscribe_token)
    footer_text = _build_footer_text(unsubscribe_token)

    if incoming.body_html or incoming.body_text:
        alt = MIMEMultipart('alternative')
        # plain text first (lowest preference)
        plain = incoming.body_text + footer_text if incoming.body_text else ''
        alt.attach(MIMEText(plain, 'plain'))
        # html second (highest preference — clients pick this when supported)
        if incoming.body_html:
            html_content = incoming.body_html
            if '</body>' in html_content.lower():
                html_content = html_content.replace('</body>', footer_html + '</body>')
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


def _build_footer_html(unsubscribe_token):
    base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
    if unsubscribe_token:
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        return (
            '<hr style="margin-top:30px;border:none;border-top:1px solid #ddd;">'
            '<p style="font-size:11px;color:#888;margin-top:10px;">'
            'This email was sent via the AImageLab mailing list. '
            f'<a href="{unsub_url}">Unsubscribe</a>'
            '</p>'
        )
    return ''


def _build_footer_text(unsubscribe_token):
    base_url = getattr(settings, 'MAILINGLIST_BASE_URL', 'https://aimagelab.unimore.it')
    if unsubscribe_token:
        unsub_url = f"{base_url}/mailinglist/unsubscribe/{unsubscribe_token}/"
        return (
            f"\n\n---\nThis email was sent via the AImageLab mailing list.\n"
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
