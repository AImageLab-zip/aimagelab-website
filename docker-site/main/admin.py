from django.contrib import admin
from .models import UserProfile, Category, Post, Project, PublicationIRIS, UserProfilePublicationIRIS, IRISImportLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'display_order', 'is_visible', 'created_at')
    list_filter = ('role', 'is_visible')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bio')
    list_editable = ('display_order', 'is_visible')
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'codice_fiscale')
        }),
        ('IRIS Integration', {
            'fields': ('iris_pid', 'iris_id', 'iris_id_ab', 'id_iris'),
            'classes': ('collapse',),
            'description': 'IRIS identifiers cached from API using Codice Fiscale'
        }),
        ('Role & Position', {
            'fields': ('role', 'current_position', 'display_order', 'is_visible')
        }),
        ('About', {
            'fields': ('bio', 'avatar')
        }),
        ('Contact', {
            'fields': ('phone_number', 'website', 'google_scholar', 'github', 'linkedin')
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

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'project_type', 'start_date', 'end_date')
    list_filter = ('project_type', 'start_date')
    search_fields = ('title', 'name', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'description', 'logo', 'website')
        }),
        ('Project Details', {
            'fields': ('project_type', 'founding_by')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PublicationIRIS)
class PublicationIRISAdmin(admin.ModelAdmin):
    list_display = ('titolo_short', 'anno', 'tipo', 'autori_short', 'hidden', 'updated_at')
    list_filter = ('anno', 'tipo', 'hidden')
    search_fields = ('titolo', 'autori', 'id_iris', 'doi')
    list_editable = ('hidden',)
    date_hierarchy = 'updated_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id_iris', 'titolo', 'anno', 'autori')
        }),
        ('Publication Details', {
            'fields': ('tipo', 'tipologia', 'rivista', 'abstract')
        }),
        ('Identifiers', {
            'fields': ('doi', 'isbn', 'issn', 'url')
        }),
        ('Publishing Info', {
            'fields': ('editore', 'luogo', 'volume', 'numero', 'pagine')
        }),
        ('Attachments', {
            'fields': ('pdf', 'allegati')
        }),
        ('Status', {
            'fields': ('stato', 'hidden')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def titolo_short(self, obj):
        return obj.titolo[:100] + '...' if len(obj.titolo) > 100 else obj.titolo
    titolo_short.short_description = 'Title'
    
    def autori_short(self, obj):
        return obj.autori[:50] + '...' if len(obj.autori) > 50 else obj.autori
    autori_short.short_description = 'Authors'


@admin.register(UserProfilePublicationIRIS)
class UserProfilePublicationIRISAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'publication_short', 'posizione', 'created_at')
    list_filter = ('user_profile__role', 'posizione')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name', 'publication__titolo')
    autocomplete_fields = ['user_profile', 'publication']
    
    fieldsets = (
        ('Link', {
            'fields': ('user_profile', 'publication', 'posizione')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def publication_short(self, obj):
        return str(obj.publication)[:80]
    publication_short.short_description = 'Publication'


@admin.register(IRISImportLog)
class IRISImportLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'started_at', 'completed_at', 
                    'staff_processed', 'publications_created', 'publications_updated')
    list_filter = ('status', 'started_at')
    search_fields = ('error_message',)
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': ('staff_processed', 'publications_created', 
                       'publications_updated', 'links_created')
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('started_at',)
    
    def has_add_permission(self, request):
        # Prevent manual creation of import logs
        return False


admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Project, ProjectAdmin)
