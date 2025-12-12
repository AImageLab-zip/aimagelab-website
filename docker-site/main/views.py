from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserProfile
from .tasks import sync_user_task
import os


def home(request):
    """Home page view."""
    return render(request, 'main/home.html')


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


@login_required
def edit_profile(request):
    """Profile edit view for authenticated users."""
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'role': 'phd',  # default role for manually created profiles
            'is_visible': True,
            'display_order': 0,
        }
    )

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
