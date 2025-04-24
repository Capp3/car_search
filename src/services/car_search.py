"""
Car search service module.

This module provides functionality to search for cars using various sources 
and enrich the data with additional information from API clients.
"""

import logging
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models.car import Car, CarCollection
from src.services.scrapers.autotrader import AutoTraderScraper
from src.services.api_clients.motorcheck import MotorcheckAPIClient
from src.services.api_clients.edmunds import EdmundsAPIClient
from src.services.api_clients.smartcar import SmartcarAPIClient

# Configure logging
logger = logging.getLogger(__name__)


class CarSearchService:
    """
    Service for searching and enriching car data from multiple sources.
    """
    
    def __init__(
        self,
        region: str = "uk",
        motorcheck_api_key: Optional[str] = None,
        edmunds_api_key: Optional[str] = None,
        smartcar_api_key: Optional[str] = None,
        smartcar_client_secret: Optional[str] = None,
        smartcar_redirect_uri: Optional[str] = None
    ):
        """
        Initialize the car search service.
        
        Args:
            region: The region to search for cars (e.g., "uk", "us").
            motorcheck_api_key: API key for Motorcheck.
            edmunds_api_key: API key for Edmunds.
            smartcar_api_key: API key for Smartcar.
            smartcar_client_secret: Client secret for Smartcar OAuth.
            smartcar_redirect_uri: Redirect URI for Smartcar OAuth.
        """
        self.region = region
        self.autotrader_scraper = AutoTraderScraper(region=region)
        
        # Initialize API clients if keys are provided
        self.motorcheck_client = None
        self.edmunds_client = None
        self.smartcar_client = None
        
        if motorcheck_api_key:
            self.motorcheck_client = MotorcheckAPIClient(api_key=motorcheck_api_key)
        
        if edmunds_api_key:
            self.edmunds_client = EdmundsAPIClient(api_key=edmunds_api_key)
        
        if smartcar_api_key:
            self.smartcar_client = SmartcarAPIClient(
                api_key=smartcar_api_key,
                client_secret=smartcar_client_secret or "",
                redirect_uri=smartcar_redirect_uri or ""
            )
        
        logger.info(f"Initialized car search service for region: {region}")
    
    def search(self, search_params: Dict[str, Any], limit: int = 10) -> CarCollection:
        """
        Search for cars based on the provided parameters.
        
        Args:
            search_params: Dictionary of search parameters.
            limit: Maximum number of results to return.
            
        Returns:
            A CarCollection containing the found cars.
        """
        logger.info(f"Searching for cars with params: {search_params}, limit: {limit}")
        
        # Get initial search results from AutoTrader
        scraper_result = self.autotrader_scraper.search(search_params, limit=limit)
        
        collection = CarCollection(scraper_result.cars)
        
        logger.info(f"Found {len(collection)} cars from AutoTrader")
        
        return collection
    
    def enrich_cars(self, collection: CarCollection, 
                   include_reliability: bool = True,
                   include_details: bool = True,
                   include_history: bool = False,
                   include_safety: bool = False,
                   include_tco: bool = False) -> CarCollection:
        """
        Enrich car data with additional information from API clients.
        
        Args:
            collection: Collection of cars to enrich.
            include_reliability: Whether to include reliability data.
            include_details: Whether to include additional car details.
            include_history: Whether to include vehicle history.
            include_safety: Whether to include safety information.
            include_tco: Whether to include true cost to own data.
            
        Returns:
            The enriched car collection.
        """
        if len(collection) == 0:
            logger.warning("No cars to enrich")
            return collection
        
        logger.info(f"Enriching {len(collection)} cars with additional data")
        
        # Process each car in parallel to improve performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for car in collection:
                future = executor.submit(
                    self._enrich_car, 
                    car, 
                    include_reliability, 
                    include_details,
                    include_history,
                    include_safety,
                    include_tco
                )
                futures.append(future)
            
            # Wait for all enrichment tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error enriching car: {str(e)}")
        
        logger.info(f"Completed enriching {len(collection)} cars")
        return collection
    
    def _enrich_car(self, car: Car, 
                   include_reliability: bool,
                   include_details: bool,
                   include_history: bool,
                   include_safety: bool,
                   include_tco: bool) -> None:
        """
        Enrich a single car with additional data from API clients.
        
        Args:
            car: The car to enrich.
            include_reliability: Whether to include reliability data.
            include_details: Whether to include additional car details.
            include_history: Whether to include vehicle history.
            include_safety: Whether to include safety information.
            include_tco: Whether to include true cost to own data.
        """
        logger.debug(f"Enriching car: {car.id}")
        
        registration = car.get_attribute("registration")
        
        # Skip if no registration and we can't fetch additional data
        if not registration and include_details and not car.make:
            logger.warning(f"No registration or make/model available for car {car.id}, limited enrichment possible")
        
        # Use Motorcheck client for additional car details and history if available
        if self.motorcheck_client and registration:
            if include_details:
                try:
                    # Get and merge additional car details
                    car_details = self.motorcheck_client.get_car_details(registration)
                    
                    if car_details:
                        # Merge the attributes from car_details into the original car
                        for attr_name, attribute in car_details.attributes.items():
                            if attr_name not in car.attributes:
                                car.attributes[attr_name] = attribute
                            else:
                                # If attribute already exists, add the new sources
                                for source_name, source in attribute.sources.items():
                                    car.attributes[attr_name].sources[source_name] = source
                    
                    logger.debug(f"Added car details for {car.id} from Motorcheck")
                except Exception as e:
                    logger.error(f"Error getting car details for {car.id}: {str(e)}")
            
            if include_history:
                try:
                    history = self.motorcheck_client.get_vehicle_history(registration)
                    
                    if history:
                        # Store the whole history data as a single attribute
                        car.set_attribute("vehicle_history", history, "motorcheck")
                        
                        # Extract and set key history attributes for easier access
                        if "previousOwners" in history:
                            car.set_attribute("previous_owners", history["previousOwners"], "motorcheck")
                        
                        if "accidents" in history:
                            car.set_attribute("accidents", history["accidents"], "motorcheck")
                        
                        if "serviceHistory" in history:
                            car.set_attribute("service_history", history["serviceHistory"], "motorcheck")
                    
                    logger.debug(f"Added vehicle history for {car.id} from Motorcheck")
                except Exception as e:
                    logger.error(f"Error getting vehicle history for {car.id}: {str(e)}")
        
        # Use Edmunds client for specs, safety, and cost of ownership
        if self.edmunds_client and car.make and car.model and car.year:
            make = car.get_attribute("make")
            model = car.get_attribute("model")
            year = car.get_attribute("year")
            
            if include_details:
                try:
                    # Get basic specs
                    specs = self.edmunds_client.get_car_details(make, model, year)
                    
                    if specs:
                        # Add specs as attributes
                        for attr_name, attribute in specs.attributes.items():
                            if attr_name not in car.attributes:
                                car.attributes[attr_name] = attribute
                            else:
                                # If attribute already exists, add the new sources
                                for source_name, source in attribute.sources.items():
                                    car.attributes[attr_name].sources[source_name] = source
                    
                    logger.debug(f"Added car specifications for {car.id} from Edmunds")
                except Exception as e:
                    logger.error(f"Error getting car specifications for {car.id}: {str(e)}")
            
            if include_safety:
                try:
                    # Get safety ratings
                    safety = self.edmunds_client.get_car_safety(make, model, year)
                    
                    if safety:
                        car.set_attribute("safety_ratings", safety, "edmunds")
                        
                        # Extract overall rating for easier access
                        if "overall" in safety:
                            car.set_attribute("safety_rating_overall", safety["overall"], "edmunds")
                    
                    logger.debug(f"Added safety ratings for {car.id} from Edmunds")
                except Exception as e:
                    logger.error(f"Error getting safety ratings for {car.id}: {str(e)}")
            
            if include_tco:
                try:
                    # Get true cost to own data
                    style_id = car.get_attribute("style_id")
                    zip_code = car.get_attribute("zip_code") or "90019"  # Default to Los Angeles
                    
                    if style_id:
                        tco = self.edmunds_client.get_car_tco(style_id, zip_code)
                        
                        if tco:
                            car.set_attribute("true_cost_to_own", tco, "edmunds")
                            
                            # Extract key TCO figures for easier access
                            if "values" in tco and "totalCash" in tco["values"]:
                                car.set_attribute("total_cost_5yr", tco["values"]["totalCash"], "edmunds")
                            
                            if "values" in tco and "depreciation" in tco["values"]:
                                car.set_attribute("depreciation_5yr", tco["values"]["depreciation"], "edmunds")
                        
                        logger.debug(f"Added true cost to own data for {car.id} from Edmunds")
                except Exception as e:
                    logger.error(f"Error getting true cost to own data for {car.id}: {str(e)}")
        
        # Use Smartcar client for additional details and real-time data if available
        if self.smartcar_client and car.make and car.model and car.year:
            make = car.get_attribute("make")
            model = car.get_attribute("model")
            year = car.get_attribute("year")
            
            if include_details:
                try:
                    # Get car details from Smartcar
                    smartcar_details = self.smartcar_client.get_car_details(make, model, year)
                    
                    if smartcar_details:
                        # Merge the attributes from smartcar_details into the original car
                        for attr_name, attribute in smartcar_details.attributes.items():
                            if attr_name not in car.attributes:
                                car.attributes[attr_name] = attribute
                            else:
                                # If attribute already exists, add the new sources
                                for source_name, source in attribute.sources.items():
                                    car.attributes[attr_name].sources[source_name] = source
                    
                    logger.debug(f"Added car details for {car.id} from Smartcar")
                except Exception as e:
                    logger.error(f"Error getting car details for {car.id} from Smartcar: {str(e)}")
            
            if include_reliability:
                try:
                    # Get reliability data
                    reliability = self.smartcar_client.get_reliability_data(make, model, year)
                    
                    if reliability:
                        car.set_attribute("reliability_data", reliability, "smartcar")
                        
                        # Extract key reliability metrics
                        if "score" in reliability:
                            car.set_attribute("reliability_score", reliability["score"], "smartcar")
                        
                        if "commonIssues" in reliability:
                            car.set_attribute("common_issues", reliability["commonIssues"], "smartcar")
                    
                    logger.debug(f"Added reliability data for {car.id} from Smartcar")
                except Exception as e:
                    logger.error(f"Error getting reliability data for {car.id} from Smartcar: {str(e)}")
            
            if include_history:
                try:
                    # Get maintenance schedule
                    maintenance = self.smartcar_client.get_maintenance_schedule(make, model, year)
                    
                    if maintenance:
                        car.set_attribute("maintenance_schedule", maintenance, "smartcar")
                    
                    logger.debug(f"Added maintenance schedule for {car.id} from Smartcar")
                except Exception as e:
                    logger.error(f"Error getting maintenance schedule for {car.id} from Smartcar: {str(e)}")
        
        # Add additional attribute processing here for other API clients or data sources
    
    def get_car_by_registration(self, registration: str) -> Optional[Car]:
        """
        Get detailed information about a specific car using its registration number.
        
        Args:
            registration: The car's registration number.
            
        Returns:
            A Car object with details, or None if not found.
        """
        logger.info(f"Getting car details for registration: {registration}")
        
        if not self.motorcheck_client:
            logger.warning("Motorcheck client not initialized, cannot fetch car details")
            return None
        
        try:
            car = self.motorcheck_client.get_car_details(registration)
            
            if car:
                # Enrich the car with additional data, including safety and TCO if Edmunds client is available
                self._enrich_car(
                    car,
                    include_reliability=True,
                    include_details=True,
                    include_history=True,
                    include_safety=self.edmunds_client is not None,
                    include_tco=self.edmunds_client is not None
                )
            
            return car
        except Exception as e:
            logger.error(f"Error getting car by registration {registration}: {str(e)}")
            return None
    
    def get_car_by_make_model_year(self, make: str, model: str, year: int) -> Optional[Car]:
        """
        Get detailed information about a specific car using make, model, and year.
        
        Args:
            make: Car make.
            model: Car model.
            year: Manufacturing year.
            
        Returns:
            A Car object with details, or None if not found.
        """
        logger.info(f"Getting car details for {make} {model} {year}")
        
        if not self.edmunds_client:
            logger.warning("Edmunds client not initialized, cannot fetch car details")
            return None
        
        try:
            car = self.edmunds_client.get_car_details(make, model, year)
            
            if car:
                # Enrich the car with additional data
                self._enrich_car(
                    car,
                    include_reliability=self.motorcheck_client is not None,
                    include_details=True,
                    include_history=False,
                    include_safety=True,
                    include_tco=True
                )
            
            return car
        except Exception as e:
            logger.error(f"Error getting car by make/model/year {make}/{model}/{year}: {str(e)}")
            return None 