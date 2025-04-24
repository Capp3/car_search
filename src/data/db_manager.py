"""
Database manager module for Car Search application.

This module provides functionality to store and retrieve car data using SQLite.
"""

import os
import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from src.models.car import Car, CarCollection
from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manager for SQLite database operations.
    
    This class provides methods to store and retrieve car data using SQLite.
    """
    
    # Database schema version - increment when schema changes
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file.
                    If None, uses the default path from config.
        """
        if db_path is None:
            db_dir = str(settings.app.data_dir)
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "car_search.db")
        
        self.db_path = db_path
        logger.info(f"Database initialized at {db_path}")
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self) -> None:
        """
        Initialize the database schema if it doesn't exist.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if schema_info table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'"
                )
                if not cursor.fetchone():
                    # Create schema_info table
                    cursor.execute(
                        """
                        CREATE TABLE schema_info (
                            version INTEGER PRIMARY KEY,
                            created_at TEXT NOT NULL
                        )
                        """
                    )
                    cursor.execute(
                        "INSERT INTO schema_info (version, created_at) VALUES (?, ?)",
                        (self.SCHEMA_VERSION, datetime.now().isoformat())
                    )
                    
                    # Create cars table
                    cursor.execute(
                        """
                        CREATE TABLE cars (
                            id TEXT PRIMARY KEY,
                            title TEXT,
                            make TEXT,
                            model TEXT,
                            year INTEGER,
                            price REAL,
                            mileage INTEGER,
                            registration TEXT,
                            attributes TEXT NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            source TEXT
                        )
                        """
                    )
                    
                    # Create searches table
                    cursor.execute(
                        """
                        CREATE TABLE searches (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            search_params TEXT NOT NULL,
                            result_count INTEGER NOT NULL,
                            created_at TEXT NOT NULL,
                            region TEXT
                        )
                        """
                    )
                    
                    # Create search_results table to track which cars were found in which searches
                    cursor.execute(
                        """
                        CREATE TABLE search_results (
                            search_id INTEGER,
                            car_id TEXT,
                            position INTEGER,
                            PRIMARY KEY (search_id, car_id),
                            FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE,
                            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                        )
                        """
                    )
                    
                    # Create favorites table
                    cursor.execute(
                        """
                        CREATE TABLE favorites (
                            car_id TEXT PRIMARY KEY,
                            notes TEXT,
                            created_at TEXT NOT NULL,
                            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                        )
                        """
                    )
                    
                    # Create comparison_sets table
                    cursor.execute(
                        """
                        CREATE TABLE comparison_sets (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            description TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                        """
                    )
                    
                    # Create comparison_cars table
                    cursor.execute(
                        """
                        CREATE TABLE comparison_cars (
                            comparison_id INTEGER,
                            car_id TEXT,
                            created_at TEXT NOT NULL,
                            PRIMARY KEY (comparison_id, car_id),
                            FOREIGN KEY (comparison_id) REFERENCES comparison_sets(id) ON DELETE CASCADE,
                            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                        )
                        """
                    )
                    
                    # Create indexes for better performance
                    cursor.execute("CREATE INDEX idx_cars_make_model ON cars(make, model)")
                    cursor.execute("CREATE INDEX idx_cars_year ON cars(year)")
                    cursor.execute("CREATE INDEX idx_cars_price ON cars(price)")
                    cursor.execute("CREATE INDEX idx_cars_registration ON cars(registration)")
                    
                    conn.commit()
                    logger.info(f"Database schema v{self.SCHEMA_VERSION} created")
                else:
                    # Check if schema needs upgrade
                    cursor.execute("SELECT version FROM schema_info LIMIT 1")
                    current_version = cursor.fetchone()[0]
                    
                    if current_version < self.SCHEMA_VERSION:
                        self._upgrade_schema(current_version)
                        logger.info(f"Database schema upgraded from v{current_version} to v{self.SCHEMA_VERSION}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _upgrade_schema(self, current_version: int) -> None:
        """
        Upgrade the database schema to the latest version.
        
        Args:
            current_version: Current schema version.
        """
        # This will be implemented when schema upgrades are needed
        logger.warning(f"Schema upgrade from v{current_version} to v{self.SCHEMA_VERSION} not implemented")
    
    def _car_to_dict(self, car: Car) -> Dict[str, Any]:
        """
        Convert a Car object to a dictionary for database storage.
        
        Args:
            car: Car object to convert.
            
        Returns:
            Dictionary representation of the car.
        """
        # Extract basic properties
        car_dict = {
            "id": car.id,
            "title": car.get_attribute("title"),
            "make": car.get_attribute("make"),
            "model": car.get_attribute("model"),
            "year": car.get_attribute("year"),
            "price": car.get_attribute("price"),
            "mileage": car.get_attribute("mileage"),
            "registration": car.get_attribute("registration"),
            "source": car.get_attribute("source"),
            "attributes": json.dumps({name: {"name": attr.name, "type": attr.type.value, 
                                             "sources": {s_name: {"source_name": s.source_name, 
                                                                 "timestamp": s.timestamp.isoformat(),
                                                                 "confidence": s.confidence.value,
                                                                 "raw_value": s.raw_value}
                                                       for s_name, s in attr.sources.items()},
                                             "computed": attr.computed}
                                     for name, attr in car.attributes.items()}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return car_dict
    
    def _dict_to_car(self, car_dict: Dict[str, Any]) -> Car:
        """
        Convert a dictionary to a Car object.
        
        Args:
            car_dict: Dictionary representation of a car.
            
        Returns:
            Car object.
        """
        # Create a new Car with the ID
        car = Car(id=car_dict["id"])
        
        # Load attributes from JSON
        attributes_json = json.loads(car_dict["attributes"])
        for attr_name, attr_data in attributes_json.items():
            # This will be handled by the Car's set_attribute method
            # We only need to add each source
            for source_name, source_data in attr_data["sources"].items():
                from src.models.car import AttributeType, ConfidenceLevel
                
                # Convert values back to appropriate types
                confidence = ConfidenceLevel(source_data["confidence"])
                
                # Use setter for each attribute source
                car.set_attribute(
                    attr_name,
                    source_data["raw_value"],
                    source_name,
                    confidence,
                    AttributeType(attr_data["type"])
                )
        
        return car
    
    def save_car(self, car: Car) -> bool:
        """
        Save a car to the database.
        
        Args:
            car: Car object to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            car_dict = self._car_to_dict(car)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if car already exists
                cursor.execute("SELECT id FROM cars WHERE id = ?", (car.id,))
                if cursor.fetchone():
                    # Update existing car
                    car_dict["updated_at"] = datetime.now().isoformat()
                    
                    fields = []
                    values = []
                    for key, value in car_dict.items():
                        if key != "id" and key != "created_at":
                            fields.append(f"{key} = ?")
                            values.append(value)
                    
                    values.append(car.id)  # For the WHERE clause
                    
                    query = f"UPDATE cars SET {', '.join(fields)} WHERE id = ?"
                    cursor.execute(query, values)
                    
                    logger.debug(f"Updated car {car.id} in database")
                else:
                    # Insert new car
                    fields = list(car_dict.keys())
                    placeholders = ["?"] * len(fields)
                    
                    query = f"INSERT INTO cars ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                    cursor.execute(query, list(car_dict.values()))
                    
                    logger.debug(f"Inserted car {car.id} into database")
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving car {car.id} to database: {str(e)}")
            return False
    
    def save_cars(self, cars: Union[List[Car], CarCollection]) -> int:
        """
        Save multiple cars to the database.
        
        Args:
            cars: List of Car objects or CarCollection to save.
            
        Returns:
            Number of cars successfully saved.
        """
        if isinstance(cars, CarCollection):
            cars = cars.cars
        
        saved_count = 0
        for car in cars:
            if self.save_car(car):
                saved_count += 1
        
        logger.info(f"Saved {saved_count}/{len(cars)} cars to database")
        return saved_count
    
    def get_car(self, car_id: str) -> Optional[Car]:
        """
        Get a car from the database by ID.
        
        Args:
            car_id: ID of the car to retrieve.
            
        Returns:
            Car object if found, None otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM cars WHERE id = ?", (car_id,))
                row = cursor.fetchone()
                
                if row:
                    car_dict = dict(row)
                    return self._dict_to_car(car_dict)
                
                return None
        except Exception as e:
            logger.error(f"Error getting car {car_id} from database: {str(e)}")
            return None
    
    def get_all_cars(self, limit: int = 1000, offset: int = 0) -> List[Car]:
        """
        Get all cars from the database.
        
        Args:
            limit: Maximum number of cars to retrieve.
            offset: Number of cars to skip before returning results.
            
        Returns:
            List of Car objects.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM cars LIMIT ? OFFSET ?", (limit, offset))
                rows = cursor.fetchall()
                
                return [self._dict_to_car(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all cars from database: {str(e)}")
            return []
    
    def get_cars_by_criteria(self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Car]:
        """
        Get cars from the database that match the given criteria.
        
        Args:
            criteria: Dictionary of field-value pairs to match against.
            limit: Maximum number of cars to retrieve.
            offset: Number of cars to skip before returning results.
            
        Returns:
            List of Car objects matching the criteria.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build WHERE clause for criteria
                where_clauses = []
                values = []
                
                for field, value in criteria.items():
                    if isinstance(value, (list, tuple)):
                        # Handle IN clauses
                        placeholders = ["?"] * len(value)
                        where_clauses.append(f"{field} IN ({', '.join(placeholders)})")
                        values.extend(value)
                    elif value is None:
                        # Handle NULL values
                        where_clauses.append(f"{field} IS NULL")
                    else:
                        # Handle regular equality
                        where_clauses.append(f"{field} = ?")
                        values.append(value)
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = f"SELECT * FROM cars WHERE {where_clause} LIMIT ? OFFSET ?"
                cursor.execute(query, values + [limit, offset])
                
                rows = cursor.fetchall()
                return [self._dict_to_car(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting cars by criteria from database: {str(e)}")
            return []
    
    def save_search(self, search_params: Dict[str, Any], result_count: int, region: str = "uk") -> Optional[int]:
        """
        Save a search to the database.
        
        Args:
            search_params: Search parameters used.
            result_count: Number of results found.
            region: Region the search was performed in.
            
        Returns:
            ID of the search if successful, None otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO searches (search_params, result_count, created_at, region)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        json.dumps(search_params),
                        result_count,
                        datetime.now().isoformat(),
                        region
                    )
                )
                
                conn.commit()
                search_id = cursor.lastrowid
                logger.debug(f"Saved search with ID {search_id} to database")
                
                return search_id
        except Exception as e:
            logger.error(f"Error saving search to database: {str(e)}")
            return None
    
    def save_search_results(self, search_id: int, car_ids: List[str]) -> bool:
        """
        Save search results to the database.
        
        Args:
            search_id: ID of the search.
            car_ids: List of car IDs in the search results.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare data for bulk insert
                data = [(search_id, car_id, idx) for idx, car_id in enumerate(car_ids)]
                
                cursor.executemany(
                    """
                    INSERT INTO search_results (search_id, car_id, position)
                    VALUES (?, ?, ?)
                    """,
                    data
                )
                
                conn.commit()
                logger.debug(f"Saved {len(car_ids)} search results for search ID {search_id} to database")
                
                return True
        except Exception as e:
            logger.error(f"Error saving search results to database: {str(e)}")
            return False
    
    def add_favorite(self, car_id: str, notes: Optional[str] = None) -> bool:
        """
        Add a car to favorites.
        
        Args:
            car_id: ID of the car to add to favorites.
            notes: Optional notes about the favorite.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if car exists
                cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add favorite: Car {car_id} not found in database")
                    return False
                
                # Check if already a favorite
                cursor.execute("SELECT car_id FROM favorites WHERE car_id = ?", (car_id,))
                if cursor.fetchone():
                    # Update existing favorite
                    cursor.execute(
                        "UPDATE favorites SET notes = ? WHERE car_id = ?",
                        (notes, car_id)
                    )
                else:
                    # Add new favorite
                    cursor.execute(
                        """
                        INSERT INTO favorites (car_id, notes, created_at)
                        VALUES (?, ?, ?)
                        """,
                        (car_id, notes, datetime.now().isoformat())
                    )
                
                conn.commit()
                logger.debug(f"Added car {car_id} to favorites")
                
                return True
        except Exception as e:
            logger.error(f"Error adding car {car_id} to favorites: {str(e)}")
            return False
    
    def remove_favorite(self, car_id: str) -> bool:
        """
        Remove a car from favorites.
        
        Args:
            car_id: ID of the car to remove from favorites.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM favorites WHERE car_id = ?", (car_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.debug(f"Removed car {car_id} from favorites")
                    return True
                else:
                    logger.warning(f"Car {car_id} not found in favorites")
                    return False
        except Exception as e:
            logger.error(f"Error removing car {car_id} from favorites: {str(e)}")
            return False
    
    def get_favorites(self) -> List[Car]:
        """
        Get all favorite cars.
        
        Returns:
            List of favorite Car objects.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT c.*, f.notes, f.created_at AS favorited_at
                    FROM cars c
                    JOIN favorites f ON c.id = f.car_id
                    ORDER BY f.created_at DESC
                    """
                )
                
                rows = cursor.fetchall()
                
                cars = []
                for row in rows:
                    car_dict = dict(row)
                    car = self._dict_to_car(car_dict)
                    
                    # Add favorite-specific attributes
                    car.set_attribute("favorite_notes", car_dict["notes"], "database")
                    car.set_attribute("favorited_at", car_dict["favorited_at"], "database")
                    
                    cars.append(car)
                
                return cars
        except Exception as e:
            logger.error(f"Error getting favorites from database: {str(e)}")
            return []
    
    def create_comparison(self, name: str, description: Optional[str] = None) -> Optional[int]:
        """
        Create a new comparison set.
        
        Args:
            name: Name of the comparison set.
            description: Optional description of the comparison set.
            
        Returns:
            ID of the comparison set if successful, None otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                cursor.execute(
                    """
                    INSERT INTO comparison_sets (name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, description, now, now)
                )
                
                conn.commit()
                comparison_id = cursor.lastrowid
                logger.debug(f"Created comparison set {name} with ID {comparison_id}")
                
                return comparison_id
        except Exception as e:
            logger.error(f"Error creating comparison set: {str(e)}")
            return None
    
    def add_car_to_comparison(self, comparison_id: int, car_id: str) -> bool:
        """
        Add a car to a comparison set.
        
        Args:
            comparison_id: ID of the comparison set.
            car_id: ID of the car to add.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if comparison exists
                cursor.execute("SELECT id FROM comparison_sets WHERE id = ?", (comparison_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add car to comparison: Comparison set {comparison_id} not found")
                    return False
                
                # Check if car exists
                cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add car to comparison: Car {car_id} not found in database")
                    return False
                
                # Check if car is already in the comparison
                cursor.execute(
                    "SELECT car_id FROM comparison_cars WHERE comparison_id = ? AND car_id = ?",
                    (comparison_id, car_id)
                )
                if cursor.fetchone():
                    logger.warning(f"Car {car_id} is already in comparison set {comparison_id}")
                    return True
                
                # Add car to comparison
                cursor.execute(
                    """
                    INSERT INTO comparison_cars (comparison_id, car_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (comparison_id, car_id, datetime.now().isoformat())
                )
                
                # Update comparison set timestamp
                cursor.execute(
                    "UPDATE comparison_sets SET updated_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), comparison_id)
                )
                
                conn.commit()
                logger.debug(f"Added car {car_id} to comparison set {comparison_id}")
                
                return True
        except Exception as e:
            logger.error(f"Error adding car {car_id} to comparison set {comparison_id}: {str(e)}")
            return False
    
    def remove_car_from_comparison(self, comparison_id: int, car_id: str) -> bool:
        """
        Remove a car from a comparison set.
        
        Args:
            comparison_id: ID of the comparison set.
            car_id: ID of the car to remove.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM comparison_cars WHERE comparison_id = ? AND car_id = ?",
                    (comparison_id, car_id)
                )
                
                if cursor.rowcount > 0:
                    # Update comparison set timestamp
                    cursor.execute(
                        "UPDATE comparison_sets SET updated_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), comparison_id)
                    )
                    
                    conn.commit()
                    logger.debug(f"Removed car {car_id} from comparison set {comparison_id}")
                    return True
                else:
                    logger.warning(f"Car {car_id} not found in comparison set {comparison_id}")
                    return False
        except Exception as e:
            logger.error(f"Error removing car {car_id} from comparison set {comparison_id}: {str(e)}")
            return False
    
    def get_comparison(self, comparison_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a comparison set with its cars.
        
        Args:
            comparison_id: ID of the comparison set.
            
        Returns:
            Dictionary with comparison set metadata and car objects if found, None otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get comparison set metadata
                cursor.execute(
                    "SELECT * FROM comparison_sets WHERE id = ?",
                    (comparison_id,)
                )
                
                comparison_row = cursor.fetchone()
                if not comparison_row:
                    logger.warning(f"Comparison set {comparison_id} not found")
                    return None
                
                comparison_data = dict(comparison_row)
                
                # Get cars in the comparison set
                cursor.execute(
                    """
                    SELECT c.*, cc.created_at AS added_at
                    FROM cars c
                    JOIN comparison_cars cc ON c.id = cc.car_id
                    WHERE cc.comparison_id = ?
                    ORDER BY cc.created_at
                    """,
                    (comparison_id,)
                )
                
                car_rows = cursor.fetchall()
                cars = []
                
                for row in car_rows:
                    car_dict = dict(row)
                    car = self._dict_to_car(car_dict)
                    
                    # Add comparison-specific attributes
                    car.set_attribute("added_to_comparison_at", car_dict["added_at"], "database")
                    
                    cars.append(car)
                
                # Assemble complete comparison data
                result = {
                    "id": comparison_data["id"],
                    "name": comparison_data["name"],
                    "description": comparison_data["description"],
                    "created_at": comparison_data["created_at"],
                    "updated_at": comparison_data["updated_at"],
                    "cars": cars
                }
                
                return result
        except Exception as e:
            logger.error(f"Error getting comparison set {comparison_id}: {str(e)}")
            return None
    
    def get_comparisons(self) -> List[Dict[str, Any]]:
        """
        Get all comparison sets with summary information.
        
        Returns:
            List of dictionaries with comparison set metadata and car counts.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT cs.*, COUNT(cc.car_id) AS car_count
                    FROM comparison_sets cs
                    LEFT JOIN comparison_cars cc ON cs.id = cc.comparison_id
                    GROUP BY cs.id
                    ORDER BY cs.updated_at DESC
                    """
                )
                
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    comparison_data = dict(row)
                    result.append({
                        "id": comparison_data["id"],
                        "name": comparison_data["name"],
                        "description": comparison_data["description"],
                        "created_at": comparison_data["created_at"],
                        "updated_at": comparison_data["updated_at"],
                        "car_count": comparison_data["car_count"]
                    })
                
                return result
        except Exception as e:
            logger.error(f"Error getting comparison sets: {str(e)}")
            return []
    
    def delete_comparison(self, comparison_id: int) -> bool:
        """
        Delete a comparison set.
        
        Args:
            comparison_id: ID of the comparison set to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM comparison_sets WHERE id = ?", (comparison_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.debug(f"Deleted comparison set {comparison_id}")
                    return True
                else:
                    logger.warning(f"Comparison set {comparison_id} not found")
                    return False
        except Exception as e:
            logger.error(f"Error deleting comparison set {comparison_id}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count total cars
                cursor.execute("SELECT COUNT(*) FROM cars")
                stats["total_cars"] = cursor.fetchone()[0]
                
                # Count favorites
                cursor.execute("SELECT COUNT(*) FROM favorites")
                stats["total_favorites"] = cursor.fetchone()[0]
                
                # Count comparison sets
                cursor.execute("SELECT COUNT(*) FROM comparison_sets")
                stats["total_comparisons"] = cursor.fetchone()[0]
                
                # Count searches
                cursor.execute("SELECT COUNT(*) FROM searches")
                stats["total_searches"] = cursor.fetchone()[0]
                
                # Get average cars per search
                cursor.execute("SELECT AVG(result_count) FROM searches")
                stats["avg_cars_per_search"] = cursor.fetchone()[0] or 0
                
                # Get database file size
                stats["database_size_bytes"] = os.path.getsize(self.db_path)
                
                return stats
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {"error": str(e)}


# Create a singleton instance
db_manager = DatabaseManager() 