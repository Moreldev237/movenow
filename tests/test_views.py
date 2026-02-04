from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import VehicleType, Driver
from accounts.models import User
from datetime import date

User = get_user_model()

class HomeViewTest(TestCase):
    """Tests pour la vue d'accueil"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')
        
        # Créer des types de véhicules
        VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50
        )
        VehicleType.objects.create(
            name='moto',
            base_price=500,
            price_per_km=150,
            price_per_minute=30
        )
    
    def test_home_view_status_code(self):
        """Test du code de statut de la vue"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_home_view_template(self):
        """Test du template utilisé"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'core/home.html')
    
    def test_home_view_context(self):
        """Test du contexte de la vue"""
        response = self.client.get(self.url)
        
        # Vérifier que les types de véhicules sont dans le contexte
        self.assertIn('vehicle_types', response.context)
        self.assertEqual(response.context['vehicle_types'].count(), 2)
        
        # Vérifier que les statistiques sont dans le contexte
        self.assertIn('stats', response.context)
        
        # Vérifier que le formulaire de réservation est dans le contexte
        self.assertIn('booking_form', response.context)

class BookingViewTest(TestCase):
    """Tests pour les vues de réservation"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='test@test.com',
            phone='677777777',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Créer un type de véhicule
        self.vehicle_type = VehicleType.objects.create(
            name='taxi',
            base_price=1000,
            price_per_km=250,
            price_per_minute=50
        )
    
    def test_book_view_requires_login(self):
        """Test que la vue de réservation nécessite une connexion"""
        url = reverse('booking:book')
        response = self.client.get(url)
        
        # Doit rediriger vers la page de connexion
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_book_view_authenticated(self):
        """Test de la vue de réservation pour un utilisateur authentifié"""
        self.client.login(email='test@test.com', password='testpass123')
        url = reverse('booking:book')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/book.html')
        
        # Vérifier que les types de véhicules sont dans le contexte
        self.assertIn('vehicle_types', response.context)
    
    def test_book_view_post(self):
        """Test de la soumission du formulaire de réservation"""
        self.client.login(email='test@test.com', password='testpass123')
        url = reverse('booking:book')
        
        data = {
            'vehicle_type': self.vehicle_type.id,
            'pickup_address': 'Bonanjo, Douala',
            'pickup_lat': '4.0511',
            'pickup_lng': '9.7679',
            'dropoff_address': 'Akwa, Douala',
            'dropoff_lat': '4.0611',
            'dropoff_lng': '9.7579',
            'is_shared': False,
        }
        
        response = self.client.post(url, data)
        
        # Doit rediriger vers la page de suivi
        self.assertEqual(response.status_code, 302)
        self.assertIn('/booking/track/', response.url)

class AuthenticationTest(TestCase):
    """Tests pour l'authentification"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        
        # Données de test
        self.user_data = {
            'email': 'newuser@test.com',
            'phone': '677777778',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
    
    def test_user_registration(self):
        """Test de l'inscription d'un nouvel utilisateur"""
        response = self.client.post(self.register_url, self.user_data)
        
        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())
        
        # Vérifier que l'utilisateur est connecté après l'inscription
        user = User.objects.get(email='newuser@test.com')
        self.assertTrue(user.is_authenticated)
    
    def test_user_login(self):
        """Test de la connexion d'un utilisateur"""
        # Créer un utilisateur d'abord
        User.objects.create_user(
            email='login@test.com',
            phone='677777779',
            password='testpass123',
            first_name='Login',
            last_name='Test'
        )
        
        response = self.client.post(self.login_url, {
            'email': 'login@test.com',
            'password': 'testpass123'
        })
        
        # Doit rediriger vers la page d'accueil
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
    
    def test_user_logout(self):
        """Test de la déconnexion"""
        # Créer et connecter un utilisateur
        user = User.objects.create_user(
            email='logout@test.com',
            phone='677777780',
            password='testpass123'
        )
        self.client.force_login(user)
        
        # Vérifier que l'utilisateur est connecté
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Se déconnecter
        logout_url = reverse('logout')
        response = self.client.get(logout_url)
        
        # Doit rediriger vers la page d'accueil
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')