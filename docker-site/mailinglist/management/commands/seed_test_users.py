"""
Create sample users covering every role for local testing of the mailing list
tag mechanism.  Safe to run multiple times (uses get_or_create).

Usage:
    python manage.py seed_test_users
    python manage.py seed_test_users --clear  # delete test users first
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from main.models import UserProfile
from mailinglist.models import MailingListPreference


# One sample user per relevant role, matching production role keys.
# The email field determines which real inbox would receive the forwarded
# mail, so we use @example.com addresses that go nowhere but are distinct.
TEST_USERS = [
    {
        'username': 'test.rector',
        'first_name': 'Rita',
        'last_name': 'Rettore',
        'email': 'test.rector@example.com',
        'role': 'rector',
    },
    {
        'username': 'test.fullprofessor',
        'first_name': 'Franco',
        'last_name': 'Fulloni',
        'email': 'test.fullprofessor@example.com',
        'role': 'full_professor',
    },
    {
        'username': 'test.assocprofessor',
        'first_name': 'Anna',
        'last_name': 'Associati',
        'email': 'test.assocprofessor@example.com',
        'role': 'assoc_professor',
    },
    {
        'username': 'test.researcher_tt',
        'first_name': 'Roberto',
        'last_name': 'Rettini',
        'email': 'test.researcher_tt@example.com',
        'role': 'researcher_tt',
    },
    {
        'username': 'test.researcher_a',
        'first_name': 'Alice',
        'last_name': 'Rossia',
        'email': 'test.researcher_a@example.com',
        'role': 'researcher_a',
    },
    {
        'username': 'test.researcher_b',
        'first_name': 'Bruno',
        'last_name': 'Rossib',
        'email': 'test.researcher_b@example.com',
        'role': 'researcher_b',
    },
    {
        'username': 'test.postdoc',
        'first_name': 'Paolo',
        'last_name': 'Postdoci',
        'email': 'test.postdoc@example.com',
        'role': 'postdoc',
    },
    {
        'username': 'test.secretariat',
        'first_name': 'Sara',
        'last_name': 'Segreteria',
        'email': 'test.secretariat@example.com',
        'role': 'secretariat_staff',
    },
    {
        'username': 'test.fellow',
        'first_name': 'Fabio',
        'last_name': 'Fellowini',
        'email': 'test.fellow@example.com',
        'role': 'research_fellow',
    },
    {
        'username': 'test.collaborator',
        'first_name': 'Carlo',
        'last_name': 'Collaboroni',
        'email': 'test.collaborator@example.com',
        'role': 'collaborator',
    },
    {
        'username': 'test.phd',
        'first_name': 'Dora',
        'last_name': 'Dottoranda',
        'email': 'test.phd@example.com',
        'role': 'phd',
    },
    {
        'username': 'test.intern',
        'first_name': 'Irene',
        'last_name': 'Internini',
        'email': 'test.intern@example.com',
        'role': 'intern',
    },
    {
        'username': 'test.guest',
        'first_name': 'Giorgio',
        'last_name': 'Guestini',
        'email': 'test.guest@example.com',
        'role': 'guest',
    },
    # Alumni / past members are intentionally excluded from @ailb-all in the
    # current production routes, so add one to verify they are NOT reached.
    {
        'username': 'test.alumni',
        'first_name': 'Alessia',
        'last_name': 'Alumnetti',
        'email': 'test.alumni@example.com',
        'role': 'alumni',
    },
]


class Command(BaseCommand):
    help = 'Seed test users (one per role) for mailing list tag mechanism testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing test users before recreating them',
        )

    def handle(self, *args, **options):
        if options['clear']:
            usernames = [u['username'] for u in TEST_USERS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(f'Deleted {deleted} existing test user(s).')

        created_count = 0
        updated_count = 0

        for data in TEST_USERS:
            user, user_created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'is_active': True,
                },
            )
            if not user_created:
                # Keep email up to date in case it changed
                user.email = data['email']
                user.is_active = True
                user.save(update_fields=['email', 'is_active'])

            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': data['role']},
            )
            if profile.role != data['role']:
                profile.role = data['role']
                profile.save(update_fields=['role'])

            MailingListPreference.objects.get_or_create(
                user=user,
                defaults={'subscribed': True},
            )

            if user_created:
                created_count += 1
                self.stdout.write(f'  Created : {user.username} ({data["role"]}) → {user.email}')
            else:
                updated_count += 1
                self.stdout.write(f'  Verified: {user.username} ({data["role"]}) → {user.email}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {created_count} created, {updated_count} already existed.'
            )
        )
        self.stdout.write('')
        self.stdout.write('Quick reference — which users each tag should reach:')
        self.stdout.write('  @ailb-all          → all active members + external recipients')
        self.stdout.write('  @ailb-active        → all active members, no external  (default when no tag)')
        self.stdout.write('  @ailb-esterni       → external recipients only')
        self.stdout.write('  @ailb-strutturati  → rector, full/assoc professor, RTT/RTD-A/RTD-B')
        self.stdout.write('  @ailb-docenti      → rector, full professor, assoc professor')
        self.stdout.write('  @ailb-dottorandi   → PhD students only')
        self.stdout.write('  @ailb-postdocs     → postdoctoral researchers only')
        self.stdout.write('  @ailb-staff        → secretariat_staff only')
        self.stdout.write('')
        self.stdout.write('Note: test.alumni is intentionally excluded from @ailb-active/@ailb-all.')
        self.stdout.write('')
        self.stdout.write('Send a test email with one of these tags in the subject, e.g.:')
        self.stdout.write('  Subject: @ailb-dottorandi Weekly meeting reminder')
        self.stdout.write('  Subject: @ailb-strutturati @ailb-staff Department notice')
