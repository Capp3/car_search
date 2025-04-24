"""
Unit tests for the filtering module.
"""

import unittest
from datetime import datetime, timedelta

from src.data.filtering import (
    FilterManager, FilterQueryBuilder, 
    FilterOperator, LogicalOperator,
    SimpleFilter, CompoundFilter
)
from src.models.car import Car, CarCollection
from src.data.filtering.filter_manager import (
    FilterQuery, FilterResult, filter_cars, create_filter_query
)


class TestFiltering(unittest.TestCase):
    """Test suite for the filtering functionality."""

    def setUp(self):
        """Set up test data before each test."""
        # Create a collection of test cars with various properties
        self.cars = [
            Car(
                id="car1",
                make="Toyota",
                model="Corolla",
                year=2018,
                price=15000,
                mileage=25000,
                transmission="Automatic",
                fuel_type="Petrol",
                location="London",
                date_listed=datetime.now() - timedelta(days=5),
                description="Good condition Toyota Corolla"
            ),
            Car(
                id="car2",
                make="Honda",
                model="Civic",
                year=2020,
                price=22000,
                mileage=10000,
                transmission="Automatic",
                fuel_type="Hybrid",
                location="Manchester",
                date_listed=datetime.now() - timedelta(days=2),
                description="Like new Honda Civic Hybrid"
            ),
            Car(
                id="car3",
                make="BMW",
                model="3 Series",
                year=2019,
                price=28000,
                mileage=15000,
                transmission="Manual",
                fuel_type="Diesel",
                location="Birmingham",
                date_listed=datetime.now() - timedelta(days=10),
                description="BMW 3 Series in excellent condition"
            ),
            Car(
                id="car4",
                make="Ford",
                model="Focus",
                year=2017,
                price=12000,
                mileage=40000,
                transmission="Manual",
                fuel_type="Petrol",
                location="Liverpool",
                date_listed=datetime.now() - timedelta(days=7),
                description="Ford Focus with good fuel economy"
            ),
            Car(
                id="car5",
                make="Audi",
                model="A4",
                year=2021,
                price=35000,
                mileage=5000,
                transmission="Automatic",
                fuel_type="Petrol",
                location="Leeds",
                date_listed=datetime.now() - timedelta(days=1),
                description="Nearly new Audi A4"
            ),
            # Car with missing data to test handling of None values
            Car(
                id="car6",
                make="Volkswagen",
                model="Golf",
                year=None,
                price=None,
                mileage=None,
                transmission=None,
                fuel_type=None,
                location=None,
                date_listed=None,
                description="Volkswagen Golf with incomplete data"
            )
        ]
        
        self.car_collection = CarCollection(self.cars)

    def test_create_filter_query(self):
        """Test creating a filter query from keyword arguments."""
        # Test with price range
        query = create_filter_query(min_price=10000, max_price=25000)
        self.assertEqual(query.price_range, (10000, 25000))
        
        # Test with year range
        query = create_filter_query(min_year=2018, max_year=2020)
        self.assertEqual(query.year_range, (2018, 2020))
        
        # Test with make and model
        query = create_filter_query(make="Toyota", model="Corolla")
        self.assertEqual(query.make, "Toyota")
        self.assertEqual(query.model, "Corolla")
        
        # Test with transmission
        query = create_filter_query(transmission="Automatic")
        self.assertEqual(query.transmission, "Automatic")
        
        # Test with location radius
        query = create_filter_query(postcode="M1 1AA", radius=10)
        self.assertEqual(query.location_radius, ("M1 1AA", 10))
        
        # Test with additional filters
        query = create_filter_query(fuel_type="Petrol", mileage=25000)
        self.assertEqual(query.additional_filters, {"fuel_type": "Petrol", "mileage": 25000})
        
        # Test with mixed parameters
        query = create_filter_query(
            min_price=10000, 
            max_price=30000,
            make="Honda",
            transmission="Automatic",
            fuel_type="Hybrid"
        )
        self.assertEqual(query.price_range, (10000, 30000))
        self.assertEqual(query.make, "Honda")
        self.assertEqual(query.transmission, "Automatic")
        self.assertEqual(query.additional_filters, {"fuel_type": "Hybrid"})

    def test_price_filter(self):
        """Test filtering by price range."""
        # Test with minimum and maximum price
        query = FilterQuery(price_range=(12000, 28000))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 3)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car1", car_ids)  # Toyota Corolla, 15000
        self.assertIn("car2", car_ids)  # Honda Civic, 22000
        self.assertIn("car3", car_ids)  # BMW 3 Series, 28000
        
        # Test with only minimum price
        query = FilterQuery(price_range=(25000, None))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 2)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car3", car_ids)  # BMW 3 Series, 28000
        self.assertIn("car5", car_ids)  # Audi A4, 35000
        
        # Test with only maximum price
        query = FilterQuery(price_range=(None, 15000))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 2)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car1", car_ids)  # Toyota Corolla, 15000
        self.assertIn("car4", car_ids)  # Ford Focus, 12000

    def test_year_filter(self):
        """Test filtering by year range."""
        # Test with minimum and maximum year
        query = FilterQuery(year_range=(2018, 2020))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 3)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car1", car_ids)  # Toyota Corolla, 2018
        self.assertIn("car2", car_ids)  # Honda Civic, 2020
        self.assertIn("car3", car_ids)  # BMW 3 Series, 2019
        
        # Test with only minimum year
        query = FilterQuery(year_range=(2020, None))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 2)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car2", car_ids)  # Honda Civic, 2020
        self.assertIn("car5", car_ids)  # Audi A4, 2021
        
        # Test with only maximum year
        query = FilterQuery(year_range=(None, 2018))
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 2)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car1", car_ids)  # Toyota Corolla, 2018
        self.assertIn("car4", car_ids)  # Ford Focus, 2017

    def test_make_filter(self):
        """Test filtering by make."""
        query = FilterQuery(make="Honda")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car2")  # Honda Civic
        
        # Test case insensitivity
        query = FilterQuery(make="toyota")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car1")  # Toyota Corolla

    def test_model_filter(self):
        """Test filtering by model."""
        query = FilterQuery(model="Focus")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car4")  # Ford Focus
        
        # Test case insensitivity
        query = FilterQuery(model="3 series")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car3")  # BMW 3 Series

    def test_transmission_filter(self):
        """Test filtering by transmission."""
        query = FilterQuery(transmission="Automatic")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 3)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car1", car_ids)  # Toyota Corolla, Automatic
        self.assertIn("car2", car_ids)  # Honda Civic, Automatic
        self.assertIn("car5", car_ids)  # Audi A4, Automatic
        
        # Test case insensitivity
        query = FilterQuery(transmission="manual")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 2)
        car_ids = [car.id for car in result.cars]
        self.assertIn("car3", car_ids)  # BMW 3 Series, Manual
        self.assertIn("car4", car_ids)  # Ford Focus, Manual

    def test_multiple_filters(self):
        """Test applying multiple filters."""
        # Test combining price, year, and transmission filters
        query = FilterQuery(
            price_range=(10000, 25000),
            year_range=(2017, 2019),
            transmission="Automatic"
        )
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car1")  # Toyota Corolla
        
        # Test combining make and model filters
        query = FilterQuery(make="BMW", model="3 Series")
        result = filter_cars(self.car_collection, query)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car3")  # BMW 3 Series

    def test_location_radius_filter(self):
        """Test filtering by location radius."""
        # This is just a basic test since our implementation is a placeholder
        query = FilterQuery(location_radius=("London", 10))
        result = filter_cars(self.car_collection, query)
        
        # All cars with a location should be included (all except car6)
        self.assertEqual(len(result), 5)
        car_ids = [car.id for car in result.cars]
        self.assertNotIn("car6", car_ids)  # VW Golf, location=None

    def test_filter_result(self):
        """Test FilterResult functionality."""
        # Test to_collection method
        query = FilterQuery(make="Honda")
        result = filter_cars(self.car_collection, query)
        
        collection = result.to_collection()
        self.assertIsInstance(collection, CarCollection)
        self.assertEqual(len(collection.cars), 1)
        self.assertEqual(collection.cars[0].id, "car2")  # Honda Civic
        
        # Test __len__ method
        self.assertEqual(len(result), 1)
        
        # Test query storage
        self.assertEqual(result.query.make, "Honda")

    def test_handling_none_values(self):
        """Test how filters handle None values."""
        # Car6 has many None values, it should be excluded from most filters
        
        # Price filter with None value
        query = FilterQuery(price_range=(5000, 50000))
        result = filter_cars(self.car_collection, query)
        self.assertEqual(len(result), 5)  # All cars except car6
        
        # Year filter with None value
        query = FilterQuery(year_range=(2010, 2022))
        result = filter_cars(self.car_collection, query)
        self.assertEqual(len(result), 5)  # All cars except car6
        
        # Make filter with None value (car6 has a make, so it should be included)
        query = FilterQuery(make="Volkswagen")
        result = filter_cars(self.car_collection, query)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.cars[0].id, "car6")
        
        # Transmission filter with None value
        query = FilterQuery(transmission="Automatic")
        result = filter_cars(self.car_collection, query)
        self.assertEqual(len(result), 3)  # car1, car2, car5 (not car6)


if __name__ == "__main__":
    unittest.main() 