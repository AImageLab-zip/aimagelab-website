import uuid
from django.db import migrations, models


def populate_unsubscribe_tokens(apps, schema_editor):
    MailingListPreference = apps.get_model('mailinglist', 'MailingListPreference')
    for pref in MailingListPreference.objects.all():
        pref.unsubscribe_token = uuid.uuid4()
        pref.save(update_fields=['unsubscribe_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglist', '0003_blacklist_whitelist'),
    ]

    operations = [
        # Step 1: add the field as non-unique with a temporary default
        migrations.AddField(
            model_name='mailinglistpreference',
            name='unsubscribe_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        # Step 2: populate unique values for existing rows
        migrations.RunPython(populate_unsubscribe_tokens, migrations.RunPython.noop),
        # Step 3: enforce uniqueness now that all rows have distinct values
        migrations.AlterField(
            model_name='mailinglistpreference',
            name='unsubscribe_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
