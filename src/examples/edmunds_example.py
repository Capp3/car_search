"""
Example demonstrating the use of the Edmunds API client.

This script shows how to use the Car Search Service with the Edmunds API
to retrieve detailed car information, safety data, and cost of ownership information.
"""

import os
import logging
from dotenv import load_dotenv

from src.models.car import Car, CarCollection
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
    print(f"Trim: {car.get_attribute('trim')}")
    
    # Engine information
    print(f"\n--- Engine Information ---")
    print(f"Engine Name: {car.get_attribute('engine_name')}")
    print(f"Cylinders: {car.get_attribute('cylinders')}")
    print(f"Engine Size: {car.get_attribute('engine_size')} L")
    
    # Fuel Economy
    print(f"\n--- Fuel Economy ---")
    print(f"MPG (City): {car.get_attribute('mpg_city')} mpg")
    print(f"MPG (Highway): {car.get_attribute('mpg_highway')} mpg")
    
    # Safety information
    safety_rating = car.get_attribute('safety_rating')
    if safety_rating:
        print(f"\n--- Safety Information ---")
        print(f"Overall Safety Rating: {safety_rating}/5")
        
        # Add detailed safety information if available
        safety_data = car.get_attribute('safety_data')
        if safety_data and 'nhtsa' in safety_data:
            nhtsa = safety_data['nhtsa']
            print(f"NHTSA Ratings:")
            for category, rating in nhtsa.items():
                if category != 'overall':
                    print(f"  {category.replace('_', ' ').title()}: {rating}/5")
    
    # Cost of ownership
    total_cost = car.get_attribute('total_cost')
    if total_cost:
        print(f"\n--- Cost of Ownership (5 Year) ---")
        print(f"Total Cost: ${total_cost:,.2f}")
        print(f"Depreciation: ${car.get_attribute('depreciation'):,.2f}")
        print(f"Maintenance: ${car.get_attribute('maintenance_cost'):,.2f}")
    
    # Expert rating
    expert_rating = car.get_attribute('expert_rating')
    if expert_rating:
        print(f"\n--- Expert Rating ---")
        print(f"Edmunds Rating: {expert_rating}/5")
    
    print(f"\n{'=' * 50}\n")


def main():
    """
    Main function to demonstrate the Edmunds API client.
    """
    # Initialize the car search service
    search_service = CarSearchService(
        region="us",
        edmunds_api_key=settings.api.edmunds_api_key,
        motorcheck_api_key=settings.api.motorcheck_api_key
    )
    
    # Example 1: Get car by make, model, year
    make = "Honda"
    model = "Accord"
    year = 2022
    
    print(f"Getting details for {year} {make} {model}")
    
    try:
        car = search_service.get_car_by_make_model_year(make, model, year)
        
        if car:
            display_car_details(car)
        else:
            print(f"No car found for {year} {make} {model}")
    
    except Exception as e:
        logger.error(f"Error getting car details: {str(e)}")
    
    # Example 2: Compare two cars
    print("\nComparing two cars:")
    
    cars_to_compare = [
        {"make": "Toyota", "model": "Camry", "year": 2022},
        {"make": "Honda", "model": "Accord", "year": 2022}
    ]
    
    car_collection = CarCollection()
    
    try:
        for car_info in cars_to_compare:
            car = search_service.get_car_by_make_model_year(
                car_info["make"], car_info["model"], car_info["year"]
            )
            if car:
                car_collection.add(car)
        
        print(f"Successfully retrieved {len(car_collection)} cars for comparison")
        
        # Display a comparison table of key attributes
        if len(car_collection) > 0:
            print("\n--- Car Comparison ---")
            
            # Table header
            print(f"{'Attribute':<20} | ", end="")
            for car in car_collection:
                print(f"{car.make} {car.model:<15} | ", end="")
            print("")
            print("-" * 60)
            
            # Compare attributes
            attributes_to_compare = [
                ("Engine Size", "engine_size"),
                ("Cylinders", "cylinders"),
                ("MPG (City)", "mpg_city"),
                ("MPG (Highway)", "mpg_highway"),
                ("Safety Rating", "safety_rating"),
                ("Total Cost", "total_cost"),
                ("Depreciation", "depreciation"),
                ("Maintenance", "maintenance_cost")
            ]
            
            for label, attr in attributes_to_compare:
                print(f"{label:<20} | ", end="")
                for car in car_collection:
                    value = car.get_attribute(attr)
                    if attr in ["total_cost", "depreciation", "maintenance_cost"] and value:
                        formatted_value = f"${value:,.0f}"
                    elif value is not None:
                        formatted_value = str(value)
                    else:
                        formatted_value = "N/A"
                    print(f"{formatted_value:<15} | ", end="")
                print("")
            
    except Exception as e:
        logger.error(f"Error comparing cars: {str(e)}")
    
    # Example 3: List available car makes
    if search_service.edmunds_client:
        print("\nAvailable car makes for 2023:")
        try:
            makes = search_service.edmunds_client.get_makes(year=2023)
            for make in makes[:10]:  # Show first 10 makes
                print(f"- {make['name']} ({make['niceName']})")
            
            # Show models for a specific make
            first_make = makes[0]["niceName"]
            print(f"\nAvailable {makes[0]['name']} models for 2023:")
            
            models = search_service.edmunds_client.get_models(first_make, year=2023)
            for model in models[:5]:  # Show first 5 models
                print(f"- {model['name']} ({model['niceName']})")
            
        except Exception as e:
            logger.error(f"Error listing makes and models: {str(e)}")


if __name__ == "__main__":
    main() 