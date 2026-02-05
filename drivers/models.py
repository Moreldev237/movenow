from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Driver


class DriverDocument(models.Model):
    """Documents du chauffeur"""
    class DocumentType(models.TextChoices):
        LICENSE = 'license', _('Permis de conduire')
        ID_CARD = 'id_card', _('Carte d\'identité')
        INSURANCE = 'insurance', _('Assurance')
        VEHICLE_REGISTRATION = 'vehicle_registration', _('Carte grise')
        POLICE_CLEARANCE = 'police_clearance', _('Casier judiciaire')
        OTHER = 'other', _('Autre')
    
    class DocumentStatus(models.TextChoices):
        PENDING = 'pending', _('En attente')
        VERIFIED = 'verified', _('Vérifié')
        REJECTED = 'rejected', _('Rejeté')
    
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices
    )
    file = models.FileField(
        upload_to='driver_documents/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING
    )
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Document du chauffeur")
        verbose_name_plural = _("Documents des chauffeurs")
    
    def __str__(self):
        return f"{self.driver.user.get_full_name()} - {self.document_type}"


class DriverVehicle(models.Model):
    """Véhicule du chauffeur"""
    driver = models.OneToOneField(
        Driver,
        on_delete=models.CASCADE,
        related_name='vehicle'
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
    plate_number = models.CharField(
        max_length=20,
        verbose_name=_("Plaque d'immatriculation")
    )
    
    # Statut du véhicule
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Véhicule du chauffeur")
        verbose_name_plural = _("Véhicules des chauffeurs")
    
    def __str__(self):
        return f"{self.make} {self.model} - {self.plate_number}"

