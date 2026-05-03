"""
Simple in-memory cache for fuel station data
"""
from functools import lru_cache


class SimpleCache:
    """Simple in-memory cache using LRU strategy"""
    
    def __init__(self, maxsize=128):
        self.cache = {}
        self.maxsize = maxsize
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        if len(self.cache) >= self.maxsize:
            # Remove oldest item (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()


# Global cache instance
fuel_cache = SimpleCache(maxsize=1000)
