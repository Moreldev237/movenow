from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include([
        path('auth/', include('accounts.urls_api')),
        path('booking/', include('booking.urls_api')),
        path('payment/', include('payment.urls_api')),
        path('fleet/', include('fleet.urls_api')),
        path('drivers/', include('drivers.urls_api')),
        path('core/', include('core.urls_api')),
    ])),
    
    # Web
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('booking/', include('booking.urls')),
    path('payment/', include('payment.urls')),
    path('fleet/', include('fleet.urls')),
    path('drivers/', include('drivers.urls')),
    
    # Static pages
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='core/contact.html'), name='contact'),
    path('privacy/', TemplateView.as_view(template_name='core/privacy_policy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='core/terms.html'), name='terms'),
    
    # Auth (Allauth) - Commented out to avoid conflicts with custom accounts
    # path('accounts/', include('allauth.urls')),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
