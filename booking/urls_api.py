from django.urls import path
from . import views

app_name = 'booking_api'

urlpatterns = [
    # Booking Creation
    path('create/', views.book, name='api_book_create'),
    path('estimate/', views.estimate_fare_api, name='api_estimate_fare'),
    
    # Booking Tracking
    path('track/<str:booking_id>/', views.track_booking, name='api_track_booking'),
    path('trip/<int:trip_id>/', views.trip_detail, name='api_trip_detail'),
    
    # Booking History
    path('history/', views.trip_history, name='api_trip_history'),
    path('history/<str:filter_type>/', views.trip_history_filtered, name='api_trip_history_filtered'),
    
    # Booking Actions
    path('trip/<int:trip_id>/cancel/', views.cancel_trip, name='api_cancel_trip'),
    path('trip/<int:trip_id>/rate/', views.rate_trip, name='api_rate_trip'),
    path('trip/<int:trip_id>/location/', views.update_trip_location, name='api_update_location'),
    
    # Booking Requests
    path('request/<int:request_id>/accept/', views.accept_booking, name='api_accept_booking'),
    path('request/<int:request_id>/reject/', views.reject_booking, name='api_reject_booking'),
    path('request/<int:request_id>/', views.get_booking_request, name='api_get_booking_request'),
    
    # Driver Availability
    path('drivers/available/', views.get_available_drivers, name='api_available_drivers'),
    path('drivers/nearby/', views.get_nearby_drivers, name='api_nearby_drivers'),
]

