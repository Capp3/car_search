#!/usr/bin/env python3
"""
Example script demonstrating the search parameter processing system.

This script shows how to:
1. Validate and process search parameters
2. Convert processed parameters to filter queries
3. Handle validation errors and warnings
"""

import os
import sys
import logging
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.param_validation import parameter_processor
from src.models.car import Car, CarCollection
from src.data.filtering import filter_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_test_cars():
    """Create a collection of test cars."""
    # Car 1: Toyota Camry
    car1 = Car(id="1")
    car1.set_attribute("make", "Toyota", "test")
    car1.set_attribute("model", "Camry", "test")
    car1.set_attribute("year", 2020, "test")
    car1.set_attribute("price", 25000, "test")
    car1.set_attribute("mileage", 15000, "test")
    car1.set_attribute("transmission", "Automatic", "test")
    car1.set_attribute("location", "London", "test")
    
    # Car 2: Honda Accord
    car2 = Car(id="2")
    car2.set_attribute("make", "Honda", "test")
    car2.set_attribute("model", "Accord", "test")
    car2.set_attribute("year", 2019, "test")
    car2.set_attribute("price", 22000, "test")
    car2.set_attribute("mileage", 20000, "test")
    car2.set_attribute("transmission", "Manual", "test")
    car2.set_attribute("location", "Manchester", "test")
    
    # Car 3: BMW X5
    car3 = Car(id="3")
    car3.set_attribute("make", "BMW", "test")
    car3.set_attribute("model", "X5", "test")
    car3.set_attribute("year", 2021, "test")
    car3.set_attribute("price", 45000, "test")
    car3.set_attribute("mileage", 5000, "test")
    car3.set_attribute("transmission", "Automatic", "test")
    car3.set_attribute("location", "Birmingham", "test")
    
    # Car 4: Audi A4
    car4 = Car(id="4")
    car4.set_attribute("make", "Audi", "test")
    car4.set_attribute("model", "A4", "test")
    car4.set_attribute("year", 2018, "test")
    car4.set_attribute("price", 30000, "test")
    car4.set_attribute("mileage", 25000, "test")
    car4.set_attribute("transmission", "Semi-Auto", "test")
    car4.set_attribute("location", "Bristol", "test")
    
    # Car 5: Ford Mustang
    car5 = Car(id="5")
    car5.set_attribute("make", "Ford", "test")
    car5.set_attribute("model", "Mustang", "test")
    car5.set_attribute("year", 2017, "test") 
    car5.set_attribute("price", 35000, "test")
    car5.set_attribute("mileage", 30000, "test")
    car5.set_attribute("transmission", "Manual", "test")
    car5.set_attribute("location", "Glasgow", "test")
    
    return CarCollection(cars=[car1, car2, car3, car4, car5])


def display_processed_params(processed: Dict[str, Any]):
    """Display processed parameters with validation status."""
    print("\n=== Processed Parameters ===")
    
    print("\nValid Parameters:")
    for param, value in processed["valid_params"].items():
        print(f"  {param}: {value}")
    
    if processed["invalid_params"]:
        print("\nInvalid Parameters:")
        for param, details in processed["invalid_params"].items():
            print(f"  {param}: {details['value']} - Error: {details['error']}")
    
    if processed["warnings"]:
        print("\nWarnings:")
        for warning in processed["warnings"]:
            print(f"  - {warning}")


def apply_filters_to_cars(processed_params: Dict[str, Any], cars: CarCollection):
    """Apply processed parameters as filters to a car collection."""
    # Create filter query from processed parameters
    query = parameter_processor.create_filter_from_params(processed_params["valid_params"])
    
    # Apply filter to cars
    filtered_cars = filter_manager.filter_cars(cars, query)
    
    print(f"\nFound {len(filtered_cars)} cars matching the filters:")
    for car in filtered_cars:
        print(f"  - {car.year} {car.make} {car.model}: £{car.price} ({car.transmission}, {car.location})")
    
    return filtered_cars


def example_1():
    """Example 1: Basic parameter processing with valid parameters."""
    print("\n=== Example 1: Basic Parameter Processing ===")
    
    # Define search parameters
    params = {
        "postcode": "SW1A 1AA",  # Valid UK postcode (Buckingham Palace)
        "radius": 50,
        "min_price": 20000,
        "max_price": 30000,
        "make": "Toyota",
        "transmission": "Automatic"
    }
    
    print("Input parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Process parameters
    processed = parameter_processor.process_parameters(params)
    display_processed_params(processed)
    
    # Apply filters to test data
    cars = create_test_cars()
    apply_filters_to_cars(processed, cars)


def example_2():
    """Example 2: Parameter processing with validation errors."""
    print("\n=== Example 2: Parameter Processing with Validation Errors ===")
    
    # Define search parameters with errors
    params = {
        "postcode": "INVALID",  # Invalid postcode
        "radius": 500,  # Too large
        "min_price": "£50,000",  # With currency symbol and comma
        "max_price": 20000,  # Less than min_price
        "make": "a",  # Too short
        "transmission": "auto"  # Will be normalized
    }
    
    print("Input parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Process parameters
    processed = parameter_processor.process_parameters(params)
    display_processed_params(processed)
    
    # Apply filters to test data
    cars = create_test_cars()
    apply_filters_to_cars(processed, cars)


def example_3():
    """Example 3: Year range filtering."""
    print("\n=== Example 3: Year Range Filtering ===")
    
    # Define search parameters
    params = {
        "min_year": 2019,
        "max_year": 2021,
        "transmission": "ANY"  # Will be handled gracefully
    }
    
    print("Input parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Process parameters
    processed = parameter_processor.process_parameters(params)
    display_processed_params(processed)
    
    # Apply filters to test data
    cars = create_test_cars()
    apply_filters_to_cars(processed, cars)


def example_4():
    """Example 4: Price range only."""
    print("\n=== Example 4: Price Range Only ===")
    
    # Define search parameters
    params = {
        "min_price": 20000,
        "max_price": 40000
    }
    
    print("Input parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    # Process parameters
    processed = parameter_processor.process_parameters(params)
    display_processed_params(processed)
    
    # Apply filters to test data
    cars = create_test_cars()
    apply_filters_to_cars(processed, cars)


def example_5():
    """Example 5: Transmission type filtering."""
    print("\n=== Example 5: Transmission Type Filtering ===")
    
    # Process each transmission type
    transmission_types = ["Automatic", "Manual", "Semi-Auto", "AUTOMATIC", "auto", "stick", "CVT"]
    
    for transmission in transmission_types:
        print(f"\nValidating transmission: '{transmission}'")
        params = {"transmission": transmission}
        
        # Process parameters
        processed = parameter_processor.process_parameters(params)
        
        # Show validation result
        if "transmission" in processed["valid_params"]:
            print(f"  Normalized to: '{processed['valid_params']['transmission']}'")
        else:
            print(f"  Invalid: {processed['invalid_params']['transmission']['error']}")


def main():
    """Run the parameter processing examples."""
    print("Search Parameter Processing Demo")
    print("================================")
    
    example_1()
    example_2()
    example_3()
    example_4()
    example_5()
    
    print("\nParameter processing demonstration complete!")


if __name__ == "__main__":
    main() 