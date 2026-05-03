class FuelOptimizerException(Exception):
    """Base exception for fuel optimizer"""
    pass


class RouteNotFoundException(FuelOptimizerException):
    """Raised when route cannot be found"""
    pass


class FuelDataException(FuelOptimizerException):
    """Raised when fuel data is missing or invalid"""
    pass


class ExternalAPIException(FuelOptimizerException):
    """Raised when external API call fails"""
    pass


class OptimizationException(FuelOptimizerException):
    """Raised when route optimization fails"""
    pass
