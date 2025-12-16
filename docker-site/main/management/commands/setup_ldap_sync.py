"""
Management command to setup periodic LDAP synchronization task.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.conf import settings
import json


class Command(BaseCommand):
    help = 'Setup periodic LDAP synchronization task'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hour',
            type=int,
            default=None,
            help='Hour to run the sync (0-23). Default from settings or 2 AM.'
        )
        parser.add_argument(
            '--minute',
            type=int,
            default=None,
            help='Minute to run the sync (0-59). Default from settings or 0.'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable the periodic task'
        )

    def handle(self, *args, **options):
        # Get schedule time from options or settings
        schedule_hour = options['hour'] if options['hour'] is not None else getattr(settings, 'LDAP_SYNC_HOUR', 2)
        schedule_minute = options['minute'] if options['minute'] is not None else getattr(settings, 'LDAP_SYNC_MINUTE', 0)
        
        # Validate
        if not (0 <= schedule_hour <= 23):
            self.stdout.write(self.style.ERROR('Hour must be between 0 and 23'))
            return
        
        if not (0 <= schedule_minute <= 59):
            self.stdout.write(self.style.ERROR('Minute must be between 0 and 59'))
            return
        
        # Create or get the crontab schedule (daily at specified time)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(schedule_minute),
            hour=str(schedule_hour),
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Created schedule: Daily at {schedule_hour:02d}:{schedule_minute:02d}'
            ))
        
        # Create or update the periodic task
        task_name = 'Daily LDAP User Sync'
        task, task_created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'crontab': schedule,
                'task': 'main.tasks.populate_users_from_ldap',
                'args': json.dumps([]),
                'kwargs': json.dumps({}),
                'enabled': not options['disable'],
            }
        )
        
        if task_created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created periodic task "{task_name}"'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Updated periodic task "{task_name}"'
            ))
        
        status = 'disabled' if options['disable'] else 'enabled'
        self.stdout.write(self.style.SUCCESS(
            f'Task is {status} and will run daily at {schedule_hour:02d}:{schedule_minute:02d}'
        ))
