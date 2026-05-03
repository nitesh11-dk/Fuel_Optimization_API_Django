"""
Management command to pre-geocode all fuel station cities using ORS API.
Run once: python manage.py geocode_stations
"""

from django.core.management.base import BaseCommand
from core.config import FUEL_DATA_PATH, OPENROUTESERVICE_API_KEY
from apps.routing.utils.geocode_cache import pre_geocode_stations


class Command(BaseCommand):
    help = 'Pre-geocode all fuel station cities using OpenRouteService API'

    def handle(self, *args, **options):
        if not OPENROUTESERVICE_API_KEY:
            self.stderr.write(self.style.ERROR('ORS_API_KEY not configured. Set it in .env'))
            return

        if not FUEL_DATA_PATH.exists():
            self.stderr.write(self.style.ERROR(f'Fuel data not found at {FUEL_DATA_PATH}'))
            return

        self.stdout.write(self.style.SUCCESS('Starting geocoding...'))
        self.stdout.write(f'Fuel data: {FUEL_DATA_PATH}')

        cache = pre_geocode_stations(
            str(FUEL_DATA_PATH),
            OPENROUTESERVICE_API_KEY,
            batch_size=40,
            delay=1.5
        )

        self.stdout.write(self.style.SUCCESS(f'Geocoding complete. {len(cache)} locations cached.'))
