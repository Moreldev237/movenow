# Web URLs for payment - Payment processing is handled via API endpoints (payment/urls_api.py)
# Web views can be added here if template-based payment flow is needed

from django.urls import path
from . import views

urlpatterns = [
    path('trip/<int:trip_id>/', views.payment_page, name='payment_page'),
]

