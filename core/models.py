from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from accounts.models import User

class VehicleType(models.Model):
    """Types de véhicules disponibles"""
    class VehicleTypeChoices(models.TextChoices):
        MOTO = 'moto', _('Moto')
        TAXI = 'taxi', _('Taxi')
        VAN = 'van', _('Van')
        VIP = 'vip', _('VIP')
    
    name = models.CharField(
        max_length=50,
        choices=VehicleTypeChoices.choices,
        default=VehicleTypeChoices.TAXI
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Prix de départ en FCFA")
    )
    price_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Prix par kilomètre en FCFA")
    )
    price_per_minute = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Prix par minute en FCFA")
    )
    capacity = models.IntegerField(
        default=1,
        help_text=_("Nombre de passagers maximum")
    )
    image = models.ImageField(
        upload_to='vehicle_types/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Type de véhicule")
        verbose_name_plural = _("Types de véhicules")
        ordering = ['base_price']
    
    def __str__(self):
        return self.get_name_display()

class Driver(models.Model):
    """Modèle pour les chauffeurs"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    license_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de permis")
    )
    license_expiry = models.DateField(
        verbose_name=_("Date d'expiration du permis")
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name='drivers'
    )
    vehicle_plate = models.CharField(
        max_length=20,
        verbose_name=_("Plaque d'immatriculation")
    )
    vehicle_model = models.CharField(
        max_length=100,
        verbose_name=_("Modèle du véhicule")
    )
    vehicle_color = models.CharField(
        max_length=50,
        verbose_name=_("Couleur du véhicule")
    )
    vehicle_year = models.IntegerField(
        verbose_name=_("Année du véhicule"),
        null=True,
        blank=True
    )
    
    # Statut
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Statistiques
    rating = models.FloatField(default=0.0)
    total_trips = models.IntegerField(default=0)
    total_earnings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Géolocalisation
    current_location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326
    )
    last_location_update = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Documents
    license_image = models.ImageField(
        upload_to='driver_licenses/',
        null=True,
        blank=True
    )
    vehicle_image = models.ImageField(
        upload_to='vehicle_images/',
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Chauffeur")
        verbose_name_plural = _("Chauffeurs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vehicle_plate}"
    
    def update_location(self, lat, lng):
        """Mettre à jour la position du chauffeur"""
        self.current_location = Point(lng, lat)
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_location', 'last_location_update'])
    
    def update_rating(self):
        """Mettre à jour la note moyenne"""
        ratings = self.ratings.all()
        if ratings:
            self.rating = sum(r.rating for r in ratings) / len(ratings)
            self.save(update_fields=['rating'])
    
    def get_earnings_today(self):
        """Récupérer les gains d'aujourd'hui"""
        from booking.models import Trip
        today = timezone.now().date()
        trips = Trip.objects.filter(
            driver=self,
            completed_at__date=today,
            status='completed'
        )
        return sum(trip.fare for trip in trips)

class Trip(models.Model):
    """Modèle pour les courses"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        ACCEPTED = 'accepted', _('Accepté')
        ARRIVED = 'arrived', _('Chauffeur arrivé')
        STARTED = 'started', _('Course commencée')
        COMPLETED = 'completed', _('Terminé')
        CANCELLED = 'cancelled', _('Annulé')
        NO_SHOW = 'no_show', _('Passager absent')
    
    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trips'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips'
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name='trips'
    )
    
    # Points de départ et d'arrivée
    pickup_address = models.CharField(
        max_length=255,
        verbose_name=_("Adresse de prise en charge")
    )
    pickup_location = gis_models.PointField(
        srid=4326,
        verbose_name=_("Position de prise en charge")
    )
    dropoff_address = models.CharField(
        max_length=255,
        verbose_name=_("Adresse de destination")
    )
    dropoff_location = gis_models.PointField(
        srid=4326,
        verbose_name=_("Position de destination")
    )
    
    # Détails de la course
    distance = models.FloatField(
        help_text=_("Distance en kilomètres"),
        default=0
    )
    duration = models.IntegerField(
        help_text=_("Durée estimée en minutes"),
        default=0
    )
    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Covoiturage
    is_shared = models.BooleanField(default=False)
    shared_passengers = models.ManyToManyField(
        User,
        blank=True,
        related_name='shared_trips'
    )
    sharing_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Pourcentage de réduction pour covoiturage")
    )
    
    # Suivi en temps réel
    current_location = gis_models.PointField(
        null=True,
        blank=True,
        srid=4326
    )
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    
    # Paiement
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('cash', _('Espèces')),
            ('mobile_money', _('Mobile Money')),
            ('card', _('Carte bancaire')),
            ('wallet', _('Portefeuille MoveNow')),
        ],
        default='mobile_money'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('paid', _('Payé')),
            ('failed', _('Échoué')),
            ('refunded', _('Remboursé')),
        ],
        default='pending'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['passenger', 'created_at']),
            models.Index(fields=['driver', 'created_at']),
        ]
    
    def __str__(self):
        return f"Course #{self.id} - {self.passenger.email}"
    
    def calculate_fare(self):
        """Calcul automatique du prix"""
        base_price = self.vehicle_type.base_price
        distance_price = self.vehicle_type.price_per_km * self.distance
        time_price = self.vehicle_type.price_per_minute * (self.duration / 60)
        
        total = base_price + distance_price + time_price
        
        # Réduction pour covoiturage
        if self.is_shared:
            discount = total * (self.sharing_discount / 100)
            total -= discount
        
        return round(total, 2)
    
    def save(self, *args, **kwargs):
        """Override save pour calcul automatique"""
        if not self.fare or self.fare == 0:
            self.fare = self.calculate_fare()
        
        # Mettre à jour les timestamps selon le statut
        now = timezone.now()
        if self.status == self.StatusChoices.ACCEPTED and not self.accepted_at:
            self.accepted_at = now
        elif self.status == self.StatusChoices.ARRIVED and not self.arrived_at:
            self.arrived_at = now
        elif self.status == self.StatusChoices.STARTED and not self.started_at:
            self.started_at = now
        elif self.status == self.StatusChoices.COMPLETED and not self.completed_at:
            self.completed_at = now
        elif self.status == self.StatusChoices.CANCELLED and not self.cancelled_at:
            self.cancelled_at = now
        
        super().save(*args, **kwargs)
    
    def get_duration_minutes(self):
        """Récupérer la durée en minutes"""
        if self.completed_at and self.started_at:
            duration = self.completed_at - self.started_at
            return int(duration.total_seconds() / 60)
        return self.duration
    
    def can_be_cancelled(self):
        """Vérifier si la course peut être annulée"""
        return self.status in [self.StatusChoices.PENDING, self.StatusChoices.ACCEPTED]

class Rating(models.Model):
    """Notation des chauffeurs"""
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_ratings'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_("Note (1-5)")
    )
    comment = models.TextField(blank=True)
    
    # Catégories de notation
    punctuality = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    cleanliness = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    driving = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    communication = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Évaluation")
        verbose_name_plural = _("Évaluations")
        ordering = ['-created_at']
        unique_together = ['trip', 'driver', 'passenger']
    
    def __str__(self):
        return f"{self.rating}/5 - {self.driver.user.get_full_name()}"

class Fleet(models.Model):
    """Gestion de flotte pour les propriétaires"""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fleets'
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la flotte")
    )
    description = models.TextField(blank=True)
    
    # Informations de contact
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    address = models.TextField()
    
    # Documents
    business_license = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Numéro d'identification fiscale")
    )
    
    # Configuration
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        help_text=_("Pourcentage de commission sur les courses")
    )
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Flotte")
        verbose_name_plural = _("Flottes")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_active_drivers(self):
        """Récupérer les chauffeurs actifs de la flotte"""
        return self.drivers.filter(is_active=True)
    
    def get_total_vehicles(self):
        """Récupérer le nombre total de véhicules"""
        return Vehicle.objects.filter(fleet=self).count()
    
    def get_monthly_earnings(self):
        """Récupérer les revenus du mois"""
        from django.db.models import Sum
        from booking.models import Trip
        
        today = timezone.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        trips = Trip.objects.filter(
            driver__in=self.drivers.all(),
            completed_at__gte=month_start,
            status='completed'
        )
        
        total_earnings = trips.aggregate(
            total=Sum('fare')
        )['total'] or 0
        
        commission = total_earnings * (self.commission_rate / 100)
        return {
            'total_earnings': total_earnings,
            'commission': commission,
            'driver_earnings': total_earnings - commission
        }

class Vehicle(models.Model):
    """Véhicule appartenant à une flotte"""
    class VehicleStatusChoices(models.TextChoices):
        ACTIVE = 'active', _('Actif')
        MAINTENANCE = 'maintenance', _('En maintenance')
        INACTIVE = 'inactive', _('Inactif')
        DAMAGED = 'damaged', _('Endommagé')
    
    fleet = models.ForeignKey(
        Fleet,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    driver = models.OneToOneField(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicle'
    )
    
    # Informations du véhicule
    plate_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Plaque d'immatriculation")
    )
    make = models.CharField(
        max_length=50,
        verbose_name=_("Marque")
    )
    model = models.CharField(
        max_length=50,
        verbose_name=_("Modèle")
    )
    year = models.IntegerField(verbose_name=_("Année"))
    color = models.CharField(
        max_length=30,
        verbose_name=_("Couleur")
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,
        related_name='fleet_vehicles'
    )
    
    # Documents
    registration_document = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Numéro de carte grise")
    )
    insurance_policy = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Numéro d'assurance")
    )
    insurance_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'expiration de l'assurance")
    )
    
    # Kilométrage et maintenance
    current_mileage = models.IntegerField(
        default=0,
        verbose_name=_("Kilométrage actuel")
    )
    last_maintenance = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Dernière maintenance")
    )
    next_maintenance = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Prochaine maintenance")
    )
    maintenance_interval = models.IntegerField(
        default=10000,
        help_text=_("Intervalle de maintenance en km")
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=VehicleStatusChoices.choices,
        default=VehicleStatusChoices.ACTIVE
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Véhicule")
        verbose_name_plural = _("Véhicules")
        ordering = ['plate_number']
    
    def __str__(self):
        return f"{self.plate_number} - {self.make} {self.model}"
    
    def needs_maintenance(self):
        """Vérifier si le véhicule a besoin de maintenance"""
        if not self.next_maintenance:
            return False
        
        today = timezone.now().date()
        km_until_maintenance = self.maintenance_interval - (
            self.current_mileage % self.maintenance_interval
        )
        
        return (
            self.next_maintenance <= today or
            km_until_maintenance <= 1000
        )
    
    def update_mileage(self, new_mileage):
        """Mettre à jour le kilométrage"""
        if new_mileage > self.current_mileage:
            self.current_mileage = new_mileage
            self.save(update_fields=['current_mileage'])

class Notification(models.Model):
    """Notifications système"""
    class NotificationTypeChoices(models.TextChoices):
        BOOKING = 'booking', _('Réservation')
        PAYMENT = 'payment', _('Paiement')
        TRIP = 'trip', _('Course')
        SYSTEM = 'system', _('Système')
        PROMOTION = 'promotion', _('Promotion')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationTypeChoices.choices
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    # Liens
    link = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True)
    
    # Statut
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def send_booking_notification(cls, user, trip, title, message):
        """Envoyer une notification de réservation"""
        return cls.objects.create(
            user=user,
            notification_type=cls.NotificationTypeChoices.BOOKING,
            title=title,
            message=message,
            data={
                'trip_id': trip.id,
                'status': trip.status
            },
            link=f"/booking/trip/{trip.id}/",
            link_text="Voir la course"
        )

class Promotion(models.Model):
    """Promotions et codes promo"""
    class PromotionTypeChoices(models.TextChoices):
        PERCENTAGE = 'percentage', _('Pourcentage')
        FIXED = 'fixed', _('Montant fixe')
        FREE_RIDE = 'free_ride', _('Course gratuite')
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Code promotionnel")
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Type et valeur
    promotion_type = models.CharField(
        max_length=20,
        choices=PromotionTypeChoices.choices
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Valeur de la réduction")
    )
    
    # Conditions
    min_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Montant minimum de la course")
    )
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Réduction maximum (pour les pourcentages)")
    )
    vehicle_types = models.ManyToManyField(
        VehicleType,
        blank=True,
        help_text=_("Types de véhicules éligibles")
    )
    
    # Limites
    usage_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Nombre maximum d'utilisations")
    )
    per_user_limit = models.IntegerField(
        default=1,
        help_text=_("Nombre maximum d'utilisations par utilisateur")
    )
    
    # Dates
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid(self):
        """Vérifier si la promotion est valide"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )
    
    def calculate_discount(self, amount):
        """Calculer la réduction"""
        if not self.is_valid():
            return 0
        
        if self.promotion_type == self.PromotionTypeChoices.PERCENTAGE:
            discount = amount * (self.value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
        elif self.promotion_type == self.PromotionTypeChoices.FIXED:
            discount = min(self.value, amount)
        else:  # FREE_RIDE
            discount = amount
        
        return discount
    
    @property
    def usage_count(self):
        """Compter le nombre d'utilisations"""
        from payment.models import Payment
        return Payment.objects.filter(promotion_code=self.code).count()