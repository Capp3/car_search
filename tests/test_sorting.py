"""
Unit tests for the sorting module.
"""

import unittest
from datetime import datetime, timedelta

from src.data.sorting import SortManager, SortCriteria, SortField, SortDirection
from src.models.car import Car, CarCollection


class TestSorting(unittest.TestCase):
    """Test cases for the sorting module."""

    def setUp(self):
        """Set up test data."""
        # Create test cars with various attributes
        self.car1 = Car(
            id="1",
            make="Toyota",
            model="Camry",
            year=2020,
            price=25000,
            mileage=15000,
            date_listed=datetime.now() - timedelta(days=10),
            location="New York"
        )
        
        self.car2 = Car(
            id="2",
            make="Honda",
            model="Accord",
            year=2019,
            price=22000,
            mileage=20000,
            date_listed=datetime.now() - timedelta(days=5),
            location="Los Angeles"
        )
        
        self.car3 = Car(
            id="3",
            make="BMW",
            model="X5",
            year=2021,
            price=45000,
            mileage=5000,
            date_listed=datetime.now() - timedelta(days=1),
            location="Chicago"
        )
        
        self.car4 = Car(
            id="4",
            make="Audi",
            model="A4",
            year=2018,
            price=30000,
            mileage=25000,
            date_listed=datetime.now() - timedelta(days=15),
            location="Miami"
        )
        
        # Car with missing values
        self.car5 = Car(
            id="5",
            make="Ford",
            model="Mustang",
            year=None,
            price=None,
            mileage=None,
            date_listed=None,
            location="Dallas"
        )
        
        # Create a car collection
        self.cars = [self.car1, self.car2, self.car3, self.car4, self.car5]
        self.car_collection = CarCollection(cars=self.cars)
        
        # Create a sort manager
        self.sort_manager = SortManager()

    def test_sort_by_price_ascending(self):
        """Test sorting by price in ascending order."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.PRICE, SortDirection.ASCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Check order: car2, car1, car4, car3, car5 (car5 has no price, should be last)
        self.assertEqual(sorted_cars[0].id, "2")
        self.assertEqual(sorted_cars[1].id, "1")
        self.assertEqual(sorted_cars[2].id, "4")
        self.assertEqual(sorted_cars[3].id, "3")
        self.assertEqual(sorted_cars[4].id, "5")  # Null price should be last in ascending sort

    def test_sort_by_price_descending(self):
        """Test sorting by price in descending order."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.PRICE, SortDirection.DESCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Check order: car3, car4, car1, car2, car5 (car5 has no price, should be last)
        self.assertEqual(sorted_cars[0].id, "3")
        self.assertEqual(sorted_cars[1].id, "4")
        self.assertEqual(sorted_cars[2].id, "1")
        self.assertEqual(sorted_cars[3].id, "2")
        self.assertEqual(sorted_cars[4].id, "5")  # Null price should be last in descending sort too

    def test_sort_by_year(self):
        """Test sorting by year."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.YEAR, SortDirection.DESCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Check order: car3, car1, car2, car4, car5 (car5 has no year, should be last)
        self.assertEqual(sorted_cars[0].id, "3")  # 2021
        self.assertEqual(sorted_cars[1].id, "1")  # 2020
        self.assertEqual(sorted_cars[2].id, "2")  # 2019
        self.assertEqual(sorted_cars[3].id, "4")  # 2018
        self.assertEqual(sorted_cars[4].id, "5")  # null year

    def test_sort_by_date_listed(self):
        """Test sorting by date listed."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.DATE_LISTED, SortDirection.ASCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Check order: car5 (null date, treated as earliest), car4, car1, car2, car3
        self.assertEqual(sorted_cars[0].id, "5")  # null date
        self.assertEqual(sorted_cars[1].id, "4")  # 15 days ago
        self.assertEqual(sorted_cars[2].id, "1")  # 10 days ago
        self.assertEqual(sorted_cars[3].id, "2")  # 5 days ago
        self.assertEqual(sorted_cars[4].id, "3")  # 1 day ago

    def test_sort_by_make(self):
        """Test sorting by make."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.MAKE, SortDirection.ASCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Check alphabetical order: Audi, BMW, Ford, Honda, Toyota
        self.assertEqual(sorted_cars[0].id, "4")  # Audi
        self.assertEqual(sorted_cars[1].id, "3")  # BMW
        self.assertEqual(sorted_cars[2].id, "5")  # Ford
        self.assertEqual(sorted_cars[3].id, "2")  # Honda
        self.assertEqual(sorted_cars[4].id, "1")  # Toyota

    def test_multiple_sort_criteria(self):
        """Test sorting with multiple criteria."""
        # Sort by year (descending) and then by price (ascending)
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.YEAR, SortDirection.DESCENDING))
        self.sort_manager.add_criteria(SortCriteria(SortField.PRICE, SortDirection.ASCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.cars)
        
        # Expected order: 
        # 1. Year 2021: car3
        # 2. Year 2020: car1
        # 3. Year 2019: car2
        # 4. Year 2018: car4
        # 5. Year null: car5
        self.assertEqual(sorted_cars[0].id, "3")
        self.assertEqual(sorted_cars[1].id, "1")
        self.assertEqual(sorted_cars[2].id, "2")
        self.assertEqual(sorted_cars[3].id, "4")
        self.assertEqual(sorted_cars[4].id, "5")

    def test_sort_car_collection(self):
        """Test sorting a CarCollection object."""
        self.sort_manager.reset_criteria()
        self.sort_manager.add_criteria(SortCriteria(SortField.PRICE, SortDirection.ASCENDING))
        
        sorted_cars = self.sort_manager.sort_cars(self.car_collection)
        
        # Same order as test_sort_by_price_ascending
        self.assertEqual(sorted_cars[0].id, "2")
        self.assertEqual(sorted_cars[1].id, "1")
        self.assertEqual(sorted_cars[2].id, "4")
        self.assertEqual(sorted_cars[3].id, "3")
        self.assertEqual(sorted_cars[4].id, "5")


if __name__ == '__main__':
    unittest.main() 