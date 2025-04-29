"""API clients for car data services.

This module provides clients for external car data APIs including API Ninjas Cars API
and Consumer Reports API.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel

from ..config.manager import config_manager
from ..core.logging import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class CarData(BaseModel):
    """Base model for car data."""

    make: str
    model: str
    year: int
    transmission: Optional[str] = None
    drive: Optional[str] = None
    fuel_type: Optional[str] = None
    cylinders: Optional[int] = None
    displacement: Optional[float] = None
    class_type: Optional[str] = None
    city_mpg: Optional[int] = None
    highway_mpg: Optional[int] = None
    combination_mpg: Optional[int] = None
    reliability_score: Optional[float] = None
    safety_score: Optional[float] = None
    owner_satisfaction: Optional[float] = None
    ownership_costs: Optional[Dict[str, float]] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None


class CarApiError(Exception):
    """Exception raised for errors in the car API clients."""

    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, endpoint: Optional[str] = None):
        """Initialize the exception.

        Args:
            message: Error message
            api_name: Name of the API where the error occurred
            status_code: HTTP status code (if applicable)
            endpoint: API endpoint that was called (if applicable)
        """
        self.api_name = api_name
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(f"{api_name} API Error: {message}")


class CarApiClient(ABC):
    """Abstract base class for car API clients."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API client.

        Args:
            api_key: API key for the service.
        """
        self.api_key = api_key

        # Set up rate limiting
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Default 1 second between requests

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
        self.retry_backoff_factor = 1.5

    def _handle_rate_limit(self):
        """Handle rate limiting to avoid overloading APIs."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting applied, sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_on_codes: Optional[List[int]] = None,
    ) -> requests.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (get, post, etc.)
            url: Request URL
            headers: HTTP headers
            params: Query parameters
            data: Request body (for POST requests)
            retry_on_codes: List of status codes to retry on

        Returns:
            Response object

        Raises:
            CarApiError: If the request fails after all retries
        """
        if retry_on_codes is None:
            retry_on_codes = [429, 500, 502, 503, 504]  # Default retry on rate limit and server errors

        self._handle_rate_limit()

        api_name = self.__class__.__name__
        retries = 0
        last_exception = None

        while retries <= self.max_retries:
            try:
                if method.lower() == "get":
                    response = requests.get(url, headers=headers, params=params)
                elif method.lower() == "post":
                    response = requests.post(url, headers=headers, params=params, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Log the request details at debug level
                logger.debug(f"{api_name} API request: {method} {url} with params={params}")

                # Check if we need to retry based on status code
                if response.status_code in retry_on_codes and retries < self.max_retries:
                    wait_time = self.retry_delay * (self.retry_backoff_factor**retries)
                    logger.warning(
                        f"{api_name} API returned status {response.status_code}, retrying in {wait_time:.1f}s (retry {retries + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    retries += 1
                    continue

                # If not retrying, raise for status to catch other errors
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                last_exception = e

                # Determine if we should retry
                if retries < self.max_retries:
                    wait_time = self.retry_delay * (self.retry_backoff_factor**retries)
                    logger.warning(
                        f"{api_name} API request failed: {e!s}. Retrying in {wait_time:.1f}s (retry {retries + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    retries += 1
                else:
                    # Final failure after all retries
                    status_code = e.response.status_code if hasattr(e, "response") and e.response else None
                    raise CarApiError(str(e), api_name, status_code, url) from e

        # Should not reach here, but just in case
        if last_exception:
            raise CarApiError(str(last_exception), api_name, None, url) from last_exception
        raise CarApiError("Unknown error during API request", api_name, None, url)

    @abstractmethod
    def search_cars(self, **kwargs) -> List[CarData]:
        """Search for cars based on the provided parameters.

        Args:
            **kwargs: Search parameters.

        Returns:
            List of CarData objects matching the search criteria.
        """
        pass

    @abstractmethod
    def get_car_details(self, make: str, model: str, year: int) -> Optional[CarData]:
        """Get detailed information about a specific car.

        Args:
            make: Car manufacturer.
            model: Car model.
            year: Car year.

        Returns:
            CarData object with detailed information or None if not found.
        """
        pass

    @abstractmethod
    def get_makes(self, year: Optional[int] = None) -> List[str]:
        """Get a list of car manufacturers.

        Args:
            year: Optional year to filter by.

        Returns:
            List of car manufacturers.
        """
        pass

    @abstractmethod
    def get_models(self, make: str, year: Optional[int] = None) -> List[str]:
        """Get a list of car models for a specific manufacturer.

        Args:
            make: Car manufacturer.
            year: Optional year to filter by.

        Returns:
            List of car models.
        """
        pass


class ApiNinjasClient(CarApiClient):
    """Client for the API Ninjas Cars API.

    API documentation: https://api-ninjas.com/api/cars
    """

    BASE_URL = "https://api.api-ninjas.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API Ninjas client.

        Args:
            api_key: API key for API Ninjas. If not provided, will try to get from settings.
        """
        api_key = api_key or config_manager.get_setting("api.api_ninjas_key")
        super().__init__(api_key)

        if not self.api_key:
            logger.warning("API Ninjas API key not provided. API calls will fail.")

    def search_cars(self, **kwargs) -> List[CarData]:
        """Search for cars using the API Ninjas Cars API.

        Args:
            **kwargs: Search parameters, can include:
                make: Vehicle manufacturer
                model: Vehicle model
                fuel_type: Type of fuel (gas, diesel, electricity)
                drive: Drive transmission (fwd, rwd, awd, 4wd)
                cylinders: Number of cylinders
                transmission: Type of transmission (manual, automatic)
                year: Vehicle model year
                min_city_mpg: Minimum city fuel consumption
                max_city_mpg: Maximum city fuel consumption
                min_hwy_mpg: Minimum highway fuel consumption
                max_hwy_mpg: Maximum highway fuel consumption
                min_comb_mpg: Minimum combined fuel consumption
                max_comb_mpg: Maximum combined fuel consumption
                limit: How many results to return (1-50)
                offset: Number of results to skip

        Returns:
            List of CarData objects matching the search criteria.
        """
        # Map API parameters
        params = {k: v for k, v in kwargs.items() if v is not None}

        try:
            response = self._make_request(
                "get", f"{self.BASE_URL}/cars", headers={"X-Api-Key": self.api_key}, params=params
            )

            data = response.json()

            # Convert API response to CarData objects
            cars = []
            for car_data in data:
                car = CarData(
                    make=car_data.get("make", ""),
                    model=car_data.get("model", ""),
                    year=car_data.get("year", 0),
                    transmission=car_data.get("transmission", None),
                    drive=car_data.get("drive", None),
                    fuel_type=car_data.get("fuel_type", None),
                    cylinders=car_data.get("cylinders", None),
                    displacement=car_data.get("displacement", None),
                    class_type=car_data.get("class", None),
                    city_mpg=car_data.get("city_mpg", None),
                    highway_mpg=car_data.get("highway_mpg", None),
                    combination_mpg=car_data.get("combination_mpg", None),
                )
                cars.append(car)

            return cars

        except CarApiError as e:
            logger.error(f"Error searching cars with API Ninjas: {e}")
            return []

    def get_car_details(self, make: str, model: str, year: int) -> Optional[CarData]:
        """Get detailed information about a specific car.

        Args:
            make: Car manufacturer.
            model: Car model.
            year: Car year.

        Returns:
            CarData object with detailed information or None if not found.
        """
        cars = self.search_cars(make=make, model=model, year=year)
        return cars[0] if cars else None

    def get_makes(self, year: Optional[int] = None) -> List[str]:
        """Get a list of car manufacturers.

        Args:
            year: Optional year to filter by.

        Returns:
            List of car manufacturers.
        """
        self._handle_rate_limit()

        params = {}
        if year:
            params["year"] = year

        try:
            response = requests.get(f"{self.BASE_URL}/carmakes", headers={"X-Api-Key": self.api_key}, params=params)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching car makes from API Ninjas: {e}")
            return []

    def get_models(self, make: str, year: Optional[int] = None) -> List[str]:
        """Get a list of car models for a specific manufacturer.

        Args:
            make: Car manufacturer.
            year: Optional year to filter by.

        Returns:
            List of car models.
        """
        self._handle_rate_limit()

        params = {"make": make}
        if year:
            params["year"] = year

        try:
            response = requests.get(f"{self.BASE_URL}/carmodels", headers={"X-Api-Key": self.api_key}, params=params)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching car models from API Ninjas: {e}")
            return []


class ConsumerReportsClient(CarApiClient):
    """Client for the Consumer Reports API.

    API documentation: https://rapidapi.com/apidojo/api/consumer-reports
    """

    BASE_URL = "https://consumer-reports.p.rapidapi.com/cars/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Consumer Reports client.

        Args:
            api_key: API key for RapidAPI. If not provided, will try to get from settings.
        """
        api_key = api_key or config_manager.get_setting("api.consumer_reports_key")
        super().__init__(api_key)

        if not self.api_key:
            logger.warning("Consumer Reports API key not provided. API calls will fail.")

        # Set a higher rate limit delay for this API to avoid throttling
        self.rate_limit_delay = 2.0

        # Increase retry delay for ConsumerReports API
        self.retry_delay = 3.0

    def search_cars(self, **kwargs) -> List[CarData]:
        """Search for cars using the Consumer Reports API.

        Args:
            **kwargs: Search parameters.

        Returns:
            List of CarData objects matching the search criteria.
        """
        # This API doesn't have a direct search endpoint like API Ninjas
        # Instead, we'll need to get all cars and filter them ourselves
        # For now, just return an empty list
        logger.warning("Consumer Reports API doesn't support direct search. Use get_makes and get_models instead.")
        return []

    def get_car_details(self, make: str, model: str, year: int) -> Optional[CarData]:
        """Get detailed information about a specific car from Consumer Reports.

        Args:
            make: Car manufacturer.
            model: Car model.
            year: Car year.

        Returns:
            CarData object with detailed information or None if not found.
        """
        self._handle_rate_limit()

        # Format the endpoint with make, model, and year
        try:
            response = requests.get(
                f"{self.BASE_URL}/models/{make}/{model}/{year}",
                headers={"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": "consumer-reports.p.rapidapi.com"},
            )

            response.raise_for_status()
            data = response.json()

            # Extract relevant information from the Consumer Reports API
            if data and "model" in data:
                model_data = data["model"]

                # Create CarData object with Consumer Reports data
                car = CarData(
                    make=make,
                    model=model,
                    year=year,
                    reliability_score=model_data.get("reliability", {}).get("score"),
                    safety_score=model_data.get("safety", {}).get("score"),
                    owner_satisfaction=model_data.get("ownerSatisfaction", {}).get("score"),
                    pros=model_data.get("pros", []),
                    cons=model_data.get("cons", []),
                )

                # Add ownership costs if available
                if "ownershipCosts" in model_data:
                    car.ownership_costs = model_data["ownershipCosts"]

                return car

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching car details from Consumer Reports: {e}")
            return None

    def get_makes(self, year: Optional[int] = None) -> List[str]:
        """Get a list of car manufacturers from Consumer Reports.

        Args:
            year: Optional year to filter by.

        Returns:
            List of car manufacturers.
        """
        self._handle_rate_limit()

        params = {}
        if year:
            params["year"] = year

        try:
            response = requests.get(
                f"{self.BASE_URL}/makes",
                headers={"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": "consumer-reports.p.rapidapi.com"},
                params=params,
            )

            response.raise_for_status()
            data = response.json()

            # Extract make names from the response
            makes = []
            if "makes" in data:
                makes = [make["name"] for make in data["makes"]]

            return makes

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching car makes from Consumer Reports: {e}")
            return []

    def get_models(self, make: str, year: Optional[int] = None) -> List[str]:
        """Get a list of car models for a specific manufacturer from Consumer Reports.

        Args:
            make: Car manufacturer.
            year: Optional year to filter by.

        Returns:
            List of car models.
        """
        self._handle_rate_limit()

        params = {}
        if year:
            params["year"] = year

        try:
            response = requests.get(
                f"{self.BASE_URL}/makes/{make}/models",
                headers={"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": "consumer-reports.p.rapidapi.com"},
                params=params,
            )

            response.raise_for_status()
            data = response.json()

            # Extract model names from the response
            models = []
            if "models" in data:
                models = [model["name"] for model in data["models"]]

            return models

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching car models from Consumer Reports: {e}")
            return []


class JDPowerClient(CarApiClient):
    """Client for the JD Power Vehicle Ratings API.

    API documentation: https://rapidapi.com/jdpower-api/api/vehicle-ratings-and-reviews
    """

    BASE_URL = "https://jdpower-vehicle-ratings-and-reviews.p.rapidapi.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the JD Power client.

        Args:
            api_key: API key for RapidAPI. If not provided, will try to get from settings.
        """
        api_key = api_key or config_manager.get_setting("api.jdpower_key")
        super().__init__(api_key)

        if not self.api_key:
            logger.warning("JD Power API key not provided. API calls will fail.")

        # Set appropriate rate limiting for this API
        self.rate_limit_delay = 2.0

    def search_cars(self, **kwargs) -> List[CarData]:
        """Search for cars using the JD Power API.

        Args:
            **kwargs: Search parameters. Can include:
                make: Vehicle manufacturer
                model: Vehicle model
                year: Vehicle model year

        Returns:
            List of CarData objects matching the search criteria.
        """
        logger.warning("JD Power API doesn't support direct search. Use get_makes and get_models instead.")
        return []

    def get_car_details(self, make: str, model: str, year: int) -> Optional[CarData]:
        """Get detailed information about a specific car from JD Power.

        Args:
            make: Car manufacturer
            model: Car model
            year: Car year

        Returns:
            CarData object with detailed information or None if not found
        """
        try:
            # Format the endpoint with make, model, and year
            # First, normalize the make and model to match JD Power's format
            normalized_make = make.lower().replace(" ", "-")
            normalized_model = model.lower().replace(" ", "-")

            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jdpower-vehicle-ratings-and-reviews.p.rapidapi.com",
            }

            response = self._make_request(
                "get", f"{self.BASE_URL}/vehicles/{normalized_make}/{normalized_model}/{year}", headers=headers
            )

            data = response.json()

            # Extract relevant information from the JD Power API
            if data and "vehicle" in data:
                vehicle_data = data["vehicle"]

                # Create CarData object with JD Power data
                car = CarData(
                    make=make,
                    model=model,
                    year=year,
                    reliability_score=self._extract_reliability_score(vehicle_data),
                    safety_score=self._extract_safety_score(vehicle_data),
                    owner_satisfaction=self._extract_owner_satisfaction(vehicle_data),
                    pros=self._extract_pros(vehicle_data),
                    cons=self._extract_cons(vehicle_data),
                )

                return car

            return None

        except CarApiError as e:
            logger.error(f"Error fetching car details from JD Power: {e}")
            return None

    def _extract_reliability_score(self, data: Dict) -> Optional[float]:
        """Extract reliability score from JD Power data.

        Args:
            data: JD Power vehicle data

        Returns:
            Reliability score (0-5) or None if not available
        """
        # JD Power uses a 100-point scale, convert to 0-5
        if "qualityScore" in data and data["qualityScore"] is not None:
            try:
                score = float(data["qualityScore"]) / 20.0  # Convert 100-point to 5-point
                return round(score, 1)  # Round to 1 decimal place
            except (ValueError, TypeError):
                return None
        return None

    def _extract_safety_score(self, data: Dict) -> Optional[float]:
        """Extract safety score from JD Power data.

        Args:
            data: JD Power vehicle data

        Returns:
            Safety score (0-5) or None if not available
        """
        # Safety score might be under different fields depending on the API version
        for field in ["safetyScore", "safetyRating", "crashTestRating"]:
            if field in data and data[field] is not None:
                try:
                    # Assuming it's also on a 100-point scale
                    score = float(data[field]) / 20.0
                    return round(score, 1)
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_owner_satisfaction(self, data: Dict) -> Optional[float]:
        """Extract owner satisfaction from JD Power data.

        Args:
            data: JD Power vehicle data

        Returns:
            Owner satisfaction (0-5) or None if not available
        """
        if "appealScore" in data and data["appealScore"] is not None:
            try:
                score = float(data["appealScore"]) / 20.0
                return round(score, 1)
            except (ValueError, TypeError):
                return None
        return None

    def _extract_pros(self, data: Dict) -> List[str]:
        """Extract pros from JD Power data.

        Args:
            data: JD Power vehicle data

        Returns:
            List of pros
        """
        pros = []
        if "pros" in data and isinstance(data["pros"], list):
            pros = data["pros"]
        return pros

    def _extract_cons(self, data: Dict) -> List[str]:
        """Extract cons from JD Power data.

        Args:
            data: JD Power vehicle data

        Returns:
            List of cons
        """
        cons = []
        if "cons" in data and isinstance(data["cons"], list):
            cons = data["cons"]
        return cons

    def get_makes(self, year: Optional[int] = None) -> List[str]:
        """Get a list of car manufacturers from JD Power.

        Args:
            year: Optional year to filter by

        Returns:
            List of car manufacturers
        """
        try:
            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jdpower-vehicle-ratings-and-reviews.p.rapidapi.com",
            }

            params = {}
            if year:
                params["year"] = year

            response = self._make_request("get", f"{self.BASE_URL}/makes", headers=headers, params=params)

            data = response.json()

            # Extract make names from the response
            makes = []
            if "makes" in data and isinstance(data["makes"], list):
                makes = [make.get("name", "") for make in data["makes"] if make.get("name")]

            return makes

        except CarApiError as e:
            logger.error(f"Error fetching car makes from JD Power: {e}")
            return []

    def get_models(self, make: str, year: Optional[int] = None) -> List[str]:
        """Get a list of car models for a specific manufacturer from JD Power.

        Args:
            make: Car manufacturer
            year: Optional year to filter by

        Returns:
            List of car models
        """
        try:
            # Normalize the make to match JD Power's format
            normalized_make = make.lower().replace(" ", "-")

            headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jdpower-vehicle-ratings-and-reviews.p.rapidapi.com",
            }

            params = {}
            if year:
                params["year"] = year

            response = self._make_request(
                "get", f"{self.BASE_URL}/makes/{normalized_make}/models", headers=headers, params=params
            )

            data = response.json()

            # Extract model names from the response
            models = []
            if "models" in data and isinstance(data["models"], list):
                models = [model.get("name", "") for model in data["models"] if model.get("name")]

            return models

        except CarApiError as e:
            logger.error(f"Error fetching car models from JD Power: {e}")
            return []


def get_api_client(api_name: str) -> Optional[CarApiClient]:
    """Get an API client instance by name.

    Args:
        api_name: Name of the API ("api_ninjas", "consumer_reports", or "jdpower").

    Returns:
        CarApiClient instance or None if not found.
    """
    if api_name == "api_ninjas":
        return ApiNinjasClient()
    elif api_name == "consumer_reports":
        return ConsumerReportsClient()
    elif api_name == "jdpower":
        return JDPowerClient()
    else:
        logger.error(f"Unknown API client: {api_name}")
        return None
