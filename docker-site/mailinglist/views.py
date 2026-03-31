import logging

from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    BlacklistedSender,
    ExternalRecipient,
    IncomingEmail,
    MailingListPreference,
    OutgoingEmail,
    SubjectRoleRoute,
    UserExtraEmail,
    WhitelistedSender,
)
from .services import resolve_recipients, resolve_recipients_for_routes
from .tasks import process_approved_email, send_email_batch

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User preferences (profile integration)
# ---------------------------------------------------------------------------

@login_required
def mailing_preferences(request):
    """Let a user manage their mailing-list subscription and extra emails."""
    pref, _ = MailingListPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_subscription':
            pref.subscribed = request.POST.get('subscribed') == 'on'
            pref.save(update_fields=['subscribed', 'updated_at'])
            django_messages.success(request, 'Mailing list preferences updated.')

        elif action == 'add_email':
            new_email = request.POST.get('extra_email', '').strip().lower()
            if new_email:
                _, created = UserExtraEmail.objects.get_or_create(
                    preference=pref, email=new_email
                )
                if created:
                    django_messages.success(request, f'Added {new_email} to your mailing list emails.')
                else:
                    django_messages.info(request, f'{new_email} is already in your list.')
            else:
                django_messages.warning(request, 'Please enter a valid email address.')

        elif action == 'remove_email':
            email_id = request.POST.get('email_id')
            UserExtraEmail.objects.filter(pk=email_id, preference=pref).delete()
            django_messages.success(request, 'Email removed.')

        return redirect('mailinglist:preferences')

    extra_emails = pref.extra_emails.all()
    return render(request, 'mailinglist/preferences.html', {
        'pref': pref,
        'extra_emails': extra_emails,
    })


# ---------------------------------------------------------------------------
# Moderation (staff only)
# ---------------------------------------------------------------------------

@login_required
def moderation_queue(request):
    """Show pending emails for moderation."""
    if not request.user.is_staff:
        django_messages.error(request, 'You do not have permission to moderate emails.')
        return redirect('dashboard')

    pending = IncomingEmail.objects.filter(status='pending')
    recent = IncomingEmail.objects.exclude(status='pending').order_by('-received_at')[:20]

    return render(request, 'mailinglist/moderation.html', {
        'pending': pending,
        'recent': recent,
    })


@login_required
def moderation_detail(request, email_id):
    """View a single pending email and approve/reject it."""
    if not request.user.is_staff:
        django_messages.error(request, 'You do not have permission to moderate emails.')
        return redirect('dashboard')

    incoming = get_object_or_404(IncomingEmail, pk=email_id)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'approve':
            incoming.status = 'approved'
            incoming.moderated_by = request.user
            incoming.moderated_at = timezone.now()
            incoming.save(update_fields=['status', 'moderated_by', 'moderated_at'])
            # Queue deliveries async
            process_approved_email.delay(incoming.pk)
            django_messages.success(request, f'Email "{incoming.subject}" approved and queued for delivery.')

        elif action == 'reject':
            incoming.status = 'rejected'
            incoming.moderated_by = request.user
            incoming.moderated_at = timezone.now()
            incoming.save(update_fields=['status', 'moderated_by', 'moderated_at'])
            django_messages.info(request, f'Email "{incoming.subject}" has been rejected.')

        elif action == 'blacklist':
            BlacklistedSender.objects.get_or_create(
                email=incoming.sender.lower(),
                defaults={'added_by': request.user, 'reason': 'Blacklisted during moderation'}
            )
            # Update this email and all other pending emails from the same sender
            updated = IncomingEmail.objects.filter(
                sender__iexact=incoming.sender, status='pending'
            ).exclude(pk=incoming.pk).update(
                status='blacklisted',
                moderated_by=request.user,
                moderated_at=timezone.now(),
            )
            incoming.status = 'blacklisted'
            incoming.moderated_by = request.user
            incoming.moderated_at = timezone.now()
            incoming.save(update_fields=['status', 'moderated_by', 'moderated_at'])
            extra = f' ({updated} other pending email(s) from this sender also rejected.)' if updated else ''
            django_messages.warning(request, f'"{incoming.sender}" has been blacklisted. Future emails from this address will be automatically rejected.{extra}')

        elif action == 'whitelist':
            WhitelistedSender.objects.get_or_create(
                email=incoming.sender.lower(),
                defaults={'added_by': request.user, 'reason': 'Whitelisted during moderation'}
            )
            incoming.status = 'approved'
            incoming.moderated_by = request.user
            incoming.moderated_at = timezone.now()
            incoming.save(update_fields=['status', 'moderated_by', 'moderated_at'])
            process_approved_email.delay(incoming.pk)
            django_messages.success(request, f'"{incoming.sender}" has been whitelisted and this email approved. Future emails from this address will be auto-approved.')

        return redirect('mailinglist:moderation')

    deliveries = incoming.deliveries.all()
    recipients = sorted(resolve_recipients(incoming))
    return render(request, 'mailinglist/moderation_detail.html', {
        'email': incoming,
        'deliveries': deliveries,
        'recipients': recipients,
    })


# ---------------------------------------------------------------------------
# Tag recipients API (authenticated users only)
# ---------------------------------------------------------------------------

@login_required
def tag_recipients_api(request):
    """Return the resolved recipient list for a routing tag as JSON.

    Used by the wiki mailing-list page to let members preview who receives
    each group's emails.  Requires login — the list of member emails must
    not be exposed to unauthenticated visitors.
    """
    tag = request.GET.get('tag', '').strip()
    if not tag:
        return JsonResponse({'error': 'Missing tag parameter.'}, status=400)

    try:
        route = SubjectRoleRoute.objects.get(tag=tag)
    except SubjectRoleRoute.DoesNotExist:
        return JsonResponse({'error': f'Unknown tag: {tag}'}, status=404)

    recipients = sorted(resolve_recipients_for_routes([route]))
    return JsonResponse({
        'tag': tag,
        'description': route.description,
        'count': len(recipients),
        'recipients': recipients,
    })


# ---------------------------------------------------------------------------
# Unsubscribe (public, token-based)
# ---------------------------------------------------------------------------

def unsubscribe(request, token):
    """Handle unsubscribe requests via unique UUID token in email footer."""

    # Case 1: UUID token for primary user email (MailingListPreference)
    pref = MailingListPreference.objects.filter(unsubscribe_token=token).first()
    if pref:
        target_label = pref.user.email or pref.user.get_full_name()

        if request.method == 'POST':
            pref.subscribed = False
            pref.save(update_fields=['subscribed', 'updated_at'])
            django_messages.success(request, 'You have been unsubscribed from the mailing list.')
            return render(request, 'mailinglist/unsubscribed.html', {'label': target_label})

        return render(request, 'mailinglist/unsubscribe_confirm.html', {'label': target_label, 'token': token})

    # Case 2: UUID token for extra emails
    extra = UserExtraEmail.objects.filter(unsubscribe_token=token).first()
    if extra:
        target_label = extra.email
        if request.method == 'POST':
            extra.delete()
            django_messages.success(request, f'{target_label} has been removed from the mailing list.')
            return render(request, 'mailinglist/unsubscribed.html', {'label': target_label})
        return render(request, 'mailinglist/unsubscribe_confirm.html', {'label': target_label, 'token': token})

    # Case 3: UUID token for external recipients
    ext = ExternalRecipient.objects.filter(unsubscribe_token=token).first()
    if ext:
        target_label = ext.email
        if request.method == 'POST':
            ext.subscribed = False
            ext.save(update_fields=['subscribed'])
            django_messages.success(request, f'{target_label} has been unsubscribed.')
            return render(request, 'mailinglist/unsubscribed.html', {'label': target_label})
        return render(request, 'mailinglist/unsubscribe_confirm.html', {'label': target_label, 'token': token})

    raise Http404


# ---------------------------------------------------------------------------
# External recipient self-subscription (optional public page)
# ---------------------------------------------------------------------------

def external_subscribe(request):
    """Public form for external people to subscribe to the mailing list."""
    if request.method == 'POST':
        email_addr = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()
        if email_addr:
            obj, created = ExternalRecipient.objects.get_or_create(
                email=email_addr,
                defaults={'name': name, 'subscribed': True},
            )
            if not created and not obj.subscribed:
                obj.subscribed = True
                obj.name = name or obj.name
                obj.save(update_fields=['subscribed', 'name'])
                django_messages.success(request, 'You have been re-subscribed to the mailing list.')
            elif created:
                django_messages.success(request, 'You have been subscribed to the mailing list.')
            else:
                django_messages.info(request, 'You are already subscribed.')
        else:
            django_messages.warning(request, 'Please enter a valid email address.')
        return redirect('mailinglist:external_subscribe')

    return render(request, 'mailinglist/external_subscribe.html')
