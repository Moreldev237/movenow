from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import VehicleType
import json

User = get_user_model()

class CalculateFareAPITest(TestCase):
    """Tests pour l'API de calcul de prix"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/calculate-fare/'
        
        # Créer un type de véhicule
        self.vehicle_type = VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50
        )
    
    def test_calculate_fare_valid(self):
        """Test de calcul de prix avec des données valides"""
        data = {
            'vehicle_type': self.vehicle_type.id,
            'distance': 5.0,
            'duration': 15,
            'shared_ride': False
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('fare', response.data)
        
        # Vérifier le calcul
        expected_fare = 1000 + (5.0 * 250) + (15/60 * 50)
        expected_fare = round(expected_fare, 2)
        self.assertEqual(response.data['fare'], expected_fare)
    
    def test_calculate_fare_shared(self):
        """Test de calcul de prix avec covoiturage"""
        data = {
            'vehicle_type': self.vehicle_type.id,
            'distance': 5.0,
            'duration': 15,
            'shared_ride': True
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Prix normal
        normal_fare = 1000 + (5.0 * 250) + (15/60 * 50)
        # Avec 30% de réduction
        expected_fare = normal_fare * 0.7
        expected_fare = round(expected_fare, 2)
        
        self.assertEqual(response.data['fare'], expected_fare)
    
    def test_calculate_fare_invalid(self):
        """Test de calcul de prix avec des données invalides"""
        data = {
            'vehicle_type': 999,  # ID inexistant
            'distance': 5.0,
            'duration': 15,
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)

class AuthenticationAPITest(TestCase):
    """Tests pour l'API d'authentification"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        
        # Créer un utilisateur pour les tests de connexion
        self.user = User.objects.create_user(
            email='test@test.com',
            phone='677777777',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_register_api(self):
        """Test de l'API d'inscription"""
        data = {
            'email': 'new@test.com',
            'phone': '677777778',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'TestPass123!',
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        
        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(email='new@test.com').exists())
    
    def test_login_api(self):
        """Test de l'API de connexion"""
        data = {
            'email': 'test@test.com',
            'password': 'testpass123',
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
    
    def test_login_api_invalid(self):
        """Test de l'API de connexion avec des identifiants invalides"""
        data = {
            'email': 'test@test.com',
            'password': 'wrongpassword',
        }
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)

class ProtectedAPITest(TestCase):
    """Tests pour les APIs protégées"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Créer et connecter un utilisateur
        self.user = User.objects.create_user(
            email='protected@test.com',
            phone='677777779',
            password='testpass123',
            first_name='Protected',
            last_name='User'
        )
        
        # Obtenir un token d'authentification
        response = self.client.post('/api/auth/login/', {
            'email': 'protected@test.com',
            'password': 'testpass123'
        })
        
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
    
    def test_protected_api_with_token(self):
        """Test d'accès à une API protégée avec token"""
        url = '/api/booking/history/'
        response = self.client.get(url)
        
        # Doit avoir accès
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
    
    def test_protected_api_without_token(self):
        """Test d'accès à une API protégée sans token"""
        client = APIClient()  # Nouveau client sans credentials
        url = '/api/booking/history/'
        response = client.get(url)
        
        # Doit refuser l'accès
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)