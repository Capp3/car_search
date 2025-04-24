"""
Mileage Analysis Service.

This module provides functionality to analyze car mileage data, including:
- Evaluating if mileage is reasonable for a car's age
- Estimating remaining lifespan based on current mileage
- Comparing mileage to similar models
- Calculating average annual mileage
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, cast
from datetime import datetime, date
import statistics
from dataclasses import dataclass

from src.models.car import Car, CarCollection

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MileageAnalysisResult:
    """Results of a mileage analysis."""
    car_id: str
    car_year: Optional[int]
    actual_mileage: Optional[int]
    expected_mileage: Optional[int]
    deviation_percent: Optional[float]  # How much actual differs from expected
    annual_mileage: Optional[float]  # Average miles driven per year
    mileage_rating: Optional[float]  # 0-10 scale, higher is better
    expected_lifespan: Optional[int]  # Expected remaining miles
    assessment: str  # Text summary of the analysis


class MileageAnalyzer:
    """
    Service for analyzing car mileage.
    
    This class provides methods to evaluate if a car's mileage is reasonable
    for its age and to estimate its remaining useful life.
    """
    
    # Average annual mileage by country
    AVERAGE_ANNUAL_MILEAGE = {
        "UK": 7400,  # Average UK annual mileage
        "US": 13500,  # Average US annual mileage
        "default": 10000,  # Default if country is unknown
    }
    
    # Estimated lifespans by make (in miles)
    MAKE_LIFESPANS = {
        "toyota": 250000,
        "lexus": 250000,
        "honda": 230000,
        "acura": 230000,
        "subaru": 220000,
        "mazda": 220000,
        "ford": 200000,
        "chevrolet": 200000,
        "nissan": 200000,
        "volkswagen": 190000,
        "audi": 180000,
        "bmw": 180000,
        "mercedes-benz": 180000,
        "kia": 180000,
        "hyundai": 180000,
        "volvo": 180000,
        "fiat": 150000,
        "mini": 150000,
        "land rover": 150000,
        "jaguar": 150000,
        "default": 180000,  # Default if make is unknown
    }
    
    def __init__(self, country: str = "UK"):
        """
        Initialize the mileage analyzer.
        
        Args:
            country: The country to use for average mileage calculations
                     (default: "UK")
        """
        self.country = country
        self.annual_mileage = self.AVERAGE_ANNUAL_MILEAGE.get(
            country, self.AVERAGE_ANNUAL_MILEAGE["default"]
        )
        logger.info(f"Mileage analyzer initialized for {country}")
    
    def analyze_mileage(self, car: Car) -> MileageAnalysisResult:
        """
        Analyze the mileage of a car.
        
        Args:
            car: The car to analyze
            
        Returns:
            MileageAnalysisResult with analysis data
        """
        # Extract required data
        car_id = car.id
        car_year = car.year
        actual_mileage = car.mileage
        
        # If we don't have year or mileage, we can't analyze
        if car_year is None or actual_mileage is None:
            assessment = "Insufficient data for mileage analysis"
            return MileageAnalysisResult(
                car_id=car_id,
                car_year=car_year,
                actual_mileage=actual_mileage,
                expected_mileage=None,
                deviation_percent=None,
                annual_mileage=None,
                mileage_rating=None,
                expected_lifespan=None,
                assessment=assessment
            )
        
        # Calculate car age
        current_year = datetime.now().year
        car_age = current_year - car_year
        
        # Calculate expected mileage based on average annual mileage
        expected_mileage = self.annual_mileage * car_age
        
        # Calculate deviation from expected
        deviation = actual_mileage - expected_mileage
        if expected_mileage > 0:
            deviation_percent = (deviation / expected_mileage) * 100
        else:
            deviation_percent = 0
        
        # Calculate annual mileage
        if car_age > 0:
            annual_mileage = float(actual_mileage / car_age)
        else:
            # For current year cars, use actual mileage
            annual_mileage = float(actual_mileage)
        
        # Determine mileage rating (0-10 scale, higher is better)
        # 10 = well below average mileage, 0 = well above average mileage
        if expected_mileage > 0:
            # Base the rating on how much lower than expected the mileage is
            ratio = actual_mileage / expected_mileage
            if ratio <= 0.5:  # 50% or less of expected mileage
                mileage_rating = 10.0
            elif ratio <= 1.0:  # between 50% and 100% of expected
                mileage_rating = 7.5 + (1.0 - ratio) * 5.0
            elif ratio <= 1.5:  # between 100% and 150% of expected
                mileage_rating = 5.0 + (1.5 - ratio) * 5.0
            else:  # more than 150% of expected
                mileage_rating = max(0.0, 5.0 - (ratio - 1.5) * 2.0)
        else:
            mileage_rating = 5.0  # Default for new cars
        
        # Calculate expected remaining lifespan
        make = car.make.lower() if car.make else "default"
        total_lifespan = self.MAKE_LIFESPANS.get(make, self.MAKE_LIFESPANS["default"])
        expected_lifespan = max(0, total_lifespan - actual_mileage)
        
        # Generate assessment text
        assessment = self._generate_assessment(
            car_year,
            car_age,
            actual_mileage,
            expected_mileage,
            deviation_percent,
            annual_mileage,
            mileage_rating,
            expected_lifespan
        )
        
        # Store analysis results as computed attributes
        car.compute_attribute("mileage_assessment", assessment)
        car.compute_attribute("mileage_rating", mileage_rating)
        car.compute_attribute("expected_lifespan", expected_lifespan)
        car.compute_attribute("annual_mileage", annual_mileage)
        
        return MileageAnalysisResult(
            car_id=car_id,
            car_year=car_year,
            actual_mileage=actual_mileage,
            expected_mileage=expected_mileage,
            deviation_percent=deviation_percent,
            annual_mileage=annual_mileage,
            mileage_rating=mileage_rating,
            expected_lifespan=expected_lifespan,
            assessment=assessment
        )
    
    def _generate_assessment(
        self,
        car_year: int,
        car_age: int,
        actual_mileage: int,
        expected_mileage: int,
        deviation_percent: float,
        annual_mileage: float,
        mileage_rating: float,
        expected_lifespan: int
    ) -> str:
        """
        Generate a human-readable assessment of the mileage analysis.
        
        Args:
            car_year: Year the car was manufactured
            car_age: Age of the car in years
            actual_mileage: Actual mileage of the car
            expected_mileage: Expected mileage based on age
            deviation_percent: Percentage deviation from expected
            annual_mileage: Average annual mileage
            mileage_rating: Mileage rating on a 0-10 scale
            expected_lifespan: Expected remaining mileage
            
        Returns:
            A string containing the assessment
        """
        # Car age description
        if car_age == 0:
            age_desc = "a current year model"
        elif car_age == 1:
            age_desc = "a 1-year-old vehicle"
        else:
            age_desc = f"a {car_age}-year-old vehicle"
        
        # Mileage comparison to expected
        if deviation_percent <= -30:
            mileage_desc = f"significantly below average ({abs(deviation_percent):.0f}% less)"
        elif deviation_percent <= -10:
            mileage_desc = f"below average ({abs(deviation_percent):.0f}% less)"
        elif deviation_percent <= 10:
            mileage_desc = "around average"
        elif deviation_percent <= 30:
            mileage_desc = f"above average ({deviation_percent:.0f}% more)"
        else:
            mileage_desc = f"significantly above average ({deviation_percent:.0f}% more)"
        
        # Annual mileage description
        annual_avg = self.annual_mileage
        if annual_mileage <= annual_avg * 0.5:
            annual_desc = f"very low annual mileage of {annual_mileage:,.0f} miles/year"
        elif annual_mileage <= annual_avg * 0.8:
            annual_desc = f"below average annual mileage of {annual_mileage:,.0f} miles/year"
        elif annual_mileage <= annual_avg * 1.2:
            annual_desc = f"average annual mileage of {annual_mileage:,.0f} miles/year"
        elif annual_mileage <= annual_avg * 1.5:
            annual_desc = f"above average annual mileage of {annual_mileage:,.0f} miles/year"
        else:
            annual_desc = f"very high annual mileage of {annual_mileage:,.0f} miles/year"
        
        # Expected lifespan description
        if expected_lifespan <= 20000:
            lifespan_desc = f"limited expected remaining life of {expected_lifespan:,} miles"
        elif expected_lifespan <= 50000:
            lifespan_desc = f"moderate expected remaining life of {expected_lifespan:,} miles"
        elif expected_lifespan <= 100000:
            lifespan_desc = f"good expected remaining life of {expected_lifespan:,} miles"
        else:
            lifespan_desc = f"excellent expected remaining life of {expected_lifespan:,} miles"
        
        # Build the full assessment
        assessment = (
            f"This is {age_desc} with {actual_mileage:,} miles, which is {mileage_desc} "
            f"for its age. It has a {annual_desc} and {lifespan_desc}."
        )
        
        return assessment
    
    def analyze_car_collection(self, cars: CarCollection) -> Dict[str, MileageAnalysisResult]:
        """
        Analyze the mileage of all cars in a collection.
        
        Args:
            cars: The collection of cars to analyze
            
        Returns:
            Dict mapping car IDs to their MileageAnalysisResult
        """
        results = {}
        for car in cars:
            results[car.id] = self.analyze_mileage(car)
        return results
    
    def compare_to_similar_models(
        self, target_car: Car, other_cars: CarCollection
    ) -> Dict[str, Any]:
        """
        Compare a car's mileage to similar models.
        
        Args:
            target_car: The car to compare
            other_cars: Collection of similar cars to compare against
            
        Returns:
            Dictionary with comparison results
        """
        if target_car.mileage is None:
            return {
                "status": "error",
                "message": "Target car has no mileage data"
            }
        
        # Filter for similar cars (same make and model) with non-None mileage
        similar_cars = []
        for car in other_cars:
            if (car.make == target_car.make and 
                car.model == target_car.model and 
                car.mileage is not None and 
                car.id != target_car.id):
                similar_cars.append(car)
        
        if not similar_cars:
            return {
                "status": "no_data",
                "message": "No similar cars found for comparison"
            }
        
        # Extract mileages, ensuring none are None (we filtered above)
        mileages = [car.mileage for car in similar_cars if car.mileage is not None]
        
        # Calculate statistics - we know these are not None due to our filter
        avg_mileage = statistics.mean(mileages)
        median_mileage = statistics.median(mileages)
        min_mileage = min(mileages)
        max_mileage = max(mileages)
        
        # Calculate percentile of target car within similar cars
        target_mileage = cast(int, target_car.mileage)  # We checked for None above
        all_mileages = sorted(mileages + [target_mileage])
        percentile = all_mileages.index(target_mileage) / len(all_mileages) * 100
        
        # Determine if the mileage is good compared to similar cars
        if target_mileage <= avg_mileage:
            comparison = "lower"
            assessment = "better"
        else:
            comparison = "higher"
            assessment = "worse"
        
        return {
            "status": "success",
            "target_mileage": target_mileage,
            "similar_car_count": len(similar_cars),
            "average_mileage": avg_mileage,
            "median_mileage": median_mileage,
            "min_mileage": min_mileage,
            "max_mileage": max_mileage,
            "percentile": percentile,
            "comparison": comparison,
            "assessment": assessment,
            "summary": (
                f"This {target_car.year} {target_car.make} {target_car.model} has a mileage of "
                f"{target_mileage:,} miles, which is {comparison} than the average of "
                f"{avg_mileage:,.0f} miles for similar models. This is {assessment} than average."
            )
        }


# Create a singleton instance for convenient access
mileage_analyzer = MileageAnalyzer() 