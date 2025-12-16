from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('people/', views.people, name='people'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('add-user/', views.add_user, name='add_user'),
    path('sync-ldap/', views.sync_ldap, name='sync_ldap'),
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('news/', views.news, name='news'),
    path('news/add/', views.post_form, name='post_add'),
    path('news/<slug:slug>/', views.post_single, name='single'),
    path('news/<slug:slug>/edit/', views.post_form, name='post_edit'),
]
