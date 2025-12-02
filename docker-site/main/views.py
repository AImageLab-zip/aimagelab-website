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
    posts = Post.objects.filter(is_published=True).order_by('-published_at')
    return render(request, 'main/news.html', {'posts': posts})

@login_required
def add_post(request):
    """Add a new post."""
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        content = request.POST.get('content')
        is_published = request.POST.get('is_published') == 'true'
        cover = request.FILES.get('cover')
        
        post = Post.objects.create(
            title=title,
            slug=slug,
            description=description,
            content=content,
            is_published=is_published,
            cover=cover
        )
        messages.success(request, 'Post added successfully!')
        return redirect('news')
    return redirect('news')

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
