from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import FleetManager, FleetDriver, FleetVehicleAssignment, FleetMaintenance, FleetReport
from core.models import Fleet, Vehicle, Driver
from accounts.decorators import fleet_owner_required


# Fleet Views
@login_required
@fleet_owner_required
def fleet_list(request):
    """Liste des flottes de l'utilisateur"""
    fleets = Fleet.objects.filter(owner=request.user)
    
    fleets_data = []
    for fleet in fleets:
        fleets_data.append({
            'id': fleet.id,
            'name': fleet.name,
            'description': fleet.description,
            'contact_phone': fleet.contact_phone,
            'contact_email': fleet.contact_email,
            'is_active': fleet.is_active,
            'is_verified': fleet.is_verified,
            'total_drivers': fleet.get_active_drivers().count(),
            'total_vehicles': fleet.get_total_vehicles(),
            'created_at': fleet.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'fleets': fleets_data,
        'count': len(fleets_data),
    })


@login_required
@fleet_owner_required
def create_fleet(request):
    """Créer une nouvelle flotte"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            fleet = Fleet.objects.create(
                owner=request.user,
                name=data.get('name'),
                description=data.get('description', ''),
                contact_phone=data.get('contact_phone'),
                contact_email=data.get('contact_email'),
                address=data.get('address'),
                business_license=data.get('business_license', ''),
                tax_id=data.get('tax_id', ''),
                commission_rate=data.get('commission_rate', 20),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Flotte créée avec succès.',
                'fleet': {
                    'id': fleet.id,
                    'name': fleet.name,
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@fleet_owner_required
def fleet_detail(request, fleet_id):
    """Détails d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    # Vérifier les permissions
    manager = FleetManager.objects.filter(fleet=fleet, user=request.user).first()
    
    fleet_data = {
        'id': fleet.id,
        'name': fleet.name,
        'description': fleet.description,
        'contact_phone': fleet.contact_phone,
        'contact_email': fleet.contact_email,
        'address': fleet.address,
        'business_license': fleet.business_license,
        'tax_id': fleet.tax_id,
        'commission_rate': float(fleet.commission_rate),
        'is_active': fleet.is_active,
        'is_verified': fleet.is_verified,
        'total_drivers': fleet.get_active_drivers().count(),
        'total_vehicles': fleet.get_total_vehicles(),
        'created_at': fleet.created_at.isoformat(),
        'updated_at': fleet.updated_at.isoformat(),
    }
    
    return JsonResponse({
        'success': True,
        'fleet': fleet_data,
    })


@login_required
@fleet_owner_required
def update_fleet(request, fleet_id):
    """Mettre à jour une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            fleet.name = data.get('name', fleet.name)
            fleet.description = data.get('description', fleet.description)
            fleet.contact_phone = data.get('contact_phone', fleet.contact_phone)
            fleet.contact_email = data.get('contact_email', fleet.contact_email)
            fleet.address = data.get('address', fleet.address)
            fleet.commission_rate = data.get('commission_rate', fleet.commission_rate)
            
            if 'business_license' in data:
                fleet.business_license = data['business_license']
            if 'tax_id' in data:
                fleet.tax_id = data['tax_id']
            
            fleet.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Flotte mise à jour avec succès.',
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@fleet_owner_required
def delete_fleet(request, fleet_id):
    """Supprimer une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    if request.method == 'POST':
        fleet.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Flotte supprimée avec succès.',
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Vehicle Views
@login_required
@fleet_owner_required
def vehicle_list(request, fleet_id):
    """Liste des véhicules d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    vehicles = Vehicle.objects.filter(fleet=fleet)
    
    vehicles_data = []
    for vehicle in vehicles:
        vehicles_data.append({
            'id': vehicle.id,
            'plate_number': vehicle.plate_number,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'color': vehicle.color,
            'vehicle_type': vehicle.vehicle_type.name if vehicle.vehicle_type else None,
            'status': vehicle.status,
            'current_mileage': vehicle.current_mileage,
            'is_active': vehicle.is_active,
            'driver': vehicle.driver.user.get_full_name() if vehicle.driver else None,
        })
    
    return JsonResponse({
        'success': True,
        'vehicles': vehicles_data,
        'count': len(vehicles_data),
    })


@login_required
@fleet_owner_required
def add_vehicle(request, fleet_id):
    """Ajouter un véhicule à une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            from core.models import VehicleType
            vehicle_type = None
            if data.get('vehicle_type_id'):
                vehicle_type = get_object_or_404(VehicleType, id=data['vehicle_type_id'])
            
            vehicle = Vehicle.objects.create(
                fleet=fleet,
                plate_number=data['plate_number'],
                make=data['make'],
                model=data['model'],
                year=data['year'],
                color=data['color'],
                vehicle_type=vehicle_type,
                registration_document=data.get('registration_document', ''),
                insurance_policy=data.get('insurance_policy', ''),
                insurance_expiry=data.get('insurance_expiry'),
                current_mileage=data.get('current_mileage', 0),
                maintenance_interval=data.get('maintenance_interval', 10000),
                status=data.get('status', 'active'),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Véhicule ajouté avec succès.',
                'vehicle': {
                    'id': vehicle.id,
                    'plate_number': vehicle.plate_number,
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@fleet_owner_required
def vehicle_detail(request, fleet_id, vehicle_id):
    """Détails d'un véhicule"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, fleet=fleet)
    
    vehicle_data = {
        'id': vehicle.id,
        'plate_number': vehicle.plate_number,
        'make': vehicle.make,
        'model': vehicle.model,
        'year': vehicle.year,
        'color': vehicle.color,
        'vehicle_type': vehicle.vehicle_type.name if vehicle.vehicle_type else None,
        'registration_document': vehicle.registration_document,
        'insurance_policy': vehicle.insurance_policy,
        'insurance_expiry': vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else None,
        'current_mileage': vehicle.current_mileage,
        'last_maintenance': vehicle.last_maintenance.isoformat() if vehicle.last_maintenance else None,
        'next_maintenance': vehicle.next_maintenance.isoformat() if vehicle.next_maintenance else None,
        'maintenance_interval': vehicle.maintenance_interval,
        'status': vehicle.status,
        'is_active': vehicle.is_active,
        'driver': vehicle.driver.user.get_full_name() if vehicle.driver else None,
        'driver_id': vehicle.driver.id if vehicle.driver else None,
    }
    
    return JsonResponse({
        'success': True,
        'vehicle': vehicle_data,
    })


@login_required
@fleet_owner_required
def update_vehicle(request, fleet_id, vehicle_id):
    """Mettre à jour un véhicule"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, fleet=fleet)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            vehicle.plate_number = data.get('plate_number', vehicle.plate_number)
            vehicle.make = data.get('make', vehicle.make)
            vehicle.model = data.get('model', vehicle.model)
            vehicle.year = data.get('year', vehicle.year)
            vehicle.color = data.get('color', vehicle.color)
            
            if 'vehicle_type_id' in data:
                from core.models import VehicleType
                vehicle_type = get_object_or_404(VehicleType, id=data['vehicle_type_id'])
                vehicle.vehicle_type = vehicle_type
            
            vehicle.registration_document = data.get('registration_document', vehicle.registration_document)
            vehicle.insurance_policy = data.get('insurance_policy', vehicle.insurance_policy)
            
            if 'insurance_expiry' in data and data['insurance_expiry']:
                from datetime import datetime
                vehicle.insurance_expiry = datetime.fromisoformat(data['insurance_expiry']).date()
            
            vehicle.current_mileage = data.get('current_mileage', vehicle.current_mileage)
            vehicle.maintenance_interval = data.get('maintenance_interval', vehicle.maintenance_interval)
            vehicle.status = data.get('status', vehicle.status)
            
            vehicle.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Véhicule mis à jour avec succès.',
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@fleet_owner_required
def delete_vehicle(request, fleet_id, vehicle_id):
    """Supprimer un véhicule"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, fleet=fleet)
    
    if request.method == 'POST':
        vehicle.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Véhicule supprimé avec succès.',
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Driver Assignment Views
@login_required
@fleet_owner_required
def fleet_drivers(request, fleet_id):
    """Liste des chauffeurs d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    fleet_drivers = FleetDriver.objects.filter(fleet=fleet, is_active=True)
    
    drivers_data = []
    for fd in fleet_drivers:
        drivers_data.append({
            'id': fd.id,
            'driver_id': fd.driver.id,
            'name': fd.driver.user.get_full_name(),
            'email': fd.driver.user.email,
            'phone': fd.driver.user.phone_number,
            'vehicle': fd.driver.vehicle_plate,
            'contract_type': fd.contract_type,
            'contract_start': fd.contract_start.isoformat() if fd.contract_start else None,
            'contract_end': fd.contract_end.isoformat() if fd.contract_end else None,
            'commission_rate': float(fd.commission_rate),
            'is_active': fd.is_active,
            'is_approved': fd.is_approved,
        })
    
    return JsonResponse({
        'success': True,
        'drivers': drivers_data,
        'count': len(drivers_data),
    })


@login_required
@fleet_owner_required
def assign_driver(request, fleet_id):
    """Assigner un chauffeur à une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            driver_id = data.get('driver_id')
            driver = get_object_or_404(Driver, id=driver_id)
            
            # Vérifier si le chauffeur est déjà assigné
            if FleetDriver.objects.filter(driver=driver, is_active=True).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce chauffeur est déjà assigné à une flotte.'
                }, status=400)
            
            fleet_driver = FleetDriver.objects.create(
                fleet=fleet,
                driver=driver,
                contract_type=data.get('contract_type', 'contractor'),
                contract_start=data.get('contract_start', timezone.now().date()),
                contract_end=data.get('contract_end'),
                commission_rate=data.get('commission_rate', 70),
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Chauffeur assigné avec succès.',
                'fleet_driver': {
                    'id': fleet_driver.id,
                    'driver': driver.user.get_full_name(),
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données JSON invalides.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
@fleet_owner_required
def remove_driver(request, fleet_id, driver_id):
    """Retirer un chauffeur d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    fleet_driver = get_object_or_404(FleetDriver, id=driver_id, fleet=fleet)
    
    if request.method == 'POST':
        fleet_driver.is_active = False
        fleet_driver.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Chauffeur retiré de la flotte avec succès.',
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Fleet Statistics Views
@login_required
@fleet_owner_required
def fleet_stats(request, fleet_id):
    """Statistiques d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    # Statistiques par défaut
    stats = {
        'total_drivers': fleet.get_active_drivers().count(),
        'total_vehicles': fleet.get_total_vehicles(),
        'active_trips': 0,
        'completed_trips': 0,
        'total_earnings': 0,
    }
    
    # Calculer les statistiques si la date est spécifiée
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        from datetime import datetime
        from django.db.models import Q
        from core.models import Trip
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        drivers = fleet.get_active_drivers()
        
        trips = Trip.objects.filter(
            driver__in=drivers,
            completed_at__range=[start, end],
            status='completed'
        )
        
        stats['total_trips'] = trips.count()
        stats['completed_trips'] = trips.count()
        stats['total_earnings'] = trips.aggregate(total=Sum('fare'))['total'] or 0
        stats['active_trips'] = Trip.objects.filter(
            driver__in=drivers,
            status__in=['accepted', 'arrived', 'started']
        ).count()
    
    return JsonResponse({
        'success': True,
        'stats': stats,
    })


@login_required
@fleet_owner_required
def fleet_earnings(request, fleet_id):
    """Revenus d'une flotte"""
    fleet = get_object_or_404(Fleet, id=fleet_id, owner=request.user)
    
    # Période (par défaut: ce mois)
    period = request.GET.get('period', 'month')
    
    today = timezone.now()
    
    if period == 'day':
        start_date = today.date()
        end_date = today.date()
    elif period == 'week':
        start_date = (today - timedelta(days=7)).date()
        end_date = today.date()
    elif period == 'month':
        start_date = today.replace(day=1).date()
        end_date = today.date()
    else:
        start_date = request.GET.get('start_date', (today - timedelta(days=30)).date())
        end_date = request.GET.get('end_date', today.date())
    
    drivers = fleet.get_active_drivers()
    
    from core.models import Trip
    trips = Trip.objects.filter(
        driver__in=drivers,
        completed_at__date__range=[start_date, end_date],
        status='completed'
    )
    
    total_earnings = trips.aggregate(total=Sum('fare'))['total'] or 0
    commission = float(total_earnings) * (float(fleet.commission_rate) / 100)
    
    earnings_data = {
        'period': {
            'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
            'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
        },
        'total_earnings': float(total_earnings),
        'commission_rate': float(fleet.commission_rate),
        'commission_amount': commission,
        'net_earnings': float(total_earnings) - commission,
        'trip_count': trips.count(),
    }
    
    # Revenus par jour
    daily_earnings = []
    current_date = start_date
    while current_date <= end_date:
        day_trips = trips.filter(completed_at__date=current_date)
        day_earnings = day_trips.aggregate(total=Sum('fare'))['total'] or 0
        
        daily_earnings.append({
            'date': str(current_date),
            'earnings': float(day_earnings),
            'trip_count': day_trips.count(),
        })
        current_date += timedelta(days=1)
    
    earnings_data['daily_earnings'] = daily_earnings
    
    return JsonResponse({
        'success': True,
        'earnings': earnings_data,
    })

