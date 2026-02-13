from django.conf import settings

def site_settings(request):
    """
    Context processor to add site-wide settings to all templates
    """
    return {
        'site_name': 'MoveNow',
        'site_description': 'Votre plateforme de transport urbain',
        'site_url': 'https://movenow.cm',
        'support_email': 'support@movenow.cm',
        'company_phone': '+237 6XX XXX XXX',
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
