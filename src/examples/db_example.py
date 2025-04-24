#!/usr/bin/env python3
"""
Example script demonstrating how to use the SQLite database manager.

This script shows how to:
1. Save cars to the database
2. Retrieve cars from the database
3. Work with favorites and comparisons
4. Query cars by various criteria
"""

import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.car import Car, ConfidenceLevel, AttributeType
from src.data.db_manager import db_manager
from src.services.car_search import CarSearchService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_sample_cars() -> list[Car]:
    """Create a few sample cars for demonstration."""
    # Car 1: Toyota Camry
    car1 = Car(id="sample_1")
    car1.set_attribute("title", "2020 Toyota Camry XLE", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car1.set_attribute("make", "Toyota", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car1.set_attribute("model", "Camry", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car1.set_attribute("year", 2020, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car1.set_attribute("price", 25000, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car1.set_attribute("mileage", 15000, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car1.set_attribute("fuel_type", "Gasoline", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car1.set_attribute("transmission", "Automatic", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car1.set_attribute("source", "sample", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    
    # Car 2: Honda Accord
    car2 = Car(id="sample_2")
    car2.set_attribute("title", "2019 Honda Accord Sport", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car2.set_attribute("make", "Honda", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car2.set_attribute("model", "Accord", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car2.set_attribute("year", 2019, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car2.set_attribute("price", 23500, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car2.set_attribute("mileage", 20000, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car2.set_attribute("fuel_type", "Gasoline", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car2.set_attribute("transmission", "Manual", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car2.set_attribute("source", "sample", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    
    # Car 3: Tesla Model 3
    car3 = Car(id="sample_3")
    car3.set_attribute("title", "2021 Tesla Model 3 Long Range", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car3.set_attribute("make", "Tesla", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car3.set_attribute("model", "Model 3", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car3.set_attribute("year", 2021, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car3.set_attribute("price", 45000, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car3.set_attribute("mileage", 5000, "sample", ConfidenceLevel.HIGH, AttributeType.NUMBER)
    car3.set_attribute("fuel_type", "Electric", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car3.set_attribute("transmission", "Automatic", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    car3.set_attribute("source", "sample", "sample", ConfidenceLevel.HIGH, AttributeType.TEXT)
    
    return [car1, car2, car3]


def main():
    """Run the database example script."""
    print(f"Database path: {db_manager.db_path}")
    
    # Example 1: Save cars to the database
    print("\n=== Example 1: Save Cars to Database ===")
    sample_cars = create_sample_cars()
    
    print(f"Saving {len(sample_cars)} sample cars to the database...")
    saved_count = db_manager.save_cars(sample_cars)
    print(f"Successfully saved {saved_count} cars")
    
    # Example 2: Retrieve a car from the database
    print("\n=== Example 2: Retrieve Car from Database ===")
    car_id = "sample_1"
    print(f"Retrieving car with ID: {car_id}")
    
    car = db_manager.get_car(car_id)
    if car:
        print(f"Found car: {car.title}")
        print(f"Make: {car.make}, Model: {car.model}, Year: {car.year}")
        print(f"Price: ${car.price}, Mileage: {car.mileage} miles")
    else:
        print(f"Car with ID {car_id} not found")
    
    # Example 3: Query cars by criteria
    print("\n=== Example 3: Query Cars by Criteria ===")
    criteria = {"make": "Toyota"}
    print(f"Querying cars with criteria: {criteria}")
    
    toyota_cars = db_manager.get_cars_by_criteria(criteria)
    print(f"Found {len(toyota_cars)} Toyota cars:")
    for car in toyota_cars:
        print(f"- {car.title} (${car.price})")
    
    # Example 4: Add a car to favorites
    print("\n=== Example 4: Add Car to Favorites ===")
    car_id = "sample_3"
    notes = "Great electric car, considering test drive"
    
    print(f"Adding car {car_id} to favorites...")
    if db_manager.add_favorite(car_id, notes):
        print(f"Successfully added car {car_id} to favorites")
    else:
        print(f"Failed to add car {car_id} to favorites")
    
    # Example 5: Get all favorites
    print("\n=== Example 5: Get All Favorites ===")
    favorites = db_manager.get_favorites()
    
    print(f"Found {len(favorites)} favorite cars:")
    for car in favorites:
        notes = car.get_attribute("favorite_notes")
        print(f"- {car.title} (Notes: {notes})")
    
    # Example 6: Create a comparison set
    print("\n=== Example 6: Create Comparison Set ===")
    comparison_name = "Sedan Comparison"
    comparison_description = "Comparing different sedan options"
    
    print(f"Creating comparison set: {comparison_name}")
    comparison_id = db_manager.create_comparison(comparison_name, comparison_description)
    
    if comparison_id:
        print(f"Created comparison set with ID: {comparison_id}")
        
        # Add cars to the comparison
        print("Adding cars to comparison...")
        db_manager.add_car_to_comparison(comparison_id, "sample_1")
        db_manager.add_car_to_comparison(comparison_id, "sample_2")
        
        # Get the comparison
        comparison = db_manager.get_comparison(comparison_id)
        
        if comparison:
            print(f"Comparison: {comparison['name']}")
            print(f"Description: {comparison['description']}")
            print(f"Cars in comparison: {len(comparison['cars'])}")
            
            for car in comparison['cars']:
                print(f"- {car.title} (${car.price})")
    else:
        print("Failed to create comparison set")
    
    # Example 7: Save a search
    print("\n=== Example 7: Save Search ===")
    search_params = {
        "make": "Honda",
        "model": "Accord",
        "max_price": 25000,
        "max_mileage": 30000
    }
    
    print(f"Saving search with parameters: {search_params}")
    search_id = db_manager.save_search(search_params, 1, region="us")
    
    if search_id:
        print(f"Saved search with ID: {search_id}")
        
        # Save search results
        print("Saving search results...")
        db_manager.save_search_results(search_id, ["sample_2"])
    else:
        print("Failed to save search")
    
    # Example 8: Get database statistics
    print("\n=== Example 8: Database Statistics ===")
    stats = db_manager.get_statistics()
    
    print("Database statistics:")
    for key, value in stats.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main() 