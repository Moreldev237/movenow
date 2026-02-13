import math
from decimal import Decimal
import os
import requests
from django.conf import settings

# Google Maps API Key from settings or environment
GOOGLE_MAPS_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', os.environ.get('GOOGLE_MAPS_API_KEY', ''))

def calculate_route(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculate route distance and duration between two points.
    Uses Google Maps Distance Matrix API if API key is available.
    Falls back to Haversine formula otherwise.

    Args:
        pickup_lat (float): Pickup latitude
        pickup_lng (float): Pickup longitude
        dropoff_lat (float): Dropoff latitude
        dropoff_lng (float): Dropoff longitude

    Returns:
        dict: {'distance': float in km, 'duration': int in minutes}
    """
    # Try to use Google Maps API if key is available
    if GOOGLE_MAPS_API_KEY:
        try:
            result = calculate_route_google_maps(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
            if result:
                return result
        except Exception as e:
            # Log the error and fall back to Haversine
            print(f"Google Maps API error: {e}")
    
    # Fall back to Haversine formula
    return calculate_route_haversine(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)


def calculate_route_google_maps(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculate route using Google Maps Distance Matrix API.
    
    Args:
        pickup_lat (float): Pickup latitude
        pickup_lng (float): Pickup longitude
        dropoff_lat (float): Dropoff latitude
        dropoff_lng (float): Dropoff longitude
        
    Returns:
        dict: {'distance': float in km, 'duration': int in minutes}
        
    Raises:
        Exception: If API call fails
    """
    if not GOOGLE_MAPS_API_KEY:
        raise Exception("Google Maps API key not configured")
    
    origin = f"{pickup_lat},{pickup_lng}"
    destination = f"{dropoff_lat},{dropoff_lng}"
    
    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origin}"
        f"&destinations={destination}"
        f"&mode=driving"
        f"&language=fr"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    if data['status'] == 'OK':
        element = data['rows'][0]['elements'][0]
        
        if element['status'] == 'OK':
            distance_meters = element['distance']['value']  # meters
            duration_seconds = element['duration']['value']  # seconds
            
            return {
                'distance': round(distance_meters / 1000, 2),  # Convert to km
                'duration': round(duration_seconds / 60)  # Convert to minutes
            }
        else:
            raise Exception(f"Element status: {element['status']}")
    else:
        raise Exception(f"API status: {data['status']}")


def calculate_route_haversine(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculate straight-line distance using Haversine formula.
    
    Args:
        pickup_lat (float): Pickup latitude
        pickup_lng (float): Pickup longitude
        dropoff_lat (float): Dropoff latitude
        dropoff_lng (float): Dropoff longitude

    Returns:
        dict: {'distance': float in km, 'duration': int in minutes}
    """
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(pickup_lat)
    lat2_rad = math.radians(dropoff_lat)
    delta_lat = math.radians(dropoff_lat - pickup_lat)
    delta_lng = math.radians(dropoff_lng - pickup_lng)

    a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lng/2) * math.sin(delta_lng/2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    # Estimate duration: assume average speed of 30 km/h in city
    # Add minimum 2 minutes for pickup/dropoff time
    duration_minutes = max(2, int((distance / 30) * 60) + 2)

    return {
        'distance': round(distance, 2),
        'duration': duration_minutes
    }


def geocode_address(address):
    """
    Geocode an address to coordinates using Google Maps Geocoding API.
    
    Args:
        address (str): The address to geocode
        
    Returns:
        dict: {'lat': float, 'lng': float, 'formatted_address': str}
        
    Raises:
        Exception: If API call fails
    """
    if not GOOGLE_MAPS_API_KEY:
        raise Exception("Google Maps API key not configured")
    
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={requests.utils.quote(address)}"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    if data['status'] == 'OK' and data['results']:
        result = data['results'][0]
        location = result['geometry']['location']
        
        return {
            'lat': location['lat'],
            'lng': location['lng'],
            'formatted_address': result['formatted_address']
        }
    else:
        raise Exception(f"Geocoding failed: {data['status']}")


def reverse_geocode(lat, lng):
    """
    Reverse geocode coordinates to an address using Google Maps Geocoding API.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        
    Returns:
        str: Formatted address
        
    Raises:
        Exception: If API call fails
    """
    if not GOOGLE_MAPS_API_KEY:
        raise Exception("Google Maps API key not configured")
    
    location = f"{lat},{lng}"
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={location}"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    if data['status'] == 'OK' and data['results']:
        return data['results'][0]['formatted_address']
    else:
        raise Exception(f"Reverse geocoding failed: {data['status']}")

def estimate_fare(vehicle_type, distance, duration, is_shared=False):
    """
    Estimate fare for a trip based on vehicle type and route details.

    Args:
        vehicle_type: VehicleType instance
        distance (float): Distance in kilometers
        duration (int): Duration in minutes
        is_shared (bool): Whether it's a shared ride

    Returns:
        Decimal: Estimated fare
    """
    # Calculate base fare
    base_price = vehicle_type.base_price
    distance_price = vehicle_type.price_per_km * Decimal(str(distance))
    time_price = vehicle_type.price_per_minute * Decimal(str(duration))

    total = base_price + distance_price + time_price

    # Apply sharing discount if applicable
    if is_shared:
        # Default 30% discount for shared rides, can be made configurable
        discount_percentage = Decimal('0.30')
        discount = total * discount_percentage
        total -= discount

    return total.quantize(Decimal('0.01'))  # Round to 2 decimal places
