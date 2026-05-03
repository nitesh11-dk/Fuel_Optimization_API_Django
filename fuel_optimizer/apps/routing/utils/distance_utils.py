from core.constants import MAX_RANGE_MILES


def calculate_segments(total_distance: float) -> int:
    """
    Calculate number of fuel segments needed
    """
    segments = int(total_distance / MAX_RANGE_MILES)
    if total_distance % MAX_RANGE_MILES > 0:
        segments += 1
    return max(0, segments - 1)  # Subtract 1 because we start with full tank
