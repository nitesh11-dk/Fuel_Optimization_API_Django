from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(max_length=255, help_text="Starting location (e.g., 'New York')")
    end = serializers.CharField(max_length=255, help_text="Ending location (e.g., 'Los Angeles')")


class FuelStopSerializer(serializers.Serializer):
    sequence = serializers.IntegerField(help_text="Sequence number in the route")
    location = serializers.CharField(help_text="Fuel station location")
    price = serializers.FloatField(help_text="Fuel price per gallon")
    truckstop_name = serializers.CharField(help_text="Name of the truckstop", required=False)
    address = serializers.CharField(help_text="Address of the truckstop", required=False)


class RouteResponseSerializer(serializers.Serializer):
    total_distance = serializers.FloatField(help_text="Total distance in miles")
    fuel_needed = serializers.FloatField(help_text="Total fuel needed in gallons")
    fuel_stops = FuelStopSerializer(many=True, help_text="List of optimal fuel stops in route order")
    route_geometry = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField()),
        help_text="Route coordinates as [[lon, lat], ...]",
        required=False
    )
    total_cost = serializers.FloatField(help_text="Total fuel cost")
    currency = serializers.CharField(help_text="Currency code", default="USD")
