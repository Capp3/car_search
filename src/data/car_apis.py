"""
Car data API integration module.

This module provides functionality to retrieve car data from various
external APIs and normalize it for use in the application.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import json
from pathlib import Path

import requests
from pydantic import BaseModel

from src.config import settings
from src.models import Car, ConfidenceLevel, AttributeType

# Configure logging
logger = logging.getLogger(__name__)


class APIRateLimiter:
    """
    Rate limiter for API requests.
    
    This class helps manage request rates to external APIs to avoid
    hitting rate limits.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute  # Time between requests in seconds
        self.last_request_time = 0
    
    def wait_if_needed(self) -> None:
        """Wait if necessary to comply with the rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.interval:
            # Need to wait
            wait_time = self.interval - time_since_last
            logger.debug(f"Rate limiting: waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()


class CarDataAPI(ABC):
    """
    Base class for car data API integrations.
    
    This abstract class defines the interface for all car data API integrations.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for authentication.
            cache_dir: Directory for caching API responses.
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or settings.app.cache_dir / self.__class__.__name__.lower()
        self.rate_limiter = APIRateLimiter()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def get_make_models(self) -> Dict[str, List[str]]:
        """
        Get a dictionary of car makes and their models.
        
        Returns:
            A dictionary where keys are make names and values are lists of model names.
        """
        pass
    
    @abstractmethod
    def get_car_details(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific car.
        
        Args:
            make: Car make.
            model: Car model.
            year: Car year.
            
        Returns:
            Dictionary of car details if found, None otherwise.
        """
        pass
    
    @abstractmethod
    def get_reliability_data(self, make: str, model: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get reliability data for a specific car.
        
        Args:
            make: Car make.
            model: Car model.
            year: Car year (optional).
            
        Returns:
            Dictionary of reliability data if found, None otherwise.
        """
        pass
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the path to a cached file.
        
        Args:
            cache_key: Unique identifier for the cached data.
            
        Returns:
            Path to the cached file.
        """
        # Sanitize the cache key to create a valid filename
        safe_key = "".join(c if c.isalnum() else "_" for c in cache_key)
        return self.cache_dir / f"{safe_key}.json"
    
    def _get_from_cache(self, cache_key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Get data from the cache if it exists and is not too old.
        
        Args:
            cache_key: Unique identifier for the cached data.
            max_age_hours: Maximum age of cache in hours.
            
        Returns:
            Cached data if valid, None otherwise.
        """
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        # Check if cache is too old
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > max_age_hours * 3600:
            logger.debug(f"Cache too old for {cache_key}: {cache_age:.2f} seconds")
            return None
        
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache for {cache_key}: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Any) -> bool:
        """
        Save data to the cache.
        
        Args:
            cache_key: Unique identifier for the cached data.
            data: Data to cache.
            
        Returns:
            True if successful, False otherwise.
        """
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            logger.warning(f"Error saving cache for {cache_key}: {e}")
            return False


class SmartcarAPI(CarDataAPI):
    """
    Smartcar API integration.
    
    This class provides methods to retrieve car data from the Smartcar API.
    """
    
    BASE_URL = "https://api.smartcar.com/v2.0"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """Initialize the Smartcar API client."""
        super().__init__(
            api_key=api_key or settings.api.smartcar_api_key,
            cache_dir=cache_dir
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Smartcar API.
        
        Args:
            endpoint: API endpoint to call.
            params: Query parameters.
            
        Returns:
            Response data if successful, None otherwise.
        """
        if not self.api_key:
            logger.warning("Smartcar API key not set")
            return None
        
        # Check cache first
        cache_key = f"smartcar_{endpoint}_{json.dumps(params or {})}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Using cached data for {endpoint}")
            return cached_data
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Cache the response
                self._save_to_cache(cache_key, data)
                return data
            else:
                logger.warning(f"Smartcar API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making Smartcar API request: {e}")
            return None
    
    def get_make_models(self) -> Dict[str, List[str]]:
        """Get a dictionary of car makes and their models."""
        # This would call the appropriate Smartcar API endpoint
        # For now, return a placeholder as the actual endpoint might be different
        logger.info("Getting makes and models from Smartcar API")
        
        makes_models = {}
        
        # Call the makes endpoint
        makes_data = self._make_request("makes")
        if not makes_data or "makes" not in makes_data:
            logger.warning("Failed to get makes from Smartcar API")
            return makes_models
        
        # For each make, get the models
        for make in makes_data["makes"]:
            models_data = self._make_request(f"makes/{make}/models")
            if models_data and "models" in models_data:
                makes_models[make] = models_data["models"]
            else:
                makes_models[make] = []
        
        return makes_models
    
    def get_car_details(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific car."""
        logger.info(f"Getting details for {year} {make} {model} from Smartcar API")
        
        # Call the vehicle details endpoint
        details = self._make_request(f"vehicles", {
            "make": make,
            "model": model,
            "year": year
        })
        
        if not details:
            logger.warning(f"Failed to get details for {year} {make} {model} from Smartcar API")
            return None
        
        return details
    
    def get_reliability_data(self, make: str, model: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get reliability data for a specific car."""
        # Smartcar might not have dedicated reliability data
        # This could call a different endpoint or service
        logger.info(f"Getting reliability data for {make} {model} from Smartcar API")
        
        # Placeholder for now
        return None


class EdmundsAPI(CarDataAPI):
    """
    Edmunds API integration.
    
    This class provides methods to retrieve car data from the Edmunds API.
    """
    
    BASE_URL = "https://api.edmunds.com/api/vehicle/v2"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """Initialize the Edmunds API client."""
        super().__init__(
            api_key=api_key or settings.api.edmunds_api_key,
            cache_dir=cache_dir
        )
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Edmunds API.
        
        Args:
            endpoint: API endpoint to call.
            params: Query parameters.
            
        Returns:
            Response data if successful, None otherwise.
        """
        if not self.api_key:
            logger.warning("Edmunds API key not set")
            return None
        
        # Add API key to parameters
        all_params = params.copy() if params else {}
        all_params["api_key"] = self.api_key
        
        # Check cache first
        cache_key = f"edmunds_{endpoint}_{json.dumps(all_params)}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Using cached data for {endpoint}")
            return cached_data
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.get(url, params=all_params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Cache the response
                self._save_to_cache(cache_key, data)
                return data
            else:
                logger.warning(f"Edmunds API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making Edmunds API request: {e}")
            return None
    
    def get_make_models(self) -> Dict[str, List[str]]:
        """Get a dictionary of car makes and their models."""
        logger.info("Getting makes and models from Edmunds API")
        
        makes_models = {}
        
        # Get all makes
        makes_data = self._make_request("makes")
        if not makes_data or "makes" not in makes_data:
            logger.warning("Failed to get makes from Edmunds API")
            return makes_models
        
        # For each make, get the models
        for make_data in makes_data["makes"]:
            make = make_data["name"]
            models = [model["name"] for model in make_data.get("models", [])]
            makes_models[make] = models
        
        return makes_models
    
    def get_car_details(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific car."""
        logger.info(f"Getting details for {year} {make} {model} from Edmunds API")
        
        # Call the vehicle details endpoint
        details = self._make_request(f"{make}/{model}/{year}")
        
        if not details:
            logger.warning(f"Failed to get details for {year} {make} {model} from Edmunds API")
            return None
        
        return details
    
    def get_reliability_data(self, make: str, model: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get reliability data for a specific car."""
        logger.info(f"Getting reliability data for {make} {model} from Edmunds API")
        
        # Construct the endpoint based on whether a year is provided
        endpoint = f"{make}/{model}"
        if year:
            endpoint = f"{endpoint}/{year}"
        endpoint = f"{endpoint}/reliability"
        
        reliability_data = self._make_request(endpoint)
        
        if not reliability_data:
            logger.warning(f"Failed to get reliability data for {make} {model} from Edmunds API")
            return None
        
        return reliability_data


class CarDataManager:
    """
    Manages car data from multiple API sources.
    
    This class coordinates data retrieval from multiple APIs and
    handles caching, normalization, and conflict resolution.
    """
    
    def __init__(self):
        """Initialize the car data manager."""
        # Initialize API clients
        self.apis = {}
        
        # Add Smartcar API if key is available
        if settings.api.smartcar_api_key:
            self.apis["smartcar"] = SmartcarAPI()
        
        # Add Edmunds API if key is available
        if settings.api.edmunds_api_key:
            self.apis["edmunds"] = EdmundsAPI()
        
        # Add other APIs as needed
        
        logger.info(f"Car data manager initialized with {len(self.apis)} APIs")
    
    def enrich_car(self, car: Car) -> Car:
        """
        Enrich a car with additional data from APIs.
        
        This method calls multiple APIs to gather more information about a car
        and adds it to the car's attributes.
        
        Args:
            car: The car to enrich.
            
        Returns:
            The enriched car.
        """
        # Get the basic car information
        make = car.make
        model = car.model
        year = car.year
        
        if not make or not model:
            logger.warning(f"Cannot enrich car without make and model: {car.id}")
            return car
        
        # Call each API to get additional data
        for api_name, api_client in self.apis.items():
            try:
                # Get car details
                if year:
                    details = api_client.get_car_details(make, model, year)
                    if details:
                        self._add_car_details(car, details, api_name)
                
                # Get reliability data
                reliability = api_client.get_reliability_data(make, model, year)
                if reliability:
                    self._add_reliability_data(car, reliability, api_name)
                
            except Exception as e:
                logger.error(f"Error enriching car from {api_name} API: {e}")
        
        return car
    
    def _add_car_details(self, car: Car, details: Dict[str, Any], source: str) -> None:
        """
        Add car details from an API to a car.
        
        Args:
            car: The car to update.
            details: The car details from the API.
            source: The name of the API that provided the details.
        """
        # This would need to be customized based on the actual structure
        # of the data from each API
        for key, value in details.items():
            if value is not None:
                # Determine the attribute type
                attr_type = None
                if isinstance(value, (int, float)):
                    attr_type = AttributeType.NUMBER
                elif isinstance(value, bool):
                    attr_type = AttributeType.BOOLEAN
                elif isinstance(value, list):
                    attr_type = AttributeType.LIST
                else:
                    attr_type = AttributeType.TEXT
                
                # Normalize the attribute name
                norm_key = key.lower().replace(' ', '_')
                
                # Add the attribute
                car.set_attribute(
                    name=norm_key,
                    value=value,
                    source=f"{source}_api",
                    confidence=ConfidenceLevel.HIGH,
                    attr_type=attr_type
                )
    
    def _add_reliability_data(self, car: Car, reliability: Dict[str, Any], source: str) -> None:
        """
        Add reliability data from an API to a car.
        
        Args:
            car: The car to update.
            reliability: The reliability data from the API.
            source: The name of the API that provided the data.
        """
        # Process reliability data, which might have a different structure
        # This is a simplified example
        
        # Add overall reliability score if available
        if 'overallScore' in reliability:
            car.set_attribute(
                name="reliability_score",
                value=reliability['overallScore'],
                source=f"{source}_api",
                confidence=ConfidenceLevel.HIGH,
                attr_type=AttributeType.NUMBER
            )
        
        # Add detailed reliability metrics if available
        if 'categories' in reliability:
            for category in reliability['categories']:
                cat_name = category.get('name', '').lower().replace(' ', '_')
                cat_score = category.get('score')
                
                if cat_name and cat_score is not None:
                    car.set_attribute(
                        name=f"reliability_{cat_name}",
                        value=cat_score,
                        source=f"{source}_api",
                        confidence=ConfidenceLevel.HIGH,
                        attr_type=AttributeType.NUMBER
                    )
    
    def get_makes_models(self) -> Dict[str, List[str]]:
        """
        Get a combined list of car makes and models from all APIs.
        
        Returns:
            A dictionary where keys are make names and values are lists of model names.
        """
        combined = {}
        
        # Gather makes and models from each API
        for api_name, api_client in self.apis.items():
            try:
                makes_models = api_client.get_make_models()
                
                # Merge with combined results
                for make, models in makes_models.items():
                    if make in combined:
                        # Add any new models
                        combined[make] = list(set(combined[make] + models))
                    else:
                        combined[make] = models
                        
            except Exception as e:
                logger.error(f"Error getting makes and models from {api_name} API: {e}")
        
        return combined


# Create a singleton instance of the car data manager
car_data_manager = CarDataManager()
