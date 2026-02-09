from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('people/', views.people, name='people'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('media/<path:path>', views.serve_media, name='serve_media'),
    path('iris/import/', views.trigger_iris_import, name='trigger_iris_import'),
    path('iris/status/', views.iris_import_status, name='iris_import_status'),
]

