from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Booking


class BookingForm(forms.ModelForm):
    """Formulaire de réservation de course"""
    
    class Meta:
        model = Booking
        fields = (
            'vehicle_type',
            'pickup_address',
            'pickup_lat',
            'pickup_lng',
            'dropoff_address',
            'dropoff_lat',
            'dropoff_lng',
            'is_shared',
            'notes',
            'special_requests',
        )
        widgets = {
            'vehicle_type': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none'
            }),
            'pickup_address': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
                'placeholder': 'Adresse de départ'
            }),
            'pickup_lat': forms.HiddenInput(),
            'pickup_lng': forms.HiddenInput(),
            'dropoff_address': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
                'placeholder': 'Adresse de destination'
            }),
            'dropoff_lat': forms.HiddenInput(),
            'dropoff_lng': forms.HiddenInput(),
            'is_shared': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-orange-500 border-gray-300 rounded'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
                'rows': 3,
                'placeholder': 'Instructions supplémentaires pour le chauffeur (optionnel)'
            }),
            'special_requests': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
        }
        labels = {
            'vehicle_type': _('Type de véhicule'),
            'pickup_address': _('Point de départ'),
            'dropoff_address': _('Destination'),
            'is_shared': _('Covoiturage (-30%)'),
            'notes': _('Notes pour le chauffeur'),
            'special_requests': _('Demandes spéciales'),
        }
        help_texts = {
            'is_shared': _('Partagez votre course et économisez 30%'),
            'special_requests': _(
                'Options disponibles: '
                'Animaux acceptés, '
                'Vélo/Scooter pliable, '
                'Siège enfant, '
                'Besoin d\'un fauteuil roulant'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-input'
        
        # Make special_requests optional
        self.fields['special_requests'].required = False
        self.fields['notes'].required = False

