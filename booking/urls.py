from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('new/', views.book, name='book'),
    path('track/<str:booking_id>/', views.track_booking, name='track'),
    path('trip/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('history/', views.trip_history, name='history'),
    path('trip/<int:trip_id>/cancel/', views.cancel_trip, name='cancel_trip'),
    path('trip/<int:trip_id>/rate/', views.rate_trip, name='rate_trip'),
    path('trip/<int:trip_id>/location/', views.update_trip_location, name='update_trip_location'),
    path('request/<int:request_id>/accept/', views.accept_booking, name='accept_booking'),
    path('request/<int:request_id>/reject/', views.reject_booking, name='reject_booking'),
    path('shared/', views.shared_ride, name='shared_ride'),
]

