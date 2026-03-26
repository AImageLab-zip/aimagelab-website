"""
Fix duplicate OutgoingEmail records and prevent future duplicates.

- Removes duplicate (incoming, recipient_email) pairs, keeping the most
  advanced delivery record (sent > failed > queued).
- Adds a unique_together constraint so bulk_create(ignore_conflicts=True)
  in queue_deliveries() is actually effective.
- Adds the 'sending' intermediate status (CharField choices only, no schema
  change needed, but included here for completeness).
"""
from django.db import migrations, models


def deduplicate_outgoing_emails(apps, schema_editor):
    OutgoingEmail = apps.get_model('mailinglist', 'OutgoingEmail')
    # Status priority: sent (best) > failed > sending > queued (worst)
    status_priority = {'sent': 0, 'failed': 1, 'sending': 2, 'queued': 3}

    seen = {}  # (incoming_id, recipient_email) -> best OutgoingEmail id
    to_delete = []

    for delivery in OutgoingEmail.objects.order_by('id'):
        key = (delivery.incoming_id, delivery.recipient_email.lower())
        if key not in seen:
            seen[key] = delivery
        else:
            existing = seen[key]
            existing_priority = status_priority.get(existing.status, 99)
            current_priority = status_priority.get(delivery.status, 99)
            if current_priority < existing_priority:
                # Current is better; delete the previous winner
                to_delete.append(existing.id)
                seen[key] = delivery
            else:
                to_delete.append(delivery.id)

    if to_delete:
        OutgoingEmail.objects.filter(id__in=to_delete).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglist', '0007_alter_subjectroleroute_roles_and_more'),
    ]

    operations = [
        migrations.RunPython(deduplicate_outgoing_emails, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='outgoingemail',
            name='status',
            field=models.CharField(
                choices=[
                    ('queued', 'Queued'),
                    ('sending', 'Sending'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                ],
                default='queued',
                max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='outgoingemail',
            unique_together={('incoming', 'recipient_email')},
        ),
    ]
