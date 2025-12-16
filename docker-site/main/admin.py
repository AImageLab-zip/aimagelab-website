from django.contrib import admin
from .models import UserProfile, Category, Post


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'display_order', 'is_visible', 'created_at')
    list_filter = ('role', 'is_visible')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bio')
    list_editable = ('display_order', 'is_visible')
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Role & Position', {
            'fields': ('role', 'current_position', 'display_order', 'is_visible')
        }),
        ('About', {
            'fields': ('bio', 'avatar')
        }),
        ('Links', {
            'fields': ('website', 'google_scholar', 'github', 'linkedin')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')



class CategoryAdmin(admin.ModelAdmin):
    pass

class PostAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)