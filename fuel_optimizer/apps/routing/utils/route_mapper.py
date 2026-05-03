"""
Route state mapper for segment-based filtering
Maps common US routes to the states they pass through
"""

from typing import List, Dict, Tuple


class RouteStateMapper:
    """Maps routes to states for geographic filtering"""
    
    # Common US cross-country routes with state sequences
    ROUTE_STATES = {
        # East Coast to West Coast routes
        'ny_to_la': ['NY', 'PA', 'OH', 'IN', 'IL', 'MO', 'KS', 'CO', 'UT', 'NV', 'CA'],
        'ny_to_sf': ['NY', 'PA', 'OH', 'IN', 'IL', 'IA', 'NE', 'WY', 'UT', 'NV', 'CA'],
        'boston_to_la': ['MA', 'NY', 'PA', 'OH', 'IN', 'IL', 'MO', 'KS', 'CO', 'UT', 'NV', 'CA'],
        'boston_to_sf': ['MA', 'NY', 'PA', 'OH', 'IN', 'IL', 'IA', 'NE', 'WY', 'UT', 'NV', 'CA'],
        
        # Midwest to West Coast
        'chicago_to_la': ['IL', 'IA', 'NE', 'CO', 'UT', 'NV', 'CA'],
        'chicago_to_sf': ['IL', 'IA', 'NE', 'WY', 'UT', 'NV', 'CA'],
        'dallas_to_la': ['TX', 'NM', 'AZ', 'CA'],
        'houston_to_la': ['TX', 'NM', 'AZ', 'CA'],
        
        # East Coast to South
        'ny_to_miami': ['NY', 'NJ', 'DE', 'MD', 'VA', 'NC', 'SC', 'GA', 'FL'],
        'boston_to_miami': ['MA', 'NY', 'NJ', 'DE', 'MD', 'VA', 'NC', 'SC', 'GA', 'FL'],
        
        # Midwest to South
        'chicago_to_miami': ['IL', 'IN', 'KY', 'TN', 'GA', 'FL'],
        
        # West Coast routes
        'seattle_to_la': ['WA', 'OR', 'CA'],
        'seattle_to_sf': ['WA', 'OR', 'CA'],
        'sf_to_la': ['CA'],
        
        # North-South routes
        'ny_to_atlanta': ['NY', 'NJ', 'PA', 'MD', 'VA', 'NC', 'SC', 'GA'],
        'chicago_to_atlanta': ['IL', 'IN', 'KY', 'TN', 'GA'],
    }
    
    # City to route mapping
    CITY_ROUTES = {
        # East Coast
        'new york': ['ny_to_la', 'ny_to_sf', 'ny_to_miami', 'ny_to_atlanta'],
        'boston': ['boston_to_la', 'boston_to_sf', 'boston_to_miami'],
        'philadelphia': ['ny_to_la', 'ny_to_sf', 'ny_to_miami'],
        
        # Midwest
        'chicago': ['chicago_to_la', 'chicago_to_sf', 'chicago_to_miami', 'chicago_to_atlanta'],
        'detroit': ['chicago_to_la', 'chicago_to_sf'],
        
        # South
        'atlanta': ['ny_to_atlanta', 'chicago_to_atlanta'],
        'miami': ['ny_to_miami', 'boston_to_miami', 'chicago_to_miami'],
        
        # Texas
        'houston': ['houston_to_la', 'dallas_to_la'],
        'dallas': ['dallas_to_la', 'houston_to_la'],
        
        # West Coast
        'los angeles': ['ny_to_la', 'boston_to_la', 'chicago_to_la', 'dallas_to_la', 'houston_to_la', 'seattle_to_la', 'sf_to_la'],
        'san francisco': ['ny_to_sf', 'boston_to_sf', 'chicago_to_sf', 'seattle_to_sf', 'sf_to_la'],
        'seattle': ['seattle_to_la', 'seattle_to_sf'],
        
        # Mountain
        'denver': ['ny_to_la', 'ny_to_sf', 'chicago_to_la', 'chicago_to_sf'],
    }
    
    @classmethod
    def get_route_states(cls, start_location: str, end_location: str) -> List[str]:
        """
        Get the sequence of states for a route
        Returns a list of state codes in order
        """
        start_lower = start_location.lower()
        end_lower = end_location.lower()
        
        # Find matching routes
        start_routes = []
        for city, routes in cls.CITY_ROUTES.items():
            if city in start_lower:
                start_routes.extend(routes)
        
        end_routes = []
        for city, routes in cls.CITY_ROUTES.items():
            if city in end_lower:
                end_routes.extend(routes)
        
        # Find common route
        common_route = None
        for route in start_routes:
            if route in end_routes:
                common_route = route
                break
        
        # If no exact match, use default east-west route
        if not common_route:
            # Determine direction based on cities
            if 'la' in end_lower or 'san francisco' in end_lower:
                common_route = 'ny_to_la'
            elif 'miami' in end_lower:
                common_route = 'ny_to_miami'
            else:
                common_route = 'ny_to_la'
        
        return cls.ROUTE_STATES.get(common_route, ['NY', 'PA', 'OH', 'IN', 'IL', 'MO', 'KS', 'CO', 'UT', 'NV', 'CA'])
    
    @classmethod
    def get_state_for_segment(cls, route_states: List[str], segment_index: int, total_segments: int) -> str:
        """
        Get the state for a specific segment
        Distributes segments across states
        """
        if not route_states:
            return 'CA'
        
        # Map segment to state index
        state_index = min(segment_index, len(route_states) - 1)
        return route_states[state_index]
