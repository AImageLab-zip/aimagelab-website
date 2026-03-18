from django.contrib import admin
from .models import (
    ExternalRecipient,
    IncomingEmail,
    IncomingEmailAttachment,
    MailingListPreference,
    OutgoingEmail,
    SubjectRoleRoute,
    UserExtraEmail,
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
    list_display = ('subject', 'sender', 'status', 'matched_route', 'received_at')
    list_filter = ('status', 'matched_route')
    search_fields = ('subject', 'sender', 'sender_name')
    readonly_fields = ('message_id', 'received_at')
    inlines = [IncomingEmailAttachmentInline]

    actions = ['approve_emails', 'reject_emails']

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


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'incoming', 'status', 'sent_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('recipient_email', 'incoming__subject')
    readonly_fields = ('created_at', 'sent_at')
