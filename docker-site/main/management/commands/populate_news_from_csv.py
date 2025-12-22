import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from pathlib import Path
from main.models import Post, Category


class Command(BaseCommand):
    help = 'Populate the database with news posts from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='news_prod.csv',
            help='Path to the CSV file (default: news_prod.csv in project root)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing posts and categories before importing',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear']
        
        # Determine the CSV file path
        if not Path(csv_file).is_absolute():
            # Assume it's relative to the project root (6 levels up from this file)
            base_path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
            csv_path = base_path / csv_file
        else:
            csv_path = Path(csv_file)
        
        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return
        
        self.stdout.write(f'Reading CSV file: {csv_path}')
        
        # Clear existing data if requested
        if clear_existing:
            Post.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing posts and categories'))
        
        # Read and process CSV
        categories_cache = {}
        created_count = 0
        skipped_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Get or create category
                    category_name = row.get('category', '').strip()
                    if category_name:
                        if category_name not in categories_cache:
                            # Create slug from category name
                            category_slug = category_name.lower().replace(' ', '-')
                            category, created = Category.objects.get_or_create(
                                slug=category_slug,
                                defaults={'name': category_name.capitalize()}
                            )
                            categories_cache[category_name] = category
                            if created:
                                self.stdout.write(f'Created category: {category.name}')
                        category = categories_cache[category_name]
                    else:
                        category = None
                    
                    # Parse dates
                    created_at = parse_datetime(row.get('created_at', ''))
                    if not created_at:
                        created_at = timezone.now()
                    
                    # Check if post already exists
                    slug = row.get('slug', '').strip()
                    if not slug:
                        self.stdout.write(self.style.WARNING(f'Skipping row with empty slug'))
                        skipped_count += 1
                        continue
                    
                    if Post.objects.filter(slug=slug).exists():
                        self.stdout.write(self.style.WARNING(f'Post with slug "{slug}" already exists, skipping'))
                        skipped_count += 1
                        continue
                    
                    # Create post
                    post = Post.objects.create(
                        slug=slug,
                        title=row.get('title', '').strip(),
                        description=row.get('description', '').strip(),
                        content=row.get('content', '').strip(),
                        is_published=row.get('is_published', '1') == '1',
                        is_pinned=False,  # Default to not pinned
                        created_at=created_at,
                        cover_image=row.get('cover', '').strip() if row.get('cover') else None,
                    )
                    
                    # Add category if exists
                    if category:
                        post.categories.add(category)
                    
                    status = "✓ Published" if post.is_published else "📝 Draft"
                    created_count += 1
                    self.stdout.write(f'{status}: {post.title}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row: {e}'))
                    self.stdout.write(self.style.ERROR(f'Row data: {row}'))
                    skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} news posts!'))
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories_cache)} categories'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped {skipped_count} posts'))
        self.stdout.write(self.style.WARNING(f'\nPublished posts: {Post.objects.filter(is_published=True).count()}'))
        self.stdout.write(self.style.WARNING(f'Draft posts: {Post.objects.filter(is_published=False).count()}'))
