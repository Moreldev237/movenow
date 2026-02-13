from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import VehicleType, Driver, Trip, Fleet, Notification
from booking.forms import BookingForm
from accounts.decorators import passenger_required, driver_required, fleet_owner_required

def home(request):
    """Page d'accueil"""
    vehicle_types = VehicleType.objects.filter(is_active=True)
    
    # Statistiques
    stats = {
        'total_drivers': Driver.objects.filter(is_verified=True).count(),
        'total_trips': Trip.objects.filter(status='completed').count(),
        'active_trips': Trip.objects.filter(
            status__in=['accepted', 'arrived', 'started']
        ).count(),
    }
    
    # Promotions actives
    from core.models import Promotion
    promotions = Promotion.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    )[:3]
    
    context = {
        'vehicle_types': vehicle_types,
        'stats': stats,
        'promotions': promotions,
        'booking_form': BookingForm(),
    }
    
    return render(request, 'core/home.html', context)

def about(request):
    """Page À propos"""
    return render(request, 'core/about.html')

def contact(request):
    """Page Contact"""
    if request.method == 'POST':
        # Traiter le formulaire de contact
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        # Envoyer l'email
        from django.core.mail import send_mail
        from django.conf import settings

        subject = f"Nouveau message de contact de {first_name} {last_name}"
        email_message = f"""
Nouveau message de contact depuis le site MoveNow :

Nom complet : {first_name} {last_name}
Email : {email}
Téléphone : {phone or 'Non fourni'}

Message :
{message}
        """

        try:
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['Moreldev237@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, 'Merci pour votre message ! Nous vous répondrons bientôt.')
        except Exception as e:
            messages.error(request, 'Une erreur s\'est produite lors de l\'envoi du message. Veuillez réessayer.')

        return redirect('contact')

    return render(request, 'core/contact.html')

@login_required
def dashboard(request):
    """Tableau de bord selon le type d'utilisateur"""
    user = request.user
    
    if user.is_driver:
        return redirect('drivers:dashboard')
    elif user.is_fleet_owner:
        return redirect('fleet:dashboard')
    else:
        return redirect('booking:history')

@login_required
@passenger_required
def passenger_dashboard(request):
    """Tableau de bord passager"""
    user = request.user
    
    # Statistiques
    stats = {
        'total_trips': user.trips.count(),
        'completed_trips': user.trips.filter(status='completed').count(),
        'total_spent': user.trips.filter(status='completed').aggregate(
            total=Sum('fare')
        )['total'] or 0,
        'avg_rating': user.given_ratings.aggregate(
            avg=Avg('rating')
        )['avg'] or 0,
    }
    
    # Courses récentes
    recent_trips = user.trips.order_by('-created_at')[:5]
    
    # Chauffeurs fréquents
    frequent_drivers = Driver.objects.filter(
        trips__passenger=user,
        trips__status='completed'
    ).annotate(
        trip_count=Count('trips')
    ).order_by('-trip_count')[:3]
    
    context = {
        'stats': stats,
        'recent_trips': recent_trips,
        'frequent_drivers': frequent_drivers,
    }
    
    return render(request, 'core/passenger_dashboard.html', context)

@login_required
def notifications(request):
    """Page des notifications"""
    notifications = request.user.notifications.all().order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Marquer toutes comme lues
        notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return JsonResponse({'success': True})
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'core/notifications.html', context)

@login_required
def notification_mark_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

def calculate_fare(request):
    """API pour calculer le prix estimé"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Récupérer les paramètres
            vehicle_type_id = data.get('vehicle_type')
            distance = float(data.get('distance', 0))
            duration = float(data.get('duration', 0))
            is_shared = data.get('shared_ride', False)
            
            # Récupérer le type de véhicule
            vehicle_type = get_object_or_404(VehicleType, id=vehicle_type_id)
            
            # Calculer le prix
            base_price = vehicle_type.base_price
            distance_price = vehicle_type.price_per_km * distance
            time_price = vehicle_type.price_per_minute * (duration / 60)
            
            total = base_price + distance_price + time_price
            
            # Appliquer la réduction pour covoiturage
            if is_shared:
                discount = total * 0.3  # 30% de réduction
                total -= discount
            
            # Vérifier la demande élevée (surge pricing)
            surge_multiplier = get_surge_multiplier()
            if surge_multiplier > 1:
                total *= surge_multiplier
            
            return JsonResponse({
                'success': True,
                'fare': round(total, 2),
                'base_price': float(base_price),
                'distance_price': round(distance_price, 2),
                'time_price': round(time_price, 2),
                'surge_multiplier': surge_multiplier,
            })
            
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_surge_multiplier():
    """Obtenir le multiplicateur de demande élevée"""
    # Logique pour calculer la demande
    # Pour l'instant, retourner 1 (pas de surge pricing)
    return 1

def search_drivers(request):
    """Rechercher des chauffeurs à proximité"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            lat = float(data.get('lat'))
            lng = float(data.get('lng'))
            vehicle_type_id = data.get('vehicle_type')
            
            # Trouver les chauffeurs disponibles à proximité
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            
            point = Point(lng, lat, srid=4326)
            
            drivers = Driver.objects.filter(
                is_available=True,
                is_verified=True,
                vehicle_type_id=vehicle_type_id,
                current_location__isnull=False
            ).annotate(
                distance=Distance('current_location', point)
            ).filter(
                distance__lt=5000  # 5km radius
            ).order_by('distance')[:10]
            
            drivers_data = []
            for driver in drivers:
                drivers_data.append({
                    'id': driver.id,
                    'name': driver.user.get_full_name(),
                    'rating': driver.rating,
                    'total_trips': driver.total_trips,
                    'vehicle': {
                        'plate': driver.vehicle_plate,
                        'model': driver.vehicle_model,
                        'color': driver.vehicle_color,
                    },
                    'distance': round(driver.distance.m, 2),
                    'eta': calculate_eta(driver.distance.m),
                })
            
            return JsonResponse({
                'success': True,
                'drivers': drivers_data,
                'count': len(drivers_data),
            })
            
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def calculate_eta(distance_meters):
    """Calculer le temps d'arrivée estimé"""
    # Vitesse moyenne en ville: 30 km/h
    speed_kmh = 30
    speed_ms = speed_kmh * 1000 / 3600  # Convertir en m/s
    
    time_seconds = distance_meters / speed_ms
    time_minutes = max(2, int(time_seconds / 60))  # Minimum 2 minutes
    
    return time_minutes

def handler404(request, exception):
    """Gestionnaire d'erreur 404"""
    return render(request, 'core/404.html', status=404)

def handler500(request):
    """Gestionnaire d'erreur 500"""
    return render(request, 'core/500.html', status=500)


# ============ NOTIFICATIONS API VIEWS ============

@login_required
def notifications_list(request):
    """API: Liste des notifications"""
    if request.method == 'GET':
        notifications = request.user.notifications.all().order_by('-created_at')[:50]
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'link': notification.link,
                'link_text': notification.link_text,
                'data': notification.data,
                'created_at': notification.created_at,
            })
        
        unread_count = request.user.notifications.filter(is_read=False).count()
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def notification_detail(request, notification_id):
    """API: Détail d'une notification"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'notification': {
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'link': notification.link,
                'link_text': notification.link_text,
                'data': notification.data,
                'created_at': notification.created_at,
                'read_at': notification.read_at,
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def notification_mark_read(request, notification_id):
    """API: Marquer une notification comme lue"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    if request.method == 'POST':
        notification.mark_as_read()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marquée comme lue.'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def mark_all_notifications_read(request):
    """API: Marquer toutes les notifications comme lues"""
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Toutes les notifications ont été marquées comme lues.'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ PING API ============

def ping(request):
    """API: Test de connexion"""
    return JsonResponse({
        'success': True,
        'message': 'Server is running',
        'timestamp': timezone.now().isoformat(),
    })


# ============ NEW VIEWS FOR NEW TEMPLATES ============

@login_required
@driver_required
def driver_dashboard(request):
    """Tableau de bord chauffeur"""
    driver = request.user.driver_profile
    
    # Statistiques du jour
    today = timezone.now().date()
    today_trips = Trip.objects.filter(
        driver=driver,
        created_at__date=today
    )
    today_earnings = today_trips.filter(status='completed').aggregate(
        total=Sum('fare')
    )['total'] or 0
    
    # Semaine
    week_start = today - timedelta(days=today.weekday())
    week_trips = Trip.objects.filter(
        driver=driver,
        created_at__date__gte=week_start
    )
    weekly_earnings = week_trips.filter(status='completed').aggregate(
        total=Sum('fare')
    )['total'] or 0
    
    # Course en cours
    current_trip = Trip.objects.filter(
        driver=driver,
        status__in=['accepted', 'arrived', 'started']
    ).first()
    
    # Demandes en attente
    from booking.models import BookingRequest
    pending_requests = BookingRequest.objects.filter(
        driver=driver,
        status='sent'
    ).select_related('booking', 'booking__passenger', 'driver')[:5]
    
    # Courses récentes
    recent_trips = Trip.objects.filter(
        driver=driver
    ).order_by('-created_at')[:5]
    
    context = {
        'driver': driver,
        'today_earnings': today_earnings,
        'weekly_earnings': weekly_earnings,
        'today_trips': today_trips.count(),
        'weekly_trips': week_trips.count(),
        'current_trip': current_trip,
        'pending_requests': pending_requests,
        'recent_trips': recent_trips,
    }
    
    return render(request, 'core/driver_dashboard.html', context)


@login_required
@fleet_owner_required
def fleet_dashboard(request):
    """Tableau de bord flotte"""
    fleet = get_object_or_404(Fleet, owner=request.user)
    
    today = timezone.now().date()
    
    # Statistiques
    active_vehicles = fleet.vehicles.filter(is_active=True).count()
    active_drivers = fleet.drivers.filter(is_active=True).count()
    
    today_trips = Trip.objects.filter(
        driver__in=fleet.drivers.all(),
        created_at__date=today
    ).count()
    
    today_revenue = Trip.objects.filter(
        driver__in=fleet.drivers.all(),
        completed_at__date=today,
        status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    # Revenus du mois
    month_start = today.replace(day=1)
    monthly_revenue = Trip.objects.filter(
        driver__in=fleet.drivers.all(),
        completed_at__date__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('fare'))['total'] or 0
    
    commission_rate = fleet.commission_rate / 100
    commission = monthly_revenue * commission_rate
    net_revenue = monthly_revenue - commission
    
    # Chauffeurs
    drivers = fleet.drivers.all()
    
    # Véhicules
    vehicles = fleet.vehicles.all()
    
    # Alertes maintenance
    maintenance_alerts = vehicles.filter(
        status='maintenance'
    )[:5]
    
    # Revenus de la semaine (pour le graphique)
    weekly_revenue = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        day_revenue = Trip.objects.filter(
            driver__in=fleet.drivers.all(),
            completed_at__date=day,
            status='completed'
        ).aggregate(total=Sum('fare'))['total'] or 0
        weekly_revenue.append({
            'date': day.strftime('%d/%m'),
            'amount': day_revenue,
            'percentage': min(100, (day_revenue / max(monthly_revenue, 1)) * 100) if monthly_revenue > 0 else 0
        })
    
    context = {
        'fleet': fleet,
        'active_vehicles': active_vehicles,
        'active_drivers': active_drivers,
        'today_trips': today_trips,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'commission': commission,
        'net_revenue': net_revenue,
        'drivers': drivers,
        'vehicles': vehicles,
        'maintenance_alerts': maintenance_alerts,
        'weekly_revenue': weekly_revenue,
    }
    
    return render(request, 'core/fleet_dashboard.html', context)


@login_required
def schedule_booking(request):
    """Page de réservation programmée"""
    vehicle_types = VehicleType.objects.filter(is_active=True)
    
    context = {
        'vehicle_types': vehicle_types,
    }
    
    return render(request, 'core/schedule_booking.html', context)


@login_required
def share_location(request):
    """Page de partage de position"""
    # Générer un lien de partage temporaire
    import secrets
    share_token = secrets.token_urlsafe(32)
    
    # Pour l'exemple, utiliser un lien statique
    share_url = request.build_absolute_uri(f'/track/shared/{share_token}/')
    
    # Vérifier s'il y a une course active
    active_trip = Trip.objects.filter(
        passenger=request.user,
        status__in=['accepted', 'arrived', 'started']
    ).first()
    
    context = {
        'share_url': share_url,
        'active_trip': active_trip,
    }
    
    return render(request, 'core/share_location.html', context)


def safety(request):
    """Page de sécurité"""
    return render(request, 'core/safety.html')


def help(request):
    """Page d'aide et FAQ"""
    return render(request, 'core/help.html')


def terms(request):
    """Page des conditions générales"""
    return render(request, 'core/terms.html')


def privacy(request):
    """Page de confidentialité"""
    return render(request, 'core/privacy.html')


@login_required
def referral(request):
    """Page de parrainage"""
    user = request.user
    
    # Générer un code de parrainage si nécessaire
    if not hasattr(user, 'referral_code') or not user.referral_code:
        user.referral_code = f"{user.first_name[:3].upper()}{user.id:06d}"
        user.save()
    
    # Statistiques
    from accounts.models import Referral
    referrals = Referral.objects.filter(
        referrer=user
    )
    referral_count = referrals.count()
    earned_credits = referrals.filter(
        status='completed'
    ).aggregate(total=Sum('bonus'))['total'] or 0
    pending_referrals = referrals.filter(status='pending').count()
    
    context = {
        'user': user,
        'referral_count': referral_count,
        'earned_credits': earned_credits,
        'pending_referrals': pending_referrals,
        'referrals': referrals[:10],
    }
    
    return render(request, 'core/referral.html', context)
