"""
Geocoding cache utility using OpenRouteService API.
Caches city+state -> lat/lon mappings to avoid repeated API calls.
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional

CACHE_FILE = Path(__file__).resolve().parent.parent / 'data' / 'geocode_cache.json'

# State centroids as fallback (lon, lat)
STATE_CENTROIDS = {
    'AL': (-86.9023, 32.3182), 'AK': (-152.4937, 64.2008), 'AZ': (-111.9400, 34.0489),
    'AR': (-92.4396, 34.7465), 'CA': (-119.6816, 37.8399), 'CO': (-105.3111, 39.3210),
    'CT': (-73.0877, 41.5978), 'DE': (-75.5072, 38.9440), 'FL': (-81.5158, 27.6648),
    'GA': (-83.4266, 33.0406), 'HI': (-157.4980, 19.8968), 'ID': (-114.4780, 44.2401),
    'IL': (-89.1994, 40.6331), 'IN': (-86.1349, 39.8494), 'IA': (-93.5001, 42.0110),
    'KS': (-96.2434, 38.5266), 'KY': (-84.6700, 37.8393), 'LA': (-91.9623, 31.2448),
    'ME': (-69.3819, 45.2538), 'MD': (-76.6413, 39.0538), 'MA': (-71.5300, 42.2596),
    'MI': (-86.2494, 44.3148), 'MN': (-93.9002, 46.7296), 'MS': (-89.3985, 33.7489),
    'MO': (-91.4959, 38.4561), 'MT': (-110.3626, 46.9219), 'NE': (-98.3808, 41.4924),
    'NV': (-117.0228, 39.8760), 'NH': (-71.5645, 43.4525), 'NJ': (-74.5210, 40.0583),
    'NM': (-106.0942, 34.8405), 'NY': (-74.2179, 43.2994), 'NC': (-79.8227, 35.7596),
    'ND': (-100.4344, 47.4460), 'OH': (-82.9071, 40.4173), 'OK': (-97.5073, 35.4676),
    'OR': (-122.3321, 44.5739), 'PA': (-77.2094, 41.2033), 'RI': (-71.4778, 41.5801),
    'SC': (-80.9470, 33.8569), 'SD': (-99.4388, 44.2998), 'TN': (-86.3432, 35.7478),
    'TX': (-99.3212, 31.9686), 'UT': (-111.6702, 39.3210), 'VT': (-72.7779, 44.0682),
    'VA': (-79.4588, 37.5248), 'WA': (-120.7401, 47.7511), 'WV': (-80.9542, 38.5976),
    'WI': (-89.6165, 43.7844), 'WY': (-107.2903, 43.0750),
    # Canadian provinces
    'AB': (-114.0680, 54.3618), 'BC': (-125.5470, 53.7267), 'MB': (-97.1354, 53.7609),
    'NB': (-66.4619, 46.5653), 'NS': (-63.5752, 44.6488), 'ON': (-85.3232, 51.2538),
    'QC': (-73.5491, 52.9399), 'SK': (-106.4507, 53.9333), 'YT': (-135.0500, 62.0000),
}


def _load_cache() -> Dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def _save_cache(cache: Dict):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def geocode_city_state(city: str, state: str, api_key: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a city+state using OpenRouteService API.
    Returns (longitude, latitude) or None if not found.
    """
    query = f"{city}, {state}, US"
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        'api_key': api_key,
        'text': query,
        'limit': 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            return (coords[0], coords[1])  # (lon, lat)
    except Exception:
        pass

    return None


def get_coordinates(city: str, state: str, api_key: str = '') -> Tuple[float, float]:
    """
    Get coordinates for a city+state. Uses cache, falls back to ORS API,
    then falls back to state centroid.
    Returns (longitude, latitude).
    """
    cache = _load_cache()
    cache_key = f"{city}, {state}"

    # 1. Check cache
    if cache_key in cache:
        return (cache[cache_key]['lon'], cache[cache_key]['lat'])

    # 2. Try ORS geocoding
    if api_key:
        coords = geocode_city_state(city, state, api_key)
        if coords:
            cache[cache_key] = {'lon': coords[0], 'lat': coords[1]}
            _save_cache(cache)
            time.sleep(0.5)  # Rate limit: ~2 req/sec for free tier
            return coords

    # 3. Fallback to state centroid
    if state in STATE_CENTROIDS:
        return STATE_CENTROIDS[state]

    # 4. Last resort
    return (-98.5795, 39.8283)  # Geographic center of US


def pre_geocode_stations(fuel_data_path: str, api_key: str, batch_size: int = 40, delay: float = 1.5):
    """
    Pre-geocode all unique city+state combinations from the fuel data CSV.
    Respects ORS rate limits by processing in batches with delays.
    Run this once via management command to populate the cache.
    """
    import pandas as pd

    cache = _load_cache()
    df = pd.read_csv(fuel_data_path)

    unique_locations = df[['City', 'State']].drop_duplicates()
    total = len(unique_locations)
    geocoded = 0
    skipped = 0
    failed = 0

    for idx, row in unique_locations.iterrows():
        city = str(row['City']).strip()
        state = str(row['State']).strip()
        cache_key = f"{city}, {state}"

        if cache_key in cache:
            skipped += 1
            continue

        coords = geocode_city_state(city, state, api_key)
        if coords:
            cache[cache_key] = {'lon': coords[0], 'lat': coords[1]}
            geocoded += 1
        else:
            # Use state centroid as fallback
            if state in STATE_CENTROIDS:
                cache[cache_key] = {'lon': STATE_CENTROIDS[state][0], 'lat': STATE_CENTROIDS[state][1]}
            failed += 1

        # Save progress every batch_size entries
        if (geocoded + failed) % batch_size == 0:
            _save_cache(cache)
            print(f"Progress: {geocoded + failed + skipped}/{total} (geocoded: {geocoded}, failed: {failed}, cached: {skipped})")
            time.sleep(delay)  # Wait between batches for rate limiting

    _save_cache(cache)
    print(f"Done! Geocoded: {geocoded}, Failed: {failed}, Already cached: {skipped}")
    return cache
