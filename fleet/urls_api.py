from django.urls import path
from . import views

app_name = 'fleet_api'

urlpatterns = [
    # Fleet Management
    path('', views.fleet_list, name='api_fleet_list'),
    path('create/', views.create_fleet, name='api_create_fleet'),
    path('<int:fleet_id>/', views.fleet_detail, name='api_fleet_detail'),
    path('<int:fleet_id>/update/', views.update_fleet, name='api_update_fleet'),
    path('<int:fleet_id>/delete/', views.delete_fleet, name='api_delete_fleet'),
    
    # Vehicle Management
    path('<int:fleet_id>/vehicles/', views.vehicle_list, name='api_vehicle_list'),
    path('<int:fleet_id>/vehicles/add/', views.add_vehicle, name='api_add_vehicle'),
    path('<int:fleet_id>/vehicles/<int:vehicle_id>/', views.vehicle_detail, name='api_vehicle_detail'),
    path('<int:fleet_id>/vehicles/<int:vehicle_id>/update/', views.update_vehicle, name='api_update_vehicle'),
    path('<int:fleet_id>/vehicles/<int:vehicle_id>/delete/', views.delete_vehicle, name='api_delete_vehicle'),
    
    # Driver Assignment
    path('<int:fleet_id>/drivers/', views.fleet_drivers, name='api_fleet_drivers'),
    path('<int:fleet_id>/drivers/assign/', views.assign_driver, name='api_assign_driver'),
    path('<int:fleet_id>/drivers/<int:driver_id>/remove/', views.remove_driver, name='api_remove_driver'),
    
    # Fleet Statistics
    path('<int:fleet_id>/stats/', views.fleet_stats, name='api_fleet_stats'),
    path('<int:fleet_id>/earnings/', views.fleet_earnings, name='api_fleet_earnings'),
]

