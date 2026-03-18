"""
Celery configuration for myproject.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'import-iris-publications-daily': {
        'task': 'main.tasks.import_iris_publications',
        'schedule': crontab(hour=0, minute=0),  # Run every day at 00:00
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    'fetch-mailinglist-emails': {
        'task': 'mailinglist.tasks.fetch_incoming_emails',
        'schedule': crontab(minute='*/3'),  # Every 3 minutes
        'options': {
            'expires': 150,  # Expire before next run
        }
    },
}

# Set timezone for beat scheduler
app.conf.timezone = 'Europe/Rome'  # Adjust to your timezone


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

