"""
Base API client module.

This module provides a base class for API clients with common functionality
like request handling and caching.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

# Configure logging
logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base class for API clients with common functionality.
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the base API client.
        
        Args:
            cache_ttl: Time-to-live for cached responses in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized base API client")
    
    def _generate_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key for a request.
        
        Args:
            url: Request URL
            params: Request parameters
            
        Returns:
            Cache key string
        """
        # Create a string representation of the request
        request_str = f"{url}"
        if params:
            request_str += f"?{json.dumps(params, sort_keys=True)}"
        
        # Hash the request string to create a cache key
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a response from the cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response if valid, None otherwise
        """
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            cache_time = datetime.fromisoformat(cache_entry["timestamp"])
            
            # Check if the cache entry is still valid
            if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for key: {cache_key}")
                return cache_entry["data"]
            
            # Remove expired cache entry
            del self._cache[cache_key]
        
        return None
    
    def _add_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Add a response to the cache.
        
        Args:
            cache_key: Cache key
            data: Response data to cache
        """
        self._cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        logger.debug(f"Added response to cache with key: {cache_key}")
    
    def clear_cache(self) -> None:
        """
        Clear the cache.
        """
        self._cache.clear()
        logger.info("Cleared API response cache") 