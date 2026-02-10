from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import Post, Category


class Command(BaseCommand):
    help = 'Populate the database with fake news posts'

    def handle(self, *args, **options):
        self.stdout.write('Creating fake news posts...')
        
        # Clear existing data
        Post.objects.all().delete()
        Category.objects.all().delete()
        
        # Create categories
        categories_data = [
            {'name': 'Research', 'slug': 'research'},
            {'name': 'Publications', 'slug': 'publications'},
            {'name': 'Awards', 'slug': 'awards'},
            {'name': 'Events', 'slug': 'events'},
            {'name': 'Collaborations', 'slug': 'collaborations'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat = Category.objects.create(**cat_data)
            categories[cat_data['slug']] = cat
            self.stdout.write(f'Created category: {cat.name}')
        
        # Create posts
        now = timezone.now()
        posts_data = [
            {
                'title': 'AImageLab Wins Best Paper Award at CVPR 2025',
                'slug': 'best-paper-award-cvpr-2025',
                'description': 'Our research on efficient vision transformers has been recognized with the prestigious Best Paper Award at the Conference on Computer Vision and Pattern Recognition.',
                'content': '''We are thrilled to announce that our paper "Efficient Vision Transformers with Dynamic Token Pruning" has won the Best Paper Award at CVPR 2025!

The research, led by PhD students Elena Russo and Matteo Villa under the supervision of Prof. Marco Ferrari, introduces a novel approach to reduce computational costs in vision transformers by up to 60% while maintaining accuracy.

This achievement represents months of dedicated work and collaboration within our team. The technique has potential applications in mobile devices, edge computing, and real-time video analysis.

Congratulations to the entire team!''',
                'categories': ['research', 'awards', 'publications'],
                'is_published': True,
                'is_pinned': True,
                'days_ago': 2,
                'event_date': now - timedelta(days=2),
            },
            {
                'title': 'New Collaboration with European AI Research Consortium',
                'slug': 'european-ai-consortium-2025',
                'description': 'AImageLab joins a multi-million euro project focused on developing trustworthy AI systems for healthcare applications.',
                'content': '''AImageLab is proud to announce our participation in the EU-funded TRUSTAI project, a 4-year initiative bringing together 15 research institutions across Europe.

Our lab will lead the work package on explainable medical image analysis, with a focus on diagnostic systems that provide transparent reasoning for their predictions.

Prof. Sofia Colombo will coordinate our efforts, with contributions from postdocs and PhD students specializing in medical AI and interpretability.

The project officially kicks off next month with a consortium meeting in Brussels. Stay tuned for updates on our progress!''',
                'categories': ['collaborations', 'research'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 5,
            },
            {
                'title': 'PhD Position Opening: Deep Learning for Autonomous Systems',
                'slug': 'phd-position-autonomous-systems',
                'description': 'We are looking for motivated candidates to join our team working on cutting-edge research in autonomous navigation and decision-making.',
                'content': '''Applications are now open for a fully-funded PhD position in our lab!

**Research Focus:**
The successful candidate will work on developing robust deep learning algorithms for autonomous vehicles, with emphasis on perception, planning, and safe decision-making in complex environments.

**Requirements:**
- Master's degree in Computer Science, Engineering, or related field
- Strong background in machine learning and computer vision
- Programming skills in Python and deep learning frameworks
- Excellent communication skills in English

**What we offer:**
- Competitive stipend and benefits
- State-of-the-art computing infrastructure
- Vibrant research environment
- Opportunities for international collaboration

**Deadline:** Applications must be submitted by January 15, 2026.

For more information and to apply, visit our careers page or contact Prof. Sofia Colombo directly.''',
                'categories': ['events'],
                'is_published': True,
                'is_pinned': True,
                'days_ago': 7,
            },
            {
                'title': 'Summer School on Advanced Computer Vision - Save the Date!',
                'slug': 'summer-school-computer-vision-2026',
                'description': 'Join us for a week-long intensive course covering the latest advances in computer vision and deep learning.',
                'content': '''Mark your calendars! AImageLab will host its 5th Annual Summer School on Advanced Computer Vision from July 14-18, 2026.

**Program Highlights:**
- Morning lectures by leading researchers in the field
- Hands-on coding sessions and practical tutorials
- Poster session for participants to present their work
- Networking opportunities with researchers and industry partners
- Lab tours and demos of cutting-edge projects

**Topics include:**
→ Vision transformers and attention mechanisms
→ Self-supervised learning for visual recognition
→ 3D reconstruction and neural rendering
→ Multimodal learning and vision-language models
→ Real-world applications and deployment strategies

**Registration opens:** March 1, 2026
**Early bird deadline:** May 1, 2026

Limited spots available! More details coming soon on our website.''',
                'categories': ['events'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 10,
                'event_date': now + timedelta(days=220),
            },
            {
                'title': 'Three Papers Accepted at NeurIPS 2025',
                'slug': 'neurips-2025-acceptances',
                'description': 'AImageLab researchers will present groundbreaking work on federated learning, neural architecture search, and time series forecasting.',
                'content': '''Exciting news from the Neural Information Processing Systems (NeurIPS) conference!

We're delighted to announce that three papers from our lab have been accepted for presentation at NeurIPS 2025:

1. **"Privacy-Preserving Federated Learning with Adaptive Aggregation"** - Francesco Rossi et al.
   This work introduces a novel aggregation strategy that improves both privacy guarantees and model performance in federated settings.

2. **"Efficient Neural Architecture Search via Progressive Sampling"** - Luca Marino et al.
   A new NAS approach that reduces search time by 10x while discovering architectures competitive with state-of-the-art.

3. **"Transformer Models for Multivariate Time Series with Missing Data"** - Sara Moretti et al.
   An innovative architecture specifically designed to handle incomplete temporal data in forecasting tasks.

Congratulations to all authors! The conference will take place in Vancouver this December.''',
                'categories': ['publications', 'research'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 15,
            },
            {
                'title': 'Welcome to Our New Postdoctoral Researchers!',
                'slug': 'new-postdocs-welcome-2025',
                'description': 'Two talented researchers join AImageLab to work on cutting-edge AI projects.',
                'content': '''We're excited to welcome Andrea Bianchi and Chiara Romano to our research group!

**Dr. Andrea Bianchi** joins us from ETH Zurich, where he completed his PhD on deep reinforcement learning. Andrea will be working on multi-agent systems and their applications to robotic coordination.

**Dr. Chiara Romano** comes from the University of Edinburgh with expertise in natural language processing. She will lead our efforts in developing more natural and context-aware conversational AI systems.

Both researchers bring unique perspectives and complementary skills that will strengthen our interdisciplinary approach to AI research.

Please join us in welcoming them to the team! 🎉''',
                'categories': ['events'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 20,
            },
            {
                'title': 'Lab Seminar Series: Guest Talk by Dr. Yoshua Bengio',
                'slug': 'seminar-yoshua-bengio-2025',
                'description': 'Distinguished lecture on "The Future of Deep Learning: Challenges and Opportunities"',
                'content': '''**Special Seminar Announcement**

We are honored to host Prof. Yoshua Bengio, Turing Award winner and one of the pioneers of deep learning, for a special seminar.

**Title:** "The Future of Deep Learning: Challenges and Opportunities"

**Date:** December 15, 2025
**Time:** 3:00 PM - 4:30 PM
**Location:** Main Auditorium + Online (hybrid format)

**Abstract:**
Prof. Bengio will discuss the current limitations of deep learning systems and outline promising research directions for the coming decade, including causality, consciousness-inspired architectures, and energy-efficient AI.

The talk will be followed by a Q&A session and informal discussion over coffee.

**Registration required** (limited in-person capacity)
Register at: events.aimagelab.org/bengio2025

This is a rare opportunity - don't miss it!''',
                'categories': ['events'],
                'is_published': True,
                'is_pinned': True,
                'days_ago': 25,
                'event_date': now + timedelta(days=11),
            },
            {
                'title': 'Industry Partnership: AI Solutions for Smart Manufacturing',
                'slug': 'industry-partnership-smart-manufacturing',
                'description': 'Multi-year collaboration aims to bring advanced computer vision to factory floors.',
                'content': '''AImageLab announces a strategic partnership with IndustryTech Solutions to develop AI-powered quality control and predictive maintenance systems.

**Project Overview:**
The collaboration will focus on deploying real-time computer vision systems for defect detection in manufacturing processes. Our algorithms will analyze thousands of products per minute with superhuman accuracy.

**Key Innovations:**
• Few-shot learning for rapid adaptation to new product types
• Edge AI deployment for low-latency processing
• Explainable predictions for regulatory compliance
• Continuous learning from production data

The project will provide valuable research opportunities for our students while addressing real-world industrial challenges.

Initial pilot deployment is scheduled for Q2 2026, with full rollout planned for 2027.''',
                'categories': ['collaborations', 'research'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 30,
            },
            {
                'title': '[DRAFT] Upcoming Workshop on Generative AI Ethics',
                'slug': 'draft-workshop-generative-ai-ethics',
                'description': 'Planning a workshop to discuss ethical implications of generative models.',
                'content': '''**DRAFT - NOT YET PUBLISHED**

We are organizing a workshop on the ethical dimensions of generative AI, bringing together researchers, ethicists, policymakers, and industry practitioners.

Topics to cover:
- Deepfakes and misinformation
- Copyright and intellectual property
- Bias and fairness in generated content
- Environmental impact of large models
- Regulatory frameworks

Date TBD - likely March 2026
More details to follow once confirmed.''',
                'categories': ['events'],
                'is_published': False,
                'is_pinned': False,
                'days_ago': 35,
            },
            {
                'title': 'Student Spotlight: Outstanding Master Thesis on Medical AI',
                'slug': 'student-spotlight-medical-ai-thesis',
                'description': 'Giulia Conti\'s thesis on explainable diagnostic systems receives highest honors and industry recognition.',
                'content': '''Congratulations to Giulia Conti for her exceptional Master's thesis, "Explainable Deep Learning for Breast Cancer Diagnosis"!

Giulia's work developed a novel attention-based architecture that not only achieves 95% accuracy in detecting malignant lesions but also provides visual explanations that radiologists found clinically useful.

**Achievements:**
✓ Graduated with maximum honors (110/110 cum laude)
✓ Thesis selected for publication in Medical Image Analysis journal
✓ Received Best Thesis Award from the Italian Association for Artificial Intelligence
✓ Sparked interest from three hospitals for clinical trials

Giulia will continue this research as a PhD student in our group starting next semester.

Her work exemplifies our commitment to AI that is not only accurate but also trustworthy and clinically actionable. We're proud to have supervised this excellent research!

Read the full thesis: [link to repository]''',
                'categories': ['awards', 'research'],
                'is_published': True,
                'is_pinned': False,
                'days_ago': 40,
            },
        ]
        
        created_count = 0
        for post_data in posts_data:
            # Create post
            post = Post.objects.create(
                title=post_data['title'],
                slug=post_data['slug'],
                description=post_data['description'],
                content=post_data['content'],
                is_published=post_data['is_published'],
                is_pinned=post_data['is_pinned'],
                event_date=post_data.get('event_date'),
                created_at=now - timedelta(days=post_data['days_ago']),
            )
            
            # Add categories
            for cat_slug in post_data['categories']:
                post.categories.add(categories[cat_slug])
            
            status = "📌 PINNED" if post.is_pinned else ("✓ Published" if post.is_published else "📝 Draft")
            created_count += 1
            self.stdout.write(f'{status}: {post.title}')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} news posts!'))
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))
        self.stdout.write(self.style.WARNING(f'\nPublished posts: {Post.objects.filter(is_published=True).count()}'))
        self.stdout.write(self.style.WARNING(f'Draft posts: {Post.objects.filter(is_published=False).count()}'))
        self.stdout.write(self.style.WARNING(f'Pinned posts: {Post.objects.filter(is_pinned=True).count()}'))
