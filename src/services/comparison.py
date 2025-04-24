"""
Car comparison service.

This module provides functionality to compare cars based on various criteria
and calculate value-for-money scores.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import statistics
from dataclasses import dataclass

from src.models import Car, CarCollection

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ComparisonFactor:
    """
    Represents a factor used in car comparisons.
    
    This class defines how a specific car attribute should be used when
    comparing cars, including its weight and whether higher values are better.
    """
    name: str  # Name of the attribute to compare
    weight: float  # Weight of this factor in the overall comparison (0-1)
    higher_is_better: bool  # Whether higher values are better
    formatter: Optional[str] = None  # Format string for display
    
    def get_value(self, car: Car) -> Optional[float]:
        """
        Get the value of this factor for a car.
        
        Args:
            car: The car to evaluate.
            
        Returns:
            The factor value as a float, or None if not available.
        """
        raw_value = car.get_attribute(self.name)
        
        if raw_value is None:
            return None
            
        # Convert to float if necessary
        if isinstance(raw_value, (int, float)):
            return float(raw_value)
        
        # Try to extract a numeric value from a string
        if isinstance(raw_value, str):
            try:
                return float(raw_value.replace(',', ''))
            except ValueError:
                return None
        
        return None
    
    def format_value(self, value: Any) -> str:
        """
        Format a value for display.
        
        Args:
            value: The value to format.
            
        Returns:
            The formatted value as a string.
        """
        if value is None:
            return "N/A"
            
        if self.formatter:
            return self.formatter.format(value)
            
        return str(value)


class ComparisonService:
    """
    Service for comparing cars based on various criteria.
    
    This class provides methods to compare cars based on price, reliability,
    features, and other factors to determine their relative value.
    """
    
    # Default comparison factors
    DEFAULT_FACTORS = [
        ComparisonFactor("price", 0.3, False, "£{:,.0f}"),
        ComparisonFactor("mileage", 0.2, False, "{:,} miles"),
        ComparisonFactor("year", 0.15, True, "{}"),
        ComparisonFactor("reliability_score", 0.25, True, "{:.1f}/10"),
        ComparisonFactor("running_cost", 0.1, False, "£{:.0f}/year"),
    ]
    
    def __init__(self, factors: Optional[List[ComparisonFactor]] = None):
        """
        Initialize the comparison service.
        
        Args:
            factors: List of factors to use for comparisons (default: DEFAULT_FACTORS).
        """
        self.factors = factors or self.DEFAULT_FACTORS
        logger.info(f"Comparison service initialized with {len(self.factors)} factors")
    
    def calculate_value_score(self, car: Car) -> float:
        """
        Calculate a value-for-money score for a car.
        
        This method evaluates a car based on the configured comparison factors
        and returns a score between 0 and 10, where higher is better.
        
        Args:
            car: The car to evaluate.
            
        Returns:
            A value score between 0 and 10.
        """
        # Check if the value score is already computed
        if car.has_attribute("value_score"):
            return car.get_attribute("value_score")
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for factor in self.factors:
            value = factor.get_value(car)
            
            if value is not None:
                # Normalize the value to a 0-10 scale
                # This is a placeholder implementation - in a real application,
                # normalization would be more sophisticated
                normalized = self._normalize_value(factor.name, value)
                
                # Invert if lower values are better
                if not factor.higher_is_better:
                    normalized = 10 - normalized
                
                # Add the weighted contribution to the score
                weighted_score += normalized * factor.weight
                total_weight += factor.weight
        
        # Calculate the final score
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            # If no factors could be evaluated, use a default score
            final_score = 5.0
        
        # Store the value score as a computed attribute
        car.compute_attribute("value_score", final_score)
        
        return final_score
    
    def _normalize_value(self, factor_name: str, value: float) -> float:
        """
        Normalize a factor value to a 0-10 scale.
        
        Args:
            factor_name: Name of the factor.
            value: The value to normalize.
            
        Returns:
            A normalized value between 0 and 10.
        """
        # This is a simplified implementation - in a real application,
        # normalization would be based on statistical analysis of the market
        
        # Default normalization parameters
        min_val = 0.0
        max_val = 1.0
        
        # Factor-specific normalization
        if factor_name == "price":
            # For price, assume a range of £500-£50,000
            min_val = 500.0
            max_val = 50000.0
        elif factor_name == "mileage":
            # For mileage, assume a range of 0-150,000 miles
            min_val = 0.0
            max_val = 150000.0
        elif factor_name == "year":
            # For year, assume a range of 2000-2023
            min_val = 2000.0
            max_val = 2023.0
        elif factor_name == "reliability_score":
            # For reliability score, assume it's already on a 0-10 scale
            min_val = 0.0
            max_val = 10.0
        elif factor_name == "running_cost":
            # For running cost, assume a range of £500-£5,000 per year
            min_val = 500.0
            max_val = 5000.0
        
        # Clamp the value to the min-max range
        clamped = max(min_val, min(value, max_val))
        
        # Normalize to 0-10 scale
        normalized = 10.0 * (clamped - min_val) / (max_val - min_val)
        
        return normalized
    
    def compare_cars(self, cars: CarCollection) -> Dict[str, Any]:
        """
        Compare a collection of cars.
        
        This method evaluates each car in the collection, calculates their value scores,
        and returns a comparison report.
        
        Args:
            cars: The collection of cars to compare.
            
        Returns:
            A dictionary containing comparison results.
        """
        if len(cars) == 0:
            logger.warning("No cars to compare")
            return {"cars": [], "best_value": None, "factors": {}}
        
        # Calculate value scores for all cars
        for car in cars:
            self.calculate_value_score(car)
        
        # Sort by value score (highest first)
        sorted_cars = cars.sort_by("value_score", reverse=True)
        
        # Collect results for each factor
        factor_results = {}
        for factor in self.factors:
            values = []
            car_values = []
            
            for car in cars:
                value = factor.get_value(car)
                if value is not None:
                    values.append(value)
                    car_values.append((car.id, value))
            
            # Calculate statistics if there are values
            stats = {}
            if values:
                stats = {
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values) if values else None,
                    "median": statistics.median(values) if values else None,
                }
            
            # Sort by this factor (higher_is_better determines direction)
            sorted_car_values = sorted(
                car_values,
                key=lambda x: x[1],
                reverse=factor.higher_is_better
            )
            
            # Best car for this factor
            best_car_id = sorted_car_values[0][0] if sorted_car_values else None
            
            factor_results[factor.name] = {
                "name": factor.name,
                "weight": factor.weight,
                "higher_is_better": factor.higher_is_better,
                "statistics": stats,
                "best_car_id": best_car_id,
                "car_values": dict(car_values),
            }
        
        # Get the best value car (first in the sorted list)
        best_value = sorted_cars[0] if len(sorted_cars) > 0 else None
        
        # Build the comparison result
        result = {
            "cars": [
                {
                    "id": car.id,
                    "title": car.title or f"Car {car.id}",
                    "value_score": car.get_attribute("value_score"),
                    "factors": {
                        factor.name: {
                            "value": factor.get_value(car),
                            "formatted": factor.format_value(factor.get_value(car)),
                        }
                        for factor in self.factors
                    },
                }
                for car in sorted_cars
            ],
            "best_value": {
                "id": best_value.id,
                "title": best_value.title or f"Car {best_value.id}",
                "value_score": best_value.get_attribute("value_score"),
            } if best_value else None,
            "factors": factor_results,
        }
        
        return result
    
    def explain_value_score(self, car: Car) -> Dict[str, Any]:
        """
        Explain how a car's value score was calculated.
        
        This method provides a detailed breakdown of the factors that
        contributed to a car's value score.
        
        Args:
            car: The car to explain.
            
        Returns:
            A dictionary with the explanation.
        """
        if not car.has_attribute("value_score"):
            # Calculate the value score if it doesn't exist
            self.calculate_value_score(car)
        
        explanation = {
            "car_id": car.id,
            "title": car.title or f"Car {car.id}",
            "value_score": car.get_attribute("value_score"),
            "factors": [],
        }
        
        for factor in self.factors:
            value = factor.get_value(car)
            
            if value is not None:
                # Normalize the value
                normalized = self._normalize_value(factor.name, value)
                
                # Invert if lower values are better
                if not factor.higher_is_better:
                    normalized = 10 - normalized
                
                # Calculate the weighted contribution
                contribution = normalized * factor.weight
                
                explanation["factors"].append({
                    "name": factor.name,
                    "weight": factor.weight,
                    "value": value,
                    "formatted": factor.format_value(value),
                    "normalized": normalized,
                    "contribution": contribution,
                })
        
        # Sort factors by contribution (highest first)
        explanation["factors"] = sorted(
            explanation["factors"],
            key=lambda x: x["contribution"],
            reverse=True
        )
        
        return explanation


# Create a singleton instance of the comparison service
comparison_service = ComparisonService()
