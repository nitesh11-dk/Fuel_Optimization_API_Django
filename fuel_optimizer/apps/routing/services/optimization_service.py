import math
from core.constants import MAX_RANGE_MILES, SEARCH_RADIUS_MILES
from core.exceptions import OptimizationException
from typing import List, Dict, Optional, Tuple
from apps.routing.utils.geo_utils import haversine_distance


class OptimizationService:
    """Service for optimizing fuel stops along a route.

    Algorithm:
      1. Compute cumulative Haversine distances along real route geometry.
      2. Walk forward in 500-mile increments (MAX_RANGE_MILES).
      3. At each target distance, identify the route-point window that falls
         within ±50 miles of the target (not a fixed ±10 index window).
      4. Among stations within SEARCH_RADIUS_MILES of ANY point in that window,
         pick the cheapest unused one.
      5. If nothing is found at the primary radius, expand up to 100 mi.
      6. Track used_station_ids and last_stop_index to guarantee forward
         progression and no duplicates.
      7. Repeat until the remaining distance to destination is ≤ MAX_RANGE_MILES.
    """

    # Fallback expanded search radius when no station is found within primary radius
    EXPANDED_RADIUS_MILES = 100

    def __init__(self, fuel_service):
        self.fuel_service = fuel_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize_route(
        self,
        route_geometry: List[List[float]],
        total_distance: float,
        all_stations: List[Dict],
        start_location: str = '',
        end_location: str = '',
    ) -> List[Dict]:
        """
        Return an ordered list of fuel stops for the given route.

        Args:
            route_geometry:  [[lon, lat], …] — real road coordinates from ORS.
            total_distance:  Reported trip distance in miles.
            all_stations:    All fuel stations with lon/lat/price.
            start_location:  Human-readable start (unused in algorithm, kept for
                             API compatibility).
            end_location:    Human-readable end (ditto).

        Returns:
            List of fuel-stop dicts ordered geographically along the route.
        """
        if not route_geometry or len(route_geometry) < 2:
            return []

        # Step 1 — compute cumulative distances from real geometry
        route_distances = self._compute_route_distances(route_geometry)
        actual_total = route_distances[-1]

        # Prefer the geometry-derived total (it reflects the real road path)
        if actual_total > 0:
            total_distance = actual_total

        # A full tank gets us MAX_RANGE_MILES; if the trip is shorter, no stops needed
        if total_distance <= MAX_RANGE_MILES:
            return []

        fuel_stops: List[Dict] = []
        used_station_ids: set = set()
        # current_target: the route-distance at which we need to refuel next
        current_target = MAX_RANGE_MILES
        # last_stop_route_idx: route index of the previous stop (enforce forward only)
        last_stop_route_idx = 0
        sequence = 1

        # Step 2 — walk forward in MAX_RANGE_MILES increments
        while current_target < total_distance - 1:  # -1 avoids floating-point edge
            # Find the route index closest to current_target
            target_idx = self._find_route_index_at_distance(
                route_distances, current_target, last_stop_route_idx
            )
            if target_idx is None:
                break  # Exhausted route

            # Step 3 — build a window of route points ≈ this segment
            window_start, window_end = self._build_distance_window(
                route_distances, current_target, target_idx, window_miles=50
            )
            # Always enforce forward progression
            window_start = max(window_start, last_stop_route_idx + 1)
            if window_start >= window_end:
                window_end = min(target_idx + 20, len(route_geometry))
                window_start = max(last_stop_route_idx + 1, target_idx - 5)

            segment_points = route_geometry[window_start:window_end]
            if not segment_points:
                current_target += MAX_RANGE_MILES
                continue

            # Step 4 — find the cheapest nearby unused station (primary radius)
            best_station = self._find_best_station(
                segment_points, all_stations, used_station_ids, SEARCH_RADIUS_MILES
            )

            # Step 5 — expand search radius if nothing found in primary window
            if best_station is None:
                best_station = self._find_best_station(
                    segment_points, all_stations, used_station_ids, self.EXPANDED_RADIUS_MILES
                )

            # Step 6 — record the stop if found
            if best_station is not None:
                station_id = best_station.get('truckstop_id') or best_station['location']
                used_station_ids.add(station_id)
                # Remember the route index nearest to this stop for forward-progression
                last_stop_route_idx = target_idx

                fuel_stops.append({
                    'sequence': sequence,
                    'location': best_station['location'],
                    'price': best_station['price'],
                    'truckstop_name': best_station.get('truckstop_name', ''),
                    'address': best_station.get('address', ''),
                })
                sequence += 1

            # Step 7 — advance to next segment target
            current_target += MAX_RANGE_MILES

        return fuel_stops

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_route_distances(self, route_geometry: List[List[float]]) -> List[float]:
        """Cumulative Haversine distances (miles) along route_geometry.

        Returns a list of the same length as route_geometry where
        distances[i] is the total road distance from the first point to point i.
        """
        distances = [0.0]
        for i in range(1, len(route_geometry)):
            lon1, lat1 = route_geometry[i - 1]
            lon2, lat2 = route_geometry[i]
            d = haversine_distance(lon1, lat1, lon2, lat2)
            distances.append(distances[-1] + d)
        return distances

    def _find_route_index_at_distance(
        self,
        route_distances: List[float],
        target_dist: float,
        from_index: int,
    ) -> Optional[int]:
        """Binary-search for the first index where cumulative distance >= target_dist.

        Searches only from `from_index` onward to enforce forward progression.
        Returns None if target_dist exceeds the total route length.
        """
        lo, hi = from_index, len(route_distances) - 1
        if route_distances[hi] < target_dist:
            return None  # Target beyond end of route

        result = hi  # Safe default: last point
        while lo <= hi:
            mid = (lo + hi) // 2
            if route_distances[mid] >= target_dist:
                result = mid
                hi = mid - 1
            else:
                lo = mid + 1
        return result

    def _build_distance_window(
        self,
        route_distances: List[float],
        target_dist: float,
        target_idx: int,
        window_miles: float,
    ) -> Tuple[int, int]:
        """Return (start_idx, end_idx) of route points within ±window_miles of target_dist.

        This is a distance-based window, not a fixed index window, so it
        remains meaningful for both dense (many points / mile) and sparse
        (few points / mile) geometries.
        """
        lo_dist = target_dist - window_miles
        hi_dist = target_dist + window_miles

        # Walk left from target_idx to find window start
        start_idx = target_idx
        while start_idx > 0 and route_distances[start_idx - 1] >= lo_dist:
            start_idx -= 1

        # Walk right from target_idx to find window end
        end_idx = target_idx
        while end_idx < len(route_distances) - 1 and route_distances[end_idx + 1] <= hi_dist:
            end_idx += 1

        return start_idx, end_idx + 1  # end is exclusive for slicing

    def _find_best_station(
        self,
        segment_points: List[List[float]],
        all_stations: List[Dict],
        used_station_ids: set,
        radius_miles: float,
    ) -> Optional[Dict]:
        """Find the cheapest unused station within radius_miles of ANY segment point.

        Uses bounding-box filtering and point downsampling for massive speedups on
        dense route geometries, followed by precise haversine checks.
        """
        if not segment_points:
            return None

        # 1. Bounding box for fast initial filtering
        min_lon = min(p[0] for p in segment_points)
        max_lon = max(p[0] for p in segment_points)
        min_lat = min(p[1] for p in segment_points)
        max_lat = max(p[1] for p in segment_points)

        # 1 degree lat is ~69 miles. For lon, it depends on latitude.
        lat_buffer = radius_miles / 69.0
        max_abs_lat = max(abs(min_lat), abs(max_lat))
        lon_buffer = radius_miles / (69.0 * math.cos(math.radians(max_abs_lat)))

        min_lon -= lon_buffer
        max_lon += lon_buffer
        min_lat -= lat_buffer
        max_lat += lat_buffer

        # 2. Downsample segment points to max ~50 points for checking
        # (50 points over a 100-mile window = 1 point every 2 miles, plenty accurate)
        step = max(1, len(segment_points) // 50)
        sampled_points = segment_points[::step]

        nearby: List[Dict] = []

        for station in all_stations:
            station_id = station.get('truckstop_id') or station.get('location')
            if station_id in used_station_ids:
                continue

            s_lon = station.get('longitude')
            s_lat = station.get('latitude')
            if s_lon is None or s_lat is None:
                continue

            # Fast bounding box check
            if not (min_lon <= s_lon <= max_lon and min_lat <= s_lat <= max_lat):
                continue

            # Precise haversine check against sampled points
            for lon, lat in sampled_points:
                if haversine_distance(lon, lat, s_lon, s_lat) <= radius_miles:
                    nearby.append(station)
                    break  # This station qualifies — no need to check more points

        if not nearby:
            return None

        return min(nearby, key=lambda x: x['price'])
