"""
Django script to populate Project model from CSV file.
Place this file in your Django app's management/commands directory
or run it as a standalone script with Django setup.
"""

import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from main.models import Project 


class Command(BaseCommand):
    help = 'Populate Project model from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file with project data'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Reset existing projects
        self.stdout.write('Deleting existing projects...')
        deleted_count = Project.objects.all().delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} projects'))
        
        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        
        # Read and populate from CSV
        self.stdout.write('Reading CSV file...')
        created_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Parse dates
                    start_date = datetime.strptime(row['start_date'], '%Y-%m-%d').date()
                    end_date = None
                    if row['end_date']:
                        end_date = datetime.strptime(row['end_date'], '%Y-%m-%d').date()
                    
                    # Create project
                    project = Project.objects.create(
                        name=row['name'],
                        title=row['title'],
                        description=row['description'],
                        founding_by=row['founding_by'],
                        project_type=row['project_type'],
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    created_count += 1
                    self.stdout.write(f'Created: {project.name}')
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error creating project {row.get("name", "unknown")}: {str(e)}')
                    )
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created: {created_count} projects'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))
