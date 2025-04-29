"""Car service for providing car data from multiple sources.

This module provides a service for retrieving car data from multiple API sources
and combining them to provide comprehensive information.
"""

from typing import Dict, List, Optional, Set

from ..core.logging import get_logger
from .api_clients import CarApiClient, CarData, get_api_client

# Set up logger for this module
logger = get_logger(__name__)


class CarService:
    """Service for retrieving and combining car data from multiple sources."""

    def __init__(self):
        """Initialize the car service."""
        self.clients: Dict[str, CarApiClient] = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients."""
        # Initialize API Ninjas client
        api_ninjas_client = get_api_client("api_ninjas")
        if api_ninjas_client:
            self.clients["api_ninjas"] = api_ninjas_client

        # Initialize Consumer Reports client
        consumer_reports_client = get_api_client("consumer_reports")
        if consumer_reports_client:
            self.clients["consumer_reports"] = consumer_reports_client

        # Initialize JD Power client
        jdpower_client = get_api_client("jdpower")
        if jdpower_client:
            self.clients["jdpower"] = jdpower_client

    def search_cars(self, **kwargs) -> List[CarData]:
        """Search for cars based on the provided parameters.

        Args:
            **kwargs: Search parameters.

        Returns:
            List of CarData objects matching the search criteria.
        """
        # API Ninjas has better search capabilities, so use it as the primary
        # source for search results
        if "api_ninjas" in self.clients:
            return self.clients["api_ninjas"].search_cars(**kwargs)

        # If API Ninjas is not available, return an empty list
        logger.warning("API Ninjas client not available for car search")
        return []

    def get_car_details(self, make: str, model: str, year: int) -> Optional[CarData]:
        """Get detailed information about a specific car from multiple sources.

        Args:
            make: Car manufacturer.
            model: Car model.
            year: Car year.

        Returns:
            CarData object with detailed information or None if not found.
        """
        # Start with data from API Ninjas for basic car information
        car_data = None
        errors = []

        try:
            if "api_ninjas" in self.clients:
                car_data = self.clients["api_ninjas"].get_car_details(make, model, year)
                logger.debug(f"Retrieved basic car data from API Ninjas for {make} {model} {year}")
        except Exception as e:
            errors.append(f"API Ninjas error: {e!s}")
            logger.error(f"Error getting car details from API Ninjas: {e}")

        # If the car is not found in API Ninjas, return None
        if not car_data:
            logger.warning(f"No car data found for {make} {model} {year}")
            if errors:
                logger.error(f"Errors encountered while retrieving car data: {', '.join(errors)}")
            return None

        # Enrich the car data with information from Consumer Reports
        try:
            if "consumer_reports" in self.clients:
                cr_data = self.clients["consumer_reports"].get_car_details(make, model, year)
                if cr_data:
                    logger.debug(f"Enriching car data with Consumer Reports for {make} {model} {year}")
                    # Update the car data with additional information from Consumer Reports
                    car_data.reliability_score = cr_data.reliability_score
                    car_data.safety_score = cr_data.safety_score
                    car_data.owner_satisfaction = cr_data.owner_satisfaction
                    car_data.ownership_costs = cr_data.ownership_costs
                    car_data.pros = cr_data.pros
                    car_data.cons = cr_data.cons
        except Exception as e:
            errors.append(f"Consumer Reports error: {e!s}")
            logger.error(f"Error getting car details from Consumer Reports: {e}")

        # Enrich the car data with information from JD Power
        try:
            if "jdpower" in self.clients:
                jdp_data = self.clients["jdpower"].get_car_details(make, model, year)
                if jdp_data:
                    logger.debug(f"Enriching car data with JD Power for {make} {model} {year}")
                    # Only update if the data doesn't already exist from Consumer Reports
                    # or if the JD Power data is more complete

                    # For reliability score, prefer JD Power if available
                    if jdp_data.reliability_score is not None:
                        car_data.reliability_score = jdp_data.reliability_score

                    # For safety score, use JD Power if not already set or if JD Power has data
                    if car_data.safety_score is None and jdp_data.safety_score is not None:
                        car_data.safety_score = jdp_data.safety_score

                    # For owner satisfaction, prefer JD Power if available
                    if jdp_data.owner_satisfaction is not None:
                        car_data.owner_satisfaction = jdp_data.owner_satisfaction

                    # Combine pros and cons from both sources (avoiding duplicates)
                    if jdp_data.pros:
                        if car_data.pros is None:
                            car_data.pros = []
                        for pro in jdp_data.pros:
                            if pro not in car_data.pros:
                                car_data.pros.append(pro)

                    if jdp_data.cons:
                        if car_data.cons is None:
                            car_data.cons = []
                        for con in jdp_data.cons:
                            if con not in car_data.cons:
                                car_data.cons.append(con)
        except Exception as e:
            errors.append(f"JD Power error: {e!s}")
            logger.error(f"Error getting car details from JD Power: {e}")

        # Log any errors encountered
        if errors:
            logger.warning(
                f"Some data sources had errors while retrieving data for {make} {model} {year}: {', '.join(errors)}"
            )

        return car_data

    def get_makes(self, year: Optional[int] = None) -> List[str]:
        """Get a list of car manufacturers from all available sources.

        Args:
            year: Optional year to filter by.

        Returns:
            List of car manufacturers.
        """
        makes: Set[str] = set()
        errors = []

        # Get makes from all available sources
        for source, client in self.clients.items():
            try:
                source_makes = client.get_makes(year)
                makes.update(source_makes)
                logger.debug(f"Retrieved {len(source_makes)} makes from {source}")
            except Exception as e:
                errors.append(f"{source} error: {e!s}")
                logger.error(f"Error getting makes from {source}: {e}")

        # Log any errors encountered
        if errors:
            logger.warning(f"Some data sources had errors while retrieving makes: {', '.join(errors)}")

        # Return sorted list of makes
        return sorted(list(makes))

    def get_models(self, make: str, year: Optional[int] = None) -> List[str]:
        """Get a list of car models for a specific manufacturer from all available sources.

        Args:
            make: Car manufacturer.
            year: Optional year to filter by.

        Returns:
            List of car models.
        """
        models: Set[str] = set()
        errors = []

        # Get models from all available sources
        for source, client in self.clients.items():
            try:
                source_models = client.get_models(make, year)
                models.update(source_models)
                logger.debug(f"Retrieved {len(source_models)} models for {make} from {source}")
            except Exception as e:
                errors.append(f"{source} error: {e!s}")
                logger.error(f"Error getting models for {make} from {source}: {e}")

        # Log any errors encountered
        if errors:
            logger.warning(f"Some data sources had errors while retrieving models for {make}: {', '.join(errors)}")

        # Return sorted list of models
        return sorted(list(models))

    def get_years_range(self) -> List[int]:
        """Get a range of years for car models.

        Returns:
            List of years from 1990 to current year.
        """
        import datetime

        current_year = datetime.datetime.now().year
        return list(range(1990, current_year + 1))

    def get_available_api_sources(self) -> List[str]:
        """Get a list of available API sources.

        Returns:
            List of available API sources.
        """
        return list(self.clients.keys())


# Create a singleton instance
car_service = CarService()
