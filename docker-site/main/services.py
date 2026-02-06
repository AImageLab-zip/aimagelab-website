"""
Business logic and services for the main app.
This module contains functions for managing users and profiles.
"""
from django.contrib.auth.models import User
from .models import UserProfile


def add_or_update_user(user_data):
    """
    Add or update a user with profile information.
    
    Args:
        user_data (dict): Dictionary containing user information with keys:
            - username (str, required): Username
            - email (str, required): Email address
            - first_name (str, optional): First name
            - last_name (str, optional): Last name
            - password (str, optional): Password (only for new users, will be set as is if provided)
            - role (str, optional): Role choice (default: 'phd')
            - bio (str, optional): Biography
            - website (str, optional): Personal website URL
            - display_order (int, optional): Display order (default: 0)
            - is_visible (bool, optional): Visibility on People page (default: True)
            - current_position (str, optional): Current position (for alumni)
            - google_scholar (str, optional): Google Scholar URL
            - github (str, optional): GitHub URL
            - linkedin (str, optional): LinkedIn URL
            - phone_number (str, optional): Phone number in international format
    
    Returns:
        tuple: (User, UserProfile, created) where created is True if a new user was created
    
    Raises:
        ValueError: If username or email are not provided
    
    Example:
        >>> user_data = {
        ...     'username': 'jdoe',
        ...     'email': 'john.doe@example.com',
        ...     'first_name': 'John',
        ...     'last_name': 'Doe',
        ...     'role': 'phd',
        ...     'bio': 'PhD student working on Computer Vision',
        ...     'google_scholar': 'https://scholar.google.com/...',
        ... }
        >>> user, profile, created = add_or_update_user(user_data)
    """
    # Required fields
    username = user_data.get('username')
    email = user_data.get('email')
    
    if not username or not email:
        raise ValueError("username and email are required fields")
    
    # Get or create user
    user, user_created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
        }
    )
    
    # Update user fields if not newly created
    if not user_created:
        user.email = email
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()
    
    # Set password only for new users and if provided
    if user_created and 'password' in user_data:
        user.set_password(user_data['password'])
        user.save()
    
    # Get or create profile
    profile, profile_created = UserProfile.objects.get_or_create(user=user)
    
    # Update profile fields
    profile_fields = [
        'role', 'bio', 'website', 'display_order', 'is_visible',
        'current_position', 'google_scholar', 'github', 'linkedin', 'phone_number'
    ]
    
    for field in profile_fields:
        if field in user_data:
            setattr(profile, field, user_data[field])
    
    # Handle avatar separately (ImageField)
    if 'avatar_path' in user_data:
        profile.avatar = user_data['avatar_path']
    
    profile.save()
    
    return user, profile, user_created


def bulk_add_or_update_users(users_data_list):
    """
    Add or update multiple users in batch.
    
    Args:
        users_data_list (list): List of user data dictionaries
    
    Returns:
        dict: Summary with 'created', 'updated', and 'errors' counts and lists
    
    Example:
        >>> users = [
        ...     {'username': 'user1', 'email': 'user1@example.com', 'role': 'phd'},
        ...     {'username': 'user2', 'email': 'user2@example.com', 'role': 'postdoc'},
        ... ]
        >>> result = bulk_add_or_update_users(users)
        >>> print(f"Created: {result['created_count']}, Updated: {result['updated_count']}")
    """
    results = {
        'created': [],
        'updated': [],
        'errors': [],
        'created_count': 0,
        'updated_count': 0,
        'error_count': 0,
    }
    
    for user_data in users_data_list:
        try:
            user, profile, created = add_or_update_user(user_data)
            if created:
                results['created'].append(user.username)
                results['created_count'] += 1
            else:
                results['updated'].append(user.username)
                results['updated_count'] += 1
        except Exception as e:
            error_info = {
                'username': user_data.get('username', 'unknown'),
                'error': str(e)
            }
            results['errors'].append(error_info)
            results['error_count'] += 1
    
    return results
