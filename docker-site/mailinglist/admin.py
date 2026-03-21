from django.contrib import admin
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


class UserExtraEmailInline(admin.TabularInline):
    model = UserExtraEmail
    extra = 0
    readonly_fields = ('unsubscribe_token',)


@admin.register(MailingListPreference)
class MailingListPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed', 'updated_at')
    list_filter = ('subscribed',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    inlines = [UserExtraEmailInline]


@admin.register(ExternalRecipient)
class ExternalRecipientAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'subscribed', 'created_at')
    list_filter = ('subscribed',)
    search_fields = ('email', 'name')
    readonly_fields = ('unsubscribe_token',)


@admin.register(SubjectRoleRoute)
class SubjectRoleRouteAdmin(admin.ModelAdmin):
    list_display = ('tag', 'description', 'send_to_external')
    search_fields = ('tag', 'description')


class IncomingEmailAttachmentInline(admin.TabularInline):
    model = IncomingEmailAttachment
    extra = 0
    readonly_fields = ('filename', 'content_type', 'file')


@admin.register(IncomingEmail)
class IncomingEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'status', 'get_routes', 'received_at')
    list_filter = ('status',)
    search_fields = ('subject', 'sender', 'sender_name')
    readonly_fields = ('message_id', 'received_at')
    inlines = [IncomingEmailAttachmentInline]

    @admin.display(description='Routes')
    def get_routes(self, obj):
        return ', '.join(r.tag for r in obj.matched_routes.all()) or '—'

    actions = ['approve_emails', 'reject_emails', 'blacklist_senders']

    @admin.action(description="Approve selected emails")
    def approve_emails(self, request, queryset):
        from .tasks import process_approved_email
        from django.utils import timezone
        count = 0
        for email_obj in queryset.filter(status='pending'):
            email_obj.status = 'approved'
            email_obj.moderated_by = request.user
            email_obj.moderated_at = timezone.now()
            email_obj.save(update_fields=['status', 'moderated_by', 'moderated_at'])
            process_approved_email.delay(email_obj.pk)
            count += 1
        self.message_user(request, f"{count} email(s) approved and queued.")

    @admin.action(description="Reject selected emails")
    def reject_emails(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(
            status='rejected',
            moderated_by=request.user,
            moderated_at=timezone.now(),
        )
        self.message_user(request, f"{count} email(s) rejected.")

    @admin.action(description="Blacklist sender and reject email")
    def blacklist_senders(self, request, queryset):
        from django.utils import timezone
        count = 0
        for email_obj in queryset:
            BlacklistedSender.objects.get_or_create(
                email=email_obj.sender.lower(),
                defaults={'added_by': request.user, 'reason': 'Blacklisted via admin moderation'}
            )
            # Bulk-reject all pending emails from this sender
            IncomingEmail.objects.filter(
                sender__iexact=email_obj.sender, status='pending'
            ).update(
                status='blacklisted',
                moderated_by=request.user,
                moderated_at=timezone.now(),
            )
            count += 1
        self.message_user(request, f"{count} sender(s) blacklisted and all their pending emails rejected.")


@admin.register(BlacklistedSender)
class BlacklistedSenderAdmin(admin.ModelAdmin):
    list_display = ('email', 'reason', 'added_by', 'added_at')
    search_fields = ('email', 'reason')
    readonly_fields = ('added_at',)


@admin.register(WhitelistedSender)
class WhitelistedSenderAdmin(admin.ModelAdmin):
    list_display = ('email', 'reason', 'added_by', 'added_at')
    search_fields = ('email', 'reason')
    readonly_fields = ('added_at',)


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'incoming', 'status', 'sent_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('recipient_email', 'incoming__subject')
    readonly_fields = ('created_at', 'sent_at')
