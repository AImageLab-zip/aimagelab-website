import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pathlib import Path
from main.models import ShortLink


class Command(BaseCommand):
    help = 'Import short links from a CSV file (columns: src, dest, user)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='short_links.csv',
            help='Path to the CSV file (default: short_links.csv in project root)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing short links before importing',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear']

        # Determine the CSV file path
        if not Path(csv_file).is_absolute():
            base_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
            csv_path = base_path / csv_file
        else:
            csv_path = Path(csv_file)

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return

        self.stdout.write(f'Reading CSV file: {csv_path}')

        if clear_existing:
            deleted_count = ShortLink.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing short links'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            # Support both header and headerless CSV
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)

            if has_header:
                reader = csv.DictReader(f)
            else:
                reader = csv.DictReader(f, fieldnames=['src', 'dest', 'user'])

            for row_num, row in enumerate(reader, start=1):
                try:
                    src = row.get('src', '').strip()
                    dest = row.get('dest', '').strip()
                    username = row.get('user', '').strip()

                    if not src or not dest or not username:
                        self.stdout.write(self.style.WARNING(
                            f'Row {row_num}: Skipping incomplete row (src={src!r}, dest={dest!r}, user={username!r})'
                        ))
                        skipped_count += 1
                        continue

                    # Look up the user by username
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'Row {row_num}: User "{username}" not found, using admin'
                        ))
                        user = User.objects.get(username='gsalici')
                        # Continue processing with the admin user

                    # Create or update the short link
                    short_link, created = ShortLink.objects.update_or_create(
                        src=src,
                        defaults={
                            'dest': dest,
                            'user': user,
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✓ Created: /go/{src} → {dest} ({username})')
                    else:
                        updated_count += 1
                        self.stdout.write(f'  ↻ Updated: /go/{src} → {dest} ({username})')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Row {row_num}: Error - {e}'))
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nImport complete!'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count}'))
        if skipped_count:
            self.stdout.write(self.style.WARNING(f'  Skipped: {skipped_count}'))
        self.stdout.write(f'  Total in DB: {ShortLink.objects.count()}')
