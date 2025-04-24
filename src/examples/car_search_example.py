"""
Example for using the Car Search Service.

This script demonstrates how to use the car search service to find and
enrich car data from AutoTrader and various API clients.
"""

import os
import logging
from dotenv import load_dotenv

from src.models.car import Car, CarCollection, ConfidenceLevel
from src.services.car_search import CarSearchService
from src.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def display_car_details(car: Car) -> None:
    """
    Display detailed information about a car.
    
    Args:
        car: The car to display.
    """
    print(f"\n{'=' * 50}")
    print(f"Car ID: {car.id}")
    print(f"{'=' * 50}")
    
    # Basic information
    print(f"Make: {car.make}")
    print(f"Model: {car.model}")
    print(f"Year: {car.year}")
    print(f"Price: £{car.price}")
    print(f"Mileage: {car.mileage} miles")
    print(f"Fuel Type: {car.fuel_type}")
    print(f"Transmission: {car.transmission}")
    print(f"Location: {car.location}")
    
    # Engine information
    print(f"\n--- Engine Information ---")
    print(f"Engine Size: {car.get_attribute('engine_size')} L")
    print(f"Engine Type: {car.get_attribute('engine_type')}")
    print(f"Horsepower: {car.get_attribute('horsepower')} hp")
    print(f"MPG (Combined): {car.get_attribute('mpg_combined')} mpg")
    
    # Reliability information
    reliability_rating = car.get_attribute('reliability_rating')
    if reliability_rating:
        print(f"\n--- Reliability Information ---")
        print(f"Reliability Rating: {reliability_rating}")
        
        common_issues = car.get_attribute('common_issues')
        if common_issues:
            print(f"Common Issues:")
            for issue in common_issues:
                print(f"  - {issue}")
        
        print(f"Average Repair Cost: £{car.get_attribute('average_repair_cost')}")
    
    # Vehicle history
    previous_owners = car.get_attribute('previous_owners')
    if previous_owners:
        print(f"\n--- Vehicle History ---")
        print(f"Previous Owners: {previous_owners}")
        
        accidents = car.get_attribute('accidents')
        if accidents:
            print(f"Accidents: {accidents}")
        
        service_history = car.get_attribute('service_history')
        if service_history:
            print(f"Service History: {'Complete' if service_history else 'Incomplete'}")
    
    # Safety information (from Edmunds)
    safety_rating = car.get_attribute('safety_rating')
    if safety_rating:
        print(f"\n--- Safety Information ---")
        print(f"Safety Rating: {safety_rating}/5")
    
    # Cost of ownership (from Edmunds)
    total_cost = car.get_attribute('total_cost')
    if total_cost:
        print(f"\n--- Cost of Ownership ---")
        print(f"Total Cost: ${total_cost:,.2f}")
        print(f"Depreciation: ${car.get_attribute('depreciation'):,.2f}")
        print(f"Maintenance Cost: ${car.get_attribute('maintenance_cost'):,.2f}")
    
    # URL
    url = car.get_attribute('url')
    if url:
        print(f"\nURL: {url}")
    
    print(f"\n{'=' * 50}\n")


def main():
    """
    Main function to demonstrate the car search service.
    """
    # Initialize the car search service with all available API keys
    search_service = CarSearchService(
        region="uk",
        motorcheck_api_key=settings.api.motorcheck_api_key,
        edmunds_api_key=settings.api.edmunds_api_key,
        smartcar_api_key=settings.api.smartcar_api_key
    )
    
    # Example 1: Search for cars
    search_params = {
        "postcode": settings.app.default_postcode,
        "radius": settings.app.default_radius,
        "max_price": settings.app.default_max_price,
        "make": "Ford",
        "transmission": "Automatic"
    }
    
    print(f"Searching for cars with parameters: {search_params}")
    
    try:
        car_collection = search_service.search(search_params, limit=3)
        
        print(f"Found {len(car_collection)} cars")
        
        # Enrich car data with additional information
        include_safety = search_service.edmunds_client is not None
        include_tco = search_service.edmunds_client is not None
        
        enriched_collection = search_service.enrich_cars(
            car_collection,
            include_reliability=True,
            include_details=True,
            include_history=True,
            include_safety=include_safety,
            include_tco=include_tco
        )
        
        # Display results
        for i, car in enumerate(enriched_collection, 1):
            print(f"Car {i}:")
            display_car_details(car)
    
    except Exception as e:
        logger.error(f"Error searching for cars: {str(e)}")
    
    # Example 2: Get car by registration
    registration = "AB12CDE"  # Example registration
    print(f"\nGetting car details for registration: {registration}")
    
    try:
        car = search_service.get_car_by_registration(registration)
        
        if car:
            display_car_details(car)
        else:
            print(f"No car found with registration: {registration}")
    
    except Exception as e:
        logger.error(f"Error getting car by registration: {str(e)}")
    
    # Example 3: Get car by make, model, year (using Edmunds API)
    if search_service.edmunds_client:
        make = "Honda"
        model = "Civic"
        year = 2020
        
        print(f"\nGetting details for {year} {make} {model}")
        
        try:
            car = search_service.get_car_by_make_model_year(make, model, year)
            
            if car:
                display_car_details(car)
            else:
                print(f"No details found for {year} {make} {model}")
        
        except Exception as e:
            logger.error(f"Error getting car by make/model/year: {str(e)}")


if __name__ == "__main__":
    main() 