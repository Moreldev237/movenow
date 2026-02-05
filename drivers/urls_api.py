from django.urls import path
from . import views

app_name = 'drivers_api'

urlpatterns = [
    # Driver Profile
    path('profile/', views.driver_profile, name='api_driver_profile'),
    path('profile/update/', views.update_driver_profile, name='api_update_driver_profile'),
    
    # Driver Status
    path('status/', views.get_driver_status, name='api_driver_status'),
    path('status/update/', views.update_driver_status, name='api_update_driver_status'),
    
    # Availability
    path('availability/', views.set_availability, name='api_set_availability'),
    path('location/update/', views.update_location, name='api_update_location'),
    
    # Trips
    path('trips/', views.driver_trips, name='api_driver_trips'),
    path('trips/available/', views.available_trips, name='api_available_trips'),
    path('trips/<int:trip_id>/accept/', views.accept_trip, name='api_accept_trip'),
    path('trips/<int:trip_id>/decline/', views.decline_trip, name='api_decline_trip'),
    path('trips/<int:trip_id>/start/', views.start_trip, name='api_start_trip'),
    path('trips/<int:trip_id>/complete/', views.complete_trip, name='api_complete_trip'),
    
    # Earnings
    path('earnings/', views.earnings, name='api_earnings'),
    path('earnings/daily/', views.daily_earnings, name='api_daily_earnings'),
    path('earnings/weekly/', views.weekly_earnings, name='api_weekly_earnings'),
    
    # Documents
    path('documents/', views.list_documents, name='api_list_documents'),
    path('documents/upload/', views.upload_document, name='api_upload_document'),
    path('documents/<int:doc_id>/', views.document_detail, name='api_document_detail'),
]

