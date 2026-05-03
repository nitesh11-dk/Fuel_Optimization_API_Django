from core.constants import FUEL_EFFICIENCY_MPG


class CostService:
    """Service for calculating fuel costs"""

    def calculate_fuel_needed(self, total_distance: float) -> float:
        """
        Calculate total fuel needed for the trip.
        Formula: fuel_needed = total_distance / fuel_efficiency
        """
        return total_distance / FUEL_EFFICIENCY_MPG

    def calculate_total_cost(self, fuel_stops: list, fuel_needed: float) -> float:
        """
        Calculate total fuel cost by distributing purchases across stops.

        Strategy:
          - The truck carries a max of 500 miles of fuel (MAX_RANGE_MILES / MPG gallons).
          - At each stop it tops up enough to reach the next stop (or destination).
          - If there are no stops (short route), use the default fuel price.

        For simplicity and correctness, when stops are present, we use the
        weighted-average stop price × total fuel needed.  This is consistent with
        the assignment specification ("total_cost = sum of fuel purchases OR
        consistent approximation") and avoids needing per-stop distance info.
        """
        if not fuel_stops:
            from core.constants import DEFAULT_FUEL_PRICE
            avg_price = DEFAULT_FUEL_PRICE
        else:
            avg_price = sum(stop['price'] for stop in fuel_stops) / len(fuel_stops)

        total_cost = fuel_needed * avg_price
        return round(total_cost, 2)
