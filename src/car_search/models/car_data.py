"""Car data models for the Car Search application.

This module provides models for storing car data from various sources.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class CarListingData(BaseModel):
    """Model for car listing data from search results.

    Represents a car listing with basic information from search results, which may
    be augmented with additional data from other sources.
    """

    # Basic car information
    id: str = Field(..., description="Unique identifier for the listing")
    title: str = Field(..., description="Listing title")
    make: str = Field(..., description="Car manufacturer")
    model: str = Field(..., description="Car model")
    variant: Optional[str] = Field(None, description="Variant/trim level")
    year: int = Field(..., description="Manufacturing year")

    # Listing details
    price: float = Field(..., description="Price in pounds")
    mileage: int = Field(..., description="Mileage in miles")
    location: str = Field(..., description="Listing location")
    seller_type: Optional[str] = Field(None, description="Type of seller (e.g., Dealer, Private)")
    seller_name: Optional[str] = Field(None, description="Name of the seller")

    # Car specifications
    engine_size: Optional[float] = Field(None, description="Engine size in liters")
    fuel_type: Optional[str] = Field(None, description="Fuel type (e.g., Petrol, Diesel)")
    transmission: Optional[str] = Field(None, description="Transmission type (e.g., Automatic, Manual)")
    body_type: Optional[str] = Field(None, description="Body type (e.g., Hatchback, SUV)")
    color: Optional[str] = Field(None, description="Car color")
    doors: Optional[int] = Field(None, description="Number of doors")

    # Images and listing URL
    image_url: Optional[HttpUrl] = Field(None, description="URL to the main image")
    listing_url: HttpUrl = Field(..., description="URL to the full listing")
    additional_images: List[HttpUrl] = Field(default_factory=list, description="URLs to additional images")

    # Listing metadata
    date_listed: Optional[datetime] = Field(None, description="Date the car was listed")
    date_scraped: datetime = Field(default_factory=datetime.now, description="Date the listing was scraped")

    # Additional data that might be added later
    additional_data: Dict = Field(default_factory=dict, description="Additional data about the car")

    # Reliability scores (added if available from other sources)
    reliability_score: Optional[float] = Field(None, description="Reliability score (0-5)")
    safety_score: Optional[float] = Field(None, description="Safety score (0-5)")
    owner_satisfaction: Optional[float] = Field(None, description="Owner satisfaction score (0-5)")

    # Pros and cons (added if available from other sources)
    pros: List[str] = Field(default_factory=list, description="Positive aspects of the car")
    cons: List[str] = Field(default_factory=list, description="Negative aspects of the car")

    # Computed scores
    value_score: Optional[float] = Field(None, description="Value for money score (0-10)")
    overall_score: Optional[float] = Field(None, description="Overall score (0-10)")

    def to_dict_for_display(self) -> Dict:
        """Convert to dictionary format suitable for display in the UI.

        Returns:
            Dictionary with formatted data for display
        """
        return {
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "price": self.price,
            "mileage": self.mileage,
            "location": self.location,
            "score": self.overall_score or 0.0,
            "data": {
                "id": self.id,
                "engine": f"{self.engine_size}L {self.fuel_type}" if self.engine_size else "Not specified",
                "transmission": self.transmission or "Not specified",
                "color": self.color or "Not specified",
                "fuel_type": self.fuel_type or "Not specified",
                "mpg": self.additional_data.get("mpg"),
                "body_type": self.body_type or "Not specified",
                "reliability_score": self.reliability_score,
                "safety_score": self.safety_score,
                "owner_satisfaction": self.owner_satisfaction,
                "pros": self.pros,
                "cons": self.cons,
            },
        }
