"""Search service for managing car search operations.

This module provides a service for managing car search operations, including
caching, history, and result processing.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from ..config.manager import config_manager
from ..core.logging import get_logger
from ..models.car_data import CarListingData
from ..models.search_parameters import SearchParameters
from .search_providers import AutoTraderProvider

# Set up logger for this module
logger = get_logger(__name__)

# Cache directory
CACHE_DIR = Path.home() / ".car_search" / "cache"
# Search history directory
HISTORY_DIR = Path.home() / ".car_search" / "history"


class SearchService:
    """Service for managing car search operations."""

    def __init__(self):
        """Initialize the search service."""
        # Create the AutoTrader provider
        self.autotrader_provider = AutoTraderProvider()

        # Cache expiry time in seconds (default 1 hour)
        self.cache_expiry = config_manager.get_setting("search.cache_expiry") or 3600

        # Create cache and history directories
        self._ensure_directories()

        logger.info("Initialized search service")

    def _ensure_directories(self):
        """Ensure that cache and history directories exist."""
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(HISTORY_DIR, exist_ok=True)

    async def search(self, parameters: SearchParameters) -> List[CarListingData]:
        """Search for cars using the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            List of car listing data objects
        """
        # Check cache first
        cached_results = self._get_cached_results(parameters)
        if cached_results:
            logger.info("Using cached search results")
            return cached_results

        # If not in cache, perform search
        logger.info(f"Performing search with parameters: {parameters}")
        results = await self.autotrader_provider.search(parameters)

        # Cache results if successful
        if results:
            self._cache_results(parameters, results)
            self._save_to_history(parameters, len(results))

        return results

    def construct_search_url(self, parameters: SearchParameters) -> str:
        """Construct a search URL from the provided parameters.

        Args:
            parameters: Search parameters

        Returns:
            Search URL
        """
        return self.autotrader_provider.construct_search_url(parameters)

    def _get_cache_path(self, parameters: SearchParameters) -> Path:
        """Get cache file path for the given parameters.

        Args:
            parameters: Search parameters

        Returns:
            Path to cache file
        """
        # Create a cache key from the parameters
        params_dict = parameters.model_dump_json()
        import hashlib

        cache_key = hashlib.md5(params_dict.encode()).hexdigest()

        return CACHE_DIR / f"{cache_key}.json"

    def _get_cached_results(self, parameters: SearchParameters) -> Optional[List[CarListingData]]:
        """Get cached search results for the given parameters if available and not expired.

        Args:
            parameters: Search parameters

        Returns:
            List of car listing data objects or None if not in cache or expired
        """
        cache_path = self._get_cache_path(parameters)

        if not cache_path.exists():
            return None

        # Check if cache is expired
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > self.cache_expiry:
            logger.debug(f"Cache expired (age: {cache_age:.1f}s, expiry: {self.cache_expiry}s)")
            return None

        try:
            # Load cache data
            with open(cache_path) as f:
                cache_data = json.load(f)

            # Convert to CarListingData objects
            results = [CarListingData.model_validate(item) for item in cache_data]
            logger.debug(f"Loaded {len(results)} results from cache")

            return results

        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _cache_results(self, parameters: SearchParameters, results: List[CarListingData]):
        """Cache search results for the given parameters.

        Args:
            parameters: Search parameters
            results: Search results to cache
        """
        cache_path = self._get_cache_path(parameters)

        try:
            # Convert results to JSON-serializable dictionaries
            results_data = [item.model_dump() for item in results]

            # Save to cache file
            with open(cache_path, "w") as f:
                json.dump(results_data, f, default=str)

            logger.debug(f"Cached {len(results)} results to {cache_path}")

        except Exception as e:
            logger.error(f"Error caching results: {e}")

    def _save_to_history(self, parameters: SearchParameters, result_count: int):
        """Save search parameters to history with timestamp.

        Args:
            parameters: Search parameters
            result_count: Number of results found
        """
        try:
            # Create a history entry
            timestamp = datetime.now().isoformat()
            history_entry = {
                "timestamp": timestamp,
                "parameters": parameters.model_dump(),
                "result_count": result_count,
            }

            # Create a unique filename based on timestamp
            filename = f"search_{timestamp.replace(':', '-')}.json"
            history_path = HISTORY_DIR / filename

            # Save to history file
            with open(history_path, "w") as f:
                json.dump(history_entry, f, default=str)

            logger.debug(f"Saved search to history: {history_path}")

        except Exception as e:
            logger.error(f"Error saving to history: {e}")

    def get_recent_searches(self, limit: int = 10) -> List[Tuple[datetime, SearchParameters, int]]:
        """Get recent searches from history.

        Args:
            limit: Maximum number of searches to return

        Returns:
            List of tuples containing (timestamp, parameters, result_count)
        """
        try:
            # List all history files
            history_files = list(HISTORY_DIR.glob("search_*.json"))

            # Sort by modification time (most recent first)
            history_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Limit to requested number
            history_files = history_files[:limit]

            recent_searches = []
            for file_path in history_files:
                try:
                    with open(file_path) as f:
                        history_entry = json.load(f)

                    timestamp = datetime.fromisoformat(history_entry["timestamp"])
                    parameters = SearchParameters.model_validate(history_entry["parameters"])
                    result_count = history_entry.get("result_count", 0)

                    recent_searches.append((timestamp, parameters, result_count))

                except Exception as e:
                    logger.error(f"Error loading history entry {file_path}: {e}")
                    continue

            return recent_searches

        except Exception as e:
            logger.error(f"Error getting recent searches: {e}")
            return []

    def clear_cache(self):
        """Clear the search cache."""
        try:
            # Remove all cache files
            for cache_file in CACHE_DIR.glob("*.json"):
                os.remove(cache_file)

            logger.info("Search cache cleared")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# Create a singleton instance
search_service = SearchService()
