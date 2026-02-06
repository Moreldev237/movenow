from django.urls import path
from . import views

app_name = 'accounts_api'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='api_login'),
    path('register/', views.register, name='api_register'),
    path('logout/', views.logout_view, name='api_logout'),
    
    # User Profile
    path('profile/update/', views.update_profile, name='api_update_profile'),
    path('profile/password/', views.change_password, name='api_change_password'),

    
    # Email Verification
    path('verify/<str:token>/', views.verify_email, name='api_verify_email'),
    path('verify/resend/', views.resend_verification, name='api_resend_verification'),
    
    # Password Reset
    path('password/reset/', views.password_reset_request, name='api_password_reset_request'),
    path('password/reset/<str:token>/', views.password_reset_confirm, name='api_password_reset_confirm'),
    
    # Account Management
    path('delete/', views.delete_account, name='api_delete_account'),
    
    # Role Management
    path('become/driver/', views.become_driver, name='api_become_driver'),
    path('become/fleet/', views.become_fleet_owner, name='api_become_fleet_owner'),
]
