"""
Smartcar API client module.

This module provides functionality to interact with the Smartcar API
to fetch car data and specifications.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64
import urllib.parse

from src.models.car import Car, ConfidenceLevel, AttributeType
from src.services.api_clients.base_api_client import BaseAPIClient

# Configure logging
logger = logging.getLogger(__name__)


class SmartcarAPIClient(BaseAPIClient):
    """
    Client for interacting with the Smartcar API.
    """
    
    BASE_URL = "https://api.smartcar.com/v2.0"
    AUTH_URL = "https://auth.smartcar.com/oauth/token"
    CONNECT_URL = "https://connect.smartcar.com/oauth/authorize"
    
    def __init__(self, api_key: str, client_secret: str = "", cache_ttl: int = 3600, redirect_uri: str = ""):
        """
        Initialize the Smartcar API client.
        
        Args:
            api_key: Smartcar API key (client_id)
            client_secret: Smartcar client secret (required for OAuth)
            cache_ttl: Time-to-live for cached responses in seconds (default: 1 hour)
            redirect_uri: Redirect URI for OAuth authentication
        """
        super().__init__(cache_ttl)
        self.api_key = api_key
        self.client_secret = client_secret if client_secret else ""
        self.redirect_uri = redirect_uri if redirect_uri else ""
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        })
        self.access_token = ""
        self.token_expiry = None
        
        logger.info("Initialized Smartcar API client")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Smartcar API.
        
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
            logger.error(f"Error making request to Smartcar API: {str(e)}")
            raise
    
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
            # Search for the car
            search_params = {
                "make": make,
                "model": model,
                "year": year
            }
            
            # First, try to get the car ID
            search_response = self._make_request("vehicles/search", search_params)
            
            if not search_response.get("vehicles"):
                logger.warning(f"No vehicles found for {make} {model} {year}")
                return None
            
            # Get the first matching vehicle
            vehicle_id = search_response["vehicles"][0]["id"]
            
            # Get detailed information
            details = self._make_request(f"vehicles/{vehicle_id}")
            
            # Create a Car object
            car = Car(id=f"smartcar_{vehicle_id}")
            
            # Set basic information
            car.set_attribute("title", f"{make} {model} {year}", "smartcar", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("make", make, "smartcar", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("model", model, "smartcar", 
                             ConfidenceLevel.HIGH, AttributeType.TEXT)
            car.set_attribute("year", year, "smartcar", 
                             ConfidenceLevel.HIGH, AttributeType.NUMBER)
            
            # Set specifications
            if "specifications" in details:
                specs = details["specifications"]
                
                # Engine information
                if "engine" in specs:
                    engine = specs["engine"]
                    if "size" in engine:
                        car.set_attribute("engine_size", float(engine["size"]), "smartcar", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
                    if "type" in engine:
                        car.set_attribute("engine_type", engine["type"], "smartcar", 
                                         ConfidenceLevel.HIGH, AttributeType.TEXT)
                
                # Transmission
                if "transmission" in specs:
                    car.set_attribute("transmission", specs["transmission"], "smartcar", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
                
                # Fuel information
                if "fuel" in specs:
                    fuel = specs["fuel"]
                    if "type" in fuel:
                        car.set_attribute("fuel_type", fuel["type"], "smartcar", 
                                         ConfidenceLevel.HIGH, AttributeType.TEXT)
                    if "mpg" in fuel:
                        car.set_attribute("mpg", float(fuel["mpg"]), "smartcar", 
                                         ConfidenceLevel.HIGH, AttributeType.NUMBER)
                
                # Body type
                if "body" in specs:
                    car.set_attribute("body_type", specs["body"], "smartcar", 
                                     ConfidenceLevel.HIGH, AttributeType.TEXT)
            
            # Set the date the data was fetched
            car.set_attribute("date_fetched", datetime.now().isoformat(), "smartcar", 
                             ConfidenceLevel.HIGH, AttributeType.DATE)
            
            return car
            
        except Exception as e:
            logger.error(f"Error getting car details from Smartcar: {str(e)}")
            return None
    
    def get_reliability_data(self, make: str, model: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get reliability data for a specific car.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            Dictionary containing reliability data, or None if not found
        """
        try:
            # Search for the car
            search_params = {
                "make": make,
                "model": model,
                "year": year
            }
            
            # Get reliability data
            reliability_response = self._make_request("reliability", search_params)
            
            if not reliability_response:
                logger.warning(f"No reliability data found for {make} {model} {year}")
                return None
            
            return reliability_response
            
        except Exception as e:
            logger.error(f"Error getting reliability data from Smartcar: {str(e)}")
            return None
    
    def get_maintenance_schedule(self, make: str, model: str, year: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get maintenance schedule for a specific car.
        
        Args:
            make: Car make
            model: Car model
            year: Manufacturing year
            
        Returns:
            List of maintenance items, or None if not found
        """
        try:
            # Search for the car
            search_params = {
                "make": make,
                "model": model,
                "year": year
            }
            
            # Get maintenance schedule
            maintenance_response = self._make_request("maintenance", search_params)
            
            if not maintenance_response:
                logger.warning(f"No maintenance schedule found for {make} {model} {year}")
                return None
            
            return maintenance_response.get("schedule", [])
            
        except Exception as e:
            logger.error(f"Error getting maintenance schedule from Smartcar: {str(e)}")
            return None
            
    # New methods for real-time vehicle data
    
    def get_auth_url(self, scopes: List[str], state: str = None) -> str:
        """
        Generate an authorization URL for connecting to a vehicle.
        
        Args:
            scopes: List of permission scopes to request
            state: Optional state parameter for OAuth
            
        Returns:
            Authorization URL for the user to initiate the connection
        """
        if not self.redirect_uri:
            raise ValueError("Redirect URI is required for authentication")
            
        params = {
            'response_type': 'code',
            'client_id': self.api_key,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'approval_prompt': 'auto'
        }
        
        if state:
            params['state'] = state
            
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{self.CONNECT_URL}?{query_string}"
        
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token.
        
        Args:
            code: Authorization code received from the redirect
            
        Returns:
            Dictionary containing the access token and related information
        """
        if not self.client_secret or not self.redirect_uri:
            raise ValueError("Client secret and redirect URI are required for token exchange")
            
        auth_header = base64.b64encode(f"{self.api_key}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(self.AUTH_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Store the access token and expiry time
            self.access_token = token_data.get('access_token', "")
            expires_in = token_data.get('expires_in', 7200)  # Default to 2 hours
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Update the session headers with the new access token
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            Dictionary containing the new access token and related information
        """
        if not self.client_secret:
            raise ValueError("Client secret is required for token refresh")
            
        auth_header = base64.b64encode(f"{self.api_key}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        try:
            response = requests.post(self.AUTH_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Store the access token and expiry time
            self.access_token = token_data.get('access_token', "")
            expires_in = token_data.get('expires_in', 7200)  # Default to 2 hours
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Update the session headers with the new access token
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """
        Get a list of connected vehicles.
        
        Returns:
            List of vehicle information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            response = self._make_request("vehicles")
            return response.get("vehicles", [])
            
        except Exception as e:
            logger.error(f"Error getting vehicles: {str(e)}")
            raise
    
    def get_vehicle_info(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get information about a specific connected vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with vehicle information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error getting vehicle info: {str(e)}")
            raise
    
    def get_vehicle_location(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get the current location of a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with location information including latitude and longitude
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/location")
            
        except Exception as e:
            logger.error(f"Error getting vehicle location: {str(e)}")
            raise
    
    def get_vehicle_odometer(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get the current odometer reading of a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with odometer information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/odometer")
            
        except Exception as e:
            logger.error(f"Error getting vehicle odometer: {str(e)}")
            raise
    
    def get_vehicle_fuel(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get the current fuel level of a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with fuel information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/fuel")
            
        except Exception as e:
            logger.error(f"Error getting vehicle fuel: {str(e)}")
            raise
    
    def get_vehicle_battery(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get the current battery level of an electric vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with battery information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/battery")
            
        except Exception as e:
            logger.error(f"Error getting vehicle battery: {str(e)}")
            raise
    
    def get_vehicle_tires(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get tire pressure information for a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with tire pressure information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/tires/pressure")
            
        except Exception as e:
            logger.error(f"Error getting vehicle tire pressure: {str(e)}")
            raise
    
    def get_vehicle_engine_oil(self, vehicle_id: str) -> Dict[str, Any]:
        """
        Get engine oil information for a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dictionary with engine oil information
        """
        if not self.access_token:
            raise ValueError("Access token is required. Use exchange_code_for_token first.")
        
        try:
            return self._make_request(f"vehicles/{vehicle_id}/engine/oil")
            
        except Exception as e:
            logger.error(f"Error getting vehicle engine oil: {str(e)}")
            raise 