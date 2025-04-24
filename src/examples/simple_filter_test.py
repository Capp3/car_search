#!/usr/bin/env python3
"""
Simple test script for the filtering module.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.car import Car, CarCollection
from src.data.filtering import filter_manager


def main():
    """Run a simple test of the filtering system."""
    # Create test cars with proper attributes
    car1 = Car(id="1")
    car1.set_attribute("make", "Toyota", "test")
    car1.set_attribute("model", "Camry", "test")
    car1.set_attribute("year", 2020, "test")
    car1.set_attribute("price", 25000, "test")
    car1.set_attribute("mileage", 15000, "test")
    car1.set_attribute("date_listed", datetime.now() - timedelta(days=10), "test")
    car1.set_attribute("location", "New York", "test")
    
    car2 = Car(id="2")
    car2.set_attribute("make", "Honda", "test")
    car2.set_attribute("model", "Accord", "test")
    car2.set_attribute("year", 2019, "test")
    car2.set_attribute("price", 22000, "test")
    car2.set_attribute("mileage", 20000, "test")
    car2.set_attribute("date_listed", datetime.now() - timedelta(days=5), "test")
    car2.set_attribute("location", "Los Angeles", "test")
    
    car3 = Car(id="3")
    car3.set_attribute("make", "BMW", "test")
    car3.set_attribute("model", "X5", "test")
    car3.set_attribute("year", 2021, "test")
    car3.set_attribute("price", 45000, "test")
    car3.set_attribute("mileage", 5000, "test")
    car3.set_attribute("date_listed", datetime.now() - timedelta(days=1), "test")
    car3.set_attribute("location", "Chicago", "test")
    
    car4 = Car(id="4")
    car4.set_attribute("make", "Audi", "test")
    car4.set_attribute("model", "A4", "test")
    car4.set_attribute("year", 2018, "test")
    car4.set_attribute("price", 30000, "test")
    car4.set_attribute("mileage", 25000, "test")
    car4.set_attribute("date_listed", datetime.now() - timedelta(days=15), "test")
    car4.set_attribute("location", "Miami", "test")
    
    # Car with missing values
    car5 = Car(id="5")
    car5.set_attribute("make", "Ford", "test")
    car5.set_attribute("model", "Mustang", "test")
    # Note: year, price, mileage, and date_listed are intentionally not set
    car5.set_attribute("location", "Dallas", "test")
    
    # Create a car collection
    cars = [car1, car2, car3, car4, car5]
    car_collection = CarCollection(cars=cars)
    
    print(f"Created test data with {len(cars)} cars")
    
    # Test a simple filter
    print("\nTest 1: Filter by make")
    query = filter_manager.create_query().make("Toyota")
    filtered_cars = filter_manager.filter_cars(cars, query)
    print(f"Found {len(filtered_cars)} Toyota cars")
    for car in filtered_cars:
        print(f"- {car.make} {car.model}")
    
    # Test price range filter
    print("\nTest 2: Filter by price range")
    query = filter_manager.create_query().price_between(20000, 30000)
    filtered_cars = filter_manager.filter_cars(cars, query)
    print(f"Found {len(filtered_cars)} cars priced between $20,000 and $30,000")
    for car in filtered_cars:
        print(f"- {car.make} {car.model}: ${car.price}")
    
    # Test a complex filter
    print("\nTest 3: Complex filter")
    toyota_honda_query = filter_manager.create_query()
    toyota_honda_query.or_(
        filter_manager.create_query().make("Toyota"),
        filter_manager.create_query().make("Honda")
    )
    
    price_query = filter_manager.create_query().price_max(30000)
    year_query = filter_manager.create_query().year_newer_than(2019)
    
    query = filter_manager.create_query().and_(toyota_honda_query, price_query, year_query)
    filtered_cars = filter_manager.filter_cars(cars, query)
    print(f"Found {len(filtered_cars)} cars that are (Toyota OR Honda) AND (price < $30k) AND (year >= 2019)")
    for car in filtered_cars:
        print(f"- {car.make} {car.model}: ${car.price} ({car.year})")
    
    # Test null/not null filters
    print("\nTest 4: Filter for cars with no price")
    query = filter_manager.create_query().field("price").is_null()
    filtered_cars = filter_manager.filter_cars(cars, query)
    print(f"Found {len(filtered_cars)} cars with no price")
    for car in filtered_cars:
        print(f"- {car.make} {car.model}")
    
    # Test location contains
    print("\nTest 5: Filter by location containing 'Los'")
    query = filter_manager.create_query().location("Los")
    filtered_cars = filter_manager.filter_cars(cars, query)
    print(f"Found {len(filtered_cars)} cars in locations containing 'Los'")
    for car in filtered_cars:
        print(f"- {car.make} {car.model}: {car.location}")

if __name__ == "__main__":
    main() 