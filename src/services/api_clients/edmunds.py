"""
Edmunds API client module.

This module provides functionality to interact with the Edmunds API
to fetch car data, specifications, reviews, and market value information.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.car import Car, ConfidenceLevel, AttributeType
from src.services.api_clients.base_api_client import BaseAPIClient

# Configure logging
logger = logging.getLogger(__name__)


class EdmundsAPIClient(BaseAPIClient):
    """
    Client for interacting with the Edmunds API.
    """
    
    BASE_URL = "https://api.edmunds.com/api/vehicle/v2"
    
    def __init__(self, api_key: str, cache_ttl: int = 3600):
        """
        Initialize the Edmunds API client.
        
        Args:
            api_key: Edmunds API key
            cache_ttl: Time-to-live for cached responses in seconds (default: 1 hour)
        """
        super().__init__(cache_ttl)
        self.api_key = api_key
        self.session = requests.Session()
        
        logger.info("Initialized Edmunds API client")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Edmunds API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            API response as a dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Add API key to parameters
        params = params or {}
        params["api_key"] = self.api_key
        params["fmt"] = "json"
        
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
            logger.error(f"Error making request to Edmunds API: {str(e)}")
            raise
    
    def get_makes(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get a list of car makes.
        
        Args:
            year: Optional year to filter makes
            
        Returns:
            List of car makes
        """
        try:
            params = {}
            if year:
                params["year"] = year
            
            data = self._make_request("makes", params)
            
            if "makes" in data:
                return data["makes"]
            return []
            
        except Exception as e:
            logger.error(f"Error getting makes from Edmunds: {str(e)}")
            return []
    
    def get_models(self, make: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get a list of models for a specific make.
        
        Args:
            make: Car make
            year: Optional year to filter models
            
        Returns:
            List of car models
        """
        try:
            endpoint = f"makes/{make}/models"
            params = {}
            if year:
                params["year"] = year
            
            data = self._make_request(endpoint, params)
            
            if "models" in data:
                return data["models"]
            return []
            
        except Exception as e:
            logger.error(f"Error getting models from Edmunds: {str(e)}")
            return []
    
    def get_car_details(self, make: str, model: str, year: int) -> Optional[Car]:
        """
        Get detailed information about a specific car.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            Car object with details, or None if not found
        """
        try:
            endpoint = f"makes/{make}/models/{model}/years/{year}"
            data = self._make_request(endpoint)
            
            if not data:
                logger.warning(f"No details found for {make} {model} {year}")
                return None
            
            # Create a Car object
            car = Car(id=f"edmunds_{make}_{model}_{year}")
            
            # Set basic information
            car.set_attribute("make", make, "edmunds", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("model", model, "edmunds", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("year", year, "edmunds", 
                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Extract and set additional attributes
            if "styles" in data and data["styles"]:
                style = data["styles"][0]  # Use the first style
                
                if "name" in style:
                    car.set_attribute("trim", style["name"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
                
                if "id" in style:
                    car.set_attribute("style_id", style["id"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
            
            if "engine" in data:
                engine = data["engine"]
                if "name" in engine:
                    car.set_attribute("engine_name", engine["name"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
                if "cylinder" in engine:
                    car.set_attribute("cylinders", engine["cylinder"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.NUMBER)
                if "size" in engine:
                    car.set_attribute("engine_size", engine["size"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            if "transmission" in data:
                transmission = data["transmission"]
                if "transmissionType" in transmission:
                    car.set_attribute("transmission", transmission["transmissionType"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
            
            if "mpg" in data:
                mpg = data["mpg"]
                if "highway" in mpg:
                    car.set_attribute("mpg_highway", mpg["highway"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.NUMBER)
                if "city" in mpg:
                    car.set_attribute("mpg_city", mpg["city"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Set the date the data was fetched
            car.set_attribute("date_fetched", datetime.now().isoformat(), "edmunds", 
                             ConfidenceLevel.HIGH, AttributeType.DATE)
            
            return car
            
        except Exception as e:
            logger.error(f"Error getting car details from Edmunds: {str(e)}")
            return None
    
    def get_car_reviews(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get reviews for a specific car.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            Dictionary containing review data, or None if not found
        """
        try:
            endpoint = f"makes/{make}/models/{model}/years/{year}/reviews"
            data = self._make_request(endpoint)
            
            if not data:
                logger.warning(f"No reviews found for {make} {model} {year}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting car reviews from Edmunds: {str(e)}")
            return None
    
    def get_car_safety(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get safety information for a specific car.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            Dictionary containing safety data, or None if not found
        """
        try:
            endpoint = f"makes/{make}/models/{model}/years/{year}/safety"
            data = self._make_request(endpoint)
            
            if not data:
                logger.warning(f"No safety information found for {make} {model} {year}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting car safety from Edmunds: {str(e)}")
            return None
    
    def get_car_tco(self, style_id: str, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Get True Cost to Own® information for a specific car.
        
        Args:
            style_id: Edmunds style ID
            zip_code: ZIP code for localized data
            
        Returns:
            Dictionary containing TCO data, or None if not found
        """
        try:
            endpoint = f"styles/{style_id}/tco"
            params = {"zip": zip_code}
            
            data = self._make_request(endpoint, params)
            
            if not data:
                logger.warning(f"No TCO information found for style {style_id}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting car TCO from Edmunds: {str(e)}")
            return None
    
    def enrich_car(self, car: Car) -> Car:
        """
        Enrich a car object with additional data from Edmunds.
        
        Args:
            car: Car object to enrich
            
        Returns:
            Enriched car object
        """
        make = car.make
        model = car.model
        year = car.year
        
        if not make or not model or not year:
            logger.warning("Cannot enrich car without make, model, and year")
            return car
        
        try:
            # Get details
            details = self.get_car_details(make, model, year)
            
            if details:
                # Merge the attributes from details into the original car
                for attr_name, attribute in details.attributes.items():
                    if attr_name not in car.attributes:
                        car.attributes[attr_name] = attribute
                    else:
                        # If attribute already exists, add the new sources
                        for source_name, source in attribute.sources.items():
                            car.attributes[attr_name].sources[source_name] = source
            
            # Get reviews
            reviews = self.get_car_reviews(make, model, year)
            if reviews:
                car.set_attribute("reviews", reviews, "edmunds")
                
                # Extract overall rating if available
                if "rating" in reviews:
                    car.set_attribute("expert_rating", reviews["rating"], "edmunds", 
                                     ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Get safety information
            safety = self.get_car_safety(make, model, year)
            if safety:
                car.set_attribute("safety_data", safety, "edmunds")
                
                # Extract safety ratings if available
                if "nhtsa" in safety:
                    nhtsa = safety["nhtsa"]
                    if "overall" in nhtsa:
                        car.set_attribute("safety_rating", nhtsa["overall"], "edmunds", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Get TCO data if style_id is available
            style_id = car.get_attribute("style_id")
            
            if style_id:
                # Use a default ZIP code if not available
                zip_code = car.get_attribute("zip_code") or "90019"  # Default to Los Angeles
                
                tco = self.get_car_tco(style_id, zip_code)
                if tco:
                    car.set_attribute("tco_data", tco, "edmunds")
                    
                    # Extract key TCO metrics if available
                    if "values" in tco:
                        values = tco["values"]
                        
                        if "totalCash" in values:
                            car.set_attribute("total_cost", values["totalCash"], "edmunds", 
                                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
                        
                        if "depreciation" in values:
                            car.set_attribute("depreciation", values["depreciation"], "edmunds", 
                                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
                        
                        if "maintenance" in values:
                            car.set_attribute("maintenance_cost", values["maintenance"], "edmunds", 
                                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            logger.debug(f"Successfully enriched car {make} {model} {year} with Edmunds data")
            return car
            
        except Exception as e:
            logger.error(f"Error enriching car with Edmunds data: {str(e)}")
            return car 