from django.urls import path
from . import views

app_name = 'payment_api'

urlpatterns = [
    # Payment Processing
    path('process/', views.process_payment, name='api_process_payment'),
    path('webhook/', views.payment_webhook, name='api_payment_webhook'),
    
    # Payment History
    path('history/', views.payment_history, name='api_payment_history'),
    path('history/<int:payment_id>/', views.payment_detail, name='api_payment_detail'),
    
    # Refunds
    path('refund/<int:payment_id>/', views.refund_payment, name='api_refund_payment'),
    path('refund/status/<int:refund_id>/', views.refund_status, name='api_refund_status'),
    
    # Payment Methods
    path('methods/', views.list_payment_methods, name='api_list_payment_methods'),
    path('methods/add/', views.add_payment_method, name='api_add_payment_method'),
    path('methods/<int:method_id>/delete/', views.delete_payment_method, name='api_delete_payment_method'),
    path('methods/<int:method_id>/set-default/', views.set_default_payment_method, name='api_set_default_method'),
    
    # Payment Status
    path('status/<str:payment_id>/', views.get_payment_status, name='api_payment_status'),
]

