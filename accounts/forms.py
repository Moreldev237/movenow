from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User
from core.models import Driver, Fleet

class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription utilisateur - Version simplifiée"""
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.com',
            'autocomplete': 'email',
            'required': True
        }),
        help_text=_("Nous ne partagerons jamais votre email.")
    )
    phone = forms.CharField(
        label=_("Téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '699123456 ou +237 699 123 456',
            'autocomplete': 'tel',
            'required': True,
            'pattern': '[+]?[0-9\\s]{9,15}',
            'title': _('Numéro de téléphone (9-15 chiffres, avec ou sans préfixe)')
        }),
        help_text=_("Entrez votre numéro MTN, Orange ou Nexttel (avec ou sans +237)")
    )
    first_name = forms.CharField(
        label=_("Prénom"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre prénom',
            'autocomplete': 'given-name',
            'required': True
        })
    )
    last_name = forms.CharField(
        label=_("Nom"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre nom',
            'autocomplete': 'family-name',
            'required': True
        })
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Au moins 4 caractères',
            'autocomplete': 'new-password'
        }),
        help_text=_("Minimum 4 caractères")
    )
    password2 = forms.CharField(
        label=_("Confirmation du mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Répétez votre mot de passe',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("Cet email est déjà utilisé. Essayez de vous connecter ou utilisez un autre email."),
                code='email_exists'
            )
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Nettoyer le numéro de téléphone
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 9:
            raise forms.ValidationError(
                _("Le numéro de téléphone doit avoir au moins 9 chiffres."),
                code='phone_short'
            )
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                _("Ce numéro de téléphone est déjà utilisé. Essayez de vous connecter."),
                code='phone_exists'
            )
        return phone
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Nettoyer le téléphone avant de sauvegarder
        phone = ''.join(filter(str.isdigit, self.cleaned_data.get('phone', '')))
        user.phone = phone
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    """Formulaire de connexion - Accepte email ou téléphone"""
    username = forms.CharField(
        label=_("Email ou Téléphone"),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre@email.com ou 6XXXXXXXX',
            'autocomplete': 'username',
            'required': True
        }),
        help_text=_("Entrez votre adresse email ou votre numéro de téléphone")
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        label=_("Se souvenir de moi"),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-orange-500 border-gray-300 rounded'
        })
    )
    
    class Meta:
        fields = ('username', 'password', 'remember_me')
    
    def clean_username(self):
        """Nettoyer et valider le champ username (email ou téléphone)"""
        username = self.cleaned_data.get('username', '').strip()
        
        # Vérifier si c'est un email
        if '@' in username:
            # C'est un email
            if not forms.EmailField().clean(username):
                raise forms.ValidationError(
                    _("Format d'email invalide."),
                    code='invalid_email'
                )
            # Normaliser l'email
            username = username.lower()
        
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Essayer de trouver l'utilisateur par email
            try:
                user = User.objects.get(email__iexact=username)
                # Vérifier le mot de passe
                if user.check_password(password):
                    cleaned_data['user'] = user
                else:
                    raise forms.ValidationError(
                        _("Mot de passe incorrect."),
                        code='invalid_password'
                    )
            except User.DoesNotExist:
                # Essayer de trouver par téléphone
                phone = ''.join(filter(str.isdigit, username))
                try:
                    user = User.objects.get(phone=phone)
                    # Vérifier le mot de passe
                    if user.check_password(password):
                        cleaned_data['user'] = user
                    else:
                        raise forms.ValidationError(
                            _("Mot de passe incorrect."),
                            code='invalid_password'
                        )
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    # Ni email ni téléphone trouvé
                    raise forms.ValidationError(
                        _("Aucun compte trouvé avec ces informations. "
                          "Vérifiez votre email ou numéro de téléphone."),
                        code='user_not_found'
                    )
        
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'birth_date', 'gender', 
                 'address', 'city', 'country', 'profile_picture', 'language', 'currency')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '6XXXXXXXX'}),
            'birth_date': forms.DateInput(
                attrs={'class': 'form-input', 'type': 'date'}
            ),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Adresse complète'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ville'}),
            'country': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Pays'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-input'}),
            'language': forms.Select(attrs={'class': 'form-input'}),
            'currency': forms.Select(attrs={'class': 'form-input'}),
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