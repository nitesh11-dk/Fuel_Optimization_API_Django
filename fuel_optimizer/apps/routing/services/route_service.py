import requests
from typing import List, Tuple
from core.exceptions import ExternalAPIException, RouteNotFoundException
from core.constants import OPENROUTESERVICE_DIRECTIONS_URL
from core.config import OPENROUTESERVICE_API_KEY


class RouteService:
    """Service for handling route-related operations"""
    
    def __init__(self, use_mock=False):
        self.api_key = OPENROUTESERVICE_API_KEY
        self.use_mock = use_mock or not self.api_key
    
    def geocode_location(self, location: str) -> tuple:
        """
        Convert location name to coordinates
        Returns: (longitude, latitude)
        """
        if self.use_mock:
            return self._mock_geocode(location)
        
        url = f"https://api.openrouteservice.org/geocode/search"
        params = {
            'api_key': self.api_key,
            'text': location,
            'limit': 1
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                raise RouteNotFoundException(f"Location not found: {location}")
            
            coords = data['features'][0]['geometry']['coordinates']
            return coords[0], coords[1]  # lon, lat
        except requests.RequestException as e:
            raise ExternalAPIException(f"Geocoding failed: {str(e)}")
    
    def _mock_geocode(self, location: str) -> tuple:
        """Mock geocoding for testing without API key"""
        # Simple mock coordinates for common US cities
        mock_coords = {
            'new york': (-74.0060, 40.7128),
            'los angeles': (-118.2437, 34.0522),
            'chicago': (-87.6298, 41.8781),
            'miami': (-80.1918, 25.7617),
            'seattle': (-122.3321, 47.6062),
            'boston': (-71.0589, 42.3601),
            'san francisco': (-122.4194, 37.7749),
            'houston': (-95.3698, 29.7604),
            'denver': (-104.9903, 39.7392),
            'dallas': (-96.7970, 32.7767),
            'atlanta': (-84.3880, 33.7490),
            'phoenix': (-112.0740, 33.4484),
        }
        
        location_lower = location.lower()
        for city, coords in mock_coords.items():
            if city in location_lower:
                return coords
        
        # Default to NYC if not found
        return (-74.0060, 40.7128)
    
    def get_route(self, start_coords: tuple, end_coords: tuple) -> dict:
        """
        Get route between two coordinates
        Returns: dict with coordinates and total distance in miles
        """
        if self.use_mock:
            return self._mock_route(start_coords, end_coords)
        
        url = OPENROUTESERVICE_DIRECTIONS_URL
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        body = {
            'coordinates': [
                list(start_coords),
                list(end_coords)
            ]
        }
        
        try:
            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not data.get('features'):
                raise RouteNotFoundException("No route found between locations")

            route = data['features'][0]
            # Sum all segments to get total distance (handles multi-waypoint routes)
            segments = route['properties'].get('segments', [])
            distance_meters = sum(seg.get('distance', 0) for seg in segments)
            if distance_meters == 0:
                # Fallback: use top-level summary distance
                distance_meters = route['properties'].get('summary', {}).get('distance', 0)
            distance_miles = distance_meters * 0.000621371  # Convert to miles

            # Extract REAL road geometry from the API response — not interpolated
            geometry = route['geometry']['coordinates']

            return {
                'coordinates': geometry,
                'total_distance': distance_miles
            }
        except requests.RequestException as e:
            raise ExternalAPIException(f"Route API failed: {str(e)}")
    
    def _mock_route(self, start_coords: tuple, end_coords: tuple) -> dict:
        """Mock route calculation for testing without API"""
        # Calculate simple Haversine distance
        from apps.routing.utils.geo_utils import haversine_distance
        distance = haversine_distance(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1]
        )
        
        # Generate intermediate points to simulate a full route polyline
        # This creates a more realistic route geometry for optimization
        num_points = max(10, int(distance / 100))  # One point per ~100 miles
        coordinates = self._generate_route_polyline(start_coords, end_coords, num_points)
        
        return {
            'coordinates': coordinates,
            'total_distance': distance
        }
    
    def _generate_route_polyline(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float], num_points: int) -> List[List[float]]:
        """Generate intermediate points between start and end coordinates"""
        coordinates = [list(start_coords)]
        
        for i in range(1, num_points - 1):
            ratio = i / (num_points - 1)
            # Linear interpolation with slight curve simulation
            lat = start_coords[1] + (end_coords[1] - start_coords[1]) * ratio
            lon = start_coords[0] + (end_coords[0] - start_coords[0]) * ratio
            
            # Add slight curve to simulate realistic route
            curve_offset = 0.5 * (1 - (2 * ratio - 1) ** 2)  # Parabolic curve
            lat += curve_offset * 0.5  # Small latitude adjustment
            
            coordinates.append([lon, lat])
        
        coordinates.append(list(end_coords))
        return coordinates
