from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User
from core.models import Driver, Fleet

class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription utilisateur"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.com'
        })
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '6XXXXXXXX'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Prénom'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nom'
        })
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mot de passe'
        })
    )
    password2 = forms.CharField(
        label=_("Confirmation du mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirmez le mot de passe'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone

class UserLoginForm(AuthenticationForm):
    """Formulaire de connexion"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Mot de passe'
        })
    )
    
    class Meta:
        fields = ('email', 'password')

class UserProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'birth_date', 'gender', 
                 'address', 'city', 'country', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'birth_date': forms.DateInput(
                attrs={'class': 'form-input', 'type': 'date'}
            ),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-input'}),
        }

class DriverRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription chauffeur"""
    license_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-input'})
    )
    vehicle_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-input'})
    )
    
    class Meta:
        model = Driver
        fields = ('license_number', 'license_expiry', 'vehicle_type', 
                 'vehicle_plate', 'vehicle_model', 'vehicle_color', 
                 'vehicle_year', 'license_image', 'vehicle_image')
        widgets = {
            'license_number': forms.TextInput(attrs={'class': 'form-input'}),
            'license_expiry': forms.DateInput(
                attrs={'class': 'form-input', 'type': 'date'}
            ),
            'vehicle_type': forms.Select(attrs={'class': 'form-input'}),
            'vehicle_plate': forms.TextInput(attrs={'class': 'form-input'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-input'}),
            'vehicle_color': forms.TextInput(attrs={'class': 'form-input'}),
            'vehicle_year': forms.NumberInput(attrs={'class': 'form-input'}),
        }
    
    def clean_license_expiry(self):
        expiry = self.cleaned_data.get('license_expiry')
        from datetime import date
        if expiry and expiry < date.today():
            raise forms.ValidationError("Le permis est expiré.")
        return expiry

class FleetOwnerRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription propriétaire de flotte"""
    class Meta:
        model = Fleet
        fields = ('name', 'description', 'contact_phone', 'contact_email',
                 'address', 'business_license', 'tax_id')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'business_license': forms.TextInput(attrs={'class': 'form-input'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-input'}),
        }