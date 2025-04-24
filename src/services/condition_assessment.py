"""
Condition Assessment Service.

This module provides functionality to analyze and assess the condition of cars,
including:
- Evaluating overall condition based on age, mileage, and reported condition
- Identifying potential issues based on make, model, and age
- Estimating maintenance needs and costs based on condition
- Providing a standardized condition rating
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, date
import re
from dataclasses import dataclass
import json

from src.models.car import Car, CarCollection

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ConditionAssessmentResult:
    """Results of a condition assessment."""
    car_id: str
    condition_rating: float  # 0-10 scale, higher is better
    condition_description: str  # Text description of condition (Excellent, Good, etc.)
    estimated_maintenance_cost: Optional[float]  # Estimated yearly cost
    potential_issues: List[str]  # List of potential issues
    assessment: str  # Text summary of the assessment


class ConditionAssessor:
    """
    Service for assessing car condition.
    
    This class provides methods to evaluate the condition of a car based
    on various factors and to estimate potential issues and maintenance costs.
    """
    
    # Condition ratings and descriptions
    CONDITION_RATINGS = {
        (9.0, 10.0): "Excellent",
        (7.0, 8.9): "Very Good",
        (5.0, 6.9): "Good",
        (3.0, 4.9): "Fair",
        (0.0, 2.9): "Poor"
    }
    
    # Base maintenance costs by car class (in £ per year)
    BASE_MAINTENANCE_COSTS = {
        "economy": 500,
        "standard": 800,
        "luxury": 1500,
        "premium": 2000,
        "exotic": 3500,
        "default": 1000
    }
    
    # Car class categorization by make
    CAR_CLASSES = {
        "toyota": "economy",
        "honda": "economy",
        "nissan": "economy",
        "ford": "standard",
        "chevrolet": "standard",
        "hyundai": "economy",
        "kia": "economy",
        "mazda": "standard",
        "volkswagen": "standard",
        "subaru": "standard",
        "bmw": "luxury",
        "mercedes-benz": "luxury",
        "audi": "luxury",
        "lexus": "luxury",
        "jaguar": "premium",
        "land rover": "premium",
        "porsche": "premium",
        "maserati": "exotic",
        "ferrari": "exotic",
        "lamborghini": "exotic",
        "bentley": "exotic",
        "rolls-royce": "exotic",
        "default": "standard"
    }
    
    # Common issues by make (make -> list of potential issues)
    COMMON_ISSUES_BY_MAKE = {
        "bmw": [
            "Oil leaks", "Cooling system issues", "Electronics problems",
            "Timing chain failures", "VANOS system failures"
        ],
        "audi": [
            "Electrical issues", "Oil consumption", "Timing chain problems",
            "DSG transmission issues", "Water pump failures"
        ],
        "mercedes-benz": [
            "Rust issues", "Airmatic suspension problems", "Electrical issues",
            "Oil leaks", "Transmission problems"
        ],
        "volkswagen": [
            "Timing belt issues", "Water pump failures", "Electrical problems",
            "DSG transmission issues", "Carbon buildup in direct injection engines"
        ],
        "ford": [
            "Rust issues", "Automatic transmission failures", "Power steering problems",
            "Spark plug issues", "Cooling system problems"
        ],
        "toyota": [
            "Oil consumption in some engines", "Water pump failures",
            "Exhaust issues", "ABS module failures"
        ],
        "honda": [
            "Automatic transmission issues in older models", "Airbag recalls",
            "A/C system failures", "Power steering pump issues"
        ],
        "default": [
            "Wear and tear issues based on age and mileage", 
            "Routine maintenance requirements"
        ]
    }
    
    # Age-specific issues (age range in years -> list of issues)
    AGE_SPECIFIC_ISSUES = {
        (0, 3): [
            "Minor warranty items", "Software updates", "Initial quality issues"
        ],
        (4, 7): [
            "Battery replacements", "Brake system wear", "Minor electrical issues",
            "Exhaust system issues", "Suspension wear"
        ],
        (8, 12): [
            "Major component wear", "Transmission problems", "Engine seals and gaskets",
            "Cooling system failures", "Electronic module failures", "Increased corrosion"
        ],
        (13, 100): [
            "Comprehensive rust issues", "Major mechanical components",
            "Electrical system problems", "Suspension rebuilds", "Extensive maintenance requirements"
        ]
    }
    
    # Mileage-specific issues (mileage range -> list of issues)
    MILEAGE_SPECIFIC_ISSUES = {
        (0, 20000): [
            "Minor initial quality issues", "Break-in period maintenance"
        ],
        (20001, 60000): [
            "Routine maintenance items", "Brake pad replacements",
            "Tire replacements", "Minor wear items"
        ],
        (60001, 100000): [
            "Timing belt/chain service", "Water pump replacements",
            "Suspension components", "Clutch wear (manual transmissions)"
        ],
        (100001, 150000): [
            "Major component wear", "Transmission service or issues",
            "Engine component wear", "Increased electrical problems"
        ],
        (150001, 1000000): [
            "Comprehensive mechanical attention required", "Major engine and transmission concerns",
            "Significant wear on all systems", "Extensive restoration needs"
        ]
    }
    
    # Keywords in description that indicate condition issues
    CONDITION_ISSUE_KEYWORDS = [
        "rust", "damage", "dent", "scratch", "worn", "issue", "problem",
        "leak", "repair", "needs", "fix", "cracked", "broken", "fault"
    ]
    
    def __init__(self):
        """Initialize the condition assessor."""
        logger.info("Condition assessor initialized")
    
    def assess_condition(self, car: Car) -> ConditionAssessmentResult:
        """
        Assess the condition of a car.
        
        Args:
            car: The car to assess
            
        Returns:
            ConditionAssessmentResult with assessment data
        """
        # Extract required data
        car_id = car.id
        
        # First check if we have a reported condition from the listing
        reported_condition = car.get_attribute("condition")
        year = car.year
        mileage = car.mileage
        make = car.make.lower() if car.make else None
        model = car.model
        description = car.get_attribute("description")
        
        # Calculate condition rating based on available data
        condition_rating = self._calculate_condition_rating(
            reported_condition, year, mileage, make, model, description
        )
        
        # Get condition description based on rating
        condition_description = self._get_condition_description(condition_rating)
        
        # Estimate maintenance costs
        maintenance_cost = self._estimate_maintenance_cost(
            year, mileage, make, condition_rating
        )
        
        # Identify potential issues
        potential_issues = self._identify_potential_issues(
            year, mileage, make, condition_rating, description
        )
        
        # Generate assessment text
        assessment = self._generate_assessment(
            car, condition_rating, condition_description, 
            maintenance_cost, potential_issues
        )
        
        # Store assessment results as computed attributes
        car.compute_attribute("condition_rating", condition_rating)
        car.compute_attribute("condition_description", condition_description)
        car.compute_attribute("maintenance_cost", maintenance_cost)
        car.compute_attribute("potential_issues", json.dumps(potential_issues))
        car.compute_attribute("condition_assessment", assessment)
        
        return ConditionAssessmentResult(
            car_id=car_id,
            condition_rating=condition_rating,
            condition_description=condition_description,
            estimated_maintenance_cost=maintenance_cost,
            potential_issues=potential_issues,
            assessment=assessment
        )
    
    def _calculate_condition_rating(
        self,
        reported_condition: Optional[str],
        year: Optional[int],
        mileage: Optional[int],
        make: Optional[str],
        model: Optional[str],
        description: Optional[str]
    ) -> float:
        """
        Calculate a condition rating on a scale of 0-10.
        
        This uses a combination of reported condition, age, mileage, and
        description analysis to estimate the condition.
        
        Args:
            reported_condition: Condition reported in the listing (if any)
            year: Year of manufacture
            mileage: Mileage on the odometer
            make: Make of the car
            model: Model of the car
            description: Description text from the listing
            
        Returns:
            Condition rating on a 0-10 scale, higher is better
        """
        # Start with a default rating
        rating = 5.0
        factors_used = 0
        
        # Adjust based on reported condition if available
        if reported_condition:
            condition_factor = self._condition_text_to_rating(reported_condition)
            if condition_factor is not None:
                rating += condition_factor
                factors_used += 1
        
        # Adjust based on age if available
        if year is not None:
            current_year = datetime.now().year
            age = current_year - year
            
            # Age factor: newer cars get higher ratings
            # Max impact: ±2.5 points
            if age <= 2:
                age_factor = 2.5  # Very new
            elif age <= 5:
                age_factor = 1.5  # Relatively new
            elif age <= 8:
                age_factor = 0  # Average age
            elif age <= 12:
                age_factor = -1.0  # Older
            else:
                age_factor = -2.5  # Very old
                
            rating += age_factor
            factors_used += 1
        
        # Adjust based on mileage if available
        if mileage is not None:
            # Mileage factor: lower mileage gets higher ratings
            # Max impact: ±2.5 points
            if mileage <= 10000:
                mileage_factor = 2.5  # Very low
            elif mileage <= 30000:
                mileage_factor = 1.5  # Low
            elif mileage <= 60000:
                mileage_factor = 0.5  # Below average
            elif mileage <= 100000:
                mileage_factor = 0  # Average
            elif mileage <= 150000:
                mileage_factor = -1.0  # Above average
            else:
                mileage_factor = -2.5  # High
                
            rating += mileage_factor
            factors_used += 1
        
        # Adjust based on make reliability if available
        if make:
            # Make reliability factor: more reliable makes get higher ratings
            # Max impact: ±1.0 point
            if make in ["toyota", "lexus", "honda", "acura"]:
                make_factor = 1.0  # Very reliable
            elif make in ["mazda", "subaru", "kia", "hyundai"]:
                make_factor = 0.5  # Above average reliability
            elif make in ["ford", "chevrolet", "nissan", "volkswagen"]:
                make_factor = 0  # Average reliability
            elif make in ["bmw", "audi", "mercedes-benz", "volvo"]:
                make_factor = -0.5  # Below average reliability
            else:
                make_factor = 0  # Unknown or neutral
                
            rating += make_factor
            factors_used += 1
        
        # Adjust based on description analysis if available
        if description:
            # Count negative keywords in description
            description_lower = description.lower()
            issue_count = sum(1 for keyword in self.CONDITION_ISSUE_KEYWORDS 
                              if keyword in description_lower)
            
            # Description factor: more issues mentioned gets lower ratings
            # Max impact: -2.0 points
            if issue_count == 0:
                description_factor = 0  # No issues mentioned
            elif issue_count == 1:
                description_factor = -0.5  # Minor issue
            elif issue_count <= 3:
                description_factor = -1.0  # Multiple issues
            else:
                description_factor = -2.0  # Many issues
                
            rating += description_factor
            factors_used += 1
        
        # Ensure we have at least one factor, otherwise return default
        if factors_used == 0:
            return 5.0
        
        # Normalize the rating to account for the number of factors used
        # This prevents cars with less data from being unfairly penalized
        normalized_rating = (rating - 5.0) / factors_used + 5.0
        
        # Clamp to 0-10 range
        return max(0.0, min(10.0, normalized_rating))
    
    def _condition_text_to_rating(self, condition_text: str) -> Optional[float]:
        """
        Convert a textual condition description to a rating adjustment.
        
        Args:
            condition_text: The text description of condition
            
        Returns:
            Rating adjustment factor, or None if no match
        """
        condition_lower = condition_text.lower()
        
        if any(term in condition_lower for term in ["excellent", "perfect", "immaculate", "mint"]):
            return 3.5  # Excellent condition
        elif any(term in condition_lower for term in ["very good", "great", "superb"]):
            return 2.0  # Very good condition
        elif any(term in condition_lower for term in ["good", "clean", "tidy"]):
            return 0.5  # Good condition
        elif any(term in condition_lower for term in ["fair", "average", "okay", "ok"]):
            return -1.0  # Fair condition
        elif any(term in condition_lower for term in ["poor", "bad", "needs work", "project"]):
            return -3.5  # Poor condition
        else:
            return None  # Unknown condition description
    
    def _get_condition_description(self, rating: float) -> str:
        """
        Get a text description of a condition rating.
        
        Args:
            rating: Condition rating on a 0-10 scale
            
        Returns:
            Text description of the condition
        """
        for (min_rating, max_rating), description in self.CONDITION_RATINGS.items():
            if min_rating <= rating <= max_rating:
                return description
        
        # Fallback
        return "Unknown"
    
    def _estimate_maintenance_cost(
        self,
        year: Optional[int],
        mileage: Optional[int],
        make: Optional[str],
        condition_rating: float
    ) -> Optional[float]:
        """
        Estimate yearly maintenance costs based on condition and other factors.
        
        Args:
            year: Year of manufacture
            mileage: Mileage on the odometer
            make: Make of the car
            condition_rating: Condition rating on a 0-10 scale
            
        Returns:
            Estimated yearly maintenance cost in pounds, or None if insufficient data
        """
        # Need at least year or mileage to estimate maintenance costs
        if year is None and mileage is None:
            return None
        
        # Determine car class for base maintenance cost
        car_class = "default"
        if make:
            car_class = self.CAR_CLASSES.get(make, "default")
        
        base_cost = self.BASE_MAINTENANCE_COSTS[car_class]
        
        # Apply age factor if available
        age_factor = 1.0
        if year is not None:
            current_year = datetime.now().year
            age = current_year - year
            
            if age <= 3:
                age_factor = 0.7  # New cars cheaper to maintain
            elif age <= 6:
                age_factor = 0.9  # Still under warranty for major items
            elif age <= 10:
                age_factor = 1.2  # Starting to need more repairs
            else:
                age_factor = 1.5  # Older cars need more maintenance
        
        # Apply mileage factor if available
        mileage_factor = 1.0
        if mileage is not None:
            if mileage <= 20000:
                mileage_factor = 0.8  # Low mileage
            elif mileage <= 60000:
                mileage_factor = 1.0  # Average mileage
            elif mileage <= 100000:
                mileage_factor = 1.3  # Above average mileage
            else:
                mileage_factor = 1.6  # High mileage
        
        # Apply condition factor
        if condition_rating >= 8.0:
            condition_factor = 0.8  # Excellent condition
        elif condition_rating >= 6.0:
            condition_factor = 1.0  # Good condition
        elif condition_rating >= 4.0:
            condition_factor = 1.3  # Fair condition
        else:
            condition_factor = 1.8  # Poor condition
        
        # Calculate final cost
        cost = base_cost * age_factor * mileage_factor * condition_factor
        
        # Round to nearest £10
        return round(cost / 10) * 10
    
    def _identify_potential_issues(
        self,
        year: Optional[int],
        mileage: Optional[int],
        make: Optional[str],
        condition_rating: float,
        description: Optional[str]
    ) -> List[str]:
        """
        Identify potential issues based on car attributes.
        
        Args:
            year: Year of manufacture
            mileage: Mileage on the odometer
            make: Make of the car
            condition_rating: Condition rating on a 0-10 scale
            description: Description text from the listing
            
        Returns:
            List of potential issues
        """
        issues: Set[str] = set()
        
        # Add make-specific issues
        if make:
            make_issues = self.COMMON_ISSUES_BY_MAKE.get(
                make, self.COMMON_ISSUES_BY_MAKE["default"]
            )
            issues.update(make_issues[:2])  # Just add a couple of most common issues
        
        # Add age-specific issues
        if year is not None:
            current_year = datetime.now().year
            age = current_year - year
            
            for (min_age, max_age), age_issues in self.AGE_SPECIFIC_ISSUES.items():
                if min_age <= age <= max_age:
                    issues.update(age_issues[:2])  # Just add a couple of most relevant issues
                    break
        
        # Add mileage-specific issues
        if mileage is not None:
            for (min_mileage, max_mileage), mileage_issues in self.MILEAGE_SPECIFIC_ISSUES.items():
                if min_mileage <= mileage <= max_mileage:
                    issues.update(mileage_issues[:2])  # Just add a couple of most relevant issues
                    break
        
        # Extract issues mentioned in the description
        if description:
            description_lower = description.lower()
            for keyword in self.CONDITION_ISSUE_KEYWORDS:
                if keyword in description_lower:
                    # Find the context around the keyword
                    pattern = r'.{0,30}' + re.escape(keyword) + r'.{0,30}'
                    matches = re.findall(pattern, description_lower)
                    for match in matches:
                        issues.add(match.strip().capitalize())
        
        # Limit the number of issues based on condition rating
        # Excellent condition cars should have fewer potential issues
        max_issues = 10
        if condition_rating >= 8.0:
            max_issues = 2
        elif condition_rating >= 6.0:
            max_issues = 4
        elif condition_rating >= 4.0:
            max_issues = 6
        
        return list(issues)[:max_issues]
    
    def _generate_assessment(
        self,
        car: Car,
        condition_rating: float,
        condition_description: str,
        maintenance_cost: Optional[float],
        potential_issues: List[str]
    ) -> str:
        """
        Generate a human-readable assessment of the car's condition.
        
        Args:
            car: The car being assessed
            condition_rating: Condition rating on a 0-10 scale
            condition_description: Text description of the condition
            maintenance_cost: Estimated yearly maintenance cost
            potential_issues: List of potential issues
            
        Returns:
            A string containing the assessment
        """
        car_name = f"{car.year} {car.make} {car.model}" if car.year and car.make and car.model else "This car"
        
        # Condition assessment
        assessment = f"{car_name} appears to be in {condition_description.lower()} condition overall. "
        
        # Maintenance cost information
        if maintenance_cost is not None:
            assessment += f"The estimated annual maintenance cost is approximately £{maintenance_cost:,.0f}. "
        
        # Potential issues information
        if potential_issues:
            if len(potential_issues) == 1:
                assessment += f"A potential concern to be aware of is {potential_issues[0].lower()}. "
            elif len(potential_issues) == 2:
                assessment += f"Potential concerns to be aware of are {potential_issues[0].lower()} and {potential_issues[1].lower()}. "
            else:
                issues_text = ", ".join(issue.lower() for issue in potential_issues[:-1])
                assessment += f"Potential concerns to be aware of include {issues_text}, and {potential_issues[-1].lower()}. "
        
        # Recommendation based on condition
        if condition_rating >= 8.0:
            assessment += "This vehicle represents an excellent choice in terms of condition."
        elif condition_rating >= 6.0:
            assessment += "This vehicle is in good condition and should be reliable with proper maintenance."
        elif condition_rating >= 4.0:
            assessment += "This vehicle may require some attention and repairs in the near future."
        else:
            assessment += "This vehicle will likely need significant work to restore to good condition."
        
        return assessment
    
    def assess_car_collection(self, cars: CarCollection) -> Dict[str, ConditionAssessmentResult]:
        """
        Assess the condition of all cars in a collection.
        
        Args:
            cars: The collection of cars to assess
            
        Returns:
            Dict mapping car IDs to their ConditionAssessmentResult
        """
        results = {}
        for car in cars:
            results[car.id] = self.assess_condition(car)
        return results


# Create a singleton instance for convenient access
condition_assessor = ConditionAssessor() 