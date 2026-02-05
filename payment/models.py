from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

class Transaction(models.Model):
    """Transaction de paiement"""
    class TransactionTypeChoices(models.TextChoices):
        DEPOSIT = 'deposit', _('Dépôt')
        WITHDRAWAL = 'withdrawal', _('Retrait')
        PAYMENT = 'payment', _('Paiement')
        REFUND = 'refund', _('Remboursement')
        COMMISSION = 'commission', _('Commission')
    
    class PaymentMethodChoices(models.TextChoices):
        CASH = 'cash', _('Espèces')
        MTN_MOMO = 'mtn_momo', _('MTN Mobile Money')
        ORANGE_MONEY = 'orange_money', _('Orange Money')
        CARD = 'card', _('Carte bancaire')
        WALLET = 'wallet', _('Portefeuille MoveNow')
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        PROCESSING = 'processing', _('En traitement')
        COMPLETED = 'completed', _('Terminé')
        FAILED = 'failed', _('Échoué')
        CANCELLED = 'cancelled', _('Annulé')
        REFUNDED = 'refunded', _('Remboursé')
    
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Informations de transaction
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionTypeChoices.choices
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodChoices.choices
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
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
    
    # Références
    reference = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )
    external_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Liens
    trip = models.ForeignKey(
        'core.Trip',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    promotion_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    
    # Détails
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Frais
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    status_message = models.TextField(blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """Calculer le montant net"""
        if not self.net_amount:
            self.net_amount = self.amount - self.fee - self.tax
        super().save(*args, **kwargs)
    
    def process(self):
        """Traiter la transaction"""
        from .processors import get_processor
        
        try:
            processor = get_processor(self.payment_method)
            result = processor.process_transaction(self)
            
            if result['success']:
                self.status = self.StatusChoices.COMPLETED
                self.processed_at = timezone.now()
                self.status_message = result.get('message', '')
                
                # Mettre à jour le portefeuille si nécessaire
                if self.transaction_type == self.TransactionTypeChoices.DEPOSIT:
                    self.user.wallet.deposit(self.net_amount, self.reference)
                elif self.transaction_type == self.TransactionTypeChoices.WITHDRAWAL:
                    self.user.wallet.withdraw(self.amount, self.reference)
                elif self.transaction_type == self.TransactionTypeChoices.PAYMENT:
                    self.user.wallet.make_payment(self.amount, self.trip, self.reference)
                
            else:
                self.status = self.StatusChoices.FAILED
                self.status_message = result.get('message', 'Échec du traitement')
            
            self.save()
            return result
        
        except Exception as e:
            self.status = self.StatusChoices.FAILED
            self.status_message = str(e)
            self.save()
            return {'success': False, 'message': str(e)}

class PaymentMethod(models.Model):
    """Méthodes de paiement enregistrées"""
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )

    # Type de paiement
    type = models.CharField(
        max_length=20,
        choices=[
            ('mobile_money', _('Mobile Money')),
            ('card', _('Carte bancaire')),
            ('bank_account', _('Compte bancaire')),
        ]
    )
    
    # Informations selon le type
    # Mobile Money
    provider = models.CharField(
        max_length=20,
        choices=[
            ('mtn', 'MTN Mobile Money'),
            ('orange', 'Orange Money'),
        ],
        blank=True,
        null=True
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    # Carte bancaire
    card_last_four = models.CharField(
        max_length=4,
        blank=True,
        null=True
    )
    card_brand = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    card_expiry_month = models.IntegerField(
        null=True,
        blank=True
    )
    card_expiry_year = models.IntegerField(
        null=True,
        blank=True
    )
    
    # Compte bancaire
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    account_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Métadonnées
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Méthode de paiement")
        verbose_name_plural = _("Méthodes de paiement")
        ordering = ['-is_default', '-created_at']
        unique_together = ['user', 'phone_number', 'provider']
    
    def __str__(self):
        if self.method_type == 'mobile_money':
            return f"{self.get_provider_display()} - {self.phone_number}"
        elif self.method_type == 'card':
            return f"Carte •••• {self.card_last_four}"
        else:
            return f"Compte bancaire - {self.bank_name}"
    
    def mask_card_number(self):
        """Masquer le numéro de carte"""
        if self.card_last_four:
            return f"•••• •••• •••• {self.card_last_four}"
        return "•••• •••• •••• ••••"
    
    def verify(self):
        """Vérifier la méthode de paiement"""
        # TODO: Implémenter la vérification selon le type
        self.is_verified = True
        self.save()

class WithdrawalRequest(models.Model):
    """Demande de retrait pour les chauffeurs"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        PROCESSING = 'processing', _('En traitement')
        COMPLETED = 'completed', _('Terminé')
        REJECTED = 'rejected', _('Rejeté')
        CANCELLED = 'cancelled', _('Annulé')
    
    request_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    driver = models.ForeignKey(
        'core.Driver',
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    
    # Informations de retrait
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='withdrawals'
    )
    
    # Frais
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    status_message = models.TextField(blank=True)
    
    # Approbation
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_withdrawals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Transactions
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdrawal_request'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Demande de retrait")
        verbose_name_plural = _("Demandes de retrait")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['status']),
            models.Index(fields=['driver', 'created_at']),
        ]
    
    def __str__(self):
        return f"Retrait #{self.request_id} - {self.amount} XAF"
    
    def save(self, *args, **kwargs):
        """Calculer le montant net"""
        if not self.net_amount:
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)
    
    def approve(self, user):
        """Approuver la demande de retrait"""
        if self.status == self.StatusChoices.PENDING:
            self.status = self.StatusChoices.PROCESSING
            self.approved_by = user
            self.approved_at = timezone.now()
            self.save()
            
            # Créer la transaction de retrait
            transaction = Transaction.objects.create(
                user=self.driver.user,
                transaction_type=Transaction.TransactionTypeChoices.WITHDRAWAL,
                payment_method=self.payment_method.method_type,
                amount=self.amount,
                fee=self.fee,
                net_amount=self.net_amount,
                description=f"Retrait vers {self.payment_method}",
                status=Transaction.StatusChoices.PROCESSING
            )
            
            self.transaction = transaction
            self.save()
            
            # Traiter le retrait
            result = transaction.process()
            
            if result['success']:
                self.status = self.StatusChoices.COMPLETED
                self.status_message = "Retrait effectué avec succès"
            else:
                self.status = self.StatusChoices.REJECTED
                self.status_message = result.get('message', 'Échec du retrait')
            
            self.save()
            return result
        
        return {'success': False, 'message': 'Demande déjà traitée'}
    
    def reject(self, reason):
        """Rejeter la demande de retrait"""
        if self.status == self.StatusChoices.PENDING:
            self.status = self.StatusChoices.REJECTED
            self.status_message = reason
            self.save()
            return True
        return False

class Payment(models.Model):
    """Paiement pour un trajet"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        PROCESSING = 'processing', _('En traitement')
        COMPLETED = 'completed', _('Terminé')
        FAILED = 'failed', _('Échoué')
        CANCELLED = 'cancelled', _('Annulé')
        REFUNDED = 'refunded', _('Remboursé')

    trip = models.ForeignKey(
        'core.Trip',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement {self.id} - {self.amount} XAF"

class Refund(models.Model):
    """Remboursement d'un paiement"""
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('En attente')
        PROCESSING = 'processing', _('En traitement')
        COMPLETED = 'completed', _('Terminé')
        FAILED = 'failed', _('Échoué')
        CANCELLED = 'cancelled', _('Annulé')

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Remboursement")
        verbose_name_plural = _("Remboursements")
        ordering = ['-created_at']

    def __str__(self):
        return f"Remboursement {self.id} - {self.amount} XAF"
