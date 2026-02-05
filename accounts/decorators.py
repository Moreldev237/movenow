"""
Custom decorators for the accounts app.
"""
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib import messages


def unauthenticated_user(view_func):
    """
    Decorator that redirects authenticated users to the home page.
    Use this on views that should only be accessible to anonymous users
    (like login, register, password reset).
    """
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper_func


def allowed_users(allowed_roles=None):
    """
    Decorator that restricts access to specific user roles.
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            user = request.user
            
            if user.is_authenticated:
                if user.user_type in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    # User is authenticated but not in allowed roles
                    return redirect('home')
            else:
                # User is not authenticated
                return redirect('login')
        return wrapper_func
    return decorator


def passenger_required(view_func):
    """
    Decorator that ensures the user is a passenger.
    Redirects to home if the user is not a passenger.
    """
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is a passenger (regular user, not driver or fleet owner)
        if hasattr(request.user, 'user_type'):
            if request.user.user_type in ['driver', 'fleet_owner']:
                return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper_func


def driver_required(view_func):
    """
    Decorator that ensures the user is a driver.
    Redirects to home if the user is not a driver.
    """
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_driver:
            messages.error(request, "Vous devez être chauffeur pour accéder à cette page.")
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper_func


def fleet_owner_required(view_func):
    """
    Decorator that ensures the user is a fleet owner.
    Redirects to home if the user is not a fleet owner.
    """
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_fleet_owner:
            messages.error(request, "Vous devez être propriétaire de flotte pour accéder à cette page.")
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper_func


def verified_user_required(view_func):
    """
    Decorator that ensures the user has verified their email.
    """
    def wrapper_func(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_verified:
            from django.contrib import messages
            messages.warning(request, "Veuillez vérifier votre email avant de continuer.")
            return redirect('resend_verification')
        
        return view_func(request, *args, **kwargs)
    return wrapper_func

