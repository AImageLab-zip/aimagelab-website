from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import UserProfile


class Command(BaseCommand):
    help = 'Populate the database with fake team members'

    def handle(self, *args, **options):
        self.stdout.write('Creating fake team members...')
        
        # Clear existing data
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Principal Investigators
        professors = [
            {
                'username': 'marco.ferrari',
                'first_name': 'Marco',
                'last_name': 'Ferrari',
                'email': 'marco.ferrari@example.com',
                'role': 'professor',
                'bio': 'Full Professor of Computer Science. Research interests include artificial intelligence, '
                       'machine learning, and computational neuroscience.',
                'website': '',
                'display_order': 1
            },
            {
                'username': 'sofia.colombo',
                'first_name': 'Sofia',
                'last_name': 'Colombo',
                'email': 'sofia.colombo@example.com',
                'role': 'assoc_professor',
                'bio': 'Associate Professor specializing in computer vision, robotics, and autonomous systems.',
                'website': '',
                'display_order': 2
            },
        ]
        
        # Postdocs
        postdocs = [
            {
                'username': 'andrea.bianchi',
                'first_name': 'Andrea',
                'last_name': 'Bianchi',
                'email': 'andrea.bianchi@example.com',
                'role': 'postdoc',
                'bio': 'Postdoctoral researcher working on deep reinforcement learning and multi-agent systems.',
                'display_order': 10
            },
            {
                'username': 'chiara.romano',
                'first_name': 'Chiara',
                'last_name': 'Romano',
                'email': 'chiara.romano@example.com',
                'role': 'postdoc',
                'bio': 'Postdoctoral researcher in natural language processing and conversational AI.',
                'display_order': 11
            },
        ]
        
        # PhD Students
        phd_students = [
            {
                'username': 'luca.marino',
                'first_name': 'Luca',
                'last_name': 'Marino',
                'email': 'luca.marino@example.com',
                'role': 'phd',
                'bio': 'PhD student researching efficient neural architectures and model compression.',
                'display_order': 20
            },
            {
                'username': 'elena.russo',
                'first_name': 'Elena',
                'last_name': 'Russo',
                'email': 'elena.russo@example.com',
                'role': 'phd',
                'bio': 'PhD student working on medical image analysis and diagnostic AI systems.',
                'display_order': 21
            },
            {
                'username': 'matteo.villa',
                'first_name': 'Matteo',
                'last_name': 'Villa',
                'email': 'matteo.villa@example.com',
                'role': 'phd',
                'bio': 'PhD student interested in generative models and image synthesis.',
                'display_order': 22
            },
            {
                'username': 'giulia.conti',
                'first_name': 'Giulia',
                'last_name': 'Conti',
                'email': 'giulia.conti@example.com',
                'role': 'phd',
                'bio': 'PhD student researching explainable AI and interpretable machine learning.',
                'display_order': 23
            },
            {
                'username': 'francesco.rossi',
                'first_name': 'Francesco',
                'last_name': 'Rossi',
                'email': 'francesco.rossi@example.com',
                'role': 'phd',
                'bio': 'PhD student focusing on federated learning and privacy-preserving AI.',
                'display_order': 24
            },
            {
                'username': 'sara.moretti',
                'first_name': 'Sara',
                'last_name': 'Moretti',
                'email': 'sara.moretti@example.com',
                'role': 'phd',
                'bio': 'PhD student working on time series analysis and predictive modeling.',
                'display_order': 25
            },
        ]
        
        # Research Interns
        interns = [
            {
                'username': 'davide.greco',
                'first_name': 'Davide',
                'last_name': 'Greco',
                'email': 'davide.greco@example.com',
                'role': 'intern',
                'display_order': 30
            },
            {
                'username': 'martina.bruno',
                'first_name': 'Martina',
                'last_name': 'Bruno',
                'email': 'martina.bruno@example.com',
                'role': 'intern',
                'display_order': 31
            },
            {
                'username': 'lorenzo.ricci',
                'first_name': 'Lorenzo',
                'last_name': 'Ricci',
                'email': 'lorenzo.ricci@example.com',
                'role': 'intern',
                'display_order': 32
            },
            {
                'username': 'alice.galli',
                'first_name': 'Alice',
                'last_name': 'Galli',
                'email': 'alice.galli@example.com',
                'role': 'intern',
                'display_order': 33
            },
        ]
        
        # Alumni
        alumni = [
            {
                'username': 'giovanni.esposito',
                'first_name': 'Giovanni',
                'last_name': 'Esposito',
                'email': 'giovanni.esposito@example.com',
                'role': 'alumni',
                'current_position': 'Machine Learning Engineer, TechCorp',
                'display_order': 40
            },
            {
                'username': 'valentina.costa',
                'first_name': 'Valentina',
                'last_name': 'Costa',
                'email': 'valentina.costa@example.com',
                'role': 'alumni',
                'current_position': 'Data Scientist, AI Solutions Ltd',
                'display_order': 41
            },
            {
                'username': 'simone.barbieri',
                'first_name': 'Simone',
                'last_name': 'Barbieri',
                'email': 'simone.barbieri@example.com',
                'role': 'alumni',
                'current_position': 'Research Scientist, Innovation Labs',
                'display_order': 42
            },
            {
                'username': 'federica.martini',
                'first_name': 'Federica',
                'last_name': 'Martini',
                'email': 'federica.martini@example.com',
                'role': 'alumni',
                'current_position': 'Assistant Professor, Technical University',
                'display_order': 43
            },
        ]
        
        # Create all users
        all_members = professors + postdocs + phd_students + interns + alumni
        created_count = 0
        
        for member_data in all_members:
            # Create user
            user = User.objects.create_user(
                username=member_data['username'],
                first_name=member_data['first_name'],
                last_name=member_data['last_name'],
                email=member_data['email'],
                password='password123'  # Default password for demo
            )
            
            # Get or create profile (signal creates it automatically)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': member_data['role'],
                    'bio': member_data.get('bio', ''),
                    'website': member_data.get('website', ''),
                    'display_order': member_data['display_order'],
                    'is_visible': True,
                    'current_position': member_data.get('current_position', ''),
                }
            )
            
            # Update if already exists
            if not created:
                profile.role = member_data['role']
                profile.bio = member_data.get('bio', '')
                profile.website = member_data.get('website', '')
                profile.display_order = member_data['display_order']
                profile.is_visible = True
                profile.current_position = member_data.get('current_position', '')
                profile.save()
            
            created_count += 1
            self.stdout.write(f'Created: {user.get_full_name()} ({profile.get_role_display()})')
        
        self.stdout.write(self.style.SUCCESS(f'\\nSuccessfully created {created_count} team members!'))
        self.stdout.write(self.style.WARNING('\\nDefault password for all users: password123'))
