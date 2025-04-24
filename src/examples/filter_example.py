#!/usr/bin/env python3
"""
Example script demonstrating how to use the flexible filtering system.

This script shows how to:
1. Create simple and complex filters
2. Apply filters to car collections
3. Save and load filter presets
4. Combine filters with logical operators
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.filtering import filter_manager
from src.data.db_manager import db_manager
from src.examples.db_example import create_sample_cars

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run the filter example script."""
    print(f"Database path: {db_manager.db_path}")
    
    # Ensure sample cars exist in the database
    sample_cars = create_sample_cars()
    db_manager.save_cars(sample_cars)
    
    # Get all cars from database
    all_cars = db_manager.get_all_cars()
    print(f"\nLoaded {len(all_cars)} cars from database")
    
    # Example 1: Simple Filtering
    print("\n=== Example 1: Simple Filtering ===")
    
    # Filter by make
    query = filter_manager.create_query().make("Toyota")
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} Toyota cars:")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 2: Price Range Filtering
    print("\n=== Example 2: Price Range Filtering ===")
    
    # Filter by price range
    query = filter_manager.create_query().price_between(20000, 30000)
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars priced between $20,000 and $30,000:")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 3: Multiple Criteria Filtering
    print("\n=== Example 3: Multiple Criteria Filtering ===")
    
    # Filter by multiple criteria (AND logic)
    query = filter_manager.create_query()
    query.year_newer_than(2019).and_(
        filter_manager.create_query().price_max(30000)
    )
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars newer than 2019 AND priced under $30,000:")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 4: OR Logic
    print("\n=== Example 4: OR Logic ===")
    
    # Filter by make (Toyota OR Honda)
    toyota_query = filter_manager.create_query().make("Toyota")
    honda_query = filter_manager.create_query().make("Honda")
    
    query = filter_manager.create_query().or_(toyota_query, honda_query)
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars that are Toyota OR Honda:")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 5: Complex Query
    print("\n=== Example 5: Complex Query ===")
    
    # Create a complex query with nested AND/OR logic
    # (Toyota OR Honda) AND (price < 30000) AND (year >= 2019)
    toyota_honda_query = filter_manager.create_query()
    toyota_honda_query.or_(
        filter_manager.create_query().make("Toyota"),
        filter_manager.create_query().make("Honda")
    )
    
    price_query = filter_manager.create_query().price_max(30000)
    year_query = filter_manager.create_query().year_newer_than(2019)
    
    query = filter_manager.create_query().and_(toyota_honda_query, price_query, year_query)
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars that are (Toyota OR Honda) AND (price < $30k) AND (year >= 2019):")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 6: Filtering by Location
    print("\n=== Example 6: Filtering by Location ===")
    
    # Filter by location containing text
    query = filter_manager.create_query().location("Los")  # Should match "Los Angeles"
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars in locations containing 'Los':")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price} (Location: {car.location})")
    
    # Example 7: Negation
    print("\n=== Example 7: Negation ===")
    
    # Filter for NOT Toyota
    query = filter_manager.create_query().make("Toyota").not_()
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars that are NOT Toyota:")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 8: Save and Load Filters
    print("\n=== Example 8: Save and Load Filters ===")
    
    # Create a filter for affordable newer cars
    query = filter_manager.create_query()
    query.price_between(20000, 30000).and_(
        filter_manager.create_query().year_newer_than(2018)
    )
    
    # Save the filter
    filter_manager.save_filter("affordable_newer", query)
    print("Saved filter 'affordable_newer'")
    
    # Load the filter
    loaded_query = filter_manager.load_filter("affordable_newer")
    filtered_cars = filter_manager.filter_cars(all_cars, loaded_query)
    
    print(f"Found {len(filtered_cars)} cars using loaded filter 'affordable_newer':")
    for car in filtered_cars:
        print(f"- {car.year} {car.make} {car.model}: ${car.price}")
    
    # Example 9: Checking for NULL values
    print("\n=== Example 9: Checking for NULL values ===")
    
    # Filter for cars with missing price
    query = filter_manager.create_query().field("price").is_null()
    filtered_cars = filter_manager.filter_cars(all_cars, query)
    
    print(f"Found {len(filtered_cars)} cars with no price information:")
    for car in filtered_cars:
        print(f"- {car.year if car.year else 'Unknown year'} {car.make} {car.model}")
    
    # Example 10: Getting saved filters
    print("\n=== Example 10: Getting Saved Filters ===")
    
    # Create more saved filters
    toyota_query = filter_manager.create_query().make("Toyota")
    filter_manager.save_filter("toyota_only", toyota_query)
    
    luxury_query = filter_manager.create_query().price_min(40000)
    filter_manager.save_filter("luxury", luxury_query)
    
    # Get all saved filters
    saved_filters = filter_manager.get_saved_filters()
    print(f"Available saved filters: {saved_filters}")
    
    # Example 11: Delete a filter
    print("\n=== Example 11: Delete a Filter ===")
    
    # Delete a filter
    filter_manager.delete_filter("luxury")
    saved_filters = filter_manager.get_saved_filters()
    print(f"Saved filters after deletion: {saved_filters}")
    
    print("\nFlexible filtering system demonstration complete!")


if __name__ == "__main__":
    main() 