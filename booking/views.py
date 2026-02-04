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