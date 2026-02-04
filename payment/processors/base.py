from abc import ABC, abstractmethod
from django.utils.translation import gettext_lazy as _

class PaymentProcessor(ABC):
    """Classe abstraite pour les processeurs de paiement"""
    
    @abstractmethod
    def process_transaction(self, transaction):
        """Traiter une transaction"""
        pass
    
    @abstractmethod
    def verify_transaction(self, reference):
        """Vérifier une transaction"""
        pass
    
    @abstractmethod
    def refund_transaction(self, transaction, amount=None):
        """Rembourser une transaction"""
        pass

class FlutterwaveProcessor(PaymentProcessor):
    """Processeur Flutterwave pour cartes bancaires"""
    
    def __init__(self):
        import requests
        self.requests = requests
        self.base_url = "https://api.flutterwave.com/v3"
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
    
    def process_transaction(self, transaction):
        """Traiter une transaction Flutterwave"""
        try:
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'tx_ref': str(transaction.reference),
                'amount': str(transaction.amount),
                'currency': transaction.currency,
                'redirect_url': f"{settings.SITE_URL}/payment/callback/",
                'customer': {
                    'email': transaction.user.email,
                    'phone_number': transaction.user.phone,
                    'name': transaction.user.get_full_name(),
                },
                'customizations': {
                    'title': 'MoveNow Payment',
                    'description': f'Payment for {transaction.description}',
                }
            }
            
            response = self.requests.post(
                f"{self.base_url}/payments",
                headers=headers,
                json=payload
            )
            
            data = response.json()
            
            if data['status'] == 'success':
                return {
                    'success': True,
                    'message': _('Transaction initiée'),
                    'payment_url': data['data']['link'],
                    'reference': data['data']['tx_ref'],
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', _('Échec de la transaction')),
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }
    
    def verify_transaction(self, reference):
        """Vérifier une transaction Flutterwave"""
        try:
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
            }
            
            response = self.requests.get(
                f"{self.base_url}/transactions/{reference}/verify",
                headers=headers
            )
            
            data = response.json()
            
            if data['status'] == 'success':
                return {
                    'success': True,
                    'verified': True,
                    'amount': data['data']['amount'],
                    'currency': data['data']['currency'],
                    'status': data['data']['status'],
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'message': data.get('message', _('Échec de la vérification')),
                }
        
        except Exception as e:
            return {
                'success': False,
                'verified': False,
                'message': str(e),
            }
    
    def refund_transaction(self, transaction, amount=None):
        """Rembourser une transaction Flutterwave"""
        try:
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'amount': str(amount or transaction.amount),
            }
            
            response = self.requests.post(
                f"{self.base_url}/transactions/{transaction.external_reference}/refund",
                headers=headers,
                json=payload
            )
            
            data = response.json()
            
            if data['status'] == 'success':
                return {
                    'success': True,
                    'message': _('Remboursement effectué'),
                    'reference': data['data']['id'],
                }
            else:
                return {
                    'success': False,
                    'message': data.get('message', _('Échec du remboursement')),
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

class MobileMoneyProcessor(PaymentProcessor):
    """Processeur Mobile Money (MTN & Orange)"""
    
    def __init__(self, provider):
        import requests
        self.requests = requests
        self.provider = provider
        
        if provider == 'mtn':
            self.api_key = settings.MTN_MOMO_API_KEY
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        elif provider == 'orange':
            self.api_key = settings.ORANGE_MONEY_API_KEY
            self.base_url = "https://api.orange.com"
    
    def process_transaction(self, transaction):
        """Traiter une transaction Mobile Money"""
        try:
            phone = transaction.metadata.get('phone')
            if not phone:
                return {
                    'success': False,
                    'message': _('Numéro de téléphone requis'),
                }
            
            if self.provider == 'mtn':
                return self._process_mtn(transaction, phone)
            elif self.provider == 'orange':
                return self._process_orange(transaction, phone)
            
            return {
                'success': False,
                'message': _('Fournisseur non supporté'),
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }
    
    def _process_mtn(self, transaction, phone):
        """Traiter une transaction MTN Mobile Money"""
        # Implémentation de l'API MTN MoMo
        # Note: Cette implémentation nécessite une configuration appropriée
        headers = {
            'X-Reference-Id': str(transaction.reference),
            'X-Target-Environment': 'sandbox',
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.api_key,
        }
        
        payload = {
            'amount': str(transaction.amount),
            'currency': transaction.currency,
            'externalId': str(transaction.id),
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone,
            },
            'payerMessage': transaction.description,
            'payeeNote': f'Payment for {transaction.description}',
        }
        
        # Créer une demande de paiement
        response = self.requests.post(
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 202:
            return {
                'success': True,
                'message': _('Demande de paiement envoyée'),
                'reference': str(transaction.reference),
            }
        else:
            return {
                'success': False,
                'message': response.text,
            }
    
    def _process_orange(self, transaction, phone):
        """Traiter une transaction Orange Money"""
        # Implémentation de l'API Orange Money
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'merchant_key': settings.ORANGE_MERCHANT_KEY,
            'currency': transaction.currency,
            'order_id': str(transaction.reference),
            'amount': str(transaction.amount),
            'return_url': f"{settings.SITE_URL}/payment/callback/",
            'cancel_url': f"{settings.SITE_URL}/payment/cancelled/",
            'notif_url': f"{settings.SITE_URL}/payment/webhook/orange/",
            'lang': 'fr',
            'reference': str(transaction.id),
        }
        
        response = self.requests.post(
            f"{self.base_url}/orange-money-webpay/cm/v1/webpayment",
            headers=headers,
            json=payload
        )
        
        data = response.json()
        
        if data['status'] == 'SUCCESS':
            return {
                'success': True,
                'message': _('Transaction initiée'),
                'payment_url': data['payment_url'],
                'reference': str(transaction.reference),
            }
        else:
            return {
                'success': False,
                'message': data.get('message', _('Échec de la transaction')),
            }
    
    def verify_transaction(self, reference):
        """Vérifier une transaction Mobile Money"""
        # Implémentation spécifique au fournisseur
        pass
    
    def refund_transaction(self, transaction, amount=None):
        """Rembourser une transaction Mobile Money"""
        # Implémentation spécifique au fournisseur
        pass

def get_processor(payment_method):
    """Obtenir le processeur approprié pour la méthode de paiement"""
    if payment_method == 'card':
        return FlutterwaveProcessor()
    elif payment_method == 'mtn_momo':
        return MobileMoneyProcessor('mtn')
    elif payment_method == 'orange_money':
        return MobileMoneyProcessor('orange')
    else:
        raise ValueError(f"Processeur non supporté pour {payment_method}")