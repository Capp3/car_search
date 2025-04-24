#!/usr/bin/env python3
"""
Example script demonstrating the car analysis features, including:
- Mileage analysis
- Condition assessment

This script shows how to:
1. Create sample cars with different attributes
2. Analyze the mileage of these cars
3. Assess the condition of these cars
4. Display the analysis results
"""

import os
import sys
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.car import Car, CarCollection
from src.services.mileage_analysis import mileage_analyzer
from src.services.condition_assessment import condition_assessor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_test_cars():
    """Create a collection of test cars with various attributes."""
    # Car 1: New Toyota with low mileage
    car1 = Car(id="1")
    car1.set_attribute("make", "Toyota", "test")
    car1.set_attribute("model", "Camry", "test")
    car1.set_attribute("year", 2022, "test")
    car1.set_attribute("price", 25000, "test")
    car1.set_attribute("mileage", 5000, "test")
    car1.set_attribute("transmission", "Automatic", "test")
    car1.set_attribute("location", "London", "test")
    car1.set_attribute("condition", "Excellent", "test")
    car1.set_attribute("description", "Almost new Toyota Camry in excellent condition. One owner, full service history.", "test")
    
    # Car 2: Older Honda with average mileage
    car2 = Car(id="2")
    car2.set_attribute("make", "Honda", "test")
    car2.set_attribute("model", "Accord", "test")
    car2.set_attribute("year", 2016, "test")
    car2.set_attribute("price", 12000, "test")
    car2.set_attribute("mileage", 75000, "test")
    car2.set_attribute("transmission", "Manual", "test")
    car2.set_attribute("location", "Manchester", "test")
    car2.set_attribute("condition", "Good", "test")
    car2.set_attribute("description", "Well-maintained Honda Accord. Regular service history. Some minor scratches on the rear bumper.", "test")
    
    # Car 3: Luxury car with low mileage
    car3 = Car(id="3")
    car3.set_attribute("make", "BMW", "test")
    car3.set_attribute("model", "X5", "test")
    car3.set_attribute("year", 2020, "test")
    car3.set_attribute("price", 45000, "test")
    car3.set_attribute("mileage", 15000, "test")
    car3.set_attribute("transmission", "Automatic", "test")
    car3.set_attribute("location", "Birmingham", "test")
    car3.set_attribute("condition", "Very Good", "test")
    car3.set_attribute("description", "Premium BMW X5 with low mileage. Still under manufacturer warranty. Full options package.", "test")
    
    # Car 4: Older car with high mileage and issues
    car4 = Car(id="4")
    car4.set_attribute("make", "Ford", "test")
    car4.set_attribute("model", "Focus", "test")
    car4.set_attribute("year", 2012, "test")
    car4.set_attribute("price", 4500, "test")
    car4.set_attribute("mileage", 130000, "test")
    car4.set_attribute("transmission", "Manual", "test")
    car4.set_attribute("location", "Bristol", "test")
    car4.set_attribute("condition", "Fair", "test")
    car4.set_attribute("description", "Ford Focus with high mileage. Some rust on the doors and needs new brake pads. Engine runs well but has a small oil leak.", "test")
    
    # Car 5: Unknown condition with missing data
    car5 = Car(id="5")
    car5.set_attribute("make", "Volkswagen", "test")
    car5.set_attribute("model", "Golf", "test")
    car5.set_attribute("year", 2015, "test")
    car5.set_attribute("price", 10000, "test")
    car5.set_attribute("transmission", "Automatic", "test")
    car5.set_attribute("location", "Glasgow", "test")
    car5.set_attribute("description", "VW Golf in great shape. Clean interior.", "test")
    
    return CarCollection(cars=[car1, car2, car3, car4, car5])


def display_car_info(car: Car):
    """Display basic information about a car."""
    print("\n=== Car Information ===")
    print(f"ID: {car.id}")
    print(f"Make/Model: {car.make} {car.model}")
    print(f"Year: {car.year}")
    print(f"Mileage: {car.mileage:,} miles" if car.mileage else "Mileage: Unknown")
    print(f"Price: £{car.price:,}" if car.price else "Price: Unknown")
    print(f"Condition: {car.get_attribute('condition')}" if car.get_attribute('condition') else "Condition: Not specified")
    print(f"Description: {car.get_attribute('description')}")


def display_mileage_analysis(car: Car):
    """Analyze and display mileage analysis for a car."""
    print("\n=== Mileage Analysis ===")
    
    # Analyze the car's mileage
    analysis = mileage_analyzer.analyze_mileage(car)
    
    if car.mileage is None:
        print("Mileage information not available for this vehicle.")
        return
    
    print(f"Actual Mileage: {analysis.actual_mileage:,} miles")
    
    if analysis.expected_mileage is not None:
        print(f"Expected Mileage: {analysis.expected_mileage:,} miles")
        print(f"Deviation: {analysis.deviation_percent:+.1f}% from expected")
    
    if analysis.annual_mileage is not None:
        print(f"Average Annual Mileage: {analysis.annual_mileage:,.0f} miles/year")
    
    if analysis.mileage_rating is not None:
        print(f"Mileage Rating: {analysis.mileage_rating:.1f}/10")
    
    if analysis.expected_lifespan is not None:
        print(f"Expected Remaining Life: {analysis.expected_lifespan:,} miles")
    
    print("\nAssessment:")
    print(analysis.assessment)


def display_condition_assessment(car: Car):
    """Assess and display condition assessment for a car."""
    print("\n=== Condition Assessment ===")
    
    # Assess the car's condition
    assessment = condition_assessor.assess_condition(car)
    
    print(f"Condition Rating: {assessment.condition_rating:.1f}/10")
    print(f"Condition Description: {assessment.condition_description}")
    
    if assessment.estimated_maintenance_cost is not None:
        print(f"Estimated Annual Maintenance: £{assessment.estimated_maintenance_cost:,.0f}")
    
    if assessment.potential_issues:
        print("\nPotential Issues:")
        for issue in assessment.potential_issues:
            print(f"- {issue}")
    
    print("\nAssessment:")
    print(assessment.assessment)


def compare_cars(cars: CarCollection):
    """Compare the analysis results for all cars in the collection."""
    print("\n=== Car Comparison ===")
    
    # Analyze all cars
    mileage_analyses = mileage_analyzer.analyze_car_collection(cars)
    condition_assessments = condition_assessor.assess_car_collection(cars)
    
    print(f"{'ID':<3} {'Make/Model':<20} {'Year':<5} {'Mileage':<10} {'Condition':<10} {'Mileage Rating':<15} {'Cond. Rating':<15} {'Maint. Cost':<12}")
    print("-" * 100)
    
    for car in cars:
        mileage_analysis = mileage_analyses.get(car.id)
        condition_assessment = condition_assessments.get(car.id)
        
        mileage_str = f"{car.mileage:,}" if car.mileage is not None else "Unknown"
        
        # Handle potential None values safely
        mileage_rating = f"{mileage_analysis.mileage_rating:.1f}/10" if mileage_analysis and mileage_analysis.mileage_rating is not None else "N/A"
        cond_rating = f"{condition_assessment.condition_rating:.1f}/10" if condition_assessment else "N/A"
        
        # Check if condition assessment exists before accessing properties
        condition_desc = condition_assessment.condition_description if condition_assessment else "Unknown"
        maint_cost = f"£{condition_assessment.estimated_maintenance_cost:,.0f}" if condition_assessment and condition_assessment.estimated_maintenance_cost is not None else "N/A"
        
        # Get make and model safely
        make = car.make if hasattr(car, 'make') and car.make is not None else ""
        model = car.model if hasattr(car, 'model') and car.model is not None else ""
        make_model = f"{make} {model}".strip()
        
        # Get year safely
        year_str = str(car.year) if hasattr(car, 'year') and car.year is not None else "N/A"
        
        print(f"{car.id:<3} {make_model:<20} {year_str:<5} {mileage_str:<10} {condition_desc:<10} {mileage_rating:<15} {cond_rating:<15} {maint_cost:<12}")


def main():
    """Run the car analysis examples."""
    print("Car Analysis Demo")
    print("================")
    
    # Create test cars
    cars = create_test_cars()
    
    # Analyze and display each car
    for car in cars:
        display_car_info(car)
        display_mileage_analysis(car)
        display_condition_assessment(car)
        print("\n" + "=" * 80)
    
    # Compare all cars
    compare_cars(cars)
    
    print("\nCar analysis demonstration complete!")


if __name__ == "__main__":
    main() 