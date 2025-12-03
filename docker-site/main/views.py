from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, Post



def home(request):
    """Home page view."""
    return render(request, 'main/home.html')

def news(request):
    """News/Blog page view."""
    if request.user.is_authenticated:
        posts = Post.objects.order_by('-created_at')
    else:
        posts = Post.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'main/news.html', {'posts': posts})

def post_single(request, slug):
    """Single post detail view."""
    post = Post.objects.get(slug=slug)
    return render(request, 'main/single.html', {'post': post})

@login_required
def post_form(request, slug=None):
    """Add or edit a post."""
    post = Post.objects.get(slug=slug) if slug else None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        title = request.POST.get('title')
        new_slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        content = request.POST.get('content')
        cover = request.FILES.get('cover')
        is_published = action == 'publish'
        
        if post:
            # Edit existing post
            post.title = title
            post.slug = new_slug
            post.description = description
            post.content = content
            if cover:
                post.cover = cover
            if action in ['publish', 'draft']:
                post.is_published = is_published
            post.save()
        else:
            # Create new post
            post = Post.objects.create(
                title=title,
                slug=new_slug,
                description=description,
                content=content,
                is_published=is_published,
                cover=cover
            )
        
        if action == 'publish':
            messages.success(request, 'Post published successfully!')
        elif action == 'draft':
            messages.success(request, 'Post saved as draft!')
        else:
            messages.success(request, 'Post updated successfully!')
        
        return redirect('single', slug=post.slug)
    
    template = 'main/post_edit.html' if post else 'main/post_edit.html'
    return render(request, template, {'post': post} if post else {})

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
