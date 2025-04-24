from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Type, Union
from enum import Enum
from datetime import datetime

class AttributeType(Enum):
    """Defines the type of a car attribute."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"
    ENUM = "enum"
    
    @classmethod
    def from_value(cls, value: Any) -> "AttributeType":
        """Infer the attribute type from a value."""
        if isinstance(value, str):
            return cls.TEXT
        elif isinstance(value, (int, float)):
            return cls.NUMBER
        elif isinstance(value, bool):
            return cls.BOOLEAN
        elif isinstance(value, datetime):
            return cls.DATE
        elif isinstance(value, list):
            return cls.LIST
        elif isinstance(value, Enum):
            return cls.ENUM
        else:
            return cls.TEXT  # Default to text for complex types


class ConfidenceLevel(Enum):
    """Defines the confidence level in an attribute's value."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class AttributeSource(BaseModel):
    """Represents a source of information for a car attribute."""
    source_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    raw_value: Any


class CarAttribute(BaseModel):
    """Represents a single attribute of a car with potentially multiple sources."""
    name: str
    type: AttributeType
    sources: Dict[str, AttributeSource] = Field(default_factory=dict)
    computed: bool = False
    
    @property
    def value(self) -> Any:
        """Return the highest confidence value or most recent if tied."""
        if not self.sources:
            return None
            
        # Sort by confidence level (highest first) then by timestamp (newest first)
        sorted_sources = sorted(
            self.sources.values(),
            key=lambda s: (-s.confidence.value, -s.timestamp.timestamp())
        )
        return sorted_sources[0].raw_value
    
    @property
    def confidence(self) -> Optional[ConfidenceLevel]:
        """Return the confidence level of the current value."""
        if not self.sources:
            return None
            
        sorted_sources = sorted(
            self.sources.values(),
            key=lambda s: (-s.confidence.value, -s.timestamp.timestamp())
        )
        return sorted_sources[0].confidence
    
    def add_source(self, source_name: str, value: Any, 
                   confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> None:
        """Add a new source for this attribute."""
        self.sources[source_name] = AttributeSource(
            source_name=source_name,
            raw_value=value,
            confidence=confidence
        )


class Car(BaseModel):
    """
    Represents a car with a flexible attribute system.
    
    This model uses an attribute-based approach to handle data from multiple sources
    with varying levels of confidence.
    """
    id: str
    attributes: Dict[str, CarAttribute] = Field(default_factory=dict)
    
    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get the value of an attribute by name."""
        attr = self.attributes.get(name)
        return attr.value if attr else default
    
    def get_attribute_confidence(self, name: str) -> Optional[ConfidenceLevel]:
        """Get the confidence level of an attribute by name."""
        attr = self.attributes.get(name)
        return attr.confidence if attr else None
    
    def set_attribute(self, name: str, value: Any, source: str, 
                      confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                      attr_type: Optional[AttributeType] = None) -> None:
        """
        Set an attribute value from a specific source.
        
        If the attribute doesn't exist, it will be created.
        If it exists, the source will be added or updated.
        """
        if name not in self.attributes:
            # Create a new attribute
            if attr_type is None:
                attr_type = AttributeType.from_value(value)
                
            self.attributes[name] = CarAttribute(
                name=name,
                type=attr_type,
                sources={
                    source: AttributeSource(
                        source_name=source,
                        raw_value=value,
                        confidence=confidence
                    )
                }
            )
        else:
            # Update existing attribute
            self.attributes[name].add_source(source, value, confidence)
    
    def compute_attribute(self, name: str, value: Any, 
                          attr_type: Optional[AttributeType] = None) -> None:
        """Set a computed attribute."""
        if attr_type is None:
            attr_type = AttributeType.from_value(value)
            
        self.attributes[name] = CarAttribute(
            name=name,
            type=attr_type,
            sources={
                "computed": AttributeSource(
                    source_name="computed",
                    raw_value=value,
                    confidence=ConfidenceLevel.HIGH
                )
            },
            computed=True
        )
    
    def has_attribute(self, name: str) -> bool:
        """Check if the car has a specific attribute."""
        return name in self.attributes
    
    def list_sources(self) -> List[str]:
        """List all unique sources that provided data for this car."""
        sources = set()
        for attr in self.attributes.values():
            for source in attr.sources.keys():
                sources.add(source)
        return list(sources)
    
    # Common attributes as properties for convenience
    @property
    def make(self) -> Optional[str]:
        return self.get_attribute("make")
    
    @property
    def model(self) -> Optional[str]:
        return self.get_attribute("model")
    
    @property
    def year(self) -> Optional[int]:
        return self.get_attribute("year")
    
    @property
    def price(self) -> Optional[float]:
        return self.get_attribute("price")
    
    @property
    def mileage(self) -> Optional[int]:
        return self.get_attribute("mileage")
    
    @property
    def fuel_type(self) -> Optional[str]:
        return self.get_attribute("fuel_type")
    
    @property
    def transmission(self) -> Optional[str]:
        return self.get_attribute("transmission")
    
    @property
    def location(self) -> Optional[str]:
        return self.get_attribute("location")
    
    @property
    def url(self) -> Optional[str]:
        return self.get_attribute("url")
    
    @property
    def description(self) -> Optional[str]:
        return self.get_attribute("description")
    
    @property
    def title(self) -> Optional[str]:
        """
        Get the display title for the car.
        
        If a title attribute exists, return it.
        Otherwise, construct a title from make, model, and year if available.
        """
        if self.has_attribute("title"):
            return self.get_attribute("title")
        
        parts = []
        if self.year:
            parts.append(str(self.year))
        if self.make:
            parts.append(self.make)
        if self.model:
            parts.append(self.model)
            
        return " ".join(parts) if parts else None


class CarCollection:
    """A collection of cars with filtering and query capabilities."""
    
    def __init__(self, cars: Optional[List[Car]] = None):
        self.cars = cars or []
    
    def add(self, car: Car) -> None:
        """Add a car to the collection."""
        self.cars.append(car)
    
    def filter(self, **kwargs) -> "CarCollection":
        """
        Filter cars by attribute values.
        
        Example: collection.filter(make="Ford", year=2015)
        """
        result = []
        for car in self.cars:
            matches = True
            for key, value in kwargs.items():
                car_value = car.get_attribute(key)
                if car_value != value:
                    matches = False
                    break
            if matches:
                result.append(car)
        return CarCollection(result)
    
    def filter_range(self, attribute: str, min_value: Optional[float] = None, 
                     max_value: Optional[float] = None) -> "CarCollection":
        """
        Filter cars by a numeric attribute range.
        
        Example: collection.filter_range("price", min_value=5000, max_value=10000)
        """
        if min_value is None and max_value is None:
            return CarCollection(self.cars.copy())
            
        result = []
        for car in self.cars:
            value = car.get_attribute(attribute)
            if value is None:
                continue
                
            if isinstance(value, (int, float)):
                if min_value is not None and value < min_value:
                    continue
                if max_value is not None and value > max_value:
                    continue
                result.append(car)
                
        return CarCollection(result)
    
    def sort_by(self, attribute: str, reverse: bool = False) -> "CarCollection":
        """
        Sort cars by an attribute.
        
        Example: collection.sort_by("price")
        """
        sorted_cars = sorted(
            self.cars,
            key=lambda car: (car.get_attribute(attribute) is not None, 
                             car.get_attribute(attribute)),
            reverse=reverse
        )
        return CarCollection(sorted_cars)
    
    def __len__(self) -> int:
        return len(self.cars)
    
    def __getitem__(self, index) -> Car:
        return self.cars[index]
    
    def __iter__(self):
        return iter(self.cars)
