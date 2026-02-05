"""
Custom middleware for the core app.
"""
from django.utils.timezone import activate
from django.conf import settings


class TimezoneMiddleware:
    """
    Middleware to activate the timezone from settings for each request.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Activate the timezone from settings
        activate(settings.TIME_ZONE)
        
        response = self.get_response(request)
        return response

