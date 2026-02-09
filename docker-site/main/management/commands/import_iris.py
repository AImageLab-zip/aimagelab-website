"""
Management command to trigger IRIS publications import manually.
"""
from django.core.management.base import BaseCommand
from main.tasks import import_iris_publications, is_import_running


class Command(BaseCommand):
    help = 'Manually trigger IRIS publications import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run import as async Celery task (default: run synchronously)',
        )

    def handle(self, *args, **options):
        """Trigger IRIS import"""
        
        # Check if import is already running
        if is_import_running():
            self.stdout.write(
                self.style.WARNING(
                    'IRIS import is already in progress. Please wait for it to complete.'
                )
            )
            return
        
        if options['async']:
            # Run as Celery task
            self.stdout.write('Starting IRIS import as background task...')
            task = import_iris_publications.delay()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import task started with ID: {task.id}\n'
                    f'Check status with: celery -A myproject inspect active'
                )
            )
        else:
            # Run synchronously
            self.stdout.write('Starting IRIS import (synchronous)...')
            self.stdout.write(
                self.style.WARNING(
                    'This may take several minutes depending on the number of staff members.\n'
                )
            )
            
            result = import_iris_publications()
            
            if result['status'] == 'completed':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nImport completed successfully!\n"
                        f"Statistics:\n"
                        f"  - Staff processed: {result['stats']['staff_processed']}\n"
                        f"  - Publications created: {result['stats']['publications_created']}\n"
                        f"  - Publications updated: {result['stats']['publications_updated']}\n"
                        f"  - Links created: {result['stats']['links_created']}\n"
                    )
                )
                
                if result['stats']['errors']:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nErrors encountered: {len(result['stats']['errors'])}"
                        )
                    )
                    for error in result['stats']['errors']:
                        self.stdout.write(self.style.ERROR(f"  - {error}"))
            elif result['status'] == 'skipped':
                self.stdout.write(
                    self.style.WARNING(result['message'])
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Import failed: {result.get('message', 'Unknown error')}"
                    )
                )
