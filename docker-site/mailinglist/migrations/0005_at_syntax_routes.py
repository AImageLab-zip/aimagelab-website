from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglist', '0004_mailinglistpreference_unsubscribe_token'),
    ]

    operations = [
        # 1. Add clean_subject field
        migrations.AddField(
            model_name='incomingemail',
            name='clean_subject',
            field=models.CharField(blank=True, max_length=998),
        ),
        # 2. Populate clean_subject from existing subject for existing rows
        migrations.RunSQL(
            "UPDATE mailinglist_incomingemail SET clean_subject = subject WHERE clean_subject = ''",
            migrations.RunSQL.noop,
        ),
        # 3. Add M2M matched_routes
        migrations.AddField(
            model_name='incomingemail',
            name='matched_routes',
            field=models.ManyToManyField(blank=True, related_name='emails', to='mailinglist.subjectroleroute'),
        ),
        # 4. Populate M2M from existing matched_route FK
        migrations.RunSQL(
            """
            INSERT INTO mailinglist_incomingemail_matched_routes (incomingemail_id, subjectroleroute_id)
            SELECT id, matched_route_id
            FROM mailinglist_incomingemail
            WHERE matched_route_id IS NOT NULL
            """,
            migrations.RunSQL.noop,
        ),
        # 5. Remove old FK
        migrations.RemoveField(
            model_name='incomingemail',
            name='matched_route',
        ),
    ]
