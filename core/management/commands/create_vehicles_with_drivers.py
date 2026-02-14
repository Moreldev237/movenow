"""
Management command to create vehicles with multiple drivers assigned.
Ensures each vehicle has at least 2 available drivers.
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from core.models import Driver, VehicleType, Fleet, Vehicle


class Command(BaseCommand):
    help = 'Create vehicles with at least 2 available drivers each'

    def handle(self, *args, **options):
        # Create vehicle types if they don't exist
        vehicle_types_data = [
            {'name': 'moto', 'base_price': 500, 'price_per_km': 250, 'price_per_minute': 50, 'capacity': 1},
            {'name': 'voiture', 'base_price': 1000, 'price_per_km': 300, 'price_per_minute': 75, 'capacity': 4},
            {'name': 'van', 'base_price': 1500, 'price_per_km': 400, 'price_per_minute': 100, 'capacity': 6},
            {'name': 'vip', 'base_price': 2000, 'price_per_km': 500, 'price_per_minute': 125, 'capacity': 4},
        ]

        vehicle_types = {}
        for vt_data in vehicle_types_data:
            vt, created = VehicleType.objects.get_or_create(
                name=vt_data['name'],
                defaults=vt_data
            )
            vehicle_types[vt_data['name']] = vt
            if created:
                self.stdout.write(f'Created vehicle type: {vt.name}')

        # Get or create a default fleet
        fleet, fleet_created = Fleet.objects.get_or_create(
            name='MoveNow Fleet',
            defaults={
                'owner': User.objects.filter(is_superuser=True).first() or User.objects.first(),
                'contact_phone': '+237600000000',
                'contact_email': 'fleet@movenow.cm',
                'address': 'Douala, Cameroon',
            }
        )
        if fleet_created:
            self.stdout.write(f'Created fleet: {fleet.name}')
        
        # Ensure fleet owner exists
        if not fleet.owner:
            # Get first user as owner
            fleet.owner = User.objects.first()
            fleet.save()

        # Define vehicles to create (each with at least 2 drivers)
        vehicles_data = [
            {
                'plate_number': 'CE-1001-AA',
                'make': 'Toyota',
                'model': 'Camry',
                'year': 2020,
                'color': 'Blanc',
                'vehicle_type': vehicle_types['voiture'],
                'drivers_count': 2,
            },
            {
                'plate_number': 'CE-1002-BB',
                'make': 'Honda',
                'model': 'Civic',
                'year': 2019,
                'color': 'Noir',
                'vehicle_type': vehicle_types['voiture'],
                'drivers_count': 2,
            },
            {
                'plate_number': 'CE-1003-CC',
                'make': 'Toyota',
                'model': 'Hiace',
                'year': 2021,
                'color': 'Gris',
                'vehicle_type': vehicle_types['van'],
                'drivers_count': 2,
            },
            {
                'plate_number': 'CE-1004-DD',
                'make': 'Mercedes',
                'model': 'Classe E',
                'year': 2023,
                'color': 'Noir',
                'vehicle_type': vehicle_types['vip'],
                'drivers_count': 2,
            },
            {
                'plate_number': 'CE-1005-EE',
                'make': 'Yamaha',
                'model': 'NMAX',
                'year': 2022,
                'color': 'Rouge',
                'vehicle_type': vehicle_types['moto'],
                'drivers_count': 2,
            },
        ]

        total_drivers_created = 0
        
        for vehicle_data in vehicles_data:
            drivers_count = vehicle_data.pop('drivers_count')
            
            # Create or get vehicle
            vehicle, vehicle_created = Vehicle.objects.get_or_create(
                plate_number=vehicle_data['plate_number'],
                defaults={
                    **vehicle_data,
                    'fleet': fleet,
                    'status': 'active',
                }
            )
            
            if vehicle_created:
                self.stdout.write(f'Created vehicle: {vehicle.plate_number}')
            else:
                self.stdout.write(f'Vehicle already exists: {vehicle.plate_number}')

            # Create drivers for this vehicle
            for i in range(1, drivers_count + 1):
                email = f'driver_{vehicle.plate_number.replace("-", "_")}_{i}@movenow.cm'
                first_name = f'Chauffeur{i}'
                last_name = vehicle.make
                phone = f'+2376{i:07d}'
                license_number = f'LIC{vehicle.plate_number.replace("-", "")}{i}'
                
                # Check if user exists
                user, user_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'user_type': User.UserTypeChoices.DRIVER,
                    }
                )
                
                if user_created:
                    user.set_password('driver123')
                    user.save()
                    self.stdout.write(f'  Created user: {email}')

                # Check if driver profile exists
                driver, driver_created = Driver.objects.get_or_create(
                    user=user,
                    defaults={
                        'license_number': license_number,
                        'license_expiry': timezone.now().date() + timedelta(days=365),
                        'vehicle_type': vehicle.vehicle_type,
                        'vehicle_plate': vehicle.plate_number,
                        'vehicle_model': f'{vehicle.make} {vehicle.model}',
                        'vehicle_color': vehicle.color,
                        'vehicle_year': vehicle.year,
                        'is_available': True,
                        'is_verified': True,
                        'is_active': True,
                        'rating': 4.5 + (i * 0.1),
                        'current_location': Point(9.7 + (i * 0.01), 4.0 + (i * 0.01), srid=4326),
                    }
                )
                
                if driver_created:
                    total_drivers_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created driver: {user.get_full_name()} - {vehicle.plate_number}')
                    )
                else:
                    # Update driver to be available
                    driver.is_available = True
                    driver.is_active = True
                    driver.save(update_fields=['is_available', 'is_active'])
                    self.stdout.write(f'  Driver already exists, marked as available: {user.get_full_name()}')

        # Verify each vehicle has at least 2 available drivers
        self.stdout.write(self.style.SUCCESS('\n=== Vérification des véhicules ==='))
        
        for vehicle in Vehicle.objects.filter(fleet=fleet, is_active=True):
            available_drivers = Driver.objects.filter(
                vehicle_plate=vehicle.plate_number,
                is_available=True,
                is_active=True
            )
            count = available_drivers.count()
            status = self.style.SUCCESS('✓') if count >= 2 else self.style.ERROR('✗')
            self.stdout.write(
                f'{status} Véhicule {vehicle.plate_number}: {count} chauffeurs disponibles'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Résumé ==='
        ))
        self.stdout.write(f'Véhicules créés: {len(vehicles_data)}')
        self.stdout.write(f'Chauffeurs créés/mis à jour: {total_drivers_created}')
        self.stdout.write('\nOpération terminée avec succès!')

