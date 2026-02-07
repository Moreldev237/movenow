/**
 * MoveNow - Auth Validation JavaScript
 * Validation en temps réel pour l'inscription et la connexion
 */

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Initialiser le toggle mot de passe
    initPasswordToggles();
    
    // Initialiser la validation pour chaque formulaire
    initFormValidation();
});

/**
 * Initialiser les boutons afficher/masquer mot de passe
 */
function initPasswordToggles() {
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId) || document.querySelector(`[name="${targetId}"]`);
            const icon = this.querySelector('i');
            
            if (input && icon) {
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            }
        });
    });
}

/**
 * Initialiser la validation des formulaires
 */
function initFormValidation() {
    // Formulaire d'inscription
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        initRegisterFormValidation(registerForm);
    }
    
    // Formulaire de connexion
    const loginForm = document.querySelector('form[action*="login"]');
    if (loginForm && !registerForm) {
        initLoginFormValidation(loginForm);
    }
}

/**
 * Validation du formulaire d'inscription
 */
function initRegisterFormValidation(form) {
    const phoneInput = form.querySelector('[name="phone"]');
    const emailInput = form.querySelector('[name="email"]');
    const password1Input = form.querySelector('[name="password1"]');
    const password2Input = form.querySelector('[name="password2"]');
    
    // Validation du téléphone en temps réel
    if (phoneInput) {
        phoneInput.addEventListener('input', debounce(function(e) {
            const phone = e.target.value;
            const cleanedPhone = phone.replace(/\D/g, '');
            
            // Mise à jour du format visuel
            if (cleanedPhone.length > 0) {
                // Ajouter un préfixe +237 si pas présent
                if (!phone.startsWith('+237') && !phone.startsWith('237')) {
                    // Ne pas modifier pendant la saisie
                }
            }
            
            // Validation de la longueur
            if (cleanedPhone.length > 0 && cleanedPhone.length < 9) {
                showFieldError(phoneInput, 'Le numéro doit avoir au moins 9 chiffres');
            } else if (cleanedPhone.length >= 9 && cleanedPhone.length <= 15) {
                // Vérifier si le numéro existe déjà
                checkPhoneExists(cleanedPhone, phoneInput);
            } else {
                hideFieldError(phoneInput);
            }
        }, 500));
    }
    
    // Validation de l'email en temps réel
    if (emailInput) {
        emailInput.addEventListener('blur', debounce(function(e) {
            const email = e.target.value.trim().toLowerCase();
            
            if (isValidEmail(email)) {
                checkEmailExists(email, emailInput);
            } else {
                hideFieldError(emailInput);
            }
        }, 500));
    }
    
    // Validation du mot de passe en temps réel
    if (password1Input) {
        password1Input.addEventListener('input', function(e) {
            const password = e.target.value;
            
            if (password.length > 0 && password.length < 4) {
                showFieldError(password1Input, 'Le mot de passe doit avoir au moins 4 caractères');
            } else {
                hideFieldError(password1Input);
            }
            
            // Vérifier la correspondance avec password2
            if (password2Input && password2Input.value) {
                if (password !== password2Input.value) {
                    showFieldError(password2Input, 'Les mots de passe ne correspondent pas');
                } else {
                    hideFieldError(password2Input);
                }
            }
        });
    }
    
    // Vérifier la correspondance des mots de passe
    if (password2Input && password1Input) {
        password2Input.addEventListener('input', function(e) {
            const password2 = e.target.value;
            const password1 = password1Input.value;
            
            if (password2 && password1 !== password2) {
                showFieldError(password2Input, 'Les mots de passe ne correspondent pas');
            } else {
                hideFieldError(password2Input);
            }
        });
    }
}

/**
 * Validation du formulaire de connexion
 */
function initLoginFormValidation(form) {
    const usernameInput = form.querySelector('[name="username"]');
    
    if (usernameInput) {
        usernameInput.addEventListener('input', debounce(function(e) {
            const username = e.target.value.trim();
            
            if (username.length > 0) {
                // Essayer de deviner si c'est un email ou un téléphone
                if (username.includes('@')) {
                    if (isValidEmail(username)) {
                        hideFieldError(usernameInput);
                    } else {
                        showFieldError(usernameInput, 'Format d\'email invalide');
                    }
                } else {
                    // C'est probablement un téléphone
                    const cleanedPhone = username.replace(/\D/g, '');
                    if (cleanedPhone.length >= 9) {
                        hideFieldError(usernameInput);
                    } else if (cleanedPhone.length > 0) {
                        showFieldError(usernameInput, 'Numéro de téléphone invalide');
                    }
                }
            }
        }, 300));
    }
}

/**
 * Vérifier si l'email existe déjà (API call)
 */
function checkEmailExists(email, input) {
    if (!csrfToken || !email) return;
    
    fetch('/api/accounts/check-email/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.exists) {
            showFieldError(input, 'Cet email est déjà utilisé. Essayez de vous connecter.');
            input.classList.add('border-red-500');
        } else {
            hideFieldError(input);
        }
    })
    .catch(error => {
        console.log('Erreur lors de la vérification de l\'email:', error);
    });
}

/**
 * Vérifier si le téléphone existe déjà (API call)
 */
function checkPhoneExists(phone, input) {
    if (!csrfToken || !phone) return;
    
    fetch('/api/accounts/check-phone/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ phone: phone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.exists) {
            showFieldError(input, 'Ce numéro est déjà utilisé. Essayez de vous connecter.');
            input.classList.add('border-red-500');
        } else {
            hideFieldError(input);
        }
    })
    .catch(error => {
        console.log('Erreur lors de la vérification du téléphone:', error);
    });
}

/**
 * Afficher une erreur de champ
 */
function showFieldError(input, message) {
    if (!input) return;
    
    // Trouver ou créer l'élément d'erreur
    let errorElement = input.parentNode.querySelector('.field-error, .error-message');
    
    if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.className = 'field-error text-red-500 text-xs mt-1';
        input.parentNode.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    input.classList.add('border-red-500', 'focus:ring-red-500');
    input.classList.remove('border-gray-300', 'focus:ring-orange-500');
}

/**
 * Masquer une erreur de champ
 */
function hideFieldError(input) {
    if (!input) return;
    
    const errorElement = input.parentNode.querySelector('.field-error, .error-message');
    if (errorElement) {
        errorElement.remove();
    }
    
    input.classList.remove('border-red-500', 'focus:ring-red-500');
    input.classList.add('border-gray-300', 'focus:ring-orange-500');
}

/**
 * Valider un email
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Valider un numéro de téléphone camerounais
 */
function isValidCameroonPhone(phone) {
    // Les numéros camerounais commencent par 6 et ont 9 chiffres
    const phoneRegex = /^[6-9]\d{8}$/;
    return phoneRegex.test(phone);
}

/**
 * Debounce function - Limiter la fréquence des appels API
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Formater un numéro de téléphone
 */
function formatPhoneNumber(phone) {
    const cleaned = ('' + phone).replace(/\D/g, '');
    const match = cleaned.match(/^(237)?(\d{3})(\d{3})(\d{3})$/);
    
    if (match) {
        if (match[1]) {
            return '+237 ' + match[2] + ' ' + match[3] + ' ' + match[4];
        }
        return match[2] + ' ' + match[3] + ' ' + match[4];
    }
    
    return phone;
}

/**
 * Nettoyer un numéro de téléphone (supprimer tous les caractères non numériques)
 */
function cleanPhoneNumber(phone) {
    return phone.replace(/\D/g, '');
}

// Exposer les fonctions globalement pour le débogage
window.MoveNowAuth = {
    checkEmailExists,
    checkPhoneExists,
    formatPhoneNumber,
    cleanPhoneNumber,
    isValidEmail,
    isValidCameroonPhone
};

