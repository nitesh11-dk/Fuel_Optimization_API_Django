import pandas as pd
from pathlib import Path
from core.config import FUEL_DATA_PATH
from core.exceptions import FuelDataException
from typing import List, Dict
from apps.routing.utils.geocode_cache import get_coordinates, _load_cache


class FuelService:
    """Service for handling fuel station data"""
    
    def __init__(self):
        self.fuel_data = None
        self._coords_cache = None
        self._load_fuel_data()
    
    def _load_fuel_data(self):
        """Load fuel price CSV data into memory"""
        try:
            if not FUEL_DATA_PATH.exists():
                raise FuelDataException(f"Fuel data file not found: {FUEL_DATA_PATH}")
            
            self.fuel_data = pd.read_csv(FUEL_DATA_PATH)
            
            # Clean and normalize data
            self.fuel_data['Retail Price'] = pd.to_numeric(
                self.fuel_data['Retail Price'], errors='coerce'
            )
            self.fuel_data = self.fuel_data.dropna(subset=['Retail Price'])
            
            # Create location identifier for easier searching (strip any padding whitespace)
            self.fuel_data['City'] = self.fuel_data['City'].str.strip()
            self.fuel_data['State'] = self.fuel_data['State'].str.strip()
            self.fuel_data['location'] = self.fuel_data['City'] + ', ' + self.fuel_data['State']
            
            # Load geocode cache for coordinates
            self._coords_cache = _load_cache()
            
        except Exception as e:
            raise FuelDataException(f"Failed to load fuel data: {str(e)}")
    
    def _get_station_coords(self, city: str, state: str):
        """Get coordinates for a station from cache, falling back to state centroid"""
        cache_key = f"{city}, {state}"
        if self._coords_cache and cache_key in self._coords_cache:
            entry = self._coords_cache[cache_key]
            return entry['lon'], entry['lat']
        # Fallback: use get_coordinates (state centroid if not in cache)
        return get_coordinates(city, state)
    
    def get_all_fuel_stations(self) -> List[Dict]:
        """Return all fuel stations with their prices and coordinates"""
        if self.fuel_data is None:
            self._load_fuel_data()
        
        stations = []
        for _, row in self.fuel_data.iterrows():
            city = str(row.get('City', '')).strip()
            state = str(row.get('State', '')).strip()
            lon, lat = self._get_station_coords(city, state)
            
            stations.append({
                'truckstop_id': row.get('OPIS Truckstop ID'),
                'truckstop_name': row.get('Truckstop Name'),
                'address': row.get('Address'),
                'city': city,
                'state': state,
                'location': row.get('location'),
                'price': float(row['Retail Price']),
                'longitude': lon,
                'latitude': lat,
            })
        
        return stations
    
    def get_cheapest_stations(self, limit: int = 10) -> List[Dict]:
        """Get the cheapest fuel stations"""
        if self.fuel_data is None:
            self._load_fuel_data()
        
        cheapest = self.fuel_data.nsmallest(limit, 'Retail Price')
        
        stations = []
        for _, row in cheapest.iterrows():
            city = str(row.get('City', '')).strip()
            state = str(row.get('State', '')).strip()
            lon, lat = self._get_station_coords(city, state)
            
            stations.append({
                'truckstop_id': row.get('OPIS Truckstop ID'),
                'truckstop_name': row.get('Truckstop Name'),
                'address': row.get('Address'),
                'city': city,
                'state': state,
                'location': row.get('location'),
                'price': float(row['Retail Price']),
                'longitude': lon,
                'latitude': lat,
            })
        
        return stations
