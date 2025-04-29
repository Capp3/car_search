"""Search parameters model for the Car Search application.

This module provides a model for validating and storing search parameters.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SearchParameters(BaseModel):
    """Model for car search parameters.

    Represents the parameters used for searching cars, including location, price range,
    and vehicle details.
    """

    postcode: Optional[str] = Field(None, description="UK postcode to search around")
    radius: int = Field(50, description="Search radius in miles", ge=5, le=200)
    min_price: int = Field(0, description="Minimum price in pounds", ge=0)
    max_price: int = Field(100000, description="Maximum price in pounds", ge=500)
    make: Optional[str] = Field(None, description="Vehicle manufacturer")
    transmission: Optional[str] = Field(None, description="Transmission type (Automatic/Manual)")

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, v: Optional[str]) -> Optional[str]:
        """Validate UK postcode format.

        Args:
            v: The postcode to validate

        Returns:
            The validated postcode or None if not provided

        Raises:
            ValueError: If the postcode is invalid
        """
        if v is None or v == "":
            return None

        # Strip whitespace and convert to uppercase
        v = v.strip().upper()

        # UK postcode regex pattern (basic validation)
        pattern = r"^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid UK postcode format")

        return v

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, v: int, values: dict) -> int:
        """Validate that max_price is greater than min_price.

        Args:
            v: The maximum price value
            values: The values dict with previously validated fields

        Returns:
            The validated maximum price

        Raises:
            ValueError: If max_price is less than or equal to min_price
        """
        min_price = values.data.get("min_price", 0)
        if v <= min_price:
            raise ValueError("Maximum price must be greater than minimum price")

        return v

    @field_validator("transmission")
    @classmethod
    def validate_transmission(cls, v: Optional[str]) -> Optional[str]:
        """Validate transmission type.

        Args:
            v: The transmission type

        Returns:
            The validated transmission type or None

        Raises:
            ValueError: If the transmission type is invalid
        """
        if v is None or v == "" or v.lower() == "any":
            return None

        valid_types = ["automatic", "manual"]
        if v.lower() not in valid_types:
            raise ValueError(f"Transmission must be one of: {', '.join(valid_types)}")

        return v.capitalize()

    def to_url_params(self) -> dict:
        """Convert search parameters to URL parameters for AutoTrader.

        Returns:
            Dictionary of URL parameters for AutoTrader search
        """
        params = {}

        # Location parameters
        if self.postcode:
            params["postcode"] = self.postcode
        if self.radius:
            params["radius"] = str(self.radius)

        # Price range
        if self.min_price > 0:
            params["price-from"] = str(self.min_price)
        if self.max_price < 100000:
            params["price-to"] = str(self.max_price)

        # Vehicle details
        if self.make and self.make.lower() != "any":
            params["make"] = self.make

        if self.transmission:
            params["transmission"] = self.transmission.lower()

        # Default parameter for including home delivery adverts
        params["homeDeliveryAdverts"] = "include"

        # Default parameter for advertising location
        params["advertising-location"] = "at_cars"

        # Default parameter for page
        params["page"] = "1"

        return params
