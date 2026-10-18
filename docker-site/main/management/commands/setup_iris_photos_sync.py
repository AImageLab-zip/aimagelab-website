"""
Management command to set up the periodic IRIS profile-photo import.

Mirrors setup_ldap_sync so both schedules are created the same way, from
code, on every container start - rather than existing only as a row someone
once added in the admin.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.conf import settings
import json

TASK_NAME = 'Daily IRIS Profile Photos Import'
TASK_PATH = 'main.tasks.import_iris_profile_photos'


class Command(BaseCommand):
    help = 'Setup the periodic IRIS profile photo import task'

    def add_arguments(self, parser):
        parser.add_argument('--hour', type=int, default=None,
                            help='Hour to run (0-23). Default from settings or 3 AM.')
        parser.add_argument('--minute', type=int, default=None,
                            help='Minute to run (0-59). Default from settings or 0.')
        parser.add_argument('--disable', action='store_true',
                            help='Disable the periodic task')

    def handle(self, *args, **options):
        hour = options['hour'] if options['hour'] is not None else getattr(
            settings, 'IRIS_PHOTOS_SYNC_HOUR', 3)
        minute = options['minute'] if options['minute'] is not None else getattr(
            settings, 'IRIS_PHOTOS_SYNC_MINUTE', 0)

        if not (0 <= hour <= 23):
            self.stdout.write(self.style.ERROR('Hour must be between 0 and 23'))
            return
        if not (0 <= minute <= 59):
            self.stdout.write(self.style.ERROR('Minute must be between 0 and 59'))
            return

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=str(minute), hour=str(hour),
            day_of_week='*', day_of_month='*', month_of_year='*',
        )

        task, created = PeriodicTask.objects.update_or_create(
            name=TASK_NAME,
            defaults={
                'crontab': schedule,
                'task': TASK_PATH,
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': not options['disable'],
            },
        )

        verb = 'Created' if created else 'Updated'
        state = 'disabled' if options['disable'] else 'enabled'
        self.stdout.write(self.style.SUCCESS(
            f'✓ {verb} periodic task "{TASK_NAME}" - {state}, daily at {hour:02d}:{minute:02d}'
        ))
