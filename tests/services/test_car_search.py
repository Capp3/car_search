"""
Tests for the Car Search Service.

This module contains tests for the Car Search Service.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.car_search import CarSearchService
from src.models.car import Car, CarCollection, ConfidenceLevel
from src.services.scrapers.autotrader import ScraperResult


class TestCarSearchService:
    """Test cases for the Car Search Service."""
    
    @pytest.fixture
    def search_service(self):
        """Create a Car Search Service for testing."""
        return CarSearchService(
            region="uk",
            motorcheck_api_key="test_api_key"
        )
    
    @pytest.fixture
    def mock_car(self):
        """Create a mock car for testing."""
        car = Car(id="test_car_1")
        car.set_attribute("make", "Ford", "autotrader")
        car.set_attribute("model", "Focus", "autotrader")
        car.set_attribute("year", 2018, "autotrader")
        car.set_attribute("registration", "AB12CDE", "autotrader")
        return car
    
    @pytest.fixture
    def mock_car_collection(self, mock_car):
        """Create a mock car collection for testing."""
        return CarCollection([mock_car])
    
    @patch("src.services.scrapers.autotrader.AutoTraderScraper.search")
    def test_search(self, mock_search, search_service, mock_car):
        """Test searching for cars."""
        # Create a mock scraper result
        result = ScraperResult(source="autotrader", region="uk", url="https://test.com")
        result.add_car(mock_car)
        result.success = True
        
        # Configure the mock to return the scraper result
        mock_search.return_value = result
        
        # Perform the search
        search_params = {
            "postcode": "BT7 3FN",
            "radius": 50,
            "max_price": 2500,
            "make": "Ford"
        }
        collection = search_service.search(search_params, limit=5)
        
        # Assert the results
        assert len(collection) == 1
        assert collection[0].make == "Ford"
        assert collection[0].model == "Focus"
        assert collection[0].year == 2018
        
        # Verify the mock was called with the correct arguments
        mock_search.assert_called_once_with(search_params, limit=5)
    
    def test_enrich_car(self, search_service, mock_car):
        """Test enriching a car with additional data."""
        # Mock the Motorcheck client methods
        search_service.motorcheck_client = MagicMock()
        search_service.motorcheck_client.get_car_details.return_value = None
        
        reliability_data = {
            "overallRating": 4.2,
            "commonIssues": ["issue1", "issue2"],
            "averageRepairCost": 450.0
        }
        search_service.motorcheck_client.get_reliability_data.return_value = reliability_data
        
        vehicle_history = {
            "previousOwners": 2,
            "accidents": [],
            "serviceHistory": True
        }
        search_service.motorcheck_client.get_vehicle_history.return_value = vehicle_history
        
        # Enrich the car
        search_service._enrich_car(
            mock_car,
            include_reliability=True,
            include_details=True,
            include_history=True
        )
        
        # Assert that the methods were called with the correct arguments
        search_service.motorcheck_client.get_car_details.assert_called_once_with(mock_car.get_attribute("registration"))
        search_service.motorcheck_client.get_reliability_data.assert_called_once_with(
            mock_car.make, mock_car.model, mock_car.year
        )
        search_service.motorcheck_client.get_vehicle_history.assert_called_once_with(
            mock_car.get_attribute("registration")
        )
        
        # Check that the car was enriched with the reliability data
        assert mock_car.get_attribute("reliability_rating") == 4.2
        assert mock_car.get_attribute("common_issues") == ["issue1", "issue2"]
        assert mock_car.get_attribute("average_repair_cost") == 450.0
        
        # Check that the car was enriched with the vehicle history data
        assert mock_car.get_attribute("previous_owners") == 2
        assert isinstance(mock_car.get_attribute("accidents"), list)
        assert mock_car.get_attribute("service_history") is True
    
    @patch("src.services.car_search.CarSearchService._enrich_car")
    def test_enrich_cars(self, mock_enrich_car, search_service, mock_car_collection):
        """Test enriching multiple cars."""
        # Enrich the cars
        enriched = search_service.enrich_cars(
            mock_car_collection,
            include_reliability=True,
            include_details=True,
            include_history=True
        )
        
        # Assert that _enrich_car was called for each car
        assert mock_enrich_car.call_count == 1
        
        # Check that the collection was returned
        assert len(enriched) == 1
        assert enriched[0].id == "test_car_1"
    
    def test_get_car_by_registration(self, search_service, mock_car):
        """Test getting a car by registration."""
        # Mock the Motorcheck client method
        search_service.motorcheck_client = MagicMock()
        search_service.motorcheck_client.get_car_details.return_value = mock_car
        
        # Mock the _enrich_car method
        search_service._enrich_car = MagicMock()
        
        # Get the car
        car = search_service.get_car_by_registration("AB12CDE")
        
        # Assert the result
        assert car is not None
        assert car.id == "test_car_1"
        
        # Verify the methods were called with the correct arguments
        search_service.motorcheck_client.get_car_details.assert_called_once_with("AB12CDE")
        search_service._enrich_car.assert_called_once_with(mock_car, True, True, True)
    
    def test_get_car_by_registration_no_client(self, search_service):
        """Test getting a car by registration when no client is available."""
        # Set the motorcheck client to None
        search_service.motorcheck_client = None
        
        # Get the car
        car = search_service.get_car_by_registration("AB12CDE")
        
        # Assert the result
        assert car is None 