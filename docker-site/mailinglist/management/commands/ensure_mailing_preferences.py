"""
Ensure all existing users have a MailingListPreference record.
Usage: python manage.py ensure_mailing_preferences
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from mailinglist.models import MailingListPreference


class Command(BaseCommand):
    help = 'Create MailingListPreference for all existing users that lack one'

    def handle(self, *args, **options):
        users_without = User.objects.exclude(
            mailing_preference__isnull=False
        )
        count = 0
        for user in users_without:
            MailingListPreference.objects.get_or_create(user=user)
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Created {count} mailing preference(s).'))
