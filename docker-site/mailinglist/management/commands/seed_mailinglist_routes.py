"""
Seed the default SubjectRoleRoute entries.
Usage: python manage.py seed_mailinglist_routes
"""
from django.core.management.base import BaseCommand
from mailinglist.models import SubjectRoleRoute


# Roles considered "active" lab members (excludes alumni and past members).
ACTIVE_ROLES = [
    'rector', 'full_professor', 'assoc_professor',
    'researcher_tt', 'researcher_a', 'researcher_b',
    'postdoc', 'secretariat_staff', 'research_fellow',
    'collaborator', 'phd', 'intern', 'guest',
]

DEFAULT_ROUTES = [
    {
        'tag': '@ailb-all',
        'description': 'All active lab members + external recipients',
        'roles': ACTIVE_ROLES,
        'send_to_external': True,
    },
    {
        'tag': '@ailb-active',
        'description': 'All active lab members (no external) — default when no tag is used',
        'roles': ACTIVE_ROLES,
        'send_to_external': False,
    },
    {
        'tag': '@ailb-esterni',
        'description': 'External recipients only (no internal users)',
        'roles': [],
        'send_to_external': True,
    },
    {
        'tag': '@ailb-strutturati',
        'description': 'Structured staff only (rector, professors, RTT/RTD researchers)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
        ],
        'send_to_external': False,
    },
    {
        'tag': '@ailb-docenti',
        'description': 'Professors only (rector, full and associate professors)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
        ],
        'send_to_external': False,
    },
    {
        'tag': '@ailb-dottorandi',
        'description': 'PhD students only',
        'roles': [
            'phd',
        ],
        'send_to_external': False,
    },
    {
        'tag': '@ailb-postdocs',
        'description': 'Postdoctoral researchers only',
        'roles': [
            'postdoc',
        ],
        'send_to_external': False,
    },
    {
        'tag': '@ailb-staff',
        'description': 'Secretariat and administrative staff',
        'roles': [
            'secretariat_staff',
        ],
        'send_to_external': False,
    },
]


class Command(BaseCommand):
    help = 'Create default subject-role routing rules for the mailing list'

    def handle(self, *args, **options):
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
