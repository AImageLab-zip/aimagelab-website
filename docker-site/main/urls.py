from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('people/', views.people, name='people'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('news/', views.news, name='news'),
    path('news/add/', views.post_add, name='post_add'),
    path('news/<slug:slug>/', views.post_single, name='single'),
    path('news/<slug:slug>/edit/', views.post_edit, name='post_edit'),
]
