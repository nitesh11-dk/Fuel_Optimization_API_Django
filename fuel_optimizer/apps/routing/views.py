from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers.route_serializer import (
    RouteRequestSerializer,
    RouteResponseSerializer
)
from .services.route_service import RouteService
from .services.fuel_service import FuelService
from .services.optimization_service import OptimizationService
from .services.cost_service import CostService
from .integrations.map_provider import MapProvider
from core.exceptions import FuelOptimizerException

# ---------------------------------------------------------------------------
# Module-level singleton for FuelService.
# The CSV (≈577 KB) is loaded once when Django starts, not on every request.
# This avoids the repeated I/O + pandas parse overhead.
# ---------------------------------------------------------------------------
_fuel_service: FuelService | None = None


def _get_fuel_service() -> FuelService:
    """Return the shared FuelService instance, creating it on first call."""
    global _fuel_service
    if _fuel_service is None:
        _fuel_service = FuelService()
    return _fuel_service


class RouteOptimizationView(APIView):
    """
    API endpoint for route optimization with fuel cost calculation

    POST /api/route/
    """

    def post(self, request):
        """Process route optimization request"""
        serializer = RouteRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_location = serializer.validated_data['start']
        end_location = serializer.validated_data['end']

        try:
            # Step 1: Get route service (uses real ORS API if key is present)
            route_service = MapProvider.get_provider()

            # Step 2: Geocode locations
            start_coords = route_service.geocode_location(start_location)
            end_coords = route_service.geocode_location(end_location)

            # Step 3: Get route — ONE API call, real road geometry
            route_info = route_service.get_route(start_coords, end_coords)
            total_distance = route_info['total_distance']

            # Step 4: Fuel station data from pre-loaded singleton
            fuel_service = _get_fuel_service()
            all_stations = fuel_service.get_all_fuel_stations()

            # Step 5: Optimize fuel stops using real route geometry
            optimization_service = OptimizationService(fuel_service)
            fuel_stops = optimization_service.optimize_route(
                route_info['coordinates'],
                total_distance,
                all_stations,
                start_location,
                end_location
            )

            # Step 6: Calculate costs
            cost_service = CostService()
            fuel_needed = cost_service.calculate_fuel_needed(total_distance)
            total_cost = cost_service.calculate_total_cost(fuel_stops, fuel_needed)

            # Step 7: Prepare response
            response_data = {
                'total_distance': round(total_distance, 2),
                'fuel_needed': round(fuel_needed, 2),
                'fuel_stops': fuel_stops,
                'route_geometry': route_info['coordinates'],
                'total_cost': total_cost,
                'currency': 'USD'
            }

            response_serializer = RouteResponseSerializer(data=response_data)
            response_serializer.is_valid()

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except FuelOptimizerException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
