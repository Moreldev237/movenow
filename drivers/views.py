from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.contrib.gis.geos import Point
from datetime import datetime, timedelta
import json

from accounts.models import User
from core.models import Trip
from .models import DriverDocument, DriverVehicle
from core.models import Driver

# ============ DRIVER PROFILE VIEWS ============

@login_required
def driver_profile(request):
    """Récupérer le profil du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'driver': {
                'id': driver.id,
                'user_id': driver.user.id,
                'email': driver.user.email,
                'first_name': driver.user.first_name,
                'last_name': driver.user.last_name,
                'phone': driver.user.phone,
                'profile_picture': driver.user.profile_picture.url if driver.user.profile_picture else None,
                'license_number': driver.license_number,
                'license_expiry': driver.license_expiry,
                'vehicle': {
                    'id': driver.vehicle.id if driver.vehicle else None,
                    'make': driver.vehicle.make if driver.vehicle else None,
                    'model': driver.vehicle.model if driver.vehicle else None,
                    'year': driver.vehicle.year if driver.vehicle else None,
                    'color': driver.vehicle.color if driver.vehicle else None,
                    'plate_number': driver.vehicle.plate_number if driver.vehicle else None,
                } if driver.vehicle else None,
                'status': driver.status,
                'is_available': driver.is_available,
                'rating': driver.rating,
                'total_trips': driver.total_trips,
                'created_at': driver.created_at,
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def update_driver_profile(request):
    """Mettre à jour le profil du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Mettre à jour les champs du driver
            if 'license_number' in data:
                driver.license_number = data['license_number']
            if 'license_expiry' in data:
                driver.license_expiry = data['license_expiry']
            
            driver.save()
            
            # Mettre à jour les champs de l'utilisateur
            if 'phone' in data:
                driver.user.phone = data['phone']
            if 'first_name' in data:
                driver.user.first_name = data['first_name']
            if 'last_name' in data:
                driver.user.last_name = data['last_name']
            
            driver.user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profil mis à jour avec succès.'
            })
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ DRIVER STATUS VIEWS ============

@login_required
def get_driver_status(request):
    """Récupérer le statut du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    return JsonResponse({
        'success': True,
        'status': {
            'current_status': driver.status,
            'is_available': driver.is_available,
            'is_on_trip': driver.is_on_trip,
            'last_location': {
                'lat': driver.user.location.y if driver.user.location else None,
                'lng': driver.user.location.x if driver.user.location else None,
            } if driver.user.location else None,
        }
    })


@login_required
def update_driver_status(request):
    """Mettre à jour le statut du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            valid_statuses = [
                Driver.DriverStatus.OFFLINE,
                Driver.DriverStatus.AVAILABLE,
                Driver.DriverStatus.BUSY,
                Driver.DriverStatus.ON_TRIP,
            ]
            
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'error': 'Statut invalide.'
                }, status=400)
            
            driver.status = new_status
            
            # Si le statut est disponible, le chauffeur est aussi disponible
            if new_status == Driver.DriverStatus.AVAILABLE:
                driver.is_available = True
            elif new_status == Driver.DriverStatus.OFFLINE:
                driver.is_available = False
            
            driver.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Statut mis à jour avec succès.',
                'status': driver.status,
                'is_available': driver.is_available,
            })
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ AVAILABILITY VIEWS ============

@login_required
def set_availability(request):
    """Définir la disponibilité du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_available = data.get('is_available', True)
            
            driver.is_available = is_available
            
            # Mettre à jour le statut automatiquement
            if is_available:
                driver.status = Driver.DriverStatus.AVAILABLE
            else:
                driver.status = Driver.DriverStatus.OFFLINE
            
            driver.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Disponibilité mise à jour avec succès.',
                'is_available': driver.is_available,
                'status': driver.status,
            })
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def update_location(request):
    """Mettre à jour la position du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('lat'))
            lng = float(data.get('lng'))
            
            driver.user.location = Point(lng, lat)
            driver.user.save(update_fields=['location'])
            
            return JsonResponse({
                'success': True,
                'message': 'Position mise à jour avec succès.',
                'location': {'lat': lat, 'lng': lng}
            })
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ TRIPS VIEWS ============

@login_required
def driver_trips(request):
    """Récupérer les courses du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        status_filter = request.GET.get('status', None)
        
        trips = Trip.objects.filter(driver=driver)
        
        if status_filter:
            trips = trips.filter(status=status_filter)
        
        trips = trips.order_by('-created_at')[:50]
        
        trips_data = []
        for trip in trips:
            trips_data.append({
                'id': trip.id,
                'passenger': {
                    'id': trip.passenger.id,
                    'name': trip.passenger.get_full_name(),
                    'phone': trip.passenger.phone,
                    'profile_picture': trip.passenger.profile_picture.url if trip.passenger.profile_picture else None,
                },
                'pickup_address': trip.pickup_address,
                'dropoff_address': trip.dropoff_address,
                'pickup_lat': trip.pickup_lat,
                'pickup_lng': trip.pickup_lng,
                'dropoff_lat': trip.dropoff_lat,
                'dropoff_lng': trip.dropoff_lng,
                'status': trip.status,
                'fare': float(trip.fare),
                'distance': trip.distance,
                'created_at': trip.created_at,
                'accepted_at': trip.accepted_at,
                'completed_at': trip.completed_at,
            })
        
        return JsonResponse({
            'success': True,
            'trips': trips_data,
            'count': len(trips_data)
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def available_trips(request):
    """Récupérer les courses disponibles (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if not driver.is_available:
        return JsonResponse({
            'success': False,
            'error': 'Vous devez être disponible pour voir les courses.'
        }, status=400)
    
    if request.method == 'GET':
        # Récupérer les courses disponibles (pas encore acceptées)
        available_trips = Trip.objects.filter(
            status=Trip.TripStatus.PENDING,
            driver__isnull=True
        ).order_by('-created_at')[:20]
        
        trips_data = []
        for trip in available_trips:
            trips_data.append({
                'id': trip.id,
                'passenger': {
                    'id': trip.passenger.id,
                    'name': trip.passenger.get_full_name(),
                    'phone': trip.passenger.phone,
                    'profile_picture': trip.passenger.profile_picture.url if trip.passenger.profile_picture else None,
                    'rating': trip.passenger.given_ratings.aggregate(
                        avg=models.Avg('rating')
                    )['avg'] or 0,
                },
                'pickup_address': trip.pickup_address,
                'dropoff_address': trip.dropoff_address,
                'pickup_lat': trip.pickup_lat,
                'pickup_lng': trip.pickup_lng,
                'dropoff_lat': trip.dropoff_lat,
                'dropoff_lng': trip.dropoff_lng,
                'fare': float(trip.fare),
                'distance': trip.distance,
                'estimated_duration': trip.estimated_duration,
                'created_at': trip.created_at,
                'vehicle_type': trip.vehicle_type.name if trip.vehicle_type else None,
            })
        
        return JsonResponse({
            'success': True,
            'trips': trips_data,
            'count': len(trips_data)
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def accept_trip(request, trip_id):
    """Accepter une course (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if not driver.is_available:
        return JsonResponse({
            'success': False,
            'error': 'Vous devez être disponible pour accepter une course.'
        }, status=400)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.status != Trip.TripStatus.PENDING:
        return JsonResponse({
            'success': False,
            'error': 'Cette course n\'est plus disponible.'
        }, status=400)
    
    if trip.driver is not None:
        return JsonResponse({
            'success': False,
            'error': 'Cette course a déjà été acceptée.'
        }, status=400)
    
    if request.method == 'POST':
        trip.driver = driver
        trip.status = Trip.TripStatus.ACCEPTED
        trip.accepted_at = timezone.now()
        trip.save()
        
        # Mettre à jour le statut du chauffeur
        driver.status = Driver.DriverStatus.BUSY
        driver.is_available = False
        driver.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Course acceptée avec succès.',
            'trip': {
                'id': trip.id,
                'status': trip.status,
                'passenger': {
                    'name': trip.passenger.get_full_name(),
                    'phone': trip.passenger.phone,
                },
                'pickup_address': trip.pickup_address,
                'dropoff_address': trip.dropoff_address,
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def decline_trip(request, trip_id):
    """Refuser une course (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if request.method == 'POST':
        # Enregistrer que le chauffeur a refusé cette course
        # Pour éviter qu'elle lui soit proposée à nouveau
        trip.declined_drivers.add(driver)
        trip.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Course refusée.'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def start_trip(request, trip_id):
    """Commencer une course (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.driver != driver:
        return JsonResponse({
            'success': False,
            'error': 'Cette course ne vous appartient pas.'
        }, status=400)
    
    if trip.status != Trip.TripStatus.ACCEPTED:
        return JsonResponse({
            'success': False,
            'error': 'Cette course ne peut pas être commencée.'
        }, status=400)
    
    if request.method == 'POST':
        trip.status = Trip.TripStatus.STARTED
        trip.started_at = timezone.now()
        trip.save()
        
        driver.status = Driver.DriverStatus.ON_TRIP
        driver.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Course commencée.',
            'trip': {
                'id': trip.id,
                'status': trip.status,
                'started_at': trip.started_at,
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def complete_trip(request, trip_id):
    """Terminer une course (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffer.'
        }, status=400)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.driver != driver:
        return JsonResponse({
            'success': False,
            'error': 'Cette course ne vous appartient pas.'
        }, status=400)
    
    if trip.status != Trip.TripStatus.STARTED:
        return JsonResponse({
            'success': False,
            'error': 'Cette course ne peut pas être terminée.'
        }, status=400)
    
    if request.method == 'POST':
        trip.status = Trip.TripStatus.COMPLETED
        trip.completed_at = timezone.now()
        
        # Calculer le revenu du chauffeur (80% du tarif)
        driver_share = trip.fare * 0.80
        trip.driver_earnings = driver_share
        
        trip.save()
        
        # Mettre à jour les statistiques du chauffeur
        driver.total_trips += 1
        driver.total_earnings += driver_share
        
        # Recalculer la note moyenne
        ratings = Trip.objects.filter(
            driver=driver,
            status=Trip.TripStatus.COMPLETED
        ).exclude(rating=None).aggregate(avg_rating=models.Avg('rating'))
        driver.rating = ratings['avg_rating'] or driver.rating
        
        driver.status = Driver.DriverStatus.AVAILABLE
        driver.is_available = True
        driver.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Course terminée avec succès.',
            'trip': {
                'id': trip.id,
                'status': trip.status,
                'completed_at': trip.completed_at,
                'fare': float(trip.fare),
                'driver_earnings': float(driver_share),
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ EARNINGS VIEWS ============

@login_required
def earnings(request):
    """Récupérer les gains du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        completed_trips = Trip.objects.filter(
            driver=driver,
            status=Trip.TripStatus.COMPLETED
        )
        
        total_earnings = completed_trips.aggregate(
            total=models.Sum('driver_earnings')
        )['total'] or 0
        
        total_trips = completed_trips.count()
        avg_earnings_per_trip = float(total_earnings) / total_trips if total_trips > 0 else 0
        
        return JsonResponse({
            'success': True,
            'earnings': {
                'total_earnings': float(total_earnings),
                'total_trips': total_trips,
                'avg_earnings_per_trip': round(avg_earnings_per_trip, 2),
                'currency': 'XAF',
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def daily_earnings(request):
    """Récupérer les gains journaliers du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        today = timezone.now().date()
        
        completed_trips = Trip.objects.filter(
            driver=driver,
            status=Trip.TripStatus.COMPLETED,
            completed_at__date=today
        )
        
        daily_earnings = completed_trips.aggregate(
            total=models.Sum('driver_earnings')
        )['total'] or 0
        
        trips_count = completed_trips.count()
        
        return JsonResponse({
            'success': True,
            'date': str(today),
            'earnings': {
                'daily_earnings': float(daily_earnings),
                'trips_count': trips_count,
                'currency': 'XAF',
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def weekly_earnings(request):
    """Récupérer les gains hebdomadaires du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        completed_trips = Trip.objects.filter(
            driver=driver,
            status=Trip.TripStatus.COMPLETED,
            completed_at__date__range=[week_start, week_end]
        )
        
        weekly_earnings = completed_trips.aggregate(
            total=models.Sum('driver_earnings')
        )['total'] or 0
        
        trips_count = completed_trips.count()
        
        # Récupérer les gains par jour
        daily_data = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_trips = Trip.objects.filter(
                driver=driver,
                status=Trip.TripStatus.COMPLETED,
                completed_at__date=day
            )
            day_earnings = day_trips.aggregate(
                total=models.Sum('driver_earnings')
            )['total'] or 0
            
            daily_data.append({
                'date': str(day),
                'day_name': day.strftime('%A'),
                'earnings': float(day_earnings),
                'trips_count': day_trips.count(),
            })
        
        return JsonResponse({
            'success': True,
            'week': {
                'start': str(week_start),
                'end': str(week_end),
            },
            'earnings': {
                'weekly_earnings': float(weekly_earnings),
                'trips_count': trips_count,
                'currency': 'XAF',
                'daily_breakdown': daily_data,
            }
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============ DOCUMENTS VIEWS ============

@login_required
def list_documents(request):
    """Lister les documents du chauffeur (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'GET':
        documents = DriverDocument.objects.filter(driver=driver)
        
        docs_data = []
        for doc in documents:
            docs_data.append({
                'id': doc.id,
                'type': doc.document_type,
                'file': doc.file.url if doc.file else None,
                'status': doc.status,
                'is_verified': doc.is_verified,
                'uploaded_at': doc.uploaded_at,
                'verified_at': doc.verified_at,
                'notes': doc.notes,
            })
        
        return JsonResponse({
            'success': True,
            'documents': docs_data,
            'count': len(docs_data)
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def upload_document(request):
    """Télécharger un document (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            document_type = data.get('document_type')
            file_data = data.get('file')  # Base64 encoded file
            
            if not document_type:
                return JsonResponse({
                    'success': False,
                    'error': 'Le type de document est requis.'
                }, status=400)
            
            valid_types = [
                DriverDocument.DocumentType.LICENSE,
                DriverDocument.DocumentType.INSURANCE,
                DriverDocument.DocumentType.ID_CARD,
                DriverDocument.DocumentType.VEHICLE_REGISTRATION,
                DriverDocument.DocumentType.POLICE_CLEARANCE,
                DriverDocument.DocumentType.OTHER,
            ]
            
            if document_type not in valid_types:
                return JsonResponse({
                    'success': False,
                    'error': 'Type de document invalide.'
                }, status=400)
            
            # Créer le document
            document = DriverDocument.objects.create(
                driver=driver,
                document_type=document_type,
                status=DriverDocument.DocumentStatus.PENDING,
                notes=data.get('notes', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Document téléchargé avec succès.',
                'document': {
                    'id': document.id,
                    'type': document.document_type,
                    'status': document.status,
                    'uploaded_at': document.uploaded_at,
                }
            })
        
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def document_detail(request, doc_id):
    """Récupérer les détails d'un document (API)"""
    try:
        driver = request.user.driver
    except Driver.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'êtes pas enregistré comme chauffeur.'
        }, status=400)
    
    document = get_object_or_404(DriverDocument, id=doc_id, driver=driver)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'document': {
                'id': document.id,
                'type': document.document_type,
                'file': document.file.url if document.file else None,
                'status': document.status,
                'is_verified': document.is_verified,
                'uploaded_at': document.uploaded_at,
                'verified_at': document.verified_at,
                'notes': document.notes,
            }
        })
    
    if request.method == 'DELETE':
        document.delete()
        return JsonResponse({
            'success': True,
            'message': 'Document supprimé avec succès.'
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

