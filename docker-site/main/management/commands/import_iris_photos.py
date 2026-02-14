"""
Django management command to import profile photos from IRIS.
"""
from django.core.management.base import BaseCommand
from main.tasks import import_iris_profile_photos


class Command(BaseCommand):
    help = 'Import profile photos from IRIS for all staff members with Codice Fiscale'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting IRIS profile photos import...'))
        
        # Call the task directly (not via Celery)
        result = import_iris_profile_photos()
        
        # Display results
        self.stdout.write(self.style.SUCCESS('IRIS profile photos import completed!'))
        self.stdout.write(f"Processed: {result['processed']}")
        self.stdout.write(f"Updated: {result['updated']}")
        self.stdout.write(f"Skipped: {result['skipped']}")
        
        if result['errors']:
            self.stdout.write(self.style.ERROR(f"Errors: {len(result['errors'])}"))
            for error in result['errors']:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        else:
            self.stdout.write(self.style.SUCCESS('No errors encountered!'))
