// MoveNow Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initMobileMenu();
    initTooltips();
    initAnimations();
});

// ===========================================
// Google Maps Helper Functions
// ===========================================

// Google Maps API Key

const GOOGLE_MAPS_API_KEY = 'AIzaSyD3bMgXddB7pUPSkVvh-mHJCkZfDbgjz10';


// Initialize Google Maps (placeholder function)
function initGoogleMaps() {
    // This function is used to check if Google Maps is loaded
    return typeof google !== 'undefined' && google.maps;
}

// Load Google Maps script dynamically
function loadGoogleMapsScript(callback) {
    if (initGoogleMaps()) {
        callback();
        return;
    }
    
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places,geometry`;
    script.async = true;
    script.defer = true;
    script.onload = callback;
    document.head.appendChild(script);
}

// Geocode address to coordinates
function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        if (!initGoogleMaps()) {
            reject(new Error('Google Maps not loaded'));
            return;
        }
        
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: address }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const location = results[0].geometry.location;
                resolve({
                    lat: location.lat(),
                    lng: location.lng(),
                    formatted_address: results[0].formatted_address
                });
            } else {
                reject(new Error('Geocoding failed: ' + status));
            }
        });
    });
}

// Reverse geocode coordinates to address
function reverseGeocodeCoordinates(lat, lng) {
    return new Promise((resolve, reject) => {
        if (!initGoogleMaps()) {
            reject(new Error('Google Maps not loaded'));
            return;
        }
        
        const geocoder = new google.maps.Geocoder();
        const latlng = { lat, lng };
        
        geocoder.geocode({ location: latlng }, (results, status) => {
            if (status === 'OK' && results[0]) {
                resolve(results[0].formatted_address);
            } else {
                reject(new Error('Reverse geocoding failed: ' + status));
            }
        });
    });
}

// Calculate route between two points
function calculateRoute(origin, destination) {
    return new Promise((resolve, reject) => {
        if (!initGoogleMaps()) {
            reject(new Error('Google Maps not loaded'));
            return;
        }
        
        const directionsService = new google.maps.DirectionsService();
        const request = {
            origin: origin,
            destination: destination,
            travelMode: google.maps.TravelMode.DRIVING,
            provideRouteAlternatives: false
        };
        
        directionsService.route(request, (response, status) => {
            if (status === 'OK') {
                const route = response.routes[0];
                const leg = route.legs[0];
                
                resolve({
                    distance: leg.distance.value / 1000, // km
                    duration: leg.duration.value / 60, // minutes
                    distance_text: leg.distance.text,
                    duration_text: leg.duration.text,
                    start_address: leg.start_address,
                    end_address: leg.end_address
                });
            } else {
                reject(new Error('Directions request failed: ' + status));
            }
        });
    });
}

// Create a marker on the map
function createMarker(map, position, options = {}) {
    if (!initGoogleMaps()) {
        console.error('Google Maps not loaded');
        return null;
    }
    
    const defaultIcon = {
        url: options.icon || 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
        scaledSize: options.scaledSize || new google.maps.Size(32, 32),
        anchor: options.anchor || new google.maps.Point(16, 32)
    };
    
    const marker = new google.maps.Marker({
        map: map,
        position: position,
        icon: options.icon ? defaultIcon : undefined,
        title: options.title || '',
        draggable: options.draggable || false
    });
    
    if (options.infoWindow) {
        const infoWindow = new google.maps.InfoWindow({
            content: options.infoWindow
        });
        marker.addListener('click', () => {
            infoWindow.open(map, marker);
        });
    }
    
    return marker;
}

// Calculate distance between two points using Haversine formula
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in km
    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLng / 2) * Math.sin(dLng / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return distance; // km
}

// Convert degrees to radians
function toRad(deg) {
    return deg * (Math.PI / 180);
}

// Format coordinates for display
function formatCoordinates(lat, lng) {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lngDir = lng >= 0 ? 'E' : 'W';
    
    return `${Math.abs(lat).toFixed(6)}° ${latDir}, ${Math.abs(lng).toFixed(6)}° ${lngDir}`;
}

// Check if a point is within a radius of another point
function isWithinRadius(lat1, lng1, lat2, lng2, radiusKm) {
    const distance = calculateDistance(lat1, lng1, lat2, lng2);
    return distance <= radiusKm;
}

// Get current location with high accuracy
function getCurrentLocationHighAccuracy() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('La géolocalisation n\'est pas supportée'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    heading: position.coords.heading,
                    speed: position.coords.speed
                });
            },
            error => {
                reject(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0
            }
        );
    });
}

// Watch location changes
function watchLocation(callback, errorCallback) {
    if (!navigator.geolocation) {
        errorCallback(new Error('La géolocalisation n\'est pas supportée'));
        return null;
    }
    
    return navigator.geolocation.watchPosition(
        position => {
            callback({
                lat: position.coords.latitude,
                lng: position.coords.longitude,
                accuracy: position.coords.accuracy
            });
        },
        errorCallback,
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 30000
        }
    );
}

// Clear location watch
function clearLocationWatch(watchId) {
    if (watchId && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchId);
    }
}

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

