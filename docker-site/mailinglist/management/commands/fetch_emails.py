"""
Management command to manually fetch and process incoming emails.
Usage: python manage.py fetch_emails
"""
from django.core.management.base import BaseCommand
from mailinglist.tasks import fetch_incoming_emails


class Command(BaseCommand):
    help = 'Fetch new emails from the mailing list inbox and process them'

    def handle(self, *args, **options):
        self.stdout.write('Fetching emails...')
        fetch_incoming_emails()
        self.stdout.write(self.style.SUCCESS('Done.'))
