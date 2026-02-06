from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json

from .models import Payment, PaymentMethod, Refund
from core.models import Trip
from accounts.decorators import passenger_required

@login_required
@passenger_required
def process_payment(request):
    """Traiter un paiement (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        trip_id = data.get('trip_id')
        payment_method_id = data.get('payment_method_id')
        amount = data.get('amount')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    try:
        trip = Trip.objects.get(id=trip_id, passenger=request.user)
        payment_method = PaymentMethod.objects.get(id=payment_method_id, user=request.user)
    except (Trip.DoesNotExist, PaymentMethod.DoesNotExist):
        return JsonResponse({'error': 'Trip ou méthode de paiement invalide'}, status=400)

    # Créer le paiement
    payment = Payment.objects.create(
        trip=trip,
        user=request.user,
        payment_method=payment_method,
        amount=amount,
        status='processing'
    )

    # TODO: Intégrer avec le processeur de paiement
    # Pour l'instant, marquer comme réussi
    payment.status = 'completed'
    payment.save()

    trip.payment_status = 'paid'
    trip.save()

    return JsonResponse({
        'payment_id': payment.id,
        'status': payment.status,
        'amount': str(payment.amount)
    })

@csrf_exempt
def payment_webhook(request):
    """Webhook pour les notifications de paiement"""
    # TODO: Implémenter la logique du webhook
    return JsonResponse({'status': 'ok'})

@login_required
def payment_history(request):
    """Historique des paiements (API)"""
    payments = Payment.objects.filter(user=request.user).select_related('trip', 'payment_method').order_by('-created_at')

    data = []
    for payment in payments:
        data.append({
            'id': payment.id,
            'trip_id': payment.trip.id if payment.trip else None,
            'amount': str(payment.amount),
            'status': payment.status,
            'payment_method': payment.payment_method.type if payment.payment_method else None,
            'created_at': payment.created_at.isoformat(),
        })

    return JsonResponse({'payments': data})

@login_required
def payment_detail(request, payment_id):
    """Détails d'un paiement (API)"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    data = {
        'id': payment.id,
        'trip_id': payment.trip.id if payment.trip else None,
        'amount': str(payment.amount),
        'status': payment.status,
        'payment_method': {
            'id': payment.payment_method.id,
            'type': payment.payment_method.type,
            'last4': payment.payment_method.last4,
        } if payment.payment_method else None,
        'created_at': payment.created_at.isoformat(),
        'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
    }

    return JsonResponse(data)

@login_required
def refund_payment(request, payment_id):
    """Rembourser un paiement (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.status != 'completed':
        return JsonResponse({'error': 'Paiement non remboursable'}, status=400)

    # Créer le remboursement
    refund = Refund.objects.create(
        payment=payment,
        amount=payment.amount,
        reason=request.POST.get('reason', ''),
        status='processing'
    )

    # TODO: Traiter le remboursement avec le processeur
    refund.status = 'completed'
    refund.save()

    payment.status = 'refunded'
    payment.save()

    return JsonResponse({
        'refund_id': refund.id,
        'status': refund.status,
        'amount': str(refund.amount)
    })

@login_required
def refund_status(request, refund_id):
    """Statut d'un remboursement (API)"""
    refund = get_object_or_404(Refund, id=refund_id, payment__user=request.user)

    return JsonResponse({
        'id': refund.id,
        'status': refund.status,
        'amount': str(refund.amount),
        'processed_at': refund.processed_at.isoformat() if refund.processed_at else None,
    })

@login_required
def list_payment_methods(request):
    """Lister les méthodes de paiement (API)"""
    methods = PaymentMethod.objects.filter(user=request.user, is_active=True)

    data = []
    for method in methods:
        data.append({
            'id': method.id,
            'type': method.type,
            'last4': method.last4,
            'is_default': method.is_default,
            'expires_at': method.expires_at.isoformat() if method.expires_at else None,
        })

    return JsonResponse({'methods': data})

@login_required
def add_payment_method(request):
    """Ajouter une méthode de paiement (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        type_ = data.get('type')
        token = data.get('token')  # Token du processeur de paiement
        last4 = data.get('last4')
        expires_at = data.get('expires_at')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    # TODO: Valider avec le processeur de paiement

    method = PaymentMethod.objects.create(
        user=request.user,
        type=type_,
        last4=last4,
        expires_at=expires_at,
        is_active=True
    )

    # Si c'est la première méthode, la définir par défaut
    if not PaymentMethod.objects.filter(user=request.user, is_default=True).exists():
        method.is_default = True
        method.save()

    return JsonResponse({
        'id': method.id,
        'type': method.type,
        'last4': method.last4,
        'is_default': method.is_default
    })

@login_required
def delete_payment_method(request, method_id):
    """Supprimer une méthode de paiement (API)"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    if method.is_default:
        return JsonResponse({'error': 'Impossible de supprimer la méthode par défaut'}, status=400)

    method.is_active = False
    method.save()

    return JsonResponse({'status': 'deleted'})

@login_required
def set_default_payment_method(request, method_id):
    """Définir une méthode de paiement par défaut (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    method = get_object_or_404(PaymentMethod, id=method_id, user=request.user, is_active=True)

    # Réinitialiser les autres méthodes
    PaymentMethod.objects.filter(user=request.user).update(is_default=False)

    method.is_default = True
    method.save()

    return JsonResponse({'status': 'set as default'})

@login_required
def get_payment_status(request, payment_id):
    """Obtenir le statut d'un paiement (API)"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    return JsonResponse({
        'id': payment.id,
        'status': payment.status,
        'amount': str(payment.amount),
        'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
    })


# ============ WEB VIEWS ============

@login_required
@passenger_required
def payment_page(request, trip_id):
    """Page de paiement pour une course"""
    trip = get_object_or_404(
        Trip,
        id=trip_id,
        passenger=request.user
    )
    
    # Vérifier si le paiement est déjà effectué
    if trip.payment_status == 'paid':
        messages.info(request, 'Cette course a déjà été payée.')
        return redirect('booking:trip_detail', trip_id=trip.id)
    
    # Récupérer les méthodes de paiement de l'utilisateur
    payment_methods = PaymentMethod.objects.filter(
        user=request.user,
        is_active=True
    )
    
    context = {
        'trip': trip,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'payment/payment.html', context)
