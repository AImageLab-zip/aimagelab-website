from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
import os
from .models import UserProfile, IRISImportLog
from .tasks import import_iris_publications, is_import_running


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
        messages.error(request, 'Invalid request method.')
        return redirect('dashboard')
    
    # Check if import is already running
    if is_import_running():
        messages.warning(
            request,
            'IRIS import is already in progress. Please wait for it to complete.'
        )
        return redirect('dashboard')
    
    # Start the import task
    task = import_iris_publications.delay()
    
    messages.success(
        request,
        f'IRIS import started successfully! Task ID: {task.id}. '
        'You will be notified when the import is complete.'
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

