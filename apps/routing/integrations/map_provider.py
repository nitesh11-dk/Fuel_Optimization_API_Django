"""
Map Provider Integration
Currently configured for OpenRouteService
Can be extended to support other providers like Mapbox
"""

from apps.routing.services.route_service import RouteService
from core.config import OPENROUTESERVICE_API_KEY

class MapProvider:
    """Factory class for map provider integrations"""
    
    @staticmethod
    def get_provider(provider_name: str = 'openrouteservice') -> RouteService:
        """
        Get map provider instance
        Args:
            provider_name: Name of the provider ('openrouteservice' or 'mapbox')
        Returns:
            RouteService instance
        """
        if provider_name == 'openrouteservice':
            # Use real API when a valid key is configured; fall back to mock otherwise
            placeholder_keys = {'', 'your-openrouteservice-api-key-here'}
            use_mock = not OPENROUTESERVICE_API_KEY or OPENROUTESERVICE_API_KEY in placeholder_keys
            return RouteService(use_mock=use_mock)
        elif provider_name == 'mapbox':
            # Mapbox integration can be added here
            raise NotImplementedError("Mapbox integration not yet implemented")
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
