"""
Migration: switch routing from @ailb- subject tags to plus-addressing.

Convert existing tag values: strip the ``@ailb-`` prefix.
"""
from django.db import migrations


def convert_tags_forward(apps, schema_editor):
    SubjectRoleRoute = apps.get_model('mailinglist', 'SubjectRoleRoute')
    for route in SubjectRoleRoute.objects.all():
        old_tag = route.tag
        if old_tag.lower().startswith('@ailb-'):
            route.tag = old_tag[6:]  # strip '@ailb-'
            route.save(update_fields=['tag'])


def convert_tags_backward(apps, schema_editor):
    SubjectRoleRoute = apps.get_model('mailinglist', 'SubjectRoleRoute')
    for route in SubjectRoleRoute.objects.all():
        if not route.tag.startswith('@ailb-'):
            route.tag = f'@ailb-{route.tag}'
            route.save(update_fields=['tag'])


class Migration(migrations.Migration):

    dependencies = [
        ('mailinglist', '0005_at_syntax_routes'),
    ]

    operations = [
        migrations.RunPython(convert_tags_forward, convert_tags_backward),
    ]
