from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

class FleetManager(models.Model):
    """Gestionnaire de flotte"""
    fleet = models.ForeignKey(
        'core.Fleet',
        on_delete=models.CASCADE,
        related_name='managers'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='managed_fleets'
    )
    
    # Rôle
    role = models.CharField(
        max_length=20,
        choices=[
            ('manager', _('Gestionnaire')),
            ('supervisor', _('Superviseur')),
            ('accountant', _('Comptable')),
            ('maintenance', _('Responsable maintenance')),
        ],
        default='manager'
    )
    
    # Permissions
    can_manage_drivers = models.BooleanField(default=True)
    can_manage_vehicles = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=True)
    can_manage_finances = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Gestionnaire de flotte")
        verbose_name_plural = _("Gestionnaires de flotte")
        unique_together = ['fleet', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.fleet.name}"

class FleetDriver(models.Model):
    """Chauffeur affilié à une flotte"""
    fleet = models.ForeignKey(
        'core.Fleet',
        on_delete=models.CASCADE,
        related_name='fleet_drivers'
    )
    driver = models.OneToOneField(
        'core.Driver',
        on_delete=models.CASCADE,
        related_name='fleet_assignment'
    )
    
    # Informations contractuelles
    contract_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', _('Temps plein')),
            ('part_time', _('Temps partiel')),
            ('contractor', _('Contractuel')),
        ],
        default='contractor'
    )
    contract_start = models.DateField()
    contract_end = models.DateField(null=True, blank=True)
    
    # Commission
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70,
        help_text=_("Pourcentage que le chauffeur garde")
    )
    
    # Statut
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Chauffeur de flotte")
        verbose_name_plural = _("Chauffeurs de flotte")
        unique_together = ['fleet', 'driver']
    
    def __str__(self):
        return f"{self.driver.user.get_full_name()} - {self.fleet.name}"
    
    def calculate_earnings(self, start_date, end_date):
        """Calculer les gains du chauffeur sur une période"""
        from core.models import Trip
        from django.db.models import Sum
        
        trips = Trip.objects.filter(
            driver=self.driver,
            completed_at__range=[start_date, end_date],
            status='completed'
        )
        
        total_earnings = trips.aggregate(
            total=Sum('fare')
        )['total'] or 0
        
        driver_share = total_earnings * (self.commission_rate / 100)
        fleet_share = total_earnings - driver_share
        
        return {
            'total_earnings': total_earnings,
            'driver_share': driver_share,
            'fleet_share': fleet_share,
            'trip_count': trips.count(),
        }

class FleetVehicleAssignment(models.Model):
    """Affectation de véhicule à un chauffeur"""
    fleet = models.ForeignKey(
        'core.Fleet',
        on_delete=models.CASCADE,
        related_name='vehicle_assignments'
    )
    vehicle = models.ForeignKey(
        'core.Vehicle',
        on_delete=models.CASCADE,
        related_name='fleet_assignments'
    )
    driver = models.ForeignKey(
        FleetDriver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicle_assignments'
    )
    
    # Période
    assigned_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    
    # Kilométrage
    start_mileage = models.IntegerField()
    end_mileage = models.IntegerField(null=True, blank=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Affectation de véhicule")
        verbose_name_plural = _("Affectations de véhicule")
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.driver.driver.user.get_full_name()}"
    
    def return_vehicle(self, end_mileage):
        """Retourner le véhicule"""
        if self.is_active:
            self.is_active = False
            self.returned_at = timezone.now()
            self.end_mileage = end_mileage
            self.save()
            
            # Mettre à jour le kilométrage du véhicule
            self.vehicle.update_mileage(end_mileage)
            
            return True
        return False

class FleetMaintenance(models.Model):
    """Maintenance de véhicule de flotte"""
    class MaintenanceTypeChoices(models.TextChoices):
        ROUTINE = 'routine', _('Maintenance routinière')
        REPAIR = 'repair', _('Réparation')
        ACCIDENT = 'accident', _('Accident')
        OTHER = 'other', _('Autre')
    
    maintenance_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    fleet = models.ForeignKey(
        'core.Fleet',
        on_delete=models.CASCADE,
        related_name='maintenances'
    )
    vehicle = models.ForeignKey(
        'core.Vehicle',
        on_delete=models.CASCADE,
        related_name='maintenances'
    )
    
    # Informations de maintenance
    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceTypeChoices.choices
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Coût
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Période
    scheduled_date = models.DateField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Kilométrage
    mileage_at_maintenance = models.IntegerField()
    
    # Fournisseur
    service_provider = models.CharField(max_length=200, blank=True)
    provider_contact = models.CharField(max_length=100, blank=True)
    
    # Documents
    invoice_number = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(
        upload_to='maintenance_receipts/',
        null=True,
        blank=True
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', _('Planifiée')),
            ('in_progress', _('En cours')),
            ('completed', _('Terminée')),
            ('cancelled', _('Annulée')),
        ],
        default='scheduled'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Maintenance")
        verbose_name_plural = _("Maintenances")
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Maintenance #{self.maintenance_id} - {self.vehicle.plate_number}"
    
    def start_maintenance(self):
        """Démarrer la maintenance"""
        if self.status == 'scheduled':
            self.status = 'in_progress'
            self.start_date = timezone.now().date()
            self.save()
            
            # Mettre à jour le statut du véhicule
            self.vehicle.status = 'maintenance'
            self.vehicle.save()
            
            return True
        return False
    
    def complete_maintenance(self, actual_cost=None):
        """Terminer la maintenance"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.end_date = timezone.now().date()
            
            if actual_cost is not None:
                self.actual_cost = actual_cost
            
            self.save()
            
            # Mettre à jour le statut du véhicule
            self.vehicle.status = 'active'
            self.vehicle.last_maintenance = self.end_date
            self.vehicle.next_maintenance = self.end_date + timezone.timedelta(
                days=self.vehicle.maintenance_interval / 50  # Estimation
            )
            self.vehicle.save()
            
            return True
        return False

class FleetReport(models.Model):
    """Rapport de flotte"""
    class ReportTypeChoices(models.TextChoices):
        DAILY = 'daily', _('Quotidien')
        WEEKLY = 'weekly', _('Hebdomadaire')
        MONTHLY = 'monthly', _('Mensuel')
        QUARTERLY = 'quarterly', _('Trimestriel')
        YEARLY = 'yearly', _('Annuel')
        CUSTOM = 'custom', _('Personnalisé')
    
    report_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    fleet = models.ForeignKey(
        'core.Fleet',
        on_delete=models.CASCADE,
        related_name='reports'
    )
    
    # Informations du rapport
    report_type = models.CharField(
        max_length=20,
        choices=ReportTypeChoices.choices
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Période
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Données
    data = models.JSONField(default=dict)
    
    # Métadonnées
    generated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    is_archived = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rapport #{self.report_id} - {self.title}"
    
    def generate(self):
        """Générer les données du rapport"""
        from django.db.models import Count, Sum, Avg, Q
        from core.models import Trip
        from datetime import timedelta
        
        # Données de base
        data = {
            'fleet': {
                'name': self.fleet.name,
                'total_drivers': self.fleet.get_active_drivers().count(),
                'total_vehicles': self.fleet.get_total_vehicles(),
            },
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
                'duration': (self.end_date - self.start_date).days,
            }
        }
        
        # Trips dans la période
        trips = Trip.objects.filter(
            driver__in=self.fleet.drivers.all(),
            completed_at__date__range=[self.start_date, self.end_date],
            status='completed'
        )
        
        # Statistiques des courses
        trip_stats = trips.aggregate(
            total_trips=Count('id'),
            total_earnings=Sum('fare'),
            avg_fare=Avg('fare'),
            avg_distance=Avg('distance'),
            avg_duration=Avg('duration'),
        )
        
        data['trips'] = trip_stats
        
        # Courses par jour
        daily_trips = []
        current_date = self.start_date
        while current_date <= self.end_date:
            day_trips = trips.filter(completed_at__date=current_date)
            daily_trips.append({
                'date': current_date.isoformat(),
                'count': day_trips.count(),
                'earnings': day_trips.aggregate(total=Sum('fare'))['total'] or 0,
            })
            current_date += timedelta(days=1)
        
        data['daily_trips'] = daily_trips
        
        # Performances des chauffeurs
        drivers_data = []
        for fleet_driver in self.fleet.fleet_drivers.filter(is_active=True):
            driver_trips = trips.filter(driver=fleet_driver.driver)
            driver_stats = driver_trips.aggregate(
                trip_count=Count('id'),
                total_earnings=Sum('fare'),
                avg_rating=Avg('rating__rating'),
            )
            
            drivers_data.append({
                'driver': {
                    'id': fleet_driver.driver.id,
                    'name': fleet_driver.driver.user.get_full_name(),
                    'vehicle': fleet_driver.driver.vehicle_plate,
                },
                'stats': driver_stats,
            })
        
        data['drivers'] = drivers_data
        
        # Véhicules
        vehicles_data = []
        for vehicle in self.fleet.vehicles.all():
            vehicle_trips = trips.filter(driver__assigned_vehicle=vehicle)
            
            vehicles_data.append({
                'vehicle': {
                    'plate': vehicle.plate_number,
                    'model': f"{vehicle.make} {vehicle.model}",
                    'status': vehicle.status,
                },
                'stats': {
                    'trip_count': vehicle_trips.count(),
                    'mileage': vehicle.current_mileage,
                    'needs_maintenance': vehicle.needs_maintenance(),
                }
            })
        
        data['vehicles'] = vehicles_data
        
        # Sauvegarder les données
        self.data = data
        self.save()
        
        return data