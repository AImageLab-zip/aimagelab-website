import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class MailingListPreference(models.Model):
    """Per-user mailing list opt-in/out and extra email addresses."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='mailing_preference'
    )
    subscribed = models.BooleanField(
        default=True,
        help_text="Receive emails from the mailing list"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "subscribed" if self.subscribed else "unsubscribed"
        return f"{self.user.get_full_name()} – {status}"


class UserExtraEmail(models.Model):
    """Additional email addresses where a user wants to receive list mail."""
    preference = models.ForeignKey(
        MailingListPreference,
        on_delete=models.CASCADE,
        related_name='extra_emails'
    )
    email = models.EmailField()
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        unique_together = ('preference', 'email')

    def __str__(self):
        return self.email


class ExternalRecipient(models.Model):
    """People who are not system users but want to receive list mail."""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    subscribed = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = self.name or self.email
        status = "subscribed" if self.subscribed else "unsubscribed"
        return f"{label} – {status}"


class SubjectRoleRoute(models.Model):
    """Maps a subject tag like [ailb-all] to a set of recipient roles.

    If ``send_to_external`` is True, external recipients also receive the mail.
    """
    tag = models.CharField(
        max_length=100,
        unique=True,
        help_text="Tag that appears in the email subject, e.g. [ailb-all]"
    )
    description = models.CharField(max_length=255, blank=True)
    roles = models.JSONField(
        default=list,
        help_text="List of role keys that should receive this mail, e.g. ['rector','full_professor']"
    )
    send_to_external = models.BooleanField(
        default=False,
        help_text="Also send to external recipients (non-system users)"
    )

    def __str__(self):
        return self.tag


class IncomingEmail(models.Model):
    """Email received on the list address, pending moderation or already handled."""
    STATUS_CHOICES = [
        ('pending', 'Pending moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('auto_approved', 'Auto-approved'),
    ]

    message_id = models.CharField(max_length=255, unique=True)
    sender = models.EmailField()
    sender_name = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=998)  # RFC 5322 max
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    raw_headers = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='moderated_emails'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    matched_route = models.ForeignKey(
        SubjectRoleRoute, null=True, blank=True, on_delete=models.SET_NULL
    )
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"[{self.status}] {self.subject} (from {self.sender})"


class IncomingEmailAttachment(models.Model):
    """Attachment stored from an incoming email."""
    email = models.ForeignKey(
        IncomingEmail, on_delete=models.CASCADE, related_name='attachments'
    )
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='mailinglist/attachments/%Y/%m/')

    def __str__(self):
        return self.filename


class OutgoingEmail(models.Model):
    """Individual delivery record – one per recipient per incoming mail."""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    incoming = models.ForeignKey(
        IncomingEmail, on_delete=models.CASCADE, related_name='deliveries'
    )
    recipient_email = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"→ {self.recipient_email} [{self.status}]"
