from django.contrib import admin
from .models import UserProfile, Category, Post, Project, PublicationIRIS, UserProfilePublicationIRIS, IRISImportLog, MeetingRoom, RoomReservation, ShortLink, HistoryMilestone, ResearchArea, DashboardCard, WikiPage, WikiPageVersion, WikiPageChangeRequest, WikiImage

admin.site.site_header = "AImageLab Admin"
admin.site.site_title = "AImageLab Admin"
admin.site.index_title = "Site Management"


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
            'fields': ('bio', 'avatar', 'avatar_iris')
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
            'fields': ('id_iris', 'titolo', 'anno', 'autori', 'keywords')
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


@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'location', 'description')
    list_editable = ('is_active',)
    fieldsets = (
        ('Room Information', {
            'fields': ('name', 'location', 'capacity', 'description', 'image')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('src', 'dest_short', 'user', 'click_count', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('src', 'dest', 'description', 'user__username')
    readonly_fields = ('click_count', 'created_at', 'updated_at')
    autocomplete_fields = ['user']
    fieldsets = (
        ('Link', {
            'fields': ('src', 'dest', 'description')
        }),
        ('Owner', {
            'fields': ('user',)
        }),
        ('Statistics', {
            'fields': ('click_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def dest_short(self, obj):
        return obj.dest[:80] + '...' if len(obj.dest) > 80 else obj.dest
    dest_short.short_description = 'Destination'


@admin.register(RoomReservation)
class RoomReservationAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'title', 'start_time', 'end_time', 'created_at')
    list_filter = ('room', 'created_at', 'start_time')
    search_fields = ('title', 'description', 'user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'start_time'
    autocomplete_fields = ['user']
    fieldsets = (
        ('Reservation Details', {
            'fields': ('room', 'user', 'title', 'description')
        }),
        ('Time Slot', {
            'fields': ('start_time', 'end_time')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(HistoryMilestone)
class HistoryMilestoneAdmin(admin.ModelAdmin):
    list_display = ('year_label', 'title', 'icon', 'display_order')
    list_editable = ('display_order',)
    search_fields = ('title', 'description')
    fieldsets = (
        ('Content', {
            'fields': ('year_label', 'title', 'icon', 'description')
        }),
        ('Display', {
            'fields': ('display_order',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ResearchArea)
class ResearchAreaAdmin(admin.ModelAdmin):
    list_display = ('title', 'area_id', 'icon', 'color', 'display_order')
    list_editable = ('display_order', 'color')
    search_fields = ('title', 'homepage_caption', 'intro', 'detail')
    prepopulated_fields = {'area_id': ('title',)}
    fieldsets = (
        ('Identity', {
            'fields': ('title', 'area_id', 'icon', 'color')
        }),
        ('Text Content', {
            'fields': ('homepage_caption', 'intro', 'detail', 'keywords')
        }),
        ('Display', {
            'fields': ('display_order',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DashboardCard)
class DashboardCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'link_type', 'logo_type', 'display_order', 'is_active')
    list_filter = ('section', 'link_type', 'logo_type', 'is_active')
    list_editable = ('display_order', 'is_active')
    search_fields = ('title', 'description', 'section')
    fieldsets = (
        ('Content', {
            'fields': ('title', 'description', 'section')
        }),
        ('Logo', {
            'fields': ('logo_type', 'logo_external_url', 'logo_lucide_icon', 'logo_upload'),
            'description': 'Choose a logo type and fill the corresponding field.'
        }),
        ('Link', {
            'fields': ('link_type', 'link_url', 'link_file'),
            'description': 'Choose link type: external URL or a downloadable file.'
        }),
        ('Display', {
            'fields': ('display_order', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')



@admin.register(WikiPage)
class WikiPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'parent', 'display_order', 'is_published', 'updated_at', 'updated_by')
    list_filter = ('is_published', 'created_at', 'updated_at')
    search_fields = ('title', 'slug', 'content')
    list_editable = ('display_order', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['created_by', 'updated_by', 'parent']
    fieldsets = (
        ('Page Content', {
            'fields': ('title', 'slug', 'content')
        }),
        ('Organization', {
            'fields': ('parent', 'display_order', 'is_published')
        }),
        ('Authorship', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WikiPageVersion)
class WikiPageVersionAdmin(admin.ModelAdmin):
    list_display = ('page', 'edited_by', 'edited_at', 'change_summary_short')
    list_filter = ('edited_at', 'edited_by')
    search_fields = ('page__title', 'title', 'content', 'change_summary')
    date_hierarchy = 'edited_at'
    autocomplete_fields = ['page', 'edited_by']
    fieldsets = (
        ('Version Info', {
            'fields': ('page', 'edited_by', 'edited_at', 'change_summary')
        }),
        ('Content', {
            'fields': ('title', 'content'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('edited_at',)
    
    def change_summary_short(self, obj):
        return obj.change_summary[:50] + '...' if len(obj.change_summary) > 50 else obj.change_summary
    change_summary_short.short_description = 'Change Summary'
    
    def has_add_permission(self, request):
        # Prevent manual creation of versions (they're auto-created)
        return False


@admin.register(WikiPageChangeRequest)
class WikiPageChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('page', 'requested_by', 'status', 'created_at', 'reviewed_by')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('page__title', 'requested_by__username', 'change_description', 'proposed_content')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['page', 'requested_by', 'reviewed_by']
    fieldsets = (
        ('Request Details', {
            'fields': ('page', 'requested_by', 'created_at')
        }),
        ('Proposed Changes', {
            'fields': ('proposed_title', 'proposed_content', 'change_description')
        }),
        ('Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from datetime import datetime
        for change_request in queryset.filter(status='pending'):
            change_request.status = 'approved'
            change_request.reviewed_by = request.user
            change_request.reviewed_at = datetime.now()
            change_request.save()
            change_request.apply_changes()
        self.message_user(request, f"{queryset.count()} change request(s) approved.")
    approve_requests.short_description = "Approve selected change requests"
    
    def reject_requests(self, request, queryset):
        from datetime import datetime
        for change_request in queryset.filter(status='pending'):
            change_request.status = 'rejected'
            change_request.reviewed_by = request.user
            change_request.reviewed_at = datetime.now()
            change_request.save()
        self.message_user(request, f"{queryset.count()} change request(s) rejected.")
    reject_requests.short_description = "Reject selected change requests"


@admin.register(WikiImage)
class WikiImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'uploaded_by', 'uploaded_at', 'image_thumbnail')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('description',)
    readonly_fields = ('uploaded_at', 'image_preview')
    
    def image_thumbnail(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px; max-width: 100px;" />'
        return '-'
    image_thumbnail.short_description = 'Thumbnail'
    image_thumbnail.allow_tags = True
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 300px; max-width: 500px;" />'
        return '-'
    image_preview.short_description = 'Preview'
    image_preview.allow_tags = True
