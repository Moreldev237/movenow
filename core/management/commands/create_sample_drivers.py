"""
Management command to create sample drivers for testing the booking flow.
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from core.models import Driver, VehicleType


class Command(BaseCommand):
    help = 'Create sample drivers for testing the booking flow'

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

        # Sample driver data - located around Douala, Cameroon
        drivers_data = [
            {
                'email': 'driver1@movenow.cm',
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'phone': '+237600000001',
                'license_number': 'LIC001234',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['voiture'],
                'vehicle_plate': 'CE-1234-AI',
                'vehicle_model': 'Toyota Camry',
                'vehicle_color': 'Blanc',
                'vehicle_year': 2020,
                'lat': 4.0511,  # Near Bonapriso
                'lng': 9.7679,
                'rating': 4.8,
            },
            {
                'email': 'driver2@movenow.cm',
                'first_name': 'Marie',
                'last_name': 'Nkoghe',
                'phone': '+237600000002',
                'license_number': 'LIC001235',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['voiture'],
                'vehicle_plate': 'CE-5678-BK',
                'vehicle_model': 'Honda Civic',
                'vehicle_color': 'Noir',
                'vehicle_year': 2019,
                'lat': 4.0275,  # Near Akwa
                'lng': 9.7043,
                'rating': 4.5,
            },
            {
                'email': 'driver3@movenow.cm',
                'first_name': 'Pierre',
                'last_name': 'Mouaha',
                'phone': '+237600000003',
                'license_number': 'LIC001236',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['moto'],
                'vehicle_plate': 'CE-9012-CM',
                'vehicle_model': 'Yamaha NMAX',
                'vehicle_color': 'Rouge',
                'vehicle_year': 2022,
                'lat': 4.0892,  # Near Deido
                'lng': 9.6923,
                'rating': 4.9,
            },
            {
                'email': 'driver4@movenow.cm',
                'first_name': 'Claire',
                'last_name': 'Biyiti',
                'phone': '+237600000004',
                'license_number': 'LIC001237',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['van'],
                'vehicle_plate': 'CE-3456-DL',
                'vehicle_model': 'Toyota Hiace',
                'vehicle_color': 'Gris',
                'vehicle_year': 2021,
                'lat': 4.0123,  # Near Bali
                'lng': 9.7156,
                'rating': 4.7,
            },
            {
                'email': 'driver5@movenow.cm',
                'first_name': 'Paul',
                'last_name': 'Essomba',
                'phone': '+237600000005',
                'license_number': 'LIC001238',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['vip'],
                'vehicle_plate': 'CE-7890-EM',
                'vehicle_model': 'Mercedes Classe E',
                'vehicle_color': 'Noir',
                'vehicle_year': 2023,
                'lat': 4.0445,  # Near Bonanjo
                'lng': 9.7321,
                'rating': 5.0,
            },
            {
                'email': 'driver6@movenow.cm',
                'first_name': 'Anne',
                'last_name': 'Mvongo',
                'phone': '+237600000006',
                'license_number': 'LIC001239',
                'license_expiry': timezone.now().date() + timedelta(days=365),
                'vehicle_type': vehicle_types['voiture'],
                'vehicle_plate': 'CE-2468-FN',
                'vehicle_model': 'Kia Sportage',
                'vehicle_color': 'Bleu',
                'vehicle_year': 2021,
                'lat': 4.0654,  # Near Ndokoti
                'lng': 9.7523,
                'rating': 4.6,
            },
        ]

        created_count = 0
        for driver_data in drivers_data:
            email = driver_data.pop('email')
            first_name = driver_data.pop('first_name')
            last_name = driver_data.pop('last_name')
            phone = driver_data.pop('phone')
            lat = driver_data.pop('lat')
            lng = driver_data.pop('lng')
            
            # Create or get user
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
                self.stdout.write(f'Created user: {email}')
            
            # Check if driver profile exists
            if hasattr(user, 'driver_profile'):
                self.stdout.write(f'Driver already exists: {email}')
                continue
            
            # Create driver with location
            location = Point(lng, lat, srid=4326)
            
            driver = Driver.objects.create(
                user=user,
                current_location=location,
                is_available=True,
                is_verified=True,
                **driver_data
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created driver: {user.get_full_name()} - {driver.vehicle_plate}')
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {created_count} drivers!'
        ))
        self.stdout.write('\nYou can now test the booking flow:')
        self.stdout.write('1. Go to /booking/new/')
        self.stdout.write('2. Enter pickup and dropoff locations')
        self.stdout.write('3. Click "Rechercher un chauffeur"')
        self.stdout.write('4. Select a driver from the list')
        self.stdout.write('5. Choose payment method and confirm')
        self.stdout.write('\nDriver login credentials:')
        for driver_data in drivers_data[:3]:
            self.stdout.write(f'  Email: {driver_data["email"]}, Password: driver123')

