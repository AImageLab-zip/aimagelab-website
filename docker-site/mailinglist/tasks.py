"""
Celery tasks for the mailing list app.

- fetch_incoming_emails: polls IMAP for new messages (runs every few minutes)
- process_approved_email: queues deliveries and starts progressive sending
- send_email_batch: sends a batch of queued outgoing emails
- send_moderator_notifications: notifies moderators of pending emails
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_incoming_emails(self):
    """Poll IMAP inbox for new emails and persist them."""
    from .services import fetch_new_emails, queue_deliveries, notify_moderators
    from .models import IncomingEmail

    try:
        new_ids = fetch_new_emails()
        logger.info("Fetched %d new email(s)", len(new_ids))

        for email_id in new_ids:
            incoming = IncomingEmail.objects.get(pk=email_id)
            if incoming.status == 'auto_approved':
                # Trusted sender → queue immediately
                count = queue_deliveries(incoming)
                logger.info("Auto-approved email %s – queued %d deliveries", incoming.pk, count)
                # Trigger progressive sending
                send_email_batch.delay()
            elif incoming.status == 'pending':
                # Needs moderation → notify moderators
                send_moderator_notification.delay(incoming.pk)
    except Exception as exc:
        logger.exception("Error in fetch_incoming_emails")
        raise self.retry(exc=exc)


@shared_task
def process_approved_email(incoming_email_id):
    """Queue deliveries for an approved email and start sending."""
    from .services import queue_deliveries
    from .models import IncomingEmail

    try:
        incoming = IncomingEmail.objects.get(pk=incoming_email_id)
        if incoming.status not in ('approved', 'auto_approved'):
            logger.warning("Email %s is not approved (status=%s), skipping", incoming.pk, incoming.status)
            return

        count = queue_deliveries(incoming)
        logger.info("Queued %d deliveries for email %s", count, incoming.pk)

        # Trigger batched sending
        send_email_batch.delay()
    except IncomingEmail.DoesNotExist:
        logger.error("IncomingEmail %s does not exist", incoming_email_id)


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_email_batch(self):
    """Send a batch of queued outgoing emails.

    If there are still queued emails after this batch, re-schedule itself
    with a small delay to implement progressive sending.
    """
    from .services import send_batch
    from .models import OutgoingEmail

    try:
        sent = send_batch()
        logger.info("Sent %d email(s) in this batch", sent)

        remaining = OutgoingEmail.objects.filter(status='queued').count()
        if remaining > 0:
            # Schedule the next batch with a delay to spread the load
            send_email_batch.apply_async(countdown=10)
            logger.info("%d email(s) still queued, next batch in 10s", remaining)
    except Exception as exc:
        logger.exception("Error sending email batch")
        raise self.retry(exc=exc)


@shared_task
def send_moderator_notification(incoming_email_id):
    """Notify moderators about a pending email."""
    from .services import notify_moderators
    from .models import IncomingEmail

    try:
        incoming = IncomingEmail.objects.get(pk=incoming_email_id)
        notify_moderators(incoming)
    except IncomingEmail.DoesNotExist:
        logger.error("IncomingEmail %s does not exist", incoming_email_id)
