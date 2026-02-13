from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
import uuid

class Booking(models.Model):
    """Réservation de course"""
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    passenger = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    vehicle_type = models.ForeignKey(
        'core.VehicleType',
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    
    # Adresses
    pickup_address = models.CharField(max_length=255)
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    dropoff_address = models.CharField(max_length=255)
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    
    # Détails
    distance = models.FloatField(default=0)  # en km
    duration = models.IntegerField(default=0)  # en minutes
    estimated_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Covoiturage
    is_shared = models.BooleanField(default=False)
    sharing_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        help_text=_("Pourcentage de réduction")
    )
    
    # Préférences
    notes = models.TextField(blank=True)
    special_requests = models.JSONField(default=list, blank=True)
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('searching', _('Recherche de chauffeur')),
            ('accepted', _('Accepté')),
            ('arrived', _('Chauffeur arrivé')),
            ('started', _('Commencé')),
            ('completed', _('Terminé')),
            ('cancelled', _('Annulé')),
            ('expired', _('Expiré')),
        ],
        default='pending'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = _("Réservation")
        verbose_name_plural = _("Réservations")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_id']),
            models.Index(fields=['status']),
            models.Index(fields=['passenger', 'created_at']),
        ]
    
    def __str__(self):
        return f"Réservation #{self.booking_id}"
    
    def save(self, *args, **kwargs):
        """Définir la date d'expiration à la création"""
        if not self.pk:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Ensure special_requests is never None
        if self.special_requests is None:
            self.special_requests = []
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Vérifier si la réservation a expiré"""
        return timezone.now() > self.expires_at
    
    def convert_to_trip(self, driver):
        """Convertir la réservation en course"""
        from core.models import Trip
        
        trip = Trip.objects.create(
            passenger=self.passenger,
            driver=driver,
            vehicle_type=self.vehicle_type,
            pickup_address=self.pickup_address,
            pickup_location=Point(self.pickup_lng, self.pickup_lat),
            dropoff_address=self.dropoff_address,
            dropoff_location=Point(self.dropoff_lng, self.dropoff_lat),
            distance=self.distance,
            duration=self.duration,
            fare=self.estimated_fare,
            is_shared=self.is_shared,
            sharing_discount=self.sharing_discount,
            status='accepted'
        )
        
        # Marquer la réservation comme acceptée
        self.status = 'accepted'
        self.save()
        
        return trip

class BookingRequest(models.Model):
    """Demande de réservation envoyée aux chauffeurs"""
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    driver = models.ForeignKey(
        'core.Driver',
        on_delete=models.CASCADE,
        related_name='booking_requests'
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', _('Envoyé')),
            ('accepted', _('Accepté')),
            ('rejected', _('Rejeté')),
            ('expired', _('Expiré')),
        ],
        default='sent'
    )
    
    # Métadonnées
    sent_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = _("Demande de réservation")
        verbose_name_plural = _("Demandes de réservation")
        ordering = ['-sent_at']
        unique_together = ['booking', 'driver']
    
    def __str__(self):
        return f"Demande #{self.id} - {self.booking.booking_id}"
    
    def accept(self):
        """Accepter la demande"""
        if self.status == 'sent':
            self.status = 'accepted'
            self.responded_at = timezone.now()
            self.save()
            
            # Convertir la réservation en course
            self.booking.convert_to_trip(self.driver)
            
            # Annuler les autres demandes
            BookingRequest.objects.filter(
                booking=self.booking,
                status='sent'
            ).update(status='expired')
            
            return True
        return False
    
    def reject(self):
        """Rejeter la demande"""
        if self.status == 'sent':
            self.status = 'rejected'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False

class TripTracking(models.Model):
    """Suivi de course en temps réel"""
    trip = models.OneToOneField(
        'core.Trip',
        on_delete=models.CASCADE,
        related_name='tracking'
    )
    
    # Positions
    driver_positions = models.JSONField(
        default=list,
        help_text=_("Historique des positions du chauffeur")
    )
    estimated_positions = models.JSONField(
        default=list,
        help_text=_("Positions estimées selon l'itinéraire")
    )
    
    # Temps
    estimated_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    # Métriques
    average_speed = models.FloatField(default=0)  # km/h
    max_speed = models.FloatField(default=0)  # km/h
    distance_traveled = models.FloatField(default=0)  # km
    
    # Alertes
    alerts = models.JSONField(
        default=list,
        help_text=_("Alertes pendant le trajet")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Suivi de course")
        verbose_name_plural = _("Suivis de course")
    
    def __str__(self):
        return f"Suivi de la course #{self.trip.id}"
    
    def add_position(self, lat, lng, timestamp=None):
        """Ajouter une position"""
        if timestamp is None:
            timestamp = timezone.now().isoformat()
        
        position = {
            'lat': lat,
            'lng': lng,
            'timestamp': timestamp,
            'speed': 0,  # Calculé plus tard
        }
        
        self.driver_positions.append(position)
        self.save(update_fields=['driver_positions'])
        
        # Mettre à jour la distance parcourue
        self.update_distance_traveled()
    
    def update_distance_traveled(self):
        """Mettre à jour la distance parcourue"""
        if len(self.driver_positions) < 2:
            return
        
        from django.contrib.gis.geos import Point
        total_distance = 0
        
        for i in range(1, len(self.driver_positions)):
            pos1 = self.driver_positions[i-1]
            pos2 = self.driver_positions[i]
            
            point1 = Point(pos1['lng'], pos1['lat'])
            point2 = Point(pos2['lng'], pos2['lat'])
            
            # Calculer la distance en km
            distance = point1.distance(point2) * 100
            total_distance += distance
        
        self.distance_traveled = total_distance
        self.save(update_fields=['distance_traveled'])

class RouteOptimization(models.Model):
    """Optimisation d'itinéraire pour covoiturage"""
    trip = models.ForeignKey(
        'core.Trip',
        on_delete=models.CASCADE,
        related_name='route_optimizations'
    )
    
    # Itinéraire optimisé
    optimized_route = models.JSONField(
        help_text=_("Itinéraire optimisé avec waypoints")
    )
    original_distance = models.FloatField()
    optimized_distance = models.FloatField()
    distance_saved = models.FloatField()
    
    # Passagers supplémentaires
    additional_passengers = models.ManyToManyField(
        'accounts.User',
        related_name='optimized_routes',
        blank=True
    )
    
    # Calculs
    fuel_saved = models.FloatField(default=0)  # en litres
    co2_saved = models.FloatField(default=0)  # en kg
    time_added = models.IntegerField(default=0)  # en minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Optimisation d'itinéraire")
        verbose_name_plural = _("Optimisations d'itinéraire")
    
    def __str__(self):
        return f"Optimisation pour la course #{self.trip.id}"
    
    def calculate_savings(self):
        """Calculer les économies"""
        # Économie de distance
        self.distance_saved = self.original_distance - self.optimized_distance
        
        # Économie de carburant (7L/100km en moyenne)
        self.fuel_saved = self.distance_saved * 7 / 100
        
        # Réduction CO2 (2.3kg CO2/L d'essence)
        self.co2_saved = self.fuel_saved * 2.3
        
        self.save()
        
        return {
            'distance_saved': self.distance_saved,
            'fuel_saved': self.fuel_saved,
            'co2_saved': self.co2_saved,
            'time_added': self.time_added,
        }