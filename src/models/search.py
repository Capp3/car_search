from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class TransmissionType(str, Enum):
    """Defines types of car transmissions."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    ANY = "any"  # Used for searches where user doesn't care about transmission


class FuelType(str, Enum):
    """Defines types of fuel for cars."""
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    LPG = "lpg"
    ANY = "any"  # Used for searches where user doesn't care about fuel type


class SearchParameters(BaseModel):
    """
    Represents search parameters for finding cars.
    
    This model is used to store and validate user search criteria.
    """
    # Location parameters
    postcode: str
    radius_miles: int = 50
    
    # Price parameters
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    
    # Vehicle specifications
    make: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    transmission: TransmissionType = TransmissionType.ANY
    fuel_type: FuelType = FuelType.ANY
    
    # Mileage parameters
    max_mileage: Optional[int] = None
    
    # Additional filters
    keywords: List[str] = Field(default_factory=list)
    include_sold: bool = False
    
    @validator('radius_miles')
    def validate_radius(cls, v):
        """Validate that radius is positive and reasonable."""
        if v <= 0:
            raise ValueError("Radius must be positive")
        if v > 200:
            raise ValueError("Radius cannot exceed 200 miles")
        return v
    
    @validator('min_price', 'max_price')
    def validate_price(cls, v):
        """Validate that price is positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Price must be positive")
        return v
    
    @validator('min_year', 'max_year')
    def validate_year(cls, v):
        """Validate that year is reasonable if provided."""
        if v is not None:
            current_year = 2024  # This could be dynamic
            if v < 1900 or v > current_year + 1:
                raise ValueError(f"Year must be between 1900 and {current_year + 1}")
        return v
    
    @validator('max_mileage')
    def validate_mileage(cls, v):
        """Validate that mileage is positive if provided."""
        if v is not None and v < 0:
            raise ValueError("Mileage must be positive")
        return v
    
    def to_autotrader_params(self) -> Dict[str, Any]:
        """
        Convert search parameters to AutoTrader query parameters.
        
        This method creates a dictionary of parameters that can be used
        to build an AutoTrader search URL.
        """
        params = {
            "postcode": self.postcode,
            "radius": self.radius_miles
        }
        
        # Add price parameters if provided
        if self.min_price is not None:
            params["price-from"] = self.min_price
        if self.max_price is not None:
            params["price-to"] = self.max_price
            
        # Add make and model if provided
        if self.make:
            params["make"] = self.make
        if self.model:
            params["model"] = self.model
            
        # Add year parameters if provided
        if self.min_year is not None:
            params["year-from"] = self.min_year
        if self.max_year is not None:
            params["year-to"] = self.max_year
            
        # Add transmission if specified
        if self.transmission != TransmissionType.ANY:
            params["transmission"] = self.transmission.value
            
        # Add fuel type if specified
        if self.fuel_type != FuelType.ANY:
            params["fuel-type"] = self.fuel_type.value
            
        # Add max mileage if provided
        if self.max_mileage is not None:
            params["maximum-mileage"] = self.max_mileage
            
        # Add keywords if provided
        if self.keywords:
            params["keywords"] = " ".join(self.keywords)
            
        # Include/exclude sold vehicles
        params["include-sold-vehicles"] = "on" if self.include_sold else "off"
        
        return params


class SearchResult:
    """
    Represents the result of a car search operation.
    
    This class stores cars matching search criteria along with metadata
    about the search operation.
    """
    def __init__(self, cars: List["Car"] = None, total_matches: int = 0, 
                 parameters: SearchParameters = None, search_time: float = 0.0):
        from .car import Car, CarCollection  # Import here to avoid circular imports
        
        self.cars = cars or []
        self.car_collection = CarCollection(self.cars)
        self.total_matches = total_matches or len(self.cars)
        self.parameters = parameters
        self.search_time = search_time  # Time taken for search in seconds
        
    def __len__(self) -> int:
        return len(self.cars)
        
    def __getitem__(self, index):
        return self.cars[index]
        
    def __iter__(self):
        return iter(self.cars)
