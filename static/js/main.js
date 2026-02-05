// MoveNow Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initMobileMenu();
    initTooltips();
    initAnimations();
});

// Mobile Menu Toggle
function initMobileMenu() {
    const menuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

// Tooltip initialization
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'tooltip';
            tooltipEl.textContent = text;
            document.body.appendChild(tooltipEl);
            
            const rect = this.getBoundingClientRect();
            tooltipEl.style.left = rect.left + rect.width / 2 - tooltipEl.offsetWidth / 2 + 'px';
            tooltipEl.style.top = rect.top - tooltipEl.offsetHeight - 10 + 'px';
        });
        
        tooltip.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}

// Scroll animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Format currency
function formatCurrency(amount, currency = 'XAF') {
    return new Intl.NumberFormat('fr-CM', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0
    }).format(amount);
}

// Format distance
function formatDistance(distanceKm) {
    if (distanceKm < 1) {
        return Math.round(distanceKm * 1000) + ' m';
    }
    return distanceKm.toFixed(1) + ' km';
}

// Format duration
function formatDuration(minutes) {
    if (minutes < 60) {
        return minutes + ' min';
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours + ' h ' + mins + ' min';
}

// Get current location
function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('La géolocalisation n\'est pas supportée'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
            },
            error => {
                reject(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
}

// Debounce function
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

// AJAX helper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Une erreur est survenue' }));
        throw new Error(error.detail || 'Une erreur est survenue');
    }
    
    return response.json();
}

// Get cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Confirm action
function confirmAction(message, onConfirm, onCancel) {
    if (confirm(message)) {
        if (onConfirm) onConfirm();
    } else {
        if (onCancel) onCancel();
    }
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copié dans le presse-papiers!', 'success');
    } catch (err) {
        showToast('Impossible de copier', 'error');
    }
}

// Format phone number
function formatPhoneNumber(phone) {
    // Cameroon phone number formatting
    const cleaned = ('' + phone).replace(/\D/g, '');
    const match = cleaned.match(/^(237)?(\d{9})$/);
    
    if (match) {
        const countryCode = match[1] ? '+237 ' : '';
        const number = match[2];
        return `${countryCode}${number.substring(0, 3)} ${number.substring(3, 6)} ${number.substring(6, 9)}`;
    }
    
    return phone;
}

// Loading state management
function setLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="loading-spinner mr-2"></span>Chargement...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

// Date formatting
function formatDate(date, format = 'short') {
    const d = new Date(date);
    
    const options = {
        short: { day: 'numeric', month: 'short' },
        long: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' },
        time: { hour: '2-digit', minute: '2-digit' },
        full: { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }
    };
    
    return d.toLocaleDateString('fr-FR', options[format] || options.short);
}

// Countdown timer
function startCountdown(element, endTime, onComplete) {
    const update = () => {
        const now = new Date().getTime();
        const distance = endTime - now;
        
        if (distance < 0) {
            if (onComplete) onComplete();
            return;
        }
        
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        element.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        setTimeout(update, 1000);
    };
    
    update();
}

// Export data to CSV
function exportToCSV(data, filename) {
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => JSON.stringify(row[header])).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}

// Phone input country code handling
document.addEventListener('input', function(e) {
    if (e.target.dataset.phoneInput) {
        let value = e.target.value.replace(/\D/g, '');
        
        // Add country code if not present
        if (value.length > 0 && !value.startsWith('237')) {
            if (value.startsWith('6') || value.startsWith('2')) {
                value = '237' + value;
            }
        }
        
        // Format as user types
        if (value.length >= 9) {
            value = value.substring(0, 3) + ' ' + value.substring(3, 6) + ' ' + value.substring(6, 9);
        }
        
        e.target.value = value;
    }
});

