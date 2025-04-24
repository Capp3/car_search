"""
Motorcheck API client module.

This module provides functionality to interact with the Motorcheck API
to fetch car data, reliability information, and vehicle history.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.car import Car, ConfidenceLevel, AttributeType
from src.services.api_clients.base_api_client import BaseAPIClient

# Configure logging
logger = logging.getLogger(__name__)


class MotorcheckAPIClient(BaseAPIClient):
    """
    Client for interacting with the Motorcheck API.
    """
    
    BASE_URL = "https://api.motorcheck.co.uk/v1"
    
    def __init__(self, api_key: str, cache_ttl: int = 3600):
        """
        Initialize the Motorcheck API client.
        
        Args:
            api_key: Motorcheck API key
            cache_ttl: Time-to-live for cached responses in seconds (default: 1 hour)
        """
        super().__init__(cache_ttl)
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        
        logger.info("Initialized Motorcheck API client")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Motorcheck API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            API response as a dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Check cache first
        cache_key = self._generate_cache_key(url, params)
        cached_response = self._get_from_cache(cache_key)
        if cached_response:
            return cached_response
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self._add_to_cache(cache_key, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Motorcheck API: {str(e)}")
            raise
    
    def get_car_details(self, registration: str) -> Optional[Car]:
        """
        Get detailed information about a specific car using its registration number.
        
        Args:
            registration: Vehicle registration number
            
        Returns:
            Car object with details, or None if not found
        """
        try:
            # Get vehicle details
            details = self._make_request(f"vehicle/{registration}")
            
            if not details:
                logger.warning(f"No details found for registration {registration}")
                return None
            
            # Create a Car object
            car = Car(id=f"motorcheck_{registration}")
            
            # Set basic information
            car.set_attribute("registration", registration, "motorcheck", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("make", details.get("make"), "motorcheck", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("model", details.get("model"), "motorcheck", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("year", details.get("year"), "motorcheck", 
                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Set specifications
            if "specifications" in details:
                specs = details["specifications"]
                
                # Engine information
                if "engine" in specs:
                    engine = specs["engine"]
                    if "size" in engine:
                        car.set_attribute("engine_size", float(engine["size"]), "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
                    if "type" in engine:
                        car.set_attribute("engine_type", engine["type"], "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.TEXT)
                    if "power" in engine:
                        car.set_attribute("horsepower", int(engine["power"]), "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
                
                # Transmission
                if "transmission" in specs:
                    trans = specs["transmission"]
                    if "type" in trans:
                        car.set_attribute("transmission", trans["type"], "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.TEXT)
                
                # Fuel information
                if "fuel" in specs:
                    fuel = specs["fuel"]
                    if "type" in fuel:
                        car.set_attribute("fuel_type", fuel["type"], "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.TEXT)
                    if "mpg" in fuel:
                        car.set_attribute("mpg_combined", float(fuel["mpg"]), "motorcheck", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Set the date the data was fetched
            car.set_attribute("date_fetched", datetime.now().isoformat(), "motorcheck", 
                             ConfidenceLevel.HIGH, AttributeType.DATE)
            
            return car
            
        except Exception as e:
            logger.error(f"Error getting car details from Motorcheck: {str(e)}")
            return None
    
    def get_reliability_data(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get reliability data for a specific car model.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            Dictionary containing reliability data, or None if not found
        """
        try:
            # Get reliability data
            reliability = self._make_request("reliability", {
                "make": make,
                "model": model,
                "year": year
            })
            
            if not reliability:
                logger.warning(f"No reliability data found for {make} {model} {year}")
                return None
            
            return reliability
            
        except Exception as e:
            logger.error(f"Error getting reliability data from Motorcheck: {str(e)}")
            return None
    
    def get_vehicle_history(self, registration: str) -> Optional[Dict[str, Any]]:
        """
        Get vehicle history for a specific car.
        
        Args:
            registration: Vehicle registration number
            
        Returns:
            Dictionary containing vehicle history, or None if not found
        """
        try:
            # Get vehicle history
            history = self._make_request(f"vehicle/{registration}/history")
            
            if not history:
                logger.warning(f"No history found for registration {registration}")
                return None
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting vehicle history from Motorcheck: {str(e)}")
            return None 