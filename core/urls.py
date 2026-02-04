from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', 
         views.notification_mark_read, name='notification_mark_read'),
]

# API URLs
api_urlpatterns = [
    path('calculate-fare/', views.calculate_fare, name='calculate_fare'),
    path('search-drivers/', views.search_drivers, name='search_drivers'),
]