"""
Search parameter validation for the Car Search application.

This module provides functionality to validate and process search parameters
such as postcodes, search radius, price ranges, and other filter criteria.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """Represents a geographic location with latitude and longitude."""
    latitude: float
    longitude: float
    postcode: str
    area: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a parameter validation."""
    is_valid: bool
    normalized_value: Any = None
    error_message: Optional[str] = None


class ParameterValidator:
    """Validator for search parameters."""
    
    # UK Postcode regex pattern (simplified)
    UK_POSTCODE_PATTERN = r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$'
    
    # Common validation limits
    MIN_PRICE = 100  # £100
    MAX_PRICE = 1000000  # £1M
    MIN_RADIUS = 1  # 1 mile
    MAX_RADIUS = 200  # 200 miles
    
    @classmethod
    def validate_postcode(cls, postcode: str) -> ValidationResult:
        """
        Validate a UK postcode.
        
        Args:
            postcode: The postcode to validate
            
        Returns:
            ValidationResult with validation status and normalized postcode
        """
        if not postcode:
            return ValidationResult(
                is_valid=False,
                error_message="Postcode cannot be empty"
            )
        
        # Normalize: uppercase and remove spaces
        normalized = postcode.upper().strip()
        
        # Add space in the correct position if missing
        if ' ' not in normalized:
            # Insert a space before the last three characters
            normalized = normalized[:-3] + ' ' + normalized[-3:]
        
        # Check against regex pattern
        if not re.match(cls.UK_POSTCODE_PATTERN, normalized):
            return ValidationResult(
                is_valid=False,
                normalized_value=normalized,
                error_message=f"Invalid UK postcode format: {normalized}"
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=normalized
        )
    
    @classmethod
    def validate_radius(cls, radius: Any) -> ValidationResult:
        """
        Validate a search radius.
        
        Args:
            radius: The radius to validate (miles)
            
        Returns:
            ValidationResult with validation status and normalized radius
        """
        try:
            # Convert to integer
            radius_int = int(radius)
            
            if radius_int < cls.MIN_RADIUS:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=cls.MIN_RADIUS,
                    error_message=f"Radius must be at least {cls.MIN_RADIUS} mile"
                )
            
            if radius_int > cls.MAX_RADIUS:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=cls.MAX_RADIUS,
                    error_message=f"Radius cannot exceed {cls.MAX_RADIUS} miles"
                )
            
            return ValidationResult(
                is_valid=True,
                normalized_value=radius_int
            )
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="Radius must be a number"
            )
    
    @classmethod
    def validate_price_range(cls, min_price: Any, max_price: Any) -> Tuple[ValidationResult, ValidationResult]:
        """
        Validate a price range.
        
        Args:
            min_price: The minimum price
            max_price: The maximum price
            
        Returns:
            Tuple of ValidationResults for min and max price
        """
        min_result = cls._validate_price(min_price, is_min=True)
        max_result = cls._validate_price(max_price, is_min=False)
        
        # If both are valid, check that min <= max
        if min_result.is_valid and max_result.is_valid:
            min_val = min_result.normalized_value
            max_val = max_result.normalized_value
            
            if min_val > max_val:
                # Swap them and set warnings
                min_result = ValidationResult(
                    is_valid=True,
                    normalized_value=max_val,
                    error_message="Min price was greater than max price; values were swapped"
                )
                max_result = ValidationResult(
                    is_valid=True,
                    normalized_value=min_val,
                    error_message="Min price was greater than max price; values were swapped"
                )
        
        return min_result, max_result
    
    @classmethod
    def _validate_price(cls, price: Any, is_min: bool) -> ValidationResult:
        """
        Validate a price value.
        
        Args:
            price: The price to validate
            is_min: Whether this is a minimum price
            
        Returns:
            ValidationResult with validation status and normalized price
        """
        # Handle None or empty string
        if price is None or (isinstance(price, str) and not price.strip()):
            default = cls.MIN_PRICE if is_min else cls.MAX_PRICE
            return ValidationResult(
                is_valid=True,
                normalized_value=default
            )
        
        try:
            # Convert to integer, handling currency symbols and commas
            if isinstance(price, str):
                # Remove currency symbols and commas
                price_str = price.replace('£', '').replace('$', '').replace(',', '').strip()
                price_int = int(float(price_str))
            else:
                price_int = int(price)
            
            # Validate range
            if price_int < cls.MIN_PRICE:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=cls.MIN_PRICE,
                    error_message=f"Price must be at least £{cls.MIN_PRICE}"
                )
            
            if price_int > cls.MAX_PRICE:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=cls.MAX_PRICE,
                    error_message=f"Price cannot exceed £{cls.MAX_PRICE}"
                )
            
            return ValidationResult(
                is_valid=True,
                normalized_value=price_int
            )
        except (ValueError, TypeError):
            default = cls.MIN_PRICE if is_min else cls.MAX_PRICE
            return ValidationResult(
                is_valid=False,
                normalized_value=default,
                error_message="Price must be a number"
            )
    
    @classmethod
    def validate_year_range(cls, min_year: Any, max_year: Any) -> Tuple[ValidationResult, ValidationResult]:
        """
        Validate a year range.
        
        Args:
            min_year: The minimum year
            max_year: The maximum year
            
        Returns:
            Tuple of ValidationResults for min and max year
        """
        min_result = cls._validate_year(min_year, is_min=True)
        max_result = cls._validate_year(max_year, is_min=False)
        
        # If both are valid, check that min <= max
        if min_result.is_valid and max_result.is_valid:
            min_val = min_result.normalized_value
            max_val = max_result.normalized_value
            
            if min_val > max_val:
                # Swap them and set warnings
                min_result = ValidationResult(
                    is_valid=True,
                    normalized_value=max_val,
                    error_message="Min year was greater than max year; values were swapped"
                )
                max_result = ValidationResult(
                    is_valid=True,
                    normalized_value=min_val,
                    error_message="Min year was greater than max year; values were swapped"
                )
        
        return min_result, max_result
    
    @classmethod
    def _validate_year(cls, year: Any, is_min: bool) -> ValidationResult:
        """
        Validate a year value.
        
        Args:
            year: The year to validate
            is_min: Whether this is a minimum year
            
        Returns:
            ValidationResult with validation status and normalized year
        """
        import datetime
        
        current_year = datetime.datetime.now().year
        min_valid_year = 1900
        max_valid_year = current_year + 1  # Allow next year's models
        
        # Handle None or empty string
        if year is None or (isinstance(year, str) and not year.strip()):
            default = min_valid_year if is_min else current_year
            return ValidationResult(
                is_valid=True,
                normalized_value=default
            )
        
        try:
            year_int = int(year)
            
            if year_int < min_valid_year:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=min_valid_year,
                    error_message=f"Year must be at least {min_valid_year}"
                )
            
            if year_int > max_valid_year:
                return ValidationResult(
                    is_valid=False,
                    normalized_value=max_valid_year,
                    error_message=f"Year cannot exceed {max_valid_year}"
                )
            
            return ValidationResult(
                is_valid=True,
                normalized_value=year_int
            )
        except (ValueError, TypeError):
            default = min_valid_year if is_min else current_year
            return ValidationResult(
                is_valid=False,
                normalized_value=default,
                error_message="Year must be a number"
            )
    
    @classmethod
    def validate_make(cls, make: str) -> ValidationResult:
        """
        Validate a car make.
        
        Args:
            make: The car make to validate
            
        Returns:
            ValidationResult with validation status and normalized make
        """
        if not make:
            return ValidationResult(
                is_valid=True,
                normalized_value=None
            )
        
        # Normalize to title case
        normalized = make.strip().title()
        
        # Basic validation (could be extended with a list of valid makes)
        if len(normalized) < 2:
            return ValidationResult(
                is_valid=False,
                normalized_value=normalized,
                error_message="Make must be at least 2 characters"
            )
        
        if len(normalized) > 50:
            return ValidationResult(
                is_valid=False,
                normalized_value=normalized[:50],
                error_message="Make cannot exceed 50 characters"
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=normalized
        )
    
    @classmethod
    def validate_model(cls, model: str) -> ValidationResult:
        """
        Validate a car model.
        
        Args:
            model: The car model to validate
            
        Returns:
            ValidationResult with validation status and normalized model
        """
        if not model:
            return ValidationResult(
                is_valid=True,
                normalized_value=None
            )
        
        # Normalize: title case and remove excessive spaces
        normalized = re.sub(r'\s+', ' ', model.strip().title())
        
        # Basic validation
        if len(normalized) < 1:
            return ValidationResult(
                is_valid=False,
                normalized_value=normalized,
                error_message="Model must be at least 1 character"
            )
        
        if len(normalized) > 100:
            return ValidationResult(
                is_valid=False,
                normalized_value=normalized[:100],
                error_message="Model cannot exceed 100 characters"
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=normalized
        )
    
    @classmethod
    def validate_transmission(cls, transmission: str) -> ValidationResult:
        """
        Validate a transmission type.
        
        Args:
            transmission: The transmission type to validate
            
        Returns:
            ValidationResult with validation status and normalized transmission
        """
        if not transmission:
            return ValidationResult(
                is_valid=True,
                normalized_value=None
            )
        
        valid_types = {
            'manual': 'Manual',
            'automatic': 'Automatic',
            'semi-auto': 'Semi-Auto',
            'semi-automatic': 'Semi-Auto',
            'cvt': 'CVT',
            'auto': 'Automatic'
        }
        
        normalized = transmission.lower().strip()
        
        if normalized in valid_types:
            return ValidationResult(
                is_valid=True,
                normalized_value=valid_types[normalized]
            )
        
        # Find closest match
        for key, value in valid_types.items():
            if key in normalized or normalized in key:
                return ValidationResult(
                    is_valid=True,
                    normalized_value=value,
                    error_message=f"Interpreted '{transmission}' as '{value}'"
                )
        
        return ValidationResult(
            is_valid=False,
            normalized_value=None,
            error_message=f"Invalid transmission type: {transmission}. " 
                          f"Valid types are: {', '.join(set(valid_types.values()))}"
        )


class PostcodeGeocoder:
    """
    Service for geocoding UK postcodes.
    
    This class provides methods to convert postcodes to latitude/longitude
    coordinates and calculate distances between locations.
    """
    
    # Cache for postcode to location mapping
    _location_cache: Dict[str, GeoLocation] = {}
    
    @classmethod
    async def geocode_postcode(cls, postcode: str) -> Optional[GeoLocation]:
        """
        Convert a postcode to latitude/longitude.
        
        Args:
            postcode: The UK postcode to geocode
            
        Returns:
            GeoLocation object if successful, None otherwise
        """
        # Validate postcode
        validation = ParameterValidator.validate_postcode(postcode)
        if not validation.is_valid:
            logger.warning(f"Invalid postcode for geocoding: {validation.error_message}")
            return None
        
        normalized_postcode = validation.normalized_value
        
        # Check cache
        if normalized_postcode in cls._location_cache:
            return cls._location_cache[normalized_postcode]
        
        try:
            # Use Postcodes.io API to geocode
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.postcodes.io/postcodes/{normalized_postcode}") as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("result", {})
                        
                        location = GeoLocation(
                            latitude=result.get("latitude"),
                            longitude=result.get("longitude"),
                            postcode=normalized_postcode,
                            area=result.get("admin_district")
                        )
                        
                        # Cache the result
                        cls._location_cache[normalized_postcode] = location
                        
                        return location
                    else:
                        logger.warning(f"Failed to geocode postcode {normalized_postcode}: " 
                                      f"HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error geocoding postcode {normalized_postcode}: {str(e)}")
            return None
    
    @staticmethod
    def calculate_distance(loc1: GeoLocation, loc2: GeoLocation) -> float:
        """
        Calculate the distance between two locations in miles.
        
        Args:
            loc1: First location
            loc2: Second location
            
        Returns:
            Distance in miles
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lon1, lat1 = radians(loc1.longitude), radians(loc1.latitude)
        lon2, lat2 = radians(loc2.longitude), radians(loc2.latitude)
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in miles
        r = 3956
        
        # Calculate distance
        return c * r


class SearchParameterProcessor:
    """
    Processor for search parameters.
    
    This class processes and validates search parameters for car searches.
    """
    
    def __init__(self):
        """Initialize the search parameter processor."""
        self.validator = ParameterValidator
        self.geocoder = PostcodeGeocoder
    
    def process_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate search parameters.
        
        Args:
            params: Dictionary of search parameters
            
        Returns:
            Dictionary of processed parameters with validation status
        """
        processed = {
            "raw_params": params.copy(),
            "valid_params": {},
            "invalid_params": {},
            "warnings": []
        }
        
        # Process postcode and radius
        if "postcode" in params:
            postcode_result = self.validator.validate_postcode(params["postcode"])
            if postcode_result.is_valid:
                processed["valid_params"]["postcode"] = postcode_result.normalized_value
            else:
                processed["invalid_params"]["postcode"] = {
                    "value": params["postcode"],
                    "error": postcode_result.error_message
                }
                if postcode_result.normalized_value:
                    processed["warnings"].append(
                        f"Invalid postcode: {postcode_result.error_message}. "
                        f"Using normalized value: {postcode_result.normalized_value}"
                    )
        
        if "radius" in params:
            radius_result = self.validator.validate_radius(params["radius"])
            if radius_result.is_valid:
                processed["valid_params"]["radius"] = radius_result.normalized_value
            else:
                processed["invalid_params"]["radius"] = {
                    "value": params["radius"],
                    "error": radius_result.error_message
                }
                if radius_result.normalized_value:
                    processed["valid_params"]["radius"] = radius_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid radius: {radius_result.error_message}. "
                        f"Using value: {radius_result.normalized_value}"
                    )
        
        # Process price range
        min_price = params.get("min_price")
        max_price = params.get("max_price")
        if min_price is not None or max_price is not None:
            min_result, max_result = self.validator.validate_price_range(min_price, max_price)
            
            if min_result.is_valid:
                processed["valid_params"]["min_price"] = min_result.normalized_value
            else:
                processed["invalid_params"]["min_price"] = {
                    "value": min_price,
                    "error": min_result.error_message
                }
                if min_result.normalized_value:
                    processed["valid_params"]["min_price"] = min_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid minimum price: {min_result.error_message}. "
                        f"Using value: {min_result.normalized_value}"
                    )
            
            if max_result.is_valid:
                processed["valid_params"]["max_price"] = max_result.normalized_value
            else:
                processed["invalid_params"]["max_price"] = {
                    "value": max_price,
                    "error": max_result.error_message
                }
                if max_result.normalized_value:
                    processed["valid_params"]["max_price"] = max_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid maximum price: {max_result.error_message}. "
                        f"Using value: {max_result.normalized_value}"
                    )
        
        # Process year range
        min_year = params.get("min_year")
        max_year = params.get("max_year")
        if min_year is not None or max_year is not None:
            min_result, max_result = self.validator.validate_year_range(min_year, max_year)
            
            if min_result.is_valid:
                processed["valid_params"]["min_year"] = min_result.normalized_value
            else:
                processed["invalid_params"]["min_year"] = {
                    "value": min_year,
                    "error": min_result.error_message
                }
                if min_result.normalized_value:
                    processed["valid_params"]["min_year"] = min_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid minimum year: {min_result.error_message}. "
                        f"Using value: {min_result.normalized_value}"
                    )
            
            if max_result.is_valid:
                processed["valid_params"]["max_year"] = max_result.normalized_value
            else:
                processed["invalid_params"]["max_year"] = {
                    "value": max_year,
                    "error": max_result.error_message
                }
                if max_result.normalized_value:
                    processed["valid_params"]["max_year"] = max_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid maximum year: {max_result.error_message}. "
                        f"Using value: {max_result.normalized_value}"
                    )
        
        # Process make and model
        if "make" in params:
            make_result = self.validator.validate_make(params["make"])
            if make_result.is_valid:
                processed["valid_params"]["make"] = make_result.normalized_value
            else:
                processed["invalid_params"]["make"] = {
                    "value": params["make"],
                    "error": make_result.error_message
                }
                if make_result.normalized_value:
                    processed["valid_params"]["make"] = make_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid make: {make_result.error_message}. "
                        f"Using value: {make_result.normalized_value}"
                    )
        
        if "model" in params:
            model_result = self.validator.validate_model(params["model"])
            if model_result.is_valid:
                processed["valid_params"]["model"] = model_result.normalized_value
            else:
                processed["invalid_params"]["model"] = {
                    "value": params["model"],
                    "error": model_result.error_message
                }
                if model_result.normalized_value:
                    processed["valid_params"]["model"] = model_result.normalized_value
                    processed["warnings"].append(
                        f"Invalid model: {model_result.error_message}. "
                        f"Using value: {model_result.normalized_value}"
                    )
        
        # Process transmission
        if "transmission" in params:
            transmission_result = self.validator.validate_transmission(params["transmission"])
            if transmission_result.is_valid:
                processed["valid_params"]["transmission"] = transmission_result.normalized_value
            else:
                processed["invalid_params"]["transmission"] = {
                    "value": params["transmission"],
                    "error": transmission_result.error_message
                }
        
        # Additional processing could be added here for other parameters
        
        return processed
    
    def create_filter_from_params(self, params: Dict[str, Any]) -> 'FilterQueryBuilder':
        """
        Create a filter query from processed parameters.
        
        Args:
            params: Dictionary of processed search parameters
            
        Returns:
            FilterQueryBuilder with filters based on parameters
        """
        from src.data.filtering import filter_manager
        
        query = filter_manager.create_query()
        
        # Add filters based on parameters
        if "make" in params and params["make"]:
            query.make(params["make"])
        
        if "model" in params and params["model"]:
            query.model_contains(params["model"])
        
        if "min_price" in params and "max_price" in params:
            query.price_between(params["min_price"], params["max_price"])
        elif "min_price" in params:
            query.price_min(params["min_price"])
        elif "max_price" in params:
            query.price_max(params["max_price"])
        
        if "min_year" in params and "max_year" in params:
            query.year_between(params["min_year"], params["max_year"])
        elif "min_year" in params:
            query.year_newer_than(params["min_year"])
        elif "max_year" in params:
            query.year_older_than(params["max_year"])
        
        if "transmission" in params and params["transmission"]:
            query.field("transmission").equals(params["transmission"])
        
        # Note: postcode and radius are typically used for the initial search,
        # not filtering after the search is performed
        
        return query


# Create a singleton instance
parameter_processor = SearchParameterProcessor() 