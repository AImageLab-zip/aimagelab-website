from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, Post, Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from datetime import datetime

from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import UserProfile

POST_PER_PAGE = 5

def home(request):
    """Home page view."""
    return render(request, 'main/home.html')

def news(request):
    """News/Blog page view with pagination and search."""
    search_query = request.GET.get('search', '')
    
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
    
    return render(request, 'main/news.html', {
        'posts': posts_page,
        'search_query': search_query,
    })

def post_single(request, slug):
    """Single post detail view."""
    post = Post.objects.get(slug=slug)
    return render(request, 'main/single.html', {'post': post})

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
        is_event_checked = request.POST.get('is_event') == 'on'
        event_date_raw = request.POST.get('event_date') or None
        event_date = None
        if is_event_checked and event_date_raw:
            try:
                event_date = datetime.strptime(event_date_raw, "%Y-%m-%d").date()
            except ValueError:
                event_date = None
        is_published = action == 'publish'
        
        if post:
            # Edit existing post
            post.title = title
            post.slug = new_slug
            post.description = description
            post.content = content
            post.event_date = event_date
            if cover:
                post.cover = cover
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
    
    return render(request, 'main/login.html')


def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard(request):
    """Dashboard view (requires login)."""
    return render(request, 'main/dashboard.html')


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
