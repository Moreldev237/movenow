from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('fleet/dashboard/', views.fleet_dashboard, name='fleet_dashboard'),
    path('schedule/', views.schedule_booking, name='schedule_booking'),
    path('share/location/', views.share_location, name='share_location'),
    path('safety/', views.safety, name='safety'),
    path('help/', views.help, name='help'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('referral/', views.referral, name='referral'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', 
         views.notification_mark_read, name='notification_mark_read'),
]
