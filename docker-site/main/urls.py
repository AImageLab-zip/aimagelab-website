from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('intranet/', views.intranet_public, name='intranet_public'),
    path('people/', views.people, name='people'),
    path('contacts/', views.contacts, name='contacts'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('add-user/', views.add_user, name='add_user'),
    path('sync-ldap/', views.sync_ldap, name='sync_ldap'),
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('iris/import/', views.trigger_iris_import, name='trigger_iris_import'),
    path('iris/import-photos/', views.trigger_iris_photo_import, name='trigger_iris_photo_import'),
    path('iris/status/', views.iris_import_status, name='iris_import_status'),
    path('research/', views.research, name='research'),
    path('news/', views.news, name='news'),
    path('publications/', views.publications, name='publications'),
    path('projects/', views.projects, name='projects'),
    path('news/add/', views.post_form, name='post_add'),
    path('news/<slug:slug>/', views.post_single, name='single'),
    path('news/<slug:slug>/edit/', views.post_form, name='post_edit'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    
    # Meeting room reservations
    path('rooms/', views.rooms_calendar, name='rooms_calendar'),
    path('rooms/list/', views.rooms_list, name='rooms_list'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/reserve/', views.create_reservation, name='create_reservation'),
    path('rooms/reservation/<int:reservation_id>/edit/', views.edit_reservation, name='edit_reservation'),
    path('rooms/reservation/<int:reservation_id>/delete/', views.delete_reservation, name='delete_reservation'),

    # Short links (Go)
    path('go/', views.go_links, name='go_links'),
    re_path(r'^go/(?P<src>[-a-zA-Z0-9_.]+)$', views.go_redirect, name='go_redirect'),
    
    # Wiki
    path('wiki/', views.wiki_home, name='wiki_home'),
    path('wiki/search/', views.wiki_search, name='wiki_search'),
    path('wiki/create/', views.wiki_create, name='wiki_create'),
    path('wiki/upload-image/', views.wiki_upload_image, name='wiki_upload_image'),
    path('wiki/changes/', views.wiki_change_requests, name='wiki_change_requests'),
    path('wiki/changes/<int:request_id>/', views.wiki_change_request_detail, name='wiki_change_request_detail'),
    path('wiki/<slug:slug>/', views.wiki_page, name='wiki_page'),
    path('wiki/<slug:slug>/edit/', views.wiki_edit, name='wiki_edit'),
    path('wiki/<slug:slug>/history/', views.wiki_history, name='wiki_history'),
    path('wiki/<slug:slug>/version/<int:version_id>/', views.wiki_version, name='wiki_version'),
    path('wiki/<slug:slug>/delete/', views.wiki_delete, name='wiki_delete'),
]

