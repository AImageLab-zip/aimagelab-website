from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
from .models import UserProfile, Post, Category, Project, PublicationIRIS, MeetingRoom, RoomReservation, ShortLink, HistoryMilestone, ResearchArea, DashboardCard, WikiPage, WikiPageVersion, WikiPageChangeRequest, WikiImage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Case, When, IntegerField
from datetime import datetime, timedelta

from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import UserProfile, IRISImportLog
from .tasks import sync_user_task, import_iris_publications, import_iris_profile_photos, is_import_running
import os

from PIL import Image
from io import BytesIO

POST_PER_PAGE = 10
PUBLICATION_PER_PAGE = 10
PROJECTS_PER_PAGE = 20


def home(request):
    """Home page view."""
    # Get latest posts without event_date
    latest_posts = Post.objects.filter(
        is_published=True,
    ).order_by('-is_pinned', '-created_at')[:10]
    
    # Calculate actual counts
    total_users = UserProfile.objects.filter(is_visible=True).count()
    total_publications = PublicationIRIS.objects.filter(hidden=False).count()
    active_projects = Project.objects.filter(
        Q(end_date__isnull=True) | Q(end_date__gte=datetime.now().date())
    ).count()
    
    featured_profiles = []
    
    rcucchiara_profile = UserProfile.objects.select_related('user').get(
            user__username='rcucchiara'
        )
    
    # Check avatar first, then avatar_iris
    if (rcucchiara_profile.avatar and hasattr(rcucchiara_profile.avatar, 'url') and rcucchiara_profile.avatar.url) or \
       (rcucchiara_profile.avatar_iris and hasattr(rcucchiara_profile.avatar_iris, 'url') and rcucchiara_profile.avatar_iris.url):
            featured_profiles.append(rcucchiara_profile)
    
    # Filter profiles that have either avatar or avatar_iris
    featured_profiles.extend(UserProfile.objects.select_related('user').filter(
        Q(avatar__isnull=False) | Q(avatar_iris__isnull=False),
        is_visible=True
    ).exclude(user__username='rcucchiara').exclude(avatar='', avatar_iris='').order_by('?')[:2])
    
    research_areas = ResearchArea.objects.all()

    return render(request, 'main/home.html', {
        'latest_posts': latest_posts,
        'total_users': total_users,
        'total_publications': total_publications,
        'active_projects': active_projects,
        'featured_profiles': featured_profiles,
        'research_areas': research_areas,
    })

def contacts(request):
    """Contacts page view."""
    return render(request, 'main/contacts.html')

def research(request):
    """Research areas page view."""
    milestones = HistoryMilestone.objects.all()
    research_areas = ResearchArea.objects.all()
    return render(request, 'main/research.html', {
        'milestones': milestones,
        'research_areas': research_areas,
    })

def news(request):
    """News/Blog page view with pagination and search."""
    search_query = request.GET.get('search', '')
    category_query = request.GET.get('category', '')
    
    # Filter posts based on authentication
    if request.user.is_authenticated:
        posts = Post.objects.all()
    else:
        posts = Post.objects.filter(is_published=True)
    
    # Apply search filter if query exists
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )
        
    if category_query:
        posts = posts.filter(categories__name__iexact=category_query)
    
    # Order by creation date and prefetch categories for efficiency
    posts = posts.order_by('is_published', '-is_pinned', '-created_at').prefetch_related('categories')
    
    # Paginate results
    paginator = Paginator(posts, POST_PER_PAGE)
    page = request.GET.get('page', 1)
    
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)
    
    # Get upcoming events (posts with event_date, ordered by event_date)
    upcoming_events = Post.objects.filter(
        is_published=True,
        event_date__isnull=False,
        event_date__gt=datetime.now()
    ).order_by('event_date')[:5]
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'main/news.html', {
        'posts': posts_page,
        'search_query': search_query,
        'category_query': category_query,
        'upcoming_events': upcoming_events,
        'categories': categories    
    })  

def projects(request):
    """Projects page view with pagination, search, and type filter."""
    search_query = request.GET.get('search', '')
    type_query = request.GET.get('type', '')
    show_all = request.GET.get('show_all', 'off') == 'on'

    projects_qs = Project.objects.all()

    # By default, show only active projects (end_date is null or in the future)
    if not show_all:
        projects_qs = projects_qs.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=datetime.now().date())
        )

    if search_query:
        projects_qs = projects_qs.filter(
            Q(name__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if type_query:
        projects_qs = projects_qs.filter(project_type__iexact=type_query)

    # Order by start date descending
    projects_qs = projects_qs.order_by('-start_date')

    paginator = Paginator(projects_qs, PROJECTS_PER_PAGE)
    page = request.GET.get('page', 1)

    try:
        projects_page = paginator.page(page)
    except PageNotAnInteger:
        projects_page = paginator.page(1)
    except EmptyPage:
        projects_page = paginator.page(paginator.num_pages)

    # Get project types with count, exclude types with ≤2 projects
    from django.db.models import Count
    project_types = (
        Project.objects.exclude(project_type="")
        .values('project_type')
        .annotate(count=Count('id'))
        .filter(count__gt=2)
        .order_by('project_type')
        .values_list('project_type', flat=True)
    )

    return render(request, 'main/projects.html', {
        'projects': projects_page,
        'search_query': search_query,
        'type_query': type_query,
        'project_types': project_types,
        'show_all': show_all,
    })

def publications(request):
    """Publications page view with pagination, search, and filters."""
    search_query = request.GET.get('search', '')
    year_query = request.GET.get('year', '')
    journal_query = request.GET.get('journal', '')
    type_query = request.GET.get('type', '')
    author_username = request.GET.get('author', '')

    # Parse @author and #keyword tokens from the search query
    tokens = search_query.split()
    author_tokens = []
    keyword_tokens = []
    text_tokens = []
    for token in tokens:
        if token.startswith('@') and len(token) > 1:
            author_tokens.append(token[1:].strip(' ,.;:'))
        elif token.startswith('#') and len(token) > 1:
            keyword_tokens.append(token[1:].strip(' ,.;:'))
        else:
            text_tokens.append(token)

    # Use the first @author token when explicit author filter is not provided
    if not author_username and author_tokens:
        author_username = author_tokens[0]

    # Keep variants for clearing filters in the UI
    search_query_without_author = " ".join([t for t in tokens if not t.startswith('@')])
    search_query_without_keywords = " ".join([t for t in tokens if not t.startswith('#')])
    
    # Start with all non-hidden publications
    publications_qs = PublicationIRIS.objects.filter(hidden=False)
    
    # Apply search filter (title or authors)
    if text_tokens:
        # Split search query into individual words
        words = text_tokens
        query = Q()
        for word in words:
            query &= (
                Q(titolo__icontains=word) |
                Q(autori__icontains=word) |
                Q(abstract__icontains=word)
            )
        publications_qs = publications_qs.filter(query)

    # Apply keyword filter from #tokens
    if keyword_tokens:
        for keyword in keyword_tokens:
            if keyword:
                publications_qs = publications_qs.filter(keywords__contains=[keyword])
        
    # Apply year filter
    if year_query:
        publications_qs = publications_qs.filter(anno=year_query)
    
    # Apply journal filter
    if journal_query:
        publications_qs = publications_qs.filter(rivista__icontains=journal_query)
    
    # Apply type filter
    if type_query:
        publications_qs = publications_qs.filter(tipo__icontains=type_query)
    
    # Apply author filter using UserProfile through UserProfilePublicationIRIS
    if author_username:
        publications_qs = publications_qs.filter(authors__user__username=author_username)
    
    # Order by year descending, then by title
    publications_qs = publications_qs.order_by('-anno', 'titolo')
    
    # Pagination
    paginator = Paginator(publications_qs, PUBLICATION_PER_PAGE)
    page = request.GET.get('page', 1)
    
    try:
        publications_page = paginator.page(page)
    except PageNotAnInteger:
        publications_page = paginator.page(1)
    except EmptyPage:
        publications_page = paginator.page(paginator.num_pages)
    
    # Get available years (for sidebar filter)
    from django.db.models import Count
    available_years = (
        PublicationIRIS.objects.filter(hidden=False, anno__isnull=False)
        .values('anno')
        .annotate(count=Count('id'))
        .order_by('-anno')
        .values_list('anno', flat=True)
    )
    
    # Get available journals (top journals with > 2 publications)
    available_journals = (
        PublicationIRIS.objects.filter(hidden=False)
        .exclude(rivista='')
        .values('rivista')
        .annotate(count=Count('id'))
        .filter(count__gt=2)
        .order_by('rivista')
        .values_list('rivista', flat=True)
    )
    
    # Get available types (with > 2 publications)
    available_types = (
        PublicationIRIS.objects.filter(hidden=False)
        .exclude(tipo='')
        .values('tipo')
        .annotate(count=Count('id'))
        .filter(count__gt=2)
        .order_by('tipo')
        .values_list('tipo', flat=True)
    )
    
    # Get available authors (UserProfiles that have publications)
    available_authors = (
        UserProfile.objects.filter(
            publication_links__publication__hidden=False
        )
        .annotate(pub_count=Count('publication_links', distinct=True))
        .filter(pub_count__gt=0)
        .order_by('user__first_name', 'user__last_name')
        .select_related('user')
        .distinct()
    )

    # Build autocomplete data for authors and keywords
    available_authors_data = [
        {
            'username': profile.user.username,
            'name': profile.get_full_name()
        }
        for profile in available_authors
    ]

    from collections import Counter
    keywords_counter = Counter()
    keywords_lists = PublicationIRIS.objects.filter(hidden=False).values_list('keywords', flat=True)
    for keywords_list in keywords_lists:
        if isinstance(keywords_list, list):
            for keyword in keywords_list:
                if isinstance(keyword, str) and keyword:
                    keywords_counter[keyword] += 1
    available_keywords = sorted(
        [keyword for keyword, count in keywords_counter.items() if count > 2],
        key=lambda k: k.lower()
    )
    
    # Get the selected author object if any
    selected_author = None
    if author_username:
        try:
            selected_author = UserProfile.objects.select_related('user').get(user__username=author_username)
        except UserProfile.DoesNotExist:
            pass
    
    return render(request, 'main/publications.html', {
        'publications': publications_page,
        'search_query': search_query,
        'year_query': year_query,
        'journal_query': journal_query,
        'type_query': type_query,
        'author_username': author_username,
        'selected_author': selected_author,
        'keyword_tokens': keyword_tokens,
        'search_query_without_author': search_query_without_author,
        'search_query_without_keywords': search_query_without_keywords,
        'available_years': available_years,
        'available_journals': available_journals,
        'available_types': available_types,
        'available_authors': available_authors,
        'available_authors_data': available_authors_data,
        'available_keywords': available_keywords,
    })

def post_single(request, slug):
    """Single post detail view."""
    post = Post.objects.get(slug=slug)
    return render(request, 'main/single.html', {'post': post})

def privacy_policy(request):
    """Privacy Policy page view."""
    return render(request, 'main/privacy_policy.html')

@login_required
def post_form(request, slug=None):
    """Add or edit a post."""
    post = Post.objects.get(slug=slug) if slug else None
    categories = Category.objects.all().order_by('name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        title = request.POST.get('title')
        new_slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        content = request.POST.get('content')
        cover = request.FILES.get('cover')
        thumbnail = request.FILES.get('thumbnail')
        category_ids = request.POST.getlist('categories')
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        # Handle event_date
        event_date = None
        remove_event_date = request.POST.get('remove_event_date') == 'on'
        
        if remove_event_date:
            event_date = None
        else:
            event_date_raw = request.POST.get('event_date')
            if event_date_raw:
                try:
                    # datetime-local format is "YYYY-MM-DDTHH:mm"
                    event_date = datetime.fromisoformat(event_date_raw)
                except (ValueError, TypeError):
                    event_date = None
        
        # Handle cover image
        remove_cover = request.POST.get('remove_cover') == 'on'
        
        # Handle thumbnail
        remove_thumbnail = request.POST.get('remove_thumbnail') == 'on'
        
        is_published = action == 'publish'
        
        if post:
            # Edit existing post
            post.title = title
            post.slug = new_slug
            post.description = description
            post.content = content
            post.event_date = event_date
            post.is_pinned = is_pinned
            if cover:
                post.cover = cover
            if remove_cover:
                post.cover = None
            if thumbnail:
                post.thumbnail = thumbnail
            if remove_thumbnail:
                post.thumbnail = None
            if action in ['publish', 'draft']:
                post.is_published = is_published
            post.save()
            post.categories.set(category_ids)
        else:
            # Create new post
            post = Post.objects.create(
                title=title,
                slug=new_slug,
                description=description,
                content=content,
                is_published=is_published,
                cover=cover,
                thumbnail=thumbnail,
                event_date=event_date,
                is_pinned=is_pinned,
            )
            post.categories.set(category_ids)
        
        if action == 'publish':
            django_messages.success(request, 'Post published successfully!')
        elif action == 'draft':
            django_messages.success(request, 'Post saved as draft!')
        else:
            django_messages.success(request, 'Post updated successfully!')
        
        return redirect('single', slug=post.slug)
    
    template = 'main/post_edit.html'
    context = {'post': post, 'categories': categories}
    return render(request, template, context)

def people(request):
    """People/Team page view."""
    # Get visible profiles grouped by role
    profiles = UserProfile.objects.filter(is_visible=True).select_related('user')
    
    # Create ordering based on LDAP_ROLE_PRIORITY
    role_priority = settings.LDAP_ROLE_PRIORITY
    role_order = Case(
        *[When(role=role, then=priority) for role, priority in role_priority.items()],
        default=0,
        output_field=IntegerField()
    )
    
    # Group by role and order by priority (descending), display_order, then first name
    grouped_profiles = {
        'professors': profiles.filter(role__in=['rector', 'full_professor', 'assoc_professor', 'researcher_tt', 'researcher_b', 'researcher_a']).order_by(-role_order, '-display_order', 'user__last_name'),
        'phd_students_and_co': profiles.filter(role__in=['phd', 'research_fellow', 'postdoc', 'collaborator']).order_by(-role_order,'-display_order', 'user__last_name'),
        'staff': profiles.filter(role__in=['secretariat_staff', 'staff']).order_by(-role_order, '-display_order', 'user__last_name'),
        'alumni': profiles.filter(role__in=['past_member']).order_by(-role_order, '-display_order', 'user__last_name'),
    }
    
    return render(request, 'main/people.html', {'grouped_profiles': grouped_profiles})


def login_view(request):
    """Login page view with Hello World message."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            django_messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            django_messages.error(request, 'Invalid username or password.')
    
    context = {
        'OIDC_PROVIDER_NAME': getattr(settings, 'OIDC_PROVIDER_NAME', 'OIDC Provider')
    }
    return render(request, 'main/login.html', context)


def logout_view(request):
    """Logout view."""
    logout(request)
    django_messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    """Dashboard view (requires login)."""
    from itertools import groupby
    cards = DashboardCard.objects.filter(is_active=True)
    grouped = []
    for section, items in groupby(cards, key=lambda c: c.section):
        grouped.append((section, list(items)))
    return render(request, 'main/dashboard.html', {'card_sections': grouped})


@login_required
def edit_profile(request):
    """Profile edit view for authenticated users with visible profiles."""
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'role': 'phd',  # default role for manually created profiles
            'is_visible': False,  # New profiles are hidden by default
            'display_order': 0,
        }
    )
    
    # Check if user profile is visible - only visible users can edit their profile
    if not profile.is_visible:
        django_messages.error(
            request,
            'Your profile is not yet visible. Please contact an administrator to activate your account.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        # Update profile fields
        profile.bio = request.POST.get('bio', '').strip()
        profile.website = request.POST.get('website', '').strip()
        profile.google_scholar = request.POST.get('google_scholar', '').strip()
        profile.github = request.POST.get('github', '').strip()
        profile.linkedin = request.POST.get('linkedin', '').strip()
        profile.phone_number = request.POST.get('phone_number', '').strip()

        # Handle avatar upload
        if 'avatar' in request.FILES and request.FILES['avatar']:
            # Delete old avatar if exists
            if profile.avatar:
                profile.avatar.delete()
            # Save new avatar
            avatar_file = request.FILES['avatar']
            
            # Open and resize image
            img = Image.open(avatar_file)
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            # Convert RGBA/P/LA images to RGB (JPEG doesn't support transparency)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            img_io.seek(0)
            profile.avatar.save(f"{request.user.username}_avatar.jpg", ContentFile(img_io.getvalue()))

        # Handle avatar removal
        if request.POST.get('remove_avatar') == 'on' and profile.avatar:
            profile.avatar.delete()
            profile.avatar = None

        profile.save()
        django_messages.success(request, 'Profile updated successfully!')
        return redirect('edit_profile')

    return render(request, 'main/edit_profile.html', {
        'profile': profile,
    })


@login_required
def add_user(request):
    """View to add a new user using Celery task."""
    if request.method == 'POST':
        # Collect form data
        user_data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'password': request.POST.get('password', ''),
            'role': request.POST.get('role', 'phd'),
            'bio': request.POST.get('bio', ''),
            'website': request.POST.get('website', ''),
            'google_scholar': request.POST.get('google_scholar', ''),
            'github': request.POST.get('github', ''),
            'linkedin': request.POST.get('linkedin', ''),
            'phone_number': request.POST.get('phone_number', ''),
            'display_order': int(request.POST.get('display_order', 0)),
            'is_visible': request.POST.get('is_visible', 'on') == 'on',
        }
        
        # Handle avatar upload - save file and pass path
        if 'avatar' in request.FILES:
            avatar_file = request.FILES['avatar']
            # Save temporarily and store the path
            filename = f"avatars/{user_data['username']}_{avatar_file.name}"
            path = default_storage.save(filename, ContentFile(avatar_file.read()))
            user_data['avatar_path'] = path
        
        # Remove password if empty
        if not user_data['password']:
            del user_data['password']
        
        try:
            # Launch Celery task asynchronously
            task = sync_user_task.delay(user_data)
            
            django_messages.success(
                request, 
                f'User creation/update task started! Task ID: {task.id}'
            )
            
            # For AJAX requests, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'task_id': task.id,
                    'message': 'Task started successfully'
                })
            
            return redirect('add_user')
            
        except Exception as e:
            django_messages.error(request, f'Error starting task: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
    
    # GET request - show form
    role_choices = UserProfile.ROLE_CHOICES
    return render(request, 'main/add_user.html', {'role_choices': role_choices})


@login_required
def sync_ldap(request):
    """View to manually trigger LDAP synchronization."""
    from .tasks import populate_users_from_ldap
    
    # Only allow staff members to trigger sync
    if not request.user.is_staff:
        django_messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Launch LDAP sync task asynchronously
            task = populate_users_from_ldap.delay()
            
            django_messages.success(
                request,
                f'LDAP synchronization started! Task ID: {task.id}. This may take a few moments.'
            )
        except Exception as e:
            django_messages.error(request, f'Error starting LDAP sync: {str(e)}')
    
    # Redirect back to the previous page or home
    return redirect(request.META.get('HTTP_REFERER', 'home'))
def serve_media(request, path):
    """
    Serve media files with access control.
    
    You can add authentication/authorization checks here:
    - Check if user is authenticated
    - Check if user has permission to access specific files
    - Log file access
    - etc.
    """
    # TODO: Add your access control logic here
    # Example: if not request.user.is_authenticated:
    #     raise Http404("File not found")
    
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # Security check: ensure the file is within MEDIA_ROOT
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise Http404("Invalid file path")
    
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    if not os.path.isfile(file_path):
        raise Http404("Not a file")
    
    # Serve the file
    return FileResponse(open(file_path, 'rb'))


@login_required
def trigger_iris_import(request):
    """
    Trigger IRIS publications import.
    
    This view starts a Celery task to import publications from IRIS.
    If an import is already running, it returns a message to the user.
    
    Only accessible to authenticated users.
    """
    if request.method != 'POST':
        django_messages.error(request, 'Invalid request method.')
        return redirect('dashboard')
    
    # Check if import is already running
    if is_import_running():
        django_messages.warning(
            request,
            'IRIS import is already in progress. Please wait for it to complete.'
        )
        return redirect('dashboard')
    
    # Start the import task
    task = import_iris_publications.delay()
    
    django_messages.success(
        request,
        f'IRIS import started successfully! Task ID: {task.id}. '
        'This may take a few minutes.'
    )
    
    return redirect('dashboard')


@login_required
def iris_import_status(request):
    """
    Get the status of IRIS imports.
    
    Returns JSON with information about recent imports.
    """
    # Get the most recent import logs
    recent_imports = IRISImportLog.objects.all()[:10]
    
    imports_data = []
    for log in recent_imports:
        imports_data.append({
            'id': log.id,
            'status': log.status,
            'started_at': log.started_at.isoformat(),
            'completed_at': log.completed_at.isoformat() if log.completed_at else None,
            'staff_processed': log.staff_processed,
            'publications_created': log.publications_created,
            'publications_updated': log.publications_updated,
            'links_created': log.links_created,
            'error_message': log.error_message
        })
    
    return JsonResponse({
        'is_running': is_import_running(),
        'recent_imports': imports_data
    })


@login_required
def trigger_iris_photo_import(request):
    """
    Trigger IRIS profile photos import.
    
    This view starts a Celery task to import profile photos from IRIS.
    
    Only accessible to authenticated users.
    """
    if request.method != 'POST':
        django_messages.error(request, 'Invalid request method.')
        return redirect('dashboard')
    
    # Start the import task
    task = import_iris_profile_photos.delay()
    
    django_messages.success(
        request,
        f'IRIS profile photo import started successfully! Task ID: {task.id}. '
        'This may take a few minutes.'
    )
    
    return redirect('dashboard')


# Meeting Room Reservation Views

@login_required
def rooms_calendar(request):
    """Display calendar view of all meeting rooms and their reservations."""
    rooms = MeetingRoom.objects.filter(is_active=True).order_by('name')
    
    # Load a wide date range (6 months back, 12 months forward) to support calendar navigation
    # This ensures all reservations are available when users navigate to different dates
    today = datetime.now()
    start_date = today - timedelta(days=180)  # 6 months back
    end_date = today + timedelta(days=365)     # 12 months forward
    
    # Get all reservations in the date range
    reservations = RoomReservation.objects.filter(
        start_time__lte=end_date,
        end_time__gte=start_date
    ).select_related('room', 'user')
    
    # Format events for FullCalendar
    events = []
    for reservation in reservations:
        user_name = reservation.user.get_full_name() or reservation.user.username
        events.append({
            'id': reservation.id,
            'title': f'{reservation.title} - {user_name}',
            'start': reservation.start_time.isoformat(),
            'end': reservation.end_time.isoformat(),
            'backgroundColor': reservation.room.color,
            'borderColor': reservation.room.color,
            'extendedProps': {
                'room': reservation.room.name,
                'user': user_name,
                'userId': reservation.user.id,
                'description': reservation.description,
            }
        })
    
    return render(request, 'main/rooms_calendar.html', {
        'rooms': rooms,
        'events': json.dumps(events),
    })


@login_required
def rooms_list(request):
    """List all meeting rooms."""
    rooms = MeetingRoom.objects.filter(is_active=True).order_by('name')
    return render(request, 'main/rooms_list.html', {'rooms': rooms})


@login_required
def room_detail(request, room_id):
    """Display details and reservations for a specific room."""
    room = get_object_or_404(MeetingRoom, pk=room_id, is_active=True)
    
    # Get upcoming reservations for this room
    now = datetime.now()
    upcoming_reservations = RoomReservation.objects.filter(
        room=room,
        end_time__gte=now
    ).select_related('user').order_by('start_time')[:10]
    
    return render(request, 'main/room_detail.html', {
        'room': room,
        'upcoming_reservations': upcoming_reservations,
    })


@login_required
def create_reservation(request):
    """Create a new room reservation."""
    if request.method == 'POST':
        room_id = request.POST.get('room')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        try:
            room = MeetingRoom.objects.get(pk=room_id, is_active=True)
            
            # Parse datetimes
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Create reservation
            reservation = RoomReservation(
                room=room,
                user=request.user,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time
            )
            
            # Validate (will check for overlaps)
            reservation.full_clean()
            reservation.save()
            
            django_messages.success(request, f'Room "{room.name}" reserved successfully!')
            return JsonResponse({'success': True, 'message': 'Reservation created successfully'})
            
        except MeetingRoom.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Room not found'}, status=404)
        except ValidationError as e:
            # Format validation errors nicely
            error_list = []
            if hasattr(e, 'message_dict'):
                for field, field_errors in e.message_dict.items():
                    error_list.extend(field_errors)
            elif hasattr(e, 'messages'):
                error_list = list(e.messages)
            else:
                error_list = [str(e)]
            return JsonResponse({'success': False, 'error': ' '.join(error_list)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET request - show form
    rooms = MeetingRoom.objects.filter(is_active=True).order_by('name')
    return render(request, 'main/create_reservation.html', {'rooms': rooms})


@login_required
def edit_reservation(request, reservation_id):
    """Edit an existing reservation."""
    reservation = get_object_or_404(RoomReservation, pk=reservation_id)
    
    # Only allow editing own reservations (or superusers)
    if reservation.user != request.user and not request.user.is_superuser:
        django_messages.error(request, 'You can only edit your own reservations.')
        return redirect('rooms_calendar')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        try:
            # Update fields
            reservation.title = title
            reservation.description = description
            reservation.start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            reservation.end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Validate
            reservation.full_clean()
            reservation.save()
            
            django_messages.success(request, 'Reservation updated successfully!')
            return JsonResponse({'success': True, 'message': 'Reservation updated successfully'})
            
        except ValidationError as e:
            # Format validation errors nicely
            error_list = []
            if hasattr(e, 'message_dict'):
                for field, field_errors in e.message_dict.items():
                    error_list.extend(field_errors)
            elif hasattr(e, 'messages'):
                error_list = list(e.messages)
            else:
                error_list = [str(e)]
            return JsonResponse({'success': False, 'error': ' '.join(error_list)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    # GET request - show form
    rooms = MeetingRoom.objects.filter(is_active=True).order_by('name')
    return render(request, 'main/edit_reservation.html', {
        'reservation': reservation,
        'rooms': rooms,
    })


@login_required
def delete_reservation(request, reservation_id):
    """Delete a reservation."""
    reservation = get_object_or_404(RoomReservation, pk=reservation_id)
    
    # Only allow deleting own reservations (or superusers)
    if reservation.user != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        reservation.delete()
        django_messages.success(request, 'Reservation deleted successfully!')
        return JsonResponse({'success': True, 'message': 'Reservation deleted successfully'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


# ─── Short Links (Go) Views ─────────────────────────────────────────────────

from django.db.models import F


def go_redirect(request, src):
    """Redirect /go/<src> to the destination URL, incrementing click count."""
    link = get_object_or_404(ShortLink, src=src)
    ShortLink.objects.filter(pk=link.pk).update(click_count=F('click_count') + 1)
    return redirect(link.dest)


def go_links(request):
    """Public landing page for unauthenticated users; full manager for authenticated ones."""
    import re as _re

    # ── Unauthenticated: show public launcher page ──
    if not request.user.is_authenticated:
        return render(request, 'main/go_public.html')

    # ── Handle POST actions (add / edit / delete) ──
    if request.method == 'POST':
        action = request.POST.get('action', '')
        pk = request.POST.get('pk', '')

        if action == 'add':
            src = request.POST.get('src', '').strip().lower()
            dest = request.POST.get('dest', '').strip()
            description = request.POST.get('description', '').strip()

            errors = []
            if not src:
                errors.append('Short code is required.')
            if not dest:
                errors.append('Destination URL is required.')
            if src and ShortLink.objects.filter(src=src).exists():
                errors.append(f'Short code "{src}" is already taken.')
            if src and not _re.match(r'^[a-z0-9][-a-z0-9_.]*[a-z0-9.]?$', src):
                errors.append('Short code must contain only lowercase letters, numbers, hyphens, underscores and dots.')

            if errors:
                for err in errors:
                    django_messages.error(request, err)
            else:
                ShortLink.objects.create(src=src, dest=dest, description=description, user=request.user)
                django_messages.success(request, f'Short link /go/{src} created!')
            return redirect('go_links')

        elif action == 'edit' and pk:
            link = get_object_or_404(ShortLink, pk=pk)
            if link.user != request.user and not request.user.is_staff:
                django_messages.error(request, 'You can only edit your own short links.')
                return redirect('go_links')

            src = request.POST.get('src', '').strip().lower()
            dest = request.POST.get('dest', '').strip()
            description = request.POST.get('description', '').strip()

            errors = []
            if not src:
                errors.append('Short code is required.')
            if not dest:
                errors.append('Destination URL is required.')
            if src and ShortLink.objects.filter(src=src).exclude(pk=link.pk).exists():
                errors.append(f'Short code "{src}" is already taken.')
            if src and not _re.match(r'^[a-z0-9][-a-z0-9_.]*[a-z0-9.]?$', src):
                errors.append('Short code must contain only lowercase letters, numbers, hyphens, underscores and dots.')

            if errors:
                for err in errors:
                    django_messages.error(request, err)
            else:
                link.src = src
                link.dest = dest
                link.description = description
                link.save()
                django_messages.success(request, f'Short link /go/{src} updated!')
            return redirect('go_links')

        elif action == 'delete' and pk:
            link = get_object_or_404(ShortLink, pk=pk)
            if link.user != request.user and not request.user.is_staff:
                django_messages.error(request, 'You can only delete your own short links.')
                return redirect('go_links')
            src = link.src
            link.delete()
            django_messages.success(request, f'Short link /go/{src} deleted.')
            return redirect('go_links')

    # ── GET: list links ──
    search_query = request.GET.get('search', '')

    if request.user.is_staff:
        links = ShortLink.objects.select_related('user').all()
    else:
        links = ShortLink.objects.filter(user=request.user)

    if search_query:
        links = links.filter(
            Q(src__icontains=search_query) |
            Q(dest__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    links = links.order_by('-created_at')

    paginator = Paginator(links, 20)
    page = request.GET.get('page', 1)
    try:
        links_page = paginator.page(page)
    except PageNotAnInteger:
        links_page = paginator.page(1)
    except EmptyPage:
        links_page = paginator.page(paginator.num_pages)

    return render(request, 'main/go_links.html', {
        'links': links_page,
        'search_query': search_query,
    })


# ============================================================================
# Wiki Views
# ============================================================================

@login_required
def wiki_home(request):
    """Display wiki home page with all top-level pages"""
    # Get all root pages (no parent)
    root_pages = WikiPage.objects.filter(
        parent=None,
        is_published=True
    ).prefetch_related('children').order_by('display_order', 'title')
    
    # Get recently updated pages
    recent_pages = WikiPage.objects.filter(
        is_published=True
    ).order_by('-updated_at')[:5]
    
    # Get pending change requests count
    pending_changes_count = WikiPageChangeRequest.objects.filter(
        status='pending'
    ).count()
    
    return render(request, 'main/wiki_home.html', {
        'root_pages': root_pages,
        'recent_pages': recent_pages,
        'pending_changes_count': pending_changes_count,
    })


@login_required
def wiki_page(request, slug):
    """Display a single wiki page"""
    page = get_object_or_404(WikiPage, slug=slug, is_published=True)
    
    # Get child pages
    children = page.children.filter(is_published=True).order_by('display_order', 'title')
    
    # Get breadcrumbs
    breadcrumbs = page.get_breadcrumbs()
    
    # Get recent versions (for showing last editor info)
    recent_versions = page.versions.select_related('edited_by').order_by('-edited_at')[:3]
    
    # Get pending change requests for this page
    pending_requests = page.change_requests.filter(status='pending').select_related('requested_by')
    
    return render(request, 'main/wiki_page.html', {
        'page': page,
        'children': children,
        'breadcrumbs': breadcrumbs,
        'recent_versions': recent_versions,
        'pending_requests': pending_requests,
    })


@login_required
def wiki_create(request):
    """Create a new wiki page"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent', None)
        
        if not title or not content:
            django_messages.error(request, 'Title and content are required.')
            return redirect('wiki_create')
        
        # Auto-generate slug from title if not provided
        if not slug:
            from django.utils.text import slugify
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while WikiPage.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
        else:
            # Check if provided slug already exists
            if WikiPage.objects.filter(slug=slug).exists():
                django_messages.error(request, 'A page with this slug already exists.')
                return redirect('wiki_create')
        
        parent = None
        if parent_id:
            try:
                parent = WikiPage.objects.get(pk=parent_id)
            except WikiPage.DoesNotExist:
                pass
        
        page = WikiPage.objects.create(
            title=title,
            slug=slug,
            content=content,
            parent=parent,
            created_by=request.user,
            updated_by=request.user,
        )
        
        # Create initial version
        WikiPageVersion.objects.create(
            page=page,
            title=title,
            content=content,
            edited_by=request.user,
            change_summary="Initial creation"
        )
        
        django_messages.success(request, f'Wiki page "{title}" created successfully!')
        return redirect('wiki_page', slug=page.slug)
    
    # GET request - show form
    all_pages = WikiPage.objects.filter(is_published=True).order_by('title')
    return render(request, 'main/wiki_create.html', {
        'all_pages': all_pages,
    })


@login_required
def wiki_edit(request, slug):
    """Edit a wiki page - direct edit or suggest changes"""
    page = get_object_or_404(WikiPage, slug=slug)
    
    # Check if user can directly edit (staff or original creator)
    can_direct_edit = request.user.is_staff or page.created_by == request.user
    
    if request.method == 'POST':
        action = request.POST.get('action', 'edit')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        change_summary = request.POST.get('change_summary', '').strip()
        
        if not title or not content:
            django_messages.error(request, 'Title and content are required.')
            return redirect('wiki_edit', slug=slug)
        
        if action == 'direct_edit' and can_direct_edit:
            # Direct edit
            page.title = title
            page.content = content
            page.updated_by = request.user
            page.save()
            
            django_messages.success(request, 'Page updated successfully!')
            return redirect('wiki_page', slug=page.slug)
        else:
            # Create change request
            WikiPageChangeRequest.objects.create(
                page=page,
                requested_by=request.user,
                proposed_title=title if title != page.title else '',
                proposed_content=content,
                change_description=change_summary or 'Suggested changes',
            )
            
            django_messages.success(request, 'Your change request has been submitted for review!')
            return redirect('wiki_page', slug=page.slug)
    
    # GET request - show form
    return render(request, 'main/wiki_edit.html', {
        'page': page,
        'can_direct_edit': can_direct_edit,
    })


@login_required
def wiki_history(request, slug):
    """View version history of a wiki page"""
    page = get_object_or_404(WikiPage, slug=slug)
    
    versions = page.versions.select_related('edited_by').order_by('-edited_at')
    
    # Pagination
    paginator = Paginator(versions, 20)
    page_num = request.GET.get('page', 1)
    try:
        versions_page = paginator.page(page_num)
    except PageNotAnInteger:
        versions_page = paginator.page(1)
    except EmptyPage:
        versions_page = paginator.page(paginator.num_pages)
    
    return render(request, 'main/wiki_history.html', {
        'page': page,
        'versions': versions_page,
    })


@login_required
def wiki_version(request, slug, version_id):
    """View a specific version of a wiki page"""
    page = get_object_or_404(WikiPage, slug=slug)
    version = get_object_or_404(WikiPageVersion, pk=version_id, page=page)
    
    return render(request, 'main/wiki_version.html', {
        'page': page,
        'version': version,
    })


@login_required
def wiki_search(request):
    """Search wiki pages"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        results = WikiPage.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query),
            is_published=True
        ).order_by('-updated_at')
    
    # Pagination
    paginator = Paginator(results, 20)
    page_num = request.GET.get('page', 1)
    try:
        results_page = paginator.page(page_num)
    except PageNotAnInteger:
        results_page = paginator.page(1)
    except EmptyPage:
        results_page = paginator.page(paginator.num_pages)
    
    return render(request, 'main/wiki_search.html', {
        'query': query,
        'results': results_page,
    })


@login_required
def wiki_change_requests(request):
    """View all change requests (filterable by status)"""
    # Only staff can view all change requests
    # Regular users can only see their own
    if request.user.is_staff:
        requests_list = WikiPageChangeRequest.objects.select_related(
            'page', 'requested_by', 'reviewed_by'
        )
    else:
        requests_list = WikiPageChangeRequest.objects.filter(
            requested_by=request.user
        ).select_related('page', 'requested_by', 'reviewed_by')
    
    # Filter by status if provided
    status = request.GET.get('status', 'all')
    if status and status != 'all':
        requests_list = requests_list.filter(status=status)
    
    requests_list = requests_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requests_list, 15)
    page_num = request.GET.get('page', 1)
    try:
        requests_page = paginator.page(page_num)
    except PageNotAnInteger:
        requests_page = paginator.page(1)
    except EmptyPage:
        requests_page = paginator.page(paginator.num_pages)
    
    return render(request, 'main/wiki_change_requests.html', {
        'requests': requests_page,
        'status': status,
    })


@login_required
def wiki_change_request_detail(request, request_id):
    """View and review a change request"""
    change_request = get_object_or_404(WikiPageChangeRequest, pk=request_id)
    
    # Check permissions
    can_review = request.user.is_staff
    is_owner = change_request.requested_by == request.user
    
    if not (can_review or is_owner):
        django_messages.error(request, 'You do not have permission to view this request.')
        return redirect('wiki_change_requests')
    
    if request.method == 'POST' and can_review:
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '').strip()
        
        if action == 'approve':
            change_request.status = 'approved'
            change_request.reviewed_by = request.user
            change_request.reviewed_at = datetime.now()
            change_request.review_notes = review_notes
            change_request.save()
            
            # Apply the changes
            change_request.apply_changes()
            
            django_messages.success(request, 'Change request approved and applied!')
            return redirect('wiki_page', slug=change_request.page.slug)
        
        elif action == 'reject':
            change_request.status = 'rejected'
            change_request.reviewed_by = request.user
            change_request.reviewed_at = datetime.now()
            change_request.review_notes = review_notes
            change_request.save()
            
            django_messages.success(request, 'Change request rejected.')
            return redirect('wiki_change_requests')
    
    return render(request, 'main/wiki_change_request_detail.html', {
        'change_request': change_request,
        'can_review': can_review,
        'is_owner': is_owner,
    })


@login_required
def wiki_upload_image(request):
    """Handle image upload for wiki pages"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            description = request.POST.get('description', '')
            
            # Create WikiImage instance
            wiki_image = WikiImage.objects.create(
                image=image_file,
                uploaded_by=request.user,
                description=description
            )
            
            # Return image URL for markdown insertion
            return JsonResponse({
                'success': True,
                'url': wiki_image.image.url,
                'id': wiki_image.id,
                'markdown': f'![{description or "Image"}]({wiki_image.image.url})'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'No image provided'
    }, status=400)
