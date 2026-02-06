from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

from accounts.decorators import passenger_required, driver_required
from .forms import BookingForm
from .models import Booking, BookingRequest, TripTracking
from core.models import Trip, Driver, VehicleType
from core.utils import calculate_route, estimate_fare
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

@login_required
@passenger_required
def book(request):
    """Réserver une course"""
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            # Créer la réservation
            booking = form.save(commit=False)
            booking.passenger = request.user
            booking.booking_id = uuid.uuid4()
            
            # Calculer l'itinéraire et le prix
            try:
                route = calculate_route(
                    booking.pickup_lat,
                    booking.pickup_lng,
                    booking.dropoff_lat,
                    booking.dropoff_lng
                )
                
                booking.distance = route['distance']
                booking.duration = route['duration']
                booking.estimated_fare = estimate_fare(
                    booking.vehicle_type,
                    booking.distance,
                    booking.duration,
                    booking.is_shared
                )
                
                booking.save()
                
                # Rechercher des chauffeurs
                search_drivers_for_booking(booking)
                
                messages.success(
                    request,
                    "Réservation créée ! Recherche de chauffeurs en cours..."
                )
                return redirect('booking:track', booking_id=booking.booking_id)
                
            except Exception as e:
                messages.error(request, f"Erreur lors du calcul de l'itinéraire: {e}")
    
    else:
        form = BookingForm()
    
    # Types de véhicules disponibles
    vehicle_types = VehicleType.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'vehicle_types': vehicle_types,
    }
    
    return render(request, 'booking/book.html', context)

def search_drivers_for_booking(booking):
    """Rechercher des chauffeurs disponibles pour une réservation"""
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    
    point = Point(booking.pickup_lng, booking.pickup_lat, srid=4326)
    
    # Trouver les chauffeurs disponibles
    drivers = Driver.objects.filter(
        is_available=True,
        is_verified=True,
        vehicle_type=booking.vehicle_type,
        current_location__isnull=False
    ).annotate(
        distance=Distance('current_location', point)
    ).filter(
        distance__lt=10000  # 10km radius
    ).order_by('distance')[:10]
    
    # Envoyer des demandes aux chauffeurs
    for driver in drivers:
        BookingRequest.objects.create(
            booking=booking,
            driver=driver,
            expires_at=timezone.now() + timezone.timedelta(minutes=2)
        )
    
    # Mettre à jour le statut de la réservation
    if drivers:
        booking.status = 'searching'
    else:
        booking.status = 'pending'
    
    booking.save()

@login_required
@passenger_required
def track_booking(request, booking_id):
    """Suivre une réservation"""
    booking = get_object_or_404(
        Booking,
        booking_id=booking_id,
        passenger=request.user
    )
    
    # Vérifier si la réservation a expiré
    if booking.is_expired() and booking.status == 'pending':
        booking.status = 'expired'
        booking.save()
    
    # Récupérer les demandes envoyées
    booking_requests = booking.requests.select_related('driver').all()
    
    # Vérifier si une demande a été acceptée
    accepted_request = booking_requests.filter(status='accepted').first()
    if accepted_request:
        # Rediriger vers la page de suivi de course
        trip = Trip.objects.get(
            passenger=request.user,
            driver=accepted_request.driver,
            created_at__gte=booking.created_at
        )
        return redirect('booking:trip_detail', trip_id=trip.id)
    
    context = {
        'booking': booking,
        'booking_requests': booking_requests,
        'accepted_request': accepted_request,
    }
    
    return render(request, 'booking/track.html', context)

@login_required
@driver_required
def accept_booking(request, request_id):
    """Accepter une demande de réservation"""
    booking_request = get_object_or_404(
        BookingRequest,
        id=request_id,
        driver=request.user.driver_profile,
        status='sent'
    )
    
    if booking_request.accept():
        messages.success(request, "Course acceptée avec succès !")
        return redirect('drivers:dashboard')
    else:
        messages.error(request, "Impossible d'accepter cette demande.")
        return redirect('drivers:dashboard')

@login_required
@driver_required
def reject_booking(request, request_id):
    """Rejeter une demande de réservation"""
    booking_request = get_object_or_404(
        BookingRequest,
        id=request_id,
        driver=request.user.driver_profile,
        status='sent'
    )
    
    if booking_request.reject():
        messages.info(request, "Demande rejetée.")
    else:
        messages.error(request, "Impossible de rejeter cette demande.")
    
    return redirect('drivers:dashboard')

@login_required
def get_booking_request(request, request_id):
    """Récupérer les détails d'une demande de réservation (API)"""
    booking_request = get_object_or_404(
        BookingRequest,
        id=request_id
    )
    
    # Vérifier que l'utilisateur est le passager ou le chauffeur
    is_passenger = booking_request.booking.passenger == request.user
    is_driver = hasattr(request.user, 'driver_profile') and booking_request.driver == request.user.driver_profile
    
    if not (is_passenger or is_driver):
        return JsonResponse(
            {'error': 'Vous n\'êtes pas autorisé à voir cette demande.'},
            status=403
        )
    
    # Construire la réponse
    data = {
        'id': booking_request.id,
        'status': booking_request.status,
        'sent_at': booking_request.sent_at.isoformat() if booking_request.sent_at else None,
        'responded_at': booking_request.responded_at.isoformat() if booking_request.responded_at else None,
        'expires_at': booking_request.expires_at.isoformat() if booking_request.expires_at else None,
        'booking': {
            'id': booking_request.booking.id,
            'booking_id': str(booking_request.booking.booking_id),
            'pickup_address': booking_request.booking.pickup_address,
            'dropoff_address': booking_request.booking.dropoff_address,
            'pickup_lat': booking_request.booking.pickup_lat,
            'pickup_lng': booking_request.booking.pickup_lng,
            'dropoff_lat': booking_request.booking.dropoff_lat,
            'dropoff_lng': booking_request.booking.dropoff_lng,
            'distance': float(booking_request.booking.distance),
            'duration': booking_request.booking.duration,
            'estimated_fare': str(booking_request.booking.estimated_fare),
            'status': booking_request.booking.status,
            'created_at': booking_request.booking.created_at.isoformat(),
        },
        'driver': {
            'id': booking_request.driver.id,
            'user': {
                'id': booking_request.driver.user.id,
                'first_name': booking_request.driver.user.first_name,
                'last_name': booking_request.driver.user.last_name,
                'phone': booking_request.driver.user.phone if hasattr(booking_request.driver.user, 'phone') else None,
            },
            'vehicle_type': booking_request.driver.vehicle_type.name if booking_request.driver.vehicle_type else None,
            'rating': float(booking_request.driver.rating) if booking_request.driver.rating else None,
        } if is_passenger or is_driver else None,
    }
    
    return JsonResponse(data)

@login_required
def trip_detail(request, trip_id):
    """Détails d'une course"""
    trip = get_object_or_404(
        Trip,
        Q(passenger=request.user) | Q(driver__user=request.user),
        id=trip_id
    )
    
    # Récupérer le suivi
    tracking, created = TripTracking.objects.get_or_create(trip=trip)
    
    context = {
        'trip': trip,
        'tracking': tracking,
    }
    
    return render(request, 'booking/trip_detail.html', context)

@login_required
def trip_history(request):
    """Historique des courses"""
    if request.user.is_driver:
        trips = Trip.objects.filter(driver=request.user.driver_profile)
    else:
        trips = Trip.objects.filter(passenger=request.user)
    
    # Filtres
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        trips = trips.filter(status=status)
    
    if date_from:
        trips = trips.filter(created_at__date__gte=date_from)
    
    if date_to:
        trips = trips.filter(created_at__date__lte=date_to)
    
    trips = trips.order_by('-created_at')
    
    context = {
        'trips': trips,
        'filters': {
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'booking/history.html', context)

@login_required
def trip_history_filtered(request, filter_type):
    """Historique des courses filtré par type (API)"""
    if request.user.is_driver:
        trips = Trip.objects.filter(driver=request.user.driver_profile)
    else:
        trips = Trip.objects.filter(passenger=request.user)
    
    # Appliquer le filtre selon le type
    filter_type = filter_type.lower()
    
    if filter_type == 'upcoming':
        # Courses à venir (scheduled, in_progress)
        trips = trips.filter(status__in=['scheduled', 'in_progress'])
    elif filter_type == 'completed':
        # Courses terminées
        trips = trips.filter(status='completed')
    elif filter_type == 'cancelled':
        # Courses annulées
        trips = trips.filter(status='cancelled')
    elif filter_type == 'all':
        # Toutes les courses (pas de filtre)
        pass
    else:
        # Type de filtre inconnu, retourner vide
        trips = trips.none()
    
    trips = trips.order_by('-created_at')
    
    # Retourner une réponse JSON pour l'API
    from django.core import serializers
    
    data = [{
        'id': trip.id,
        'status': trip.status,
        'created_at': trip.created_at.isoformat(),
        'pickup_address': trip.pickup_address,
        'dropoff_address': trip.dropoff_address,
        'fare': str(trip.fare) if trip.fare else None,
    } for trip in trips]
    
    return JsonResponse({'trips': data, 'filter_type': filter_type})

@login_required
def cancel_trip(request, trip_id):
    """Annuler une course"""
    trip = get_object_or_404(
        Trip,
        Q(passenger=request.user) | Q(driver__user=request.user),
        id=trip_id
    )
    
    if not trip.can_be_cancelled():
        messages.error(request, "Cette course ne peut pas être annulée.")
        return redirect('booking:trip_detail', trip_id=trip.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Annuler la course
        trip.status = 'cancelled'
        trip.cancelled_at = timezone.now()
        trip.save()
        
        # Rembourser si nécessaire
        if trip.payment_status == 'paid':
            # TODO: Gérer le remboursement
            pass
        
        messages.success(request, "Course annulée avec succès.")
        return redirect('booking:history')
    
    return render(request, 'booking/cancel_trip.html', {'trip': trip})

@csrf_exempt
@login_required
@driver_required
def update_trip_location(request, trip_id):
    """Mettre à jour la position pendant une course (API)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('lat'))
            lng = float(data.get('lng'))
            
            trip = get_object_or_404(
                Trip,
                id=trip_id,
                driver=request.user.driver_profile
            )
            
            # Mettre à jour la position
            trip.current_location = Point(lng, lat)
            trip.save(update_fields=['current_location'])
            
            # Ajouter à l'historique de suivi
            tracking, created = TripTracking.objects.get_or_create(trip=trip)
            tracking.add_position(lat, lng)
            
            return JsonResponse({'success': True})
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def rate_trip(request, trip_id):
    """Noter une course"""
    trip = get_object_or_404(
        Trip,
        passenger=request.user,
        id=trip_id,
        status='completed'
    )
    
    # Vérifier si la course a déjà été notée
    if hasattr(trip, 'rating'):
        messages.info(request, "Vous avez déjà noté cette course.")
        return redirect('booking:trip_detail', trip_id=trip.id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        # Créer la note
        from core.models import Rating
        Rating.objects.create(
            trip=trip,
            driver=trip.driver,
            passenger=request.user,
            rating=int(rating),
            comment=comment
        )
        
        # Mettre à jour la note du chauffeur
        trip.driver.update_rating()
        
        messages.success(request, "Merci pour votre évaluation !")
        return redirect('booking:trip_detail', trip_id=trip.id)
    
    return render(request, 'booking/rate_trip.html', {'trip': trip})

def estimate_fare(request):
    """Estimer le prix d'une course (API)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            distance = float(data.get('distance'))
            duration = int(data.get('duration'))
            vehicle_type_id = int(data.get('vehicle_type'))
            is_shared = data.get('is_shared', False)
        except (ValueError, KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Données invalides'}, status=400)
    else:
        # GET parameters
        try:
            distance = float(request.GET.get('distance'))
            duration = int(request.GET.get('duration'))
            vehicle_type_id = int(request.GET.get('vehicle_type'))
            is_shared = request.GET.get('is_shared', 'false').lower() == 'true'
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Paramètres invalides'}, status=400)

    try:
        vehicle_type = VehicleType.objects.get(id=vehicle_type_id, is_active=True)
    except VehicleType.DoesNotExist:
        return JsonResponse({'error': 'Type de véhicule invalide'}, status=400)

    estimated_fare = estimate_fare(vehicle_type, distance, duration, is_shared)

    return JsonResponse({
        'estimated_fare': str(estimated_fare),
        'distance': distance,
        'duration': duration,
        'vehicle_type': vehicle_type.name,
        'is_shared': is_shared
    })

def get_available_drivers(request):
    """Récupérer les chauffeurs disponibles (API)"""
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Coordonnées invalides'}, status=400)

    point = Point(lng, lat, srid=4326)

    # Trouver les chauffeurs disponibles dans un rayon de 10km
    drivers = Driver.objects.filter(
        is_available=True,
        is_verified=True,
        current_location__isnull=False
    ).annotate(
        distance=Distance('current_location', point)
    ).filter(
        distance__lt=10000  # 10km
    ).select_related('user', 'vehicle_type').order_by('distance')[:20]

    data = []
    for driver in drivers:
        data.append({
            'id': driver.id,
            'name': f"{driver.user.first_name} {driver.user.last_name}",
            'vehicle_type': driver.vehicle_type.name if driver.vehicle_type else None,
            'rating': float(driver.rating) if driver.rating else None,
            'distance': float(driver.distance.m) if driver.distance else None,
            'lat': driver.current_location.y if driver.current_location else None,
            'lng': driver.current_location.x if driver.current_location else None,
        })

    return JsonResponse({'drivers': data})

def get_nearby_drivers(request):
    """Récupérer les chauffeurs à proximité (API)"""
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        radius = int(request.GET.get('radius', 5000))  # 5km par défaut
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Paramètres invalides'}, status=400)

    point = Point(lng, lat, srid=4326)

    # Trouver les chauffeurs à proximité
    drivers = Driver.objects.filter(
        current_location__isnull=False
    ).annotate(
        distance=Distance('current_location', point)
    ).filter(
        distance__lt=radius
    ).select_related('user', 'vehicle_type').order_by('distance')[:50]

    data = []
    for driver in drivers:
        data.append({
            'id': driver.id,
            'name': f"{driver.user.first_name} {driver.user.last_name}",
            'vehicle_type': driver.vehicle_type.name if driver.vehicle_type else None,
            'rating': float(driver.rating) if driver.rating else None,
            'distance': float(driver.distance.m) if driver.distance else None,
            'is_available': driver.is_available,
            'is_verified': driver.is_verified,
            'lat': driver.current_location.y if driver.current_location else None,
            'lng': driver.current_location.x if driver.current_location else None,
        })

    return JsonResponse({'drivers': data})


def shared_ride(request):
    """Page de covoiturage"""
    # Récupérer les trajets avec covoiturage disponibles
    shared_trips = []
    
    # Pour l'exemple, retourner des données fictives
    context = {
        'shared_trips': shared_trips,
    }
    
    return render(request, 'booking/shared_ride.html', context)
