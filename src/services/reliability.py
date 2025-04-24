"""
Reliability assessment service.

This module provides functionality to assess car reliability based on
various data sources and calculate overall reliability scores.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import statistics
import re

from src.models import Car, ConfidenceLevel, AttributeType

# Configure logging
logger = logging.getLogger(__name__)


class ReliabilityAssessment:
    """
    Model for storing reliability assessment results.
    
    This class represents the outcome of a reliability assessment for a car,
    including overall and component-specific scores.
    """
    
    def __init__(self, car_id: str, car_title: Optional[str] = None):
        """
        Initialize a reliability assessment.
        
        Args:
            car_id: ID of the car being assessed.
            car_title: Title of the car (optional).
        """
        self.car_id = car_id
        self.car_title = car_title or f"Car {car_id}"
        self.overall_score: Optional[float] = None
        self.components: Dict[str, float] = {}
        self.data_sources: List[str] = []
        self.confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the assessment to a dictionary.
        
        Returns:
            A dictionary representation of the assessment.
        """
        return {
            "car_id": self.car_id,
            "car_title": self.car_title,
            "overall_score": self.overall_score,
            "components": self.components,
            "data_sources": self.data_sources,
            "confidence_level": self.confidence_level.value,
        }


class ReliabilityService:
    """
    Service for assessing car reliability.
    
    This class provides methods to evaluate car reliability based on
    various data sources and reliability metrics.
    """
    
    # Component weight map for overall reliability scoring
    COMPONENT_WEIGHTS = {
        "engine": 0.25,
        "transmission": 0.20,
        "electrical": 0.15,
        "suspension": 0.15,
        "brakes": 0.10,
        "fuel_system": 0.10,
        "body": 0.05,
    }
    
    # Reliability-related attributes to consider
    RELIABILITY_ATTRIBUTES = [
        "reliability_score",
        "reliability_engine",
        "reliability_transmission",
        "reliability_electrical",
        "reliability_suspension",
        "reliability_brakes",
        "reliability_fuel_system",
        "reliability_body",
    ]
    
    def __init__(self):
        """Initialize the reliability service."""
        logger.info("Reliability service initialized")
    
    def assess_reliability(self, car: Car) -> ReliabilityAssessment:
        """
        Assess the reliability of a car.
        
        This method evaluates a car's reliability based on its attributes and
        returns a comprehensive assessment.
        
        Args:
            car: The car to assess.
            
        Returns:
            A ReliabilityAssessment object with the results.
        """
        assessment = ReliabilityAssessment(car.id, car.title)
        
        # Track data sources
        data_sources = set()
        
        # Check if there's an overall reliability score already
        if car.has_attribute("reliability_score"):
            assessment.overall_score = car.get_attribute("reliability_score")
            source = car.get_attribute_confidence("reliability_score")
            if source:
                data_sources.add(source.name)
        
        # Check for component-specific reliability scores
        component_scores = {}
        for attr in self.RELIABILITY_ATTRIBUTES:
            if attr != "reliability_score" and car.has_attribute(attr):
                # Extract component name from attribute name
                component = attr.replace("reliability_", "")
                component_scores[component] = car.get_attribute(attr)
                
                # Track data source
                source = car.get_attribute_confidence(attr)
                if source:
                    data_sources.add(source.name)
        
        assessment.components = component_scores
        
        # Calculate overall score if not already available
        if assessment.overall_score is None and component_scores:
            weighted_sum = 0
            total_weight = 0
            
            for component, score in component_scores.items():
                weight = self.COMPONENT_WEIGHTS.get(component, 0.1)
                weighted_sum += score * weight
                total_weight += weight
            
            if total_weight > 0:
                assessment.overall_score = weighted_sum / total_weight
        
        # Infer component scores from descriptions or reviews if available
        if car.has_attribute("description"):
            description = car.get_attribute("description")
            if description:
                self._extract_reliability_from_text(description, assessment)
                
                # Track data source
                source = car.get_attribute_confidence("description")
                if source:
                    data_sources.add(source.name)
        
        # Set data sources
        assessment.data_sources = list(data_sources)
        
        # Determine confidence level based on available data
        if assessment.overall_score is not None and len(assessment.components) >= 3:
            assessment.confidence_level = ConfidenceLevel.HIGH
        elif assessment.overall_score is not None or len(assessment.components) >= 2:
            assessment.confidence_level = ConfidenceLevel.MEDIUM
        else:
            assessment.confidence_level = ConfidenceLevel.LOW
        
        # Store the assessment results in the car
        if assessment.overall_score is not None:
            car.compute_attribute(
                "reliability_score",
                assessment.overall_score
            )
        
        for component, score in assessment.components.items():
            car.compute_attribute(
                f"reliability_{component}",
                score
            )
        
        return assessment
    
    def _extract_reliability_from_text(self, text: str, assessment: ReliabilityAssessment) -> None:
        """
        Extract reliability information from descriptive text.
        
        This method uses simple pattern matching to find reliability-related information
        in text descriptions.
        
        Args:
            text: The text to analyze.
            assessment: The reliability assessment to update.
        """
        # This is a very simplified implementation - in a real application,
        # this would use more sophisticated NLP techniques
        
        # Basic patterns for reliability mentions
        patterns = {
            "engine": [
                r"(reliable|solid|robust|problematic|unreliable)\s+(engine|motor)",
                r"engine\s+(reliability|issues|problems|failure)",
            ],
            "transmission": [
                r"(reliable|solid|robust|problematic|unreliable)\s+transmission",
                r"transmission\s+(reliability|issues|problems|failure)",
                r"(gearbox|clutch)\s+(reliability|issues|problems|failure)",
            ],
            "electrical": [
                r"(reliable|solid|robust|problematic|unreliable)\s+electr(ical|onic)",
                r"electr(ical|onic)\s+(reliability|issues|problems|failure)",
                r"(wiring|battery|alternator)\s+(reliability|issues|problems|failure)",
            ],
            "suspension": [
                r"(reliable|solid|robust|problematic|unreliable)\s+suspension",
                r"suspension\s+(reliability|issues|problems|failure)",
            ],
            "brakes": [
                r"(reliable|solid|robust|problematic|unreliable)\s+brake",
                r"brake\s+(reliability|issues|problems|failure)",
            ],
        }
        
        # Score modifiers based on adjectives
        score_modifiers = {
            "very reliable": 2.0,
            "reliable": 1.0,
            "solid": 1.0,
            "robust": 1.0,
            "average": 0.0,
            "ok": 0.0,
            "minor issues": -0.5,
            "some issues": -1.0,
            "problems": -1.0,
            "problematic": -1.5,
            "unreliable": -2.0,
            "failure": -2.0,
        }
        
        # Process the text for each component
        for component, component_patterns in patterns.items():
            score_adjustments = []
            
            for pattern in component_patterns:
                matches = re.finditer(pattern, text.lower())
                for match in matches:
                    matched_text = match.group(0)
                    # Determine the sentiment
                    sentiment_score = 0
                    for term, modifier in score_modifiers.items():
                        if term in matched_text:
                            sentiment_score += modifier
                    
                    if sentiment_score != 0:
                        score_adjustments.append(sentiment_score)
            
            # If we found any sentiment about this component, calculate an average score
            if score_adjustments:
                # Convert from sentiment (-2 to +2) to a 0-10 scale
                avg_sentiment = statistics.mean(score_adjustments)
                component_score = 5.0 + (avg_sentiment * 2.5)
                
                # Clamp to 0-10 range
                component_score = max(0.0, min(10.0, component_score))
                
                # Update the assessment if the component doesn't already have a score
                if component not in assessment.components:
                    assessment.components[component] = component_score
    
    def calculate_reliability_trends(self, make: str, model: str, years_range: Tuple[int, int]) -> Dict[str, Any]:
        """
        Calculate reliability trends for a specific make and model over time.
        
        This method would analyze reliability data across multiple years to identify
        trends and problematic areas.
        
        Args:
            make: The car make.
            model: The car model.
            years_range: Tuple of (start_year, end_year) to analyze.
            
        Returns:
            A dictionary containing trend analysis results.
        """
        # This would be implemented with actual data sources and analysis
        # For now, return a placeholder result
        logger.info(f"Calculating reliability trends for {make} {model} ({years_range[0]}-{years_range[1]})")
        
        return {
            "make": make,
            "model": model,
            "years": list(range(years_range[0], years_range[1] + 1)),
            "trends": {
                "overall": {
                    "trend": "stable",
                    "scores_by_year": {}
                }
            },
            "common_issues": [],
            "improvement_areas": [],
            "best_years": [],
            "avoid_years": [],
        }


# Create a singleton instance of the reliability service
reliability_service = ReliabilityService()
