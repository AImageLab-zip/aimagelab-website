from django.core.management.base import BaseCommand
from main.models import MeetingRoom


class Command(BaseCommand):
    help = 'Create sample meeting rooms'

    def handle(self, *args, **options):
        rooms = [
            {
                'name': 'Room A',
                'location': 'Building 1, Floor 2',
                'capacity': 8,
                'description': 'Small meeting room with whiteboard and projector',
                'color': '#3B82F6',  # Blue
            },
            {
                'name': 'Room B',
                'location': 'Building 1, Floor 2',
                'capacity': 12,
                'description': 'Medium meeting room with video conferencing',
                'color': '#10B981',  # Green
            },
            {
                'name': 'Room C',
                'location': 'Building 1, Floor 3',
                'capacity': 6,
                'description': 'Small discussion room',
                'color': '#F59E0B',  # Orange
            },
            {
                'name': 'Conference Room',
                'location': 'Building 1, Ground Floor',
                'capacity': 20,
                'description': 'Large conference room with full AV setup',
                'color': '#EF4444',  # Red
            },
            {
                'name': 'Lab Meeting Room',
                'location': 'Building 2, Floor 1',
                'capacity': 10,
                'description': 'Meeting room near the lab area',
                'color': '#8B5CF6',  # Purple
            },
        ]

        created_count = 0
        for room_data in rooms:
            room, created = MeetingRoom.objects.get_or_create(
                name=room_data['name'],
                defaults=room_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created room: {room.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Room already exists: {room.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nCreated {created_count} new meeting rooms')
        )
