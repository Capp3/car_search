"""
Filter Manager Module

This module provides functionality to filter car collections based on various criteria.
It supports filtering by price range, year range, make, model, transmission, and more.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field

from src.models.car import Car, CarCollection

logger = logging.getLogger(__name__)


@dataclass
class FilterQuery:
    """Represents a structured filter query with normalized parameters."""
    price_range: Optional[Tuple[float, float]] = None
    year_range: Optional[Tuple[int, int]] = None
    make: Optional[str] = None
    model: Optional[str] = None
    transmission: Optional[str] = None
    location_radius: Optional[Tuple[str, float]] = None  # (postcode, radius in miles)
    additional_filters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.additional_filters is None:
            self.additional_filters = {}


class FilterResult:
    """Container for the results of a filter operation."""
    
    def __init__(self, cars: List[Car], query: FilterQuery):
        """
        Initialize a filter result with a list of filtered cars and the query that produced them.
        
        Args:
            cars: List of cars that match the filter criteria
            query: The FilterQuery that was used to filter the cars
        """
        self.cars = cars
        self.query = query
    
    def to_collection(self) -> CarCollection:
        """Convert the filter result to a CarCollection."""
        return CarCollection(self.cars)
    
    def __len__(self) -> int:
        """Return the number of cars in the result."""
        return len(self.cars)


class FilterPredicate:
    """Represents a filter predicate that can be applied to a Car."""
    
    def __init__(self, predicate_func: Callable[[Car], bool], description: str):
        """
        Initialize a filter predicate with a function and description.
        
        Args:
            predicate_func: A function that takes a Car and returns True if it matches the filter
            description: A string describing what the predicate does
        """
        self.predicate_func = predicate_func
        self.description = description
    
    def apply(self, car: Car) -> bool:
        """
        Apply the predicate to a car, with error handling.
        
        Args:
            car: The car to check against the predicate
            
        Returns:
            True if the car matches the predicate, False otherwise
        """
        try:
            return self.predicate_func(car)
        except Exception as e:
            logger.error(f"Error applying filter {self.description} to car {car.id}: {str(e)}")
            return False
    
    def __call__(self, car: Car) -> bool:
        """Make the predicate callable directly."""
        return self.apply(car)


class FilterManager:
    """Manages the creation and application of filters to cars."""
    
    @staticmethod
    def create_price_filter(min_price: Optional[float] = None, max_price: Optional[float] = None) -> FilterPredicate:
        """
        Create a price range filter.
        
        Args:
            min_price: Minimum price (inclusive), or None for no minimum
            max_price: Maximum price (inclusive), or None for no maximum
            
        Returns:
            A FilterPredicate that checks if a car's price is within the specified range
        """
        def price_predicate(car: Car) -> bool:
            if car.price is None:
                return False
            
            if min_price is not None and car.price < min_price:
                return False
                
            if max_price is not None and car.price > max_price:
                return False
                
            return True
            
        description = f"Price range: {min_price or 'Any'} to {max_price or 'Any'}"
        return FilterPredicate(price_predicate, description)
    
    @staticmethod
    def create_year_filter(min_year: Optional[int] = None, max_year: Optional[int] = None) -> FilterPredicate:
        """
        Create a year range filter.
        
        Args:
            min_year: Minimum year (inclusive), or None for no minimum
            max_year: Maximum year (inclusive), or None for no maximum
            
        Returns:
            A FilterPredicate that checks if a car's year is within the specified range
        """
        def year_predicate(car: Car) -> bool:
            if car.year is None:
                return False
                
            if min_year is not None and car.year < min_year:
                return False
                
            if max_year is not None and car.year > max_year:
                return False
                
            return True
            
        description = f"Year range: {min_year or 'Any'} to {max_year or 'Any'}"
        return FilterPredicate(year_predicate, description)
    
    @staticmethod
    def create_make_filter(make: str) -> FilterPredicate:
        """
        Create a make filter.
        
        Args:
            make: The make to filter by
            
        Returns:
            A FilterPredicate that checks if a car's make matches the specified make
        """
        def make_predicate(car: Car) -> bool:
            if car.make is None:
                return False
                
            return car.make.lower() == make.lower()
            
        description = f"Make: {make}"
        return FilterPredicate(make_predicate, description)
    
    @staticmethod
    def create_model_filter(model: str) -> FilterPredicate:
        """
        Create a model filter.
        
        Args:
            model: The model to filter by
            
        Returns:
            A FilterPredicate that checks if a car's model matches the specified model
        """
        def model_predicate(car: Car) -> bool:
            if car.model is None:
                return False
                
            return car.model.lower() == model.lower()
            
        description = f"Model: {model}"
        return FilterPredicate(model_predicate, description)
    
    @staticmethod
    def create_transmission_filter(transmission: str) -> FilterPredicate:
        """
        Create a transmission filter.
        
        Args:
            transmission: The transmission type to filter by
            
        Returns:
            A FilterPredicate that checks if a car's transmission matches the specified transmission
        """
        def transmission_predicate(car: Car) -> bool:
            if car.transmission is None:
                return False
                
            return car.transmission.lower() == transmission.lower()
            
        description = f"Transmission: {transmission}"
        return FilterPredicate(transmission_predicate, description)
    
    @staticmethod
    def create_location_radius_filter(postcode: str, radius: float) -> FilterPredicate:
        """
        Create a location radius filter.
        
        Args:
            postcode: The center postcode
            radius: The radius in miles
            
        Returns:
            A FilterPredicate that checks if a car is within the specified radius of the postcode
        """
        def location_predicate(car: Car) -> bool:
            # This is a placeholder. In a real implementation, we would use a
            # geocoding service to convert postcodes to coordinates and calculate
            # the distance between the car's location and the center postcode.
            # For now, we'll just return True if the car has a location.
            if car.location is None:
                return False
                
            return True  # Placeholder - in reality would check distance
            
        description = f"Location: Within {radius} miles of {postcode}"
        return FilterPredicate(location_predicate, description)
    
    @staticmethod
    def apply_filters(cars: List[Car], predicates: List[FilterPredicate]) -> List[Car]:
        """
        Apply a list of filter predicates to a list of cars.
        
        Args:
            cars: The list of cars to filter
            predicates: The list of predicates to apply
            
        Returns:
            A list of cars that match all the predicates
        """
        if not predicates:
            return cars.copy()
            
        result = []
        
        for car in cars:
            matches = all(predicate(car) for predicate in predicates)
            if matches:
                result.append(car)
                
        return result


def filter_cars(car_collection: CarCollection, query: FilterQuery) -> FilterResult:
    """
    Filter a car collection based on a FilterQuery.
    
    Args:
        car_collection: The collection of cars to filter
        query: The filter query to apply
        
    Returns:
        A FilterResult containing the filtered cars and the query
    """
    predicates = []
    
    # Create predicates based on the query parameters
    if query.price_range:
        min_price, max_price = query.price_range
        predicates.append(FilterManager.create_price_filter(min_price, max_price))
        
    if query.year_range:
        min_year, max_year = query.year_range
        predicates.append(FilterManager.create_year_filter(min_year, max_year))
        
    if query.make:
        predicates.append(FilterManager.create_make_filter(query.make))
        
    if query.model:
        predicates.append(FilterManager.create_model_filter(query.model))
        
    if query.transmission:
        predicates.append(FilterManager.create_transmission_filter(query.transmission))
        
    if query.location_radius:
        postcode, radius = query.location_radius
        predicates.append(FilterManager.create_location_radius_filter(postcode, radius))
    
    # Apply the predicates to the cars
    filtered_cars = FilterManager.apply_filters(car_collection.cars, predicates)
    
    return FilterResult(filtered_cars, query)


def create_filter_query(**kwargs) -> FilterQuery:
    """
    Create a FilterQuery from keyword arguments.
    
    This function allows for convenient creation of filter queries, handling the
    conversion of individual parameters like min_price and max_price to the 
    structured price_range tuple expected by FilterQuery.
    
    Args:
        **kwargs: Keyword arguments for the filter query
            Supported keys:
            - min_price, max_price: Combined into price_range
            - min_year, max_year: Combined into year_range
            - make, model, transmission: Passed through directly
            - postcode, radius: Combined into location_radius
            - Any other keys will be added to additional_filters
            
    Returns:
        A FilterQuery instance configured with the provided parameters
    """
    # Extract known parameters
    price_range = None
    if 'min_price' in kwargs or 'max_price' in kwargs:
        min_price = kwargs.pop('min_price', None)
        max_price = kwargs.pop('max_price', None)
        price_range = (min_price, max_price)
    
    year_range = None
    if 'min_year' in kwargs or 'max_year' in kwargs:
        min_year = kwargs.pop('min_year', None)
        max_year = kwargs.pop('max_year', None)
        year_range = (min_year, max_year)
    
    location_radius = None
    if 'postcode' in kwargs and 'radius' in kwargs:
        postcode = kwargs.pop('postcode')
        radius = kwargs.pop('radius')
        location_radius = (postcode, radius)
    
    # Extract direct parameters
    make = kwargs.pop('make', None)
    model = kwargs.pop('model', None)
    transmission = kwargs.pop('transmission', None)
    
    # Any remaining kwargs become additional_filters
    additional_filters = kwargs
    
    return FilterQuery(
        price_range=price_range,
        year_range=year_range,
        make=make,
        model=model,
        transmission=transmission,
        location_radius=location_radius,
        additional_filters=additional_filters
    ) 