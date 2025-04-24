"""
Tests for the Motorcheck API client.

This module contains tests for the Motorcheck API client.
"""

import pytest
import responses
import requests
import json
from datetime import datetime
from unittest.mock import patch

from src.services.api_clients.motorcheck import MotorcheckAPIClient
from src.models.car import Car, ConfidenceLevel


class TestMotorcheckAPIClient:
    """Test cases for the Motorcheck API client."""
    
    @pytest.fixture
    def api_client(self):
        """Create a Motorcheck API client for testing."""
        return MotorcheckAPIClient(api_key="test_api_key")
    
    @responses.activate
    def test_make_request(self, api_client):
        """Test making a request to the Motorcheck API."""
        # Mock the response
        responses.add(
            responses.GET,
            f"{api_client.BASE_URL}/test-endpoint",
            json={"success": True, "data": "test_data"},
            status=200
        )
        
        # Make the request
        response = api_client._make_request("test-endpoint")
        
        # Assert the response
        assert response["success"] is True
        assert response["data"] == "test_data"
    
    @responses.activate
    def test_get_car_details(self, api_client):
        """Test getting car details from the API."""
        registration = "AB12CDE"
        
        # Mock the response
        responses.add(
            responses.GET,
            f"{api_client.BASE_URL}/vehicle/{registration}",
            json={
                "make": "Ford",
                "model": "Focus",
                "year": 2018,
                "specifications": {
                    "engine": {
                        "size": "2.0",
                        "type": "Petrol",
                        "power": "150"
                    },
                    "transmission": {
                        "type": "Automatic"
                    },
                    "fuel": {
                        "type": "Petrol",
                        "mpg": "45.6"
                    }
                }
            },
            status=200
        )
        
        # Get car details
        car = api_client.get_car_details(registration)
        
        # Assert the result
        assert car is not None
        assert car.make == "Ford"
        assert car.model == "Focus"
        assert car.year == 2018
        assert car.get_attribute("engine_size") == 2.0
        assert car.get_attribute("engine_type") == "Petrol"
        assert car.get_attribute("horsepower") == 150
        assert car.get_attribute("transmission") == "Automatic"
        assert car.get_attribute("fuel_type") == "Petrol"
        assert car.get_attribute("mpg_combined") == 45.6
        
        # Check sources and confidence levels
        assert car.get_attribute_confidence("make") == ConfidenceLevel.HIGH
        assert car.attributes["make"].sources["motorcheck"].source_name == "motorcheck"
    
    @responses.activate
    def test_get_reliability_data(self, api_client):
        """Test getting reliability data from the API."""
        make = "Ford"
        model = "Focus"
        year = 2018
        
        # Mock the response
        responses.add(
            responses.GET,
            f"{api_client.BASE_URL}/reliability",
            json={
                "overallRating": 4.2,
                "commonIssues": ["issue1", "issue2"],
                "averageRepairCost": 450.0
            },
            status=200
        )
        
        # Get reliability data
        data = api_client.get_reliability_data(make, model, year)
        
        # Assert the result
        assert data is not None
        assert data["overallRating"] == 4.2
        assert "issue1" in data["commonIssues"]
        assert data["averageRepairCost"] == 450.0
    
    @responses.activate
    def test_get_vehicle_history(self, api_client):
        """Test getting vehicle history from the API."""
        registration = "AB12CDE"
        
        # Mock the response
        responses.add(
            responses.GET,
            f"{api_client.BASE_URL}/vehicle/{registration}/history",
            json={
                "previousOwners": 2,
                "accidents": [],
                "serviceHistory": True
            },
            status=200
        )
        
        # Get vehicle history
        history = api_client.get_vehicle_history(registration)
        
        # Assert the result
        assert history is not None
        assert history["previousOwners"] == 2
        assert len(history["accidents"]) == 0
        assert history["serviceHistory"] is True
    
    @responses.activate
    def test_api_error_handling(self, api_client):
        """Test error handling in the API client."""
        registration = "AB12CDE"
        
        # Mock an error response
        responses.add(
            responses.GET,
            f"{api_client.BASE_URL}/vehicle/{registration}",
            json={"error": "Not found"},
            status=404
        )
        
        # Attempt to get car details
        with pytest.raises(requests.exceptions.RequestException):
            api_client.get_car_details(registration)
    
    def test_caching(self, api_client):
        """Test that responses are cached."""
        with patch.object(api_client.session, 'get') as mock_get:
            mock_get.return_value.json.return_value = {"test": "data"}
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            
            # First request should call the session.get method
            api_client._make_request("test-endpoint")
            assert mock_get.call_count == 1
            
            # Second request to the same endpoint should use the cache
            api_client._make_request("test-endpoint")
            assert mock_get.call_count == 1  # No additional calls 