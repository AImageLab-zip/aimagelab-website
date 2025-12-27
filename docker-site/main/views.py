from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserProfile, Post, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from datetime import datetime

from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import UserProfile
from .tasks import sync_user_task
import os

POST_PER_PAGE = 10

def home(request):
    """Home page view."""
    # Get latest posts without event_date
    latest_posts = Post.objects.filter(
        is_published=True,
        event_date__isnull=True
    ).order_by('-created_at')[:4]
    
    
    return render(request, 'main/home.html', {
        'latest_posts': latest_posts
    })

def contacts(request):
    """Contacts page view."""
    return render(request, 'main/contacts.html')

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
        event_date__isnull=False
    ).order_by('event_date')[:5]
    
    categories = Category.objects.all().order_by('name')
    
    return render(request, 'main/news.html', {
        'posts': posts_page,
        'search_query': search_query,
        'category_query': category_query,
        'upcoming_events': upcoming_events,
        'categories': categories    
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
                event_date=event_date,
                is_pinned=is_pinned,
            )
            post.categories.set(category_ids)
        
        if action == 'publish':
            messages.success(request, 'Post published successfully!')
        elif action == 'draft':
            messages.success(request, 'Post saved as draft!')
        else:
            messages.success(request, 'Post updated successfully!')
        
        return redirect('single', slug=post.slug)
    
    template = 'main/post_edit.html'
    context = {'post': post, 'categories': categories}
    return render(request, template, context)

def people(request):
    """People/Team page view."""
    # Get visible profiles grouped by role
    profiles = UserProfile.objects.filter(is_visible=True).select_related('user')
    
    # Group by role
    grouped_profiles = {
        'professors': profiles.filter(role__in=['professor', 'assoc_professor', 'asst_professor']),
        'postdocs': profiles.filter(role='postdoc'),
        'phd_students': profiles.filter(role='phd'),
        'interns': profiles.filter(role='intern'),
        'alumni': profiles.filter(role='alumni'),
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
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'OIDC_PROVIDER_NAME': getattr(settings, 'OIDC_PROVIDER_NAME', 'OIDC Provider')
    }
    return render(request, 'main/login.html', context)


def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    """Dashboard view (requires login)."""
    return render(request, 'main/dashboard.html')


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
        messages.error(
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
        profile.phone_number = request.POST.get('phone_number', '').strip() or None

        # Handle avatar upload
        if 'avatar' in request.FILES and request.FILES['avatar']:
            # Delete old avatar if exists
            if profile.avatar:
                profile.avatar.delete()
            # Save new avatar
            avatar_file = request.FILES['avatar']
            profile.avatar.save(f"{request.user.username}_{avatar_file.name}", avatar_file)

        # Handle avatar removal
        if request.POST.get('remove_avatar') == 'on' and profile.avatar:
            profile.avatar.delete()
            profile.avatar = None

        profile.save()
        messages.success(request, 'Profile updated successfully!')
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
            
            messages.success(
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
            messages.error(request, f'Error starting task: {str(e)}')
            
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
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    if request.method == 'POST':
        try:
            # Launch LDAP sync task asynchronously
            task = populate_users_from_ldap.delay()
            
            messages.success(
                request,
                f'LDAP synchronization started! Task ID: {task.id}. This may take a few moments.'
            )
        except Exception as e:
            messages.error(request, f'Error starting LDAP sync: {str(e)}')
    
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
