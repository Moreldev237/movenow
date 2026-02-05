from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
import uuid

class UserManager(BaseUserManager):
    """Custom manager for User model with email as username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Modèle utilisateur personnalisé"""
    class UserTypeChoices(models.TextChoices):
        PASSENGER = 'passenger', _('Passager')
        DRIVER = 'driver', _('Chauffeur')
        FLEET_OWNER = 'fleet_owner', _('Propriétaire de flotte')
        ADMIN = 'admin', _('Administrateur')
    
    # Informations personnelles
    user_type = models.CharField(
        max_length=20,
        choices=UserTypeChoices.choices,
        default=UserTypeChoices.PASSENGER
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Numéro de téléphone")
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de naissance")
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', _('Homme')),
            ('female', _('Femme')),
            ('other', _('Autre')),
        ],
        blank=True,
        null=True
    )
    
    # Localisation
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, default="Douala")
    country = models.CharField(max_length=100, blank=True, default="Cameroun")
    location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326
    )
    
    # Photo de profil
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )
    
    # Vérification
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Préférences
    language = models.CharField(
        max_length=10,
        default='fr',
        choices=[
            ('fr', 'Français'),
            ('en', 'English'),
        ]
    )
    currency = models.CharField(
        max_length=3,
        default='XAF',
        choices=[
            ('XAF', 'FCFA'),
            ('USD', 'USD'),
            ('EUR', 'EUR'),
        ]
    )
    
    # Métadonnées
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_location = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Champs non utilisés de AbstractUser
    username = None
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    first_name = models.CharField(_("Prénom"), max_length=150)
    last_name = models.CharField(_("Nom"), max_length=150)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_driver(self):
        return self.user_type == self.UserTypeChoices.DRIVER
    
    @property
    def is_fleet_owner(self):
        return self.user_type == self.UserTypeChoices.FLEET_OWNER
    
    @property
    def is_passenger(self):
        return self.user_type == self.UserTypeChoices.PASSENGER
    
    def get_initials(self):
        """Récupérer les initiales"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.email:
            return self.email[0].upper()
        return 'U'
    
    def get_full_name(self):
        """Récupérer le nom complet"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def send_verification_email(self):
        """Envoyer l'email de vérification"""
        from .utils import send_verification_email
        send_verification_email(self)
    
    def verify(self):
        """Vérifier le compte utilisateur"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])
    
    def update_location(self, lat, lng):
        """Mettre à jour la position de l'utilisateur"""
        self.location = Point(lng, lat)
        self.save(update_fields=['location'])

class UserSession(models.Model):
    """Sessions utilisateur pour le suivi"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Session utilisateur")
        verbose_name_plural = _("Sessions utilisateur")
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"

class UserWallet(models.Model):
    """Portefeuille utilisateur"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Statistiques
    total_deposited = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_withdrawn = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Dernière transaction
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Portefeuille")
        verbose_name_plural = _("Portefeuilles")
    
    def __str__(self):
        return f"Wallet de {self.user.email}"
    
    def deposit(self, amount, reference=None):
        """Déposer des fonds"""
        from payment.models import Transaction
        
        self.balance += amount
        self.total_deposited += amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        # Créer une transaction
        Transaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type='deposit',
            reference=reference,
            status='completed'
        )
    
    def withdraw(self, amount, reference=None):
        """Retirer des fonds"""
        from payment.models import Transaction
        
        if self.balance < amount:
            raise ValueError("Solde insuffisant")
        
        self.balance -= amount
        self.total_withdrawn += amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        # Créer une transaction
        Transaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type='withdrawal',
            reference=reference,
            status='completed'
        )
    
    def make_payment(self, amount, trip=None, reference=None):
        """Effectuer un paiement"""
        from payment.models import Transaction
        
        if self.balance < amount:
            return False
        
        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        # Créer une transaction
        Transaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type='payment',
            reference=reference,
            trip=trip,
            status='completed'
        )
        
        return True

class UserSettings(models.Model):
    """Paramètres utilisateur"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Préférences de voyage
    preferred_vehicle_type = models.ForeignKey(
        'core.VehicleType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    auto_share_location = models.BooleanField(
        default=False,
        help_text=_("Partager automatiquement la position pendant les courses")
    )
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Contact d'urgence à prévenir")
    )
    
    # Sécurité
    two_factor_auth = models.BooleanField(default=False)
    login_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Paramètres utilisateur")
        verbose_name_plural = _("Paramètres utilisateur")
    
    def __str__(self):
        return f"Paramètres de {self.user.email}"