import math
from decimal import Decimal

def calculate_route(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Calculate route distance and duration between two points.
    For now, uses straight-line distance as a mock implementation.
    In production, this would integrate with a mapping service like Google Maps or OpenStreetMap.

    Args:
        pickup_lat (float): Pickup latitude
        pickup_lng (float): Pickup longitude
        dropoff_lat (float): Dropoff latitude
        dropoff_lng (float): Dropoff longitude

    Returns:
        dict: {'distance': float in km, 'duration': int in minutes}
    """
    # Calculate straight-line distance using Haversine formula
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
