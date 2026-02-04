from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import VehicleType, Driver, Trip
from accounts.models import User
from datetime import date
from django.contrib.gis.geos import Point

User = get_user_model()

class VehicleTypeModelTest(TestCase):
    """Tests pour le modèle VehicleType"""
    
    def setUp(self):
        self.vehicle_type = VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50,
            capacity=4
        )
    
    def test_vehicle_type_creation(self):
        """Test de création d'un type de véhicule"""
        self.assertEqual(self.vehicle_type.name, 'taxi')
        self.assertEqual(self.vehicle_type.base_price, 1000)
        self.assertEqual(self.vehicle_type.price_per_km, 250)
        self.assertEqual(self.vehicle_type.get_name_display(), 'Taxi')
    
    def test_vehicle_type_str(self):
        """Test de la méthode __str__"""
        self.assertEqual(str(self.vehicle_type), 'Taxi')

class DriverModelTest(TestCase):
    """Tests pour le modèle Driver"""
    
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='driver@test.com',
            phone='677777777',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Créer un type de véhicule
        self.vehicle_type = VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50
        )
        
        # Créer un chauffeur
        self.driver = Driver.objects.create(
            user=self.user,
            license_number='DL123456',
            license_expiry=date(2025, 12, 31),
            vehicle_type=self.vehicle_type,
            vehicle_plate='CE 123 AB',
            vehicle_model='Toyota Corolla',
            vehicle_color='White',
            is_verified=True
        )
    
    def test_driver_creation(self):
        """Test de création d'un chauffeur"""
        self.assertEqual(self.driver.user.email, 'driver@test.com')
        self.assertEqual(self.driver.license_number, 'DL123456')
        self.assertEqual(self.driver.vehicle_plate, 'CE 123 AB')
        self.assertTrue(self.driver.is_verified)
    
    def test_driver_str(self):
        """Test de la méthode __str__"""
        expected = f"{self.user.get_full_name()} - {self.driver.vehicle_plate}"
        self.assertEqual(str(self.driver), expected)
    
    def test_update_location(self):
        """Test de la mise à jour de position"""
        lat = 4.0511
        lng = 9.7679
        
        self.driver.update_location(lat, lng)
        
        # Recharger le chauffeur depuis la base de données
        driver = Driver.objects.get(id=self.driver.id)
        
        self.assertIsNotNone(driver.current_location)
        self.assertEqual(driver.current_location.y, lat)
        self.assertEqual(driver.current_location.x, lng)
        self.assertIsNotNone(driver.last_location_update)

class TripModelTest(TestCase):
    """Tests pour le modèle Trip"""
    
    def setUp(self):
        # Créer un passager
        self.passenger = User.objects.create_user(
            email='passenger@test.com',
            phone='677777778',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        
        # Créer un chauffeur
        self.driver_user = User.objects.create_user(
            email='driver2@test.com',
            phone='677777779',
            password='testpass123',
            first_name='Mike',
            last_name='Smith'
        )
        
        self.vehicle_type = VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50
        )
        
        self.driver = Driver.objects.create(
            user=self.driver_user,
            license_number='DL123457',
            license_expiry=date(2025, 12, 31),
            vehicle_type=self.vehicle_type,
            vehicle_plate='CE 124 AB',
            vehicle_model='Toyota Camry',
            vehicle_color='Black'
        )
        
        # Créer une course
        self.trip = Trip.objects.create(
            passenger=self.passenger,
            driver=self.driver,
            vehicle_type=self.vehicle_type,
            pickup_address='Bonanjo, Douala',
            pickup_location=Point(9.7679, 4.0511),
            dropoff_address='Akwa, Douala',
            dropoff_location=Point(9.7579, 4.0611),
            distance=5.2,
            duration=15,
            fare=2500,
            status='accepted'
        )
    
    def test_trip_creation(self):
        """Test de création d'une course"""
        self.assertEqual(self.trip.passenger.email, 'passenger@test.com')
        self.assertEqual(self.trip.driver.user.email, 'driver2@test.com')
        self.assertEqual(self.trip.distance, 5.2)
        self.assertEqual(self.trip.fare, 2500)
        self.assertEqual(self.trip.status, 'accepted')
        self.assertIsNotNone(self.trip.accepted_at)
    
    def test_trip_str(self):
        """Test de la méthode __str__"""
        expected = f"Course #{self.trip.id} - {self.passenger.email}"
        self.assertEqual(str(self.trip), expected)
    
    def test_calculate_fare(self):
        """Test du calcul du prix"""
        calculated_fare = self.trip.calculate_fare()
        
        # Calcul manuel: 1000 + (5.2 * 250) + (15/60 * 50)
        expected = 1000 + (5.2 * 250) + (0.25 * 50)
        expected = round(expected, 2)
        
        self.assertEqual(calculated_fare, expected)
    
    def test_can_be_cancelled(self):
        """Test de la vérification d'annulation"""
        # Course en attente peut être annulée
        self.trip.status = 'pending'
        self.assertTrue(self.trip.can_be_cancelled())
        
        # Course acceptée peut être annulée
        self.trip.status = 'accepted'
        self.assertTrue(self.trip.can_be_cancelled())
        
        # Course commencée ne peut pas être annulée
        self.trip.status = 'started'
        self.assertFalse(self.trip.can_be_cancelled())
        
        # Course terminée ne peut pas être annulée
        self.trip.status = 'completed'
        self.assertFalse(self.trip.can_be_cancelled())