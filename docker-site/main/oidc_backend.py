"""
Custom OIDC Authentication Backend for AImageLab Website

This module provides a custom OpenID Connect (OIDC) authentication backend
that integrates with the UserProfile model and handles user creation/updates
during OIDC authentication.
"""

from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User
from django.conf import settings
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)


class CustomOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """
    Custom OIDC authentication backend that creates/updates UserProfile
    along with Django User on OIDC authentication.
    """

    def create_user(self, claims):
        """
        Create a new Django user from OIDC claims.
        
        Args:
            claims (dict): User information from OIDC provider
            
        Returns:
            User: Newly created Django user
        """
        email = claims.get('email', '')
        username = self.get_username(claims)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=claims.get('given_name', ''),
            last_name=claims.get('family_name', ''),
        )
        
        logger.info(f"Created new user via OIDC: {username}")
        
        # Create associated UserProfile
        self.create_or_update_profile(user, claims)
        
        return user

    def update_user(self, user, claims):
        """
        Do NOT update existing user information from OIDC claims.
        Existing users should maintain their current data and not be modified.
        
        Args:
            user (User): Existing Django user
            claims (dict): User information from OIDC provider
            
        Returns:
            User: Unchanged Django user
        """
        logger.info(f"User {user.username} logged in via OIDC (no updates to existing user)")
        
        # Do not modify existing user or profile
        # Just authenticate and return
        return user

    def create_or_update_profile(self, user, claims):
        """
        Create UserProfile ONLY if it doesn't exist.
        Do NOT update existing profiles - preserve existing user data.
        
        Args:
            user (User): Django user object
            claims (dict): User information from OIDC provider
        """
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': getattr(settings, 'OIDC_DEFAULT_USER_ROLE', 'phd'),
                'is_visible': False,  # New users are hidden by default
                'display_order': 0,
            }
        )
        
        if created:
            logger.info(f"Created UserProfile for new OIDC user: {user.username} (is_visible=False)")
        else:
            logger.info(f"UserProfile already exists for {user.username} (no changes made)")
        
        # Do NOT update existing profiles
        # Profile data should only be modified through the edit_profile view

    def filter_users_by_claims(self, claims):
        """
        Filter users by OIDC claims to find existing user.
        
        Args:
            claims (dict): User information from OIDC provider
            
        Returns:
            QuerySet: Filtered User queryset
        """
        email = claims.get('email')
        
        if not email:
            return User.objects.none()
        
        # Try to find user by email first
        users = User.objects.filter(email__iexact=email)
        
        if users.exists():
            return users
        
        # Fall back to username-based lookup
        username = self.get_username(claims)
        return User.objects.filter(username__iexact=username)

    def get_username(self, claims):
        """
        Generate username from OIDC claims.
        
        Args:
            claims (dict): User information from OIDC provider
            
        Returns:
            str: Username for the user
        """
        return generate_username(claims)


def generate_username(claims):
    """
    Generate a unique username from OIDC claims.
    
    This function is used by the OIDC_USERNAME_ALGO setting.
    You can customize this based on your OIDC provider's claims.
    
    Args:
        claims (dict): User information from OIDC provider
        
    Returns:
        str: Generated username
    """
    # Try different claim fields in order of preference
    username = (
        claims.get('preferred_username') or
        claims.get('username') or
        claims.get('sub') or
        claims.get('email', '').split('@')[0]
    )
    
    # Sanitize username (remove special characters, limit length)
    username = username.lower().strip()[:150]
    
    # Ensure username is unique
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


def provider_logout(request):
    """
    Generate the logout URL for the OIDC provider.
    
    This function is used by the OIDC_OP_LOGOUT_URL_METHOD setting.
    
    Args:
        request: Django HTTP request
        
    Returns:
        str: Provider logout URL with redirect parameter
    """
    logout_url = getattr(settings, 'OIDC_OP_LOGOUT_ENDPOINT', None)
    
    if not logout_url:
        return None
    
    # Build the redirect URL (where user should return after logout)
    redirect_url = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)
    
    # Construct the full logout URL with redirect parameter
    # Adjust the parameter name based on your OIDC provider's requirements
    return f"{logout_url}?redirect_uri={redirect_url}"
