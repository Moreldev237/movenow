"""
Utility functions for the accounts app.
"""
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings


def send_verification_email(user, request=None):
    """
    Send a verification email to the user.
    
    Args:
        user: The User instance to send verification email to
        request: Optional request object for generating absolute URLs
    """
    # Generate verification token
    token = default_token_generator.make_token(user)
    
    # Build verification URL
    if request:
        verification_url = request.build_absolute_uri(
            f'/accounts/verify/{token}/'
        )
    else:
        verification_url = f'{settings.SITE_URL}/accounts/verify/{token}/'
    
    # Render email template
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'MoveNow',
    }
    
    subject = 'Vérifiez votre adresse email - MoveNow'
    html_message = render_to_string(
        'accounts/emails/verification_email.html', context
    )
    plain_message = render_to_string(
        'accounts/emails/verification_email.txt', context
    )
    
    # Send email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


def send_password_reset_email(user, request=None):
    """
    Send a password reset email to the user.
    
    Args:
        user: The User instance to send password reset email to
        request: Optional request object for generating absolute URLs
    """
    # Generate reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build reset URL
    if request:
        reset_url = request.build_absolute_uri(
            f'/accounts/reset-password/{uid}/{token}/'
        )
    else:
        reset_url = f'{settings.SITE_URL}/accounts/reset-password/{uid}/{token}/'
    
    # Render email template
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'MoveNow',
    }
    
    subject = 'Réinitialisation de votre mot de passe - MoveNow'
    html_message = render_to_string(
        'accounts/emails/password_reset_email.html', context
    )
    plain_message = render_to_string(
        'accounts/emails/password_reset_email.txt', context
    )
    
    # Send email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


def send_welcome_email(user, request=None):
    """
    Send a welcome email to the newly registered user.
    
    Args:
        user: The User instance to send welcome email to
        request: Optional request object
    """
    context = {
        'user': user,
        'site_name': 'MoveNow',
    }
    
    subject = 'Bienvenue sur MoveNow !'
    html_message = render_to_string(
        'accounts/emails/welcome_email.html', context
    )
    plain_message = render_to_string(
        'accounts/emails/welcome_email.txt', context
    )
    
    # Send email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


def send_account_approved_email(user, request=None):
    """
    Send an email when user account is approved (e.g., driver application).
    
    Args:
        user: The User instance to send approval email to
        request: Optional request object
    """
    context = {
        'user': user,
        'site_name': 'MoveNow',
    }
    
    subject = 'Votre compte a été approuvé - MoveNow'
    html_message = render_to_string(
        'accounts/emails/account_approved.html', context
    )
    plain_message = render_to_string(
        'accounts/emails/account_approved.txt', context
    )
    
    # Send email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)


def send_booking_admin_notification(booking):
    """
    Send an email notification to the admin when a new booking is created.
    
    Args:
        booking: The Booking instance that was created
    """
    from django.utils import timezone
    
    # Get admin email from settings
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    
    if not admin_email:
        # Try to get from ADMINS setting
        if hasattr(settings, 'ADMINS') and settings.ADMINS:
            admin_email = settings.ADMINS[0][1] if isinstance(settings.ADMINS[0], (list, tuple)) else settings.ADMINS[0]
        else:
            return False
    
    context = {
        'booking': booking,
        'passenger': booking.passenger,
        'site_name': 'MoveNow',
        'created_at': timezone.now(),
    }
    
    subject = f'Nouvelle réservation - #{booking.booking_id}'
    html_message = render_to_string(
        'booking/emails/admin_booking_notification.html', context
    )
    
    # Send email to admin
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[admin_email],
    )
    email.content_subtype = 'html'
    
    try:
        email.send(fail_silently=False)
        return True
    except Exception:
        return False

