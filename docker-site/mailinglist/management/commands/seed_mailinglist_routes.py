"""
Seed the default SubjectRoleRoute entries.
Usage: python manage.py seed_mailinglist_routes
"""
from django.core.management.base import BaseCommand
from mailinglist.models import SubjectRoleRoute


# Current active roles — all profile roles except past_member.
ACTIVE_ROLES = [
    'rector', 'full_professor', 'assoc_professor',
    'researcher_tt', 'researcher_a', 'researcher_b',
    'postdoc', 'secretariat_staff', 'research_fellow',
    'collaborator', 'phd', 'intern',
]

DEFAULT_ROUTES = [
    {
        'tag': 'all',
        'description': 'All active members + past members + external recipients',
        'roles': ACTIVE_ROLES + ['past_member'],
        'send_to_external': True,
    },
    {
        'tag': 'default',
        'description': 'All active lab members (no past members, no externals) — used when no suffix is specified',
        'roles': ACTIVE_ROLES,
        'send_to_external': False,
    },
    {
        'tag': 'past',
        'description': 'Past lab members only',
        'roles': ['past_member'],
        'send_to_external': False,
    },
    {
        'tag': 'esterni',
        'description': 'External recipients only (no internal users)',
        'roles': [],
        'send_to_external': True,
    },
    {
        'tag': 'strutturati',
        'description': 'Structured staff (rector, professors, RTT/RTD-A/RTD-B researchers)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
        ],
        'send_to_external': False,
    },
    {
        'tag': 'proff',
        'description': 'Professors (rector, full and associate professors)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
        ],
        'send_to_external': False,
    },
    {
        'tag': 'dottorandi',
        'description': 'PhD students only',
        'roles': ['phd'],
        'send_to_external': False,
    },
    {
        'tag': 'non-strutturati',
        'description': 'Non-structured members (research fellows, collaborators, interns, PhD students)',
        'roles': ['research_fellow', 'collaborator', 'intern', 'phd'],
        'send_to_external': False,
    },
    {
        'tag': 'staff',
        'description': 'Secretariat and administrative staff',
        'roles': ['secretariat_staff'],
        'send_to_external': False,
    },
    {
        'tag': 'admin',
        'description': 'Site administrators (Django staff users)',
        'roles': ['__admin__'],
        'send_to_external': False,
    },
]

# Tags that have been retired and should be removed from the database.
OBSOLETE_TAGS = ['active', 'docenti', 'postdocs']


class Command(BaseCommand):
    help = 'Create or update default subject-role routing rules for the mailing list'

    def handle(self, *args, **options):
        # Remove obsolete routes
        deleted, _ = SubjectRoleRoute.objects.filter(tag__in=OBSOLETE_TAGS).delete()
        if deleted:
            self.stdout.write(self.style.WARNING(
                f'Removed {deleted} obsolete route(s): {", ".join(OBSOLETE_TAGS)}'
            ))

        # Upsert current routes
        for route_data in DEFAULT_ROUTES:
            obj, created = SubjectRoleRoute.objects.update_or_create(
                tag=route_data['tag'],
                defaults={
                    'description': route_data['description'],
                    'roles': route_data['roles'],
                    'send_to_external': route_data['send_to_external'],
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action}: {obj.tag}')

        self.stdout.write(self.style.SUCCESS('Done.'))
