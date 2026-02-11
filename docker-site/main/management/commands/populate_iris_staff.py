"""
Management command to populate staff members with IRIS IDs for testing.
"""
from django.core.management.base import BaseCommand
from main.models import Staff


class Command(BaseCommand):
    help = 'Populate staff members with IRIS IDs from the old system'

    def handle(self, *args, **options):
        """Create sample staff members"""
        
        sample_staff = [
            {'nome': 'Costantino', 'cognome': 'Grana', 'id_iris': 65510},
            {'nome': 'Federico', 'cognome': 'Bolelli', 'id_iris': 114470},
            {'nome': 'Simone', 'cognome': 'Calderara', 'id_iris': 69712},
        ]
        
        created_count = 0
        updated_count = 0
        
        for staff_data in sample_staff:
            staff, created = Staff.objects.update_or_create(
                id_iris=staff_data['id_iris'],
                defaults={
                    'nome': staff_data['nome'],
                    'cognome': staff_data['cognome'],
                    'hidden': False
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created staff: {staff.cognome} {staff.nome} (IRIS ID: {staff.id_iris})"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated staff: {staff.cognome} {staff.nome} (IRIS ID: {staff.id_iris})"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: Created {created_count}, Updated {updated_count}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "\nYou can now run the IRIS import to fetch publications for these staff members."
            )
        )
