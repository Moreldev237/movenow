from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('verify/resend/', views.resend_verification, name='resend_verification'),
    path('password/reset/', views.password_reset_request, name='password_reset_request'),
    path('password/reset/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('become/driver/', views.become_driver, name='become_driver'),
    path('become/fleet/', views.become_fleet_owner, name='become_fleet_owner'),
    path('delete/', views.delete_account, name='delete_account'),
]

