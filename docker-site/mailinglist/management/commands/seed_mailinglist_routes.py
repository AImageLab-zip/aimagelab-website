"""
Seed the default SubjectRoleRoute entries.
Usage: python manage.py seed_mailinglist_routes
"""
from django.core.management.base import BaseCommand
from mailinglist.models import SubjectRoleRoute


DEFAULT_ROUTES = [
    {
        'tag': '[ailb-all]',
        'description': 'All mailing list recipients (users + external)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
            'postdoc', 'secretariat_staff', 'research_fellow',
            'collaborator', 'phd', 'intern', 'alumni', 'past_member', 'guest',
        ],
        'send_to_external': True,
    },
    {
        'tag': '[ailb-strutturati]',
        'description': 'Structured staff only (professors, researchers)',
        'roles': [
            'rector', 'full_professor', 'assoc_professor',
            'researcher_tt', 'researcher_a', 'researcher_b',
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
