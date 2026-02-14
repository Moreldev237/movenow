from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    """Formulaire de contact"""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
            'placeholder': _('Votre prénom')
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
            'placeholder': _('Votre nom')
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
            'placeholder': _('Votre adresse email')
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
            'placeholder': _('Votre numéro de téléphone')
        })
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none',
            'rows': 5,
            'placeholder': _('Votre message...')
        })
    )

