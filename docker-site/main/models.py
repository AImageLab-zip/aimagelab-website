# Main app models
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile for team members"""
    
    ROLE_CHOICES = [
        ('professor', 'Full Professor'),
        ('assoc_professor', 'Associate Professor'),
        ('asst_professor', 'Assistant Professor'),
        ('postdoc', 'Postdoctoral Researcher'),
        ('phd', 'PhD Student'),
        ('intern', 'Research Intern'),
        ('alumni', 'Alumni'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='phd')
    bio = models.TextField(blank=True, help_text="Short biography")
    website = models.URLField(blank=True, help_text="Personal website or homepage")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    display_order = models.IntegerField(default=0, help_text="Order in team listing (lower first)")
    is_visible = models.BooleanField(default=True, help_text="Show on People page")
    
    # Alumni-specific fields
    current_position = models.CharField(max_length=200, blank=True, help_text="Current position (for alumni)")
    
    # Additional info
    google_scholar = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def get_full_name(self):
        return self.user.get_full_name() or self.user.username
