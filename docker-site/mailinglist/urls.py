from django.urls import path
from . import views

app_name = 'mailinglist'

urlpatterns = [
    # User preferences
    path('preferences/', views.mailing_preferences, name='preferences'),

    # Moderation (staff)
    path('moderation/', views.moderation_queue, name='moderation'),
    path('moderation/<int:email_id>/', views.moderation_detail, name='moderation_detail'),

    # Unsubscribe (public, token-based)
    path('unsubscribe/<str:token>/', views.unsubscribe, name='unsubscribe'),

    # External subscription (public)
    path('subscribe/', views.external_subscribe, name='external_subscribe'),
]
