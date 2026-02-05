from django.urls import path
from . import views

app_name = 'core_api'

urlpatterns = [
    path('calculate-fare/', views.calculate_fare, name='api_calculate_fare'),
    path('search-drivers/', views.search_drivers, name='api_search_drivers'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='api_notifications'),
    path('notifications/<int:notification_id>/', views.notification_detail, name='api_notification_detail'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='api_notification_mark_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='api_mark_all_read'),
    
    # General
    path('dashboard/', views.dashboard, name='api_dashboard'),
    path('ping/', views.ping, name='api_ping'),
]

