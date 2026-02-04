from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json

from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    PasswordChangeForm,
    DriverRegistrationForm,
    FleetOwnerRegistrationForm
)
from .models import User, UserWallet, UserSettings
from .decorators import unauthenticated_user, passenger_required
from .utils import send_verification_email, send_password_reset_email

@unauthenticated_user
def register(request):
    """Inscription utilisateur"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Connecter l'utilisateur
            login(request, user)
            
            # Créer le portefeuille et les paramètres
            UserWallet.objects.create(user=user)
            UserSettings.objects.create(user=user)
            
            # Envoyer l'email de vérification
            user.send_verification_email()
            
            messages.success(
                request,
                "Compte créé avec succès ! Veuillez vérifier votre email."
            )
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@unauthenticated_user
def login_view(request):
    """Connexion utilisateur"""
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Mettre à jour la dernière connexion
                user.last_login = timezone.now()
                if 'HTTP_X_FORWARDED_FOR' in request.META:
                    user.last_login_ip = request.META['HTTP_X_FORWARDED_FOR']
                else:
                    user.last_login_ip = request.META.get('REMOTE_ADDR')
                user.save()
                
                messages.success(request, f"Bienvenue {user.get_full_name()} !")
                
                # Redirection selon le type d'utilisateur
                next_url = request.GET.get('next', 'home')
                if user.is_driver:
                    next_url = 'drivers:dashboard'
                elif user.is_fleet_owner:
                    next_url = 'fleet:dashboard'
                
                return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """Déconnexion utilisateur"""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')

@login_required
def profile(request):
    """Profil utilisateur"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    
    # Statistiques
    stats = {
        'total_trips': user.trips.count(),
        'completed_trips': user.trips.filter(status='completed').count(),
        'avg_rating': user.given_ratings.aggregate(
            avg=models.Avg('rating')
        )['avg'] or 0,
    }
    
    context = {
        'form': form,
        'stats': stats,
        'wallet': user.wallet,
        'settings': user.settings,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    """Changer le mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

@unauthenticated_user
def verify_email(request, token):
    """Vérifier l'email"""
    try:
        user = User.objects.get(verification_token=token)
        
        # Vérifier si le token est expiré (24h)
        token_age = timezone.now() - user.verification_sent_at
        if token_age.total_seconds() > 86400:  # 24 heures
            messages.error(request, "Le lien de vérification a expiré.")
            return redirect('resend_verification')
        
        user.verify()
        messages.success(request, "Email vérifié avec succès !")
        
        if not request.user.is_authenticated:
            login(request, user)
        
        return redirect('home')
    
    except User.DoesNotExist:
        messages.error(request, "Lien de vérification invalide.")
        return redirect('home')

@login_required
def resend_verification(request):
    """Renvoyer l'email de vérification"""
    if request.user.is_verified:
        messages.info(request, "Votre compte est déjà vérifié.")
        return redirect('home')
    
    request.user.send_verification_email()
    messages.success(request, "Email de vérification envoyé !")
    return redirect('home')

@unauthenticated_user
def password_reset_request(request):
    """Demande de réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
            messages.success(
                request,
                "Instructions de réinitialisation envoyées par email."
            )
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Aucun compte avec cet email.")
    
    return render(request, 'accounts/password_reset_request.html')

@unauthenticated_user
def password_reset_confirm(request, token):
    """Confirmer la réinitialisation du mot de passe"""
    try:
        user = User.objects.get(verification_token=token)
        
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return render(request, 'accounts/password_reset_confirm.html')
            
            user.set_password(password)
            user.save()
            
            messages.success(request, "Mot de passe réinitialisé avec succès.")
            return redirect('login')
        
        return render(request, 'accounts/password_reset_confirm.html')
    
    except User.DoesNotExist:
        messages.error(request, "Lien de réinitialisation invalide.")
        return redirect('password_reset_request')

@login_required
@passenger_required
def become_driver(request):
    """Devenir chauffeur"""
    if request.user.is_driver:
        messages.info(request, "Vous êtes déjà chauffeur.")
        return redirect('drivers:dashboard')
    
    if request.method == 'POST':
        form = DriverRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.user = request.user
            
            # Vérifier l'âge minimum (21 ans)
            from datetime import date
            age = date.today().year - request.user.birth_date.year
            if age < 21:
                messages.error(request, "Vous devez avoir au moins 21 ans.")
                return redirect('become_driver')
            
            driver.save()
            
            # Mettre à jour le type d'utilisateur
            request.user.user_type = User.UserTypeChoices.DRIVER
            request.user.save()
            
            messages.success(
                request,
                "Votre demande de chauffeur a été soumise. "
                "Elle sera traitée dans les 24h."
            )
            return redirect('drivers:dashboard')
    else:
        form = DriverRegistrationForm()
    
    return render(request, 'accounts/become_driver.html', {'form': form})

@login_required
def become_fleet_owner(request):
    """Devenir propriétaire de flotte"""
    if request.user.is_fleet_owner:
        messages.info(request, "Vous êtes déjà propriétaire de flotte.")
        return redirect('fleet:dashboard')
    
    if request.method == 'POST':
        form = FleetOwnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            fleet = form.save(commit=False)
            fleet.owner = request.user
            fleet.save()
            
            # Mettre à jour le type d'utilisateur
            request.user.user_type = User.UserTypeChoices.FLEET_OWNER
            request.user.save()
            
            messages.success(
                request,
                "Votre demande de propriétaire de flotte a été soumise. "
                "Elle sera traitée dans les 48h."
            )
            return redirect('fleet:dashboard')
    else:
        form = FleetOwnerRegistrationForm()
    
    return render(request, 'accounts/become_fleet_owner.html', {'form': form})

@login_required
def delete_account(request):
    """Supprimer le compte"""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Vérifier le mot de passe
        user = authenticate(email=request.user.email, password=password)
        
        if user is not None:
            user.delete()
            messages.success(request, "Votre compte a été supprimé.")
            return redirect('home')
        else:
            messages.error(request, "Mot de passe incorrect.")
    
    return render(request, 'accounts/delete_account.html')

@csrf_exempt
@login_required
def update_location(request):
    """Mettre à jour la position de l'utilisateur (API)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('lat'))
            lng = float(data.get('lng'))
            
            request.user.update_location(lat, lng)
            
            return JsonResponse({'success': True})
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)