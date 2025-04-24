"""
Tag Manager for Car Search application.

This module provides functionality to manage tags for cars, allowing users
to categorize and filter their search results and favorites.
"""

import logging
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.models.car import Car, CarCollection
from src.data.db_manager import db_manager

# Configure logging
logger = logging.getLogger(__name__)


class Tag:
    """
    Represents a tag that can be applied to cars.
    
    Tags allow users to categorize cars and filter their search results.
    """
    
    def __init__(self, id: Optional[int] = None, name: str = "", color: str = "#cccccc"):
        """
        Initialize a tag.
        
        Args:
            id: Tag ID in the database (None for new tags)
            name: Tag name
            color: Tag color in hex format
        """
        self.id = id
        self.name = name
        self.color = color
        self.created_at: Optional[str] = None
    
    def __str__(self) -> str:
        """Return string representation of the tag."""
        return f"{self.name} [{self.color}]"
    
    def __repr__(self) -> str:
        """Return string representation of the tag."""
        return f"Tag(id={self.id}, name='{self.name}', color='{self.color}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tag to a dictionary.
        
        Returns:
            Dictionary representation of the tag
        """
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        """
        Create a tag from a dictionary.
        
        Args:
            data: Dictionary containing tag data
            
        Returns:
            Tag object
        """
        tag = cls(id=data.get("id"), name=data.get("name", ""), color=data.get("color", "#cccccc"))
        tag.created_at = data.get("created_at")
        return tag


class TagManager:
    """
    Manager for tag operations.
    
    This class provides methods to create, retrieve, update, and delete tags,
    as well as associate tags with cars.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the tag manager.
        
        Args:
            db_path: Path to the SQLite database file.
                    If None, uses the database from db_manager.
        """
        self.db_path = db_path or db_manager.db_path
    
    def create_tag(self, name: str, color: str = "#cccccc") -> Optional[Tag]:
        """
        Create a new tag.
        
        Args:
            name: Tag name
            color: Tag color in hex format
            
        Returns:
            Created tag object if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if tag with same name already exists
                cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
                if cursor.fetchone():
                    logger.warning(f"Tag with name '{name}' already exists")
                    return None
                
                # Create a new tag
                created_at = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?)",
                    (name, color, created_at)
                )
                
                tag_id = cursor.lastrowid
                
                tag = Tag(id=tag_id, name=name, color=color)
                tag.created_at = created_at
                
                logger.debug(f"Created tag: {tag}")
                return tag
        except sqlite3.Error as e:
            logger.error(f"Error creating tag: {str(e)}")
            return None
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """
        Get a tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag object if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id, name, color, created_at FROM tags WHERE id = ?", (tag_id,))
                row = cursor.fetchone()
                
                if row:
                    tag = Tag(id=row[0], name=row[1], color=row[2])
                    tag.created_at = row[3]
                    return tag
                
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting tag {tag_id}: {str(e)}")
            return None
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Get a tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag object if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id, name, color, created_at FROM tags WHERE name = ?", (name,))
                row = cursor.fetchone()
                
                if row:
                    tag = Tag(id=row[0], name=row[1], color=row[2])
                    tag.created_at = row[3]
                    return tag
                
                return None
        except sqlite3.Error as e:
            logger.error(f"Error getting tag by name '{name}': {str(e)}")
            return None
    
    def get_all_tags(self) -> List[Tag]:
        """
        Get all tags.
        
        Returns:
            List of tag objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id, name, color, created_at FROM tags ORDER BY name")
                rows = cursor.fetchall()
                
                tags = []
                for row in rows:
                    tag = Tag(id=row[0], name=row[1], color=row[2])
                    tag.created_at = row[3]
                    tags.append(tag)
                return tags
        except sqlite3.Error as e:
            logger.error(f"Error getting all tags: {str(e)}")
            return []
    
    def update_tag(self, tag_id: int, name: Optional[str] = None, color: Optional[str] = None) -> bool:
        """
        Update a tag.
        
        Args:
            tag_id: Tag ID
            name: New tag name (if None, not updated)
            color: New tag color (if None, not updated)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if name is None and color is None:
                return True  # Nothing to update
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if tag exists
                cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
                if not cursor.fetchone():
                    logger.warning(f"Tag with ID {tag_id} not found")
                    return False
                
                # Check if new name already exists
                if name is not None:
                    cursor.execute("SELECT id FROM tags WHERE name = ? AND id != ?", (name, tag_id))
                    if cursor.fetchone():
                        logger.warning(f"Tag with name '{name}' already exists")
                        return False
                
                # Build update query
                update_fields = []
                params = []
                
                if name is not None:
                    update_fields.append("name = ?")
                    params.append(name)
                
                if color is not None:
                    update_fields.append("color = ?")
                    params.append(color)
                
                # Add tag_id to params
                params.append(tag_id)
                
                # Execute update query
                cursor.execute(
                    f"UPDATE tags SET {', '.join(update_fields)} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"Updated tag {tag_id}")
                    return True
                else:
                    logger.warning(f"No changes made to tag {tag_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error updating tag {tag_id}: {str(e)}")
            return False
    
    def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if tag exists
                cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
                if not cursor.fetchone():
                    logger.warning(f"Tag with ID {tag_id} not found")
                    return False
                
                # Delete the tag (car_tags will be deleted automatically due to CASCADE)
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                
                if cursor.rowcount > 0:
                    logger.debug(f"Deleted tag {tag_id}")
                    return True
                else:
                    logger.warning(f"Could not delete tag {tag_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting tag {tag_id}: {str(e)}")
            return False
    
    def add_tag_to_car(self, car_id: str, tag_id: int) -> bool:
        """
        Add a tag to a car.
        
        Args:
            car_id: Car ID
            tag_id: Tag ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if car exists
                cursor.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
                if not cursor.fetchone():
                    logger.warning(f"Car with ID {car_id} not found")
                    return False
                
                # Check if tag exists
                cursor.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
                if not cursor.fetchone():
                    logger.warning(f"Tag with ID {tag_id} not found")
                    return False
                
                # Check if car already has this tag
                cursor.execute(
                    "SELECT 1 FROM car_tags WHERE car_id = ? AND tag_id = ?",
                    (car_id, tag_id)
                )
                if cursor.fetchone():
                    logger.debug(f"Car {car_id} already has tag {tag_id}")
                    return True
                
                # Add tag to car
                cursor.execute(
                    "INSERT INTO car_tags (car_id, tag_id, created_at) VALUES (?, ?, ?)",
                    (car_id, tag_id, datetime.now().isoformat())
                )
                
                logger.debug(f"Added tag {tag_id} to car {car_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding tag {tag_id} to car {car_id}: {str(e)}")
            return False
    
    def add_tag_to_car_by_name(self, car_id: str, tag_name: str) -> bool:
        """
        Add a tag to a car by tag name.
        
        If the tag doesn't exist, it will be created.
        
        Args:
            car_id: Car ID
            tag_name: Tag name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create tag
            tag = self.get_tag_by_name(tag_name)
            if not tag:
                tag = self.create_tag(tag_name)
                if not tag:
                    return False
            
            # Add tag to car (tag.id will not be None at this point)
            if tag.id is None:
                logger.error(f"Tag ID is None for tag '{tag_name}'")
                return False
                
            return self.add_tag_to_car(car_id, tag.id)
        except Exception as e:
            logger.error(f"Error adding tag '{tag_name}' to car {car_id}: {str(e)}")
            return False
    
    def remove_tag_from_car(self, car_id: str, tag_id: int) -> bool:
        """
        Remove a tag from a car.
        
        Args:
            car_id: Car ID
            tag_id: Tag ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete the car-tag association
                cursor.execute(
                    "DELETE FROM car_tags WHERE car_id = ? AND tag_id = ?",
                    (car_id, tag_id)
                )
                
                if cursor.rowcount > 0:
                    logger.debug(f"Removed tag {tag_id} from car {car_id}")
                    return True
                else:
                    logger.warning(f"Car {car_id} does not have tag {tag_id}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"Error removing tag {tag_id} from car {car_id}: {str(e)}")
            return False
    
    def get_car_tags(self, car_id: str) -> List[Tag]:
        """
        Get all tags for a car.
        
        Args:
            car_id: Car ID
            
        Returns:
            List of tags for the car
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.color, t.created_at
                    FROM tags t
                    JOIN car_tags ct ON t.id = ct.tag_id
                    WHERE ct.car_id = ?
                    ORDER BY t.name
                    """,
                    (car_id,)
                )
                
                rows = cursor.fetchall()
                
                tags = []
                for row in rows:
                    tag = Tag(id=row[0], name=row[1], color=row[2])
                    tag.created_at = row[3]
                    tags.append(tag)
                return tags
        except sqlite3.Error as e:
            logger.error(f"Error getting tags for car {car_id}: {str(e)}")
            return []
    
    def get_cars_by_tag(self, tag_id: int) -> List[str]:
        """
        Get all car IDs with a specific tag.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            List of car IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT car_id FROM car_tags WHERE tag_id = ?",
                    (tag_id,)
                )
                
                rows = cursor.fetchall()
                
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting cars with tag {tag_id}: {str(e)}")
            return []
    
    def get_cars_by_tag_name(self, tag_name: str) -> List[str]:
        """
        Get all car IDs with a specific tag name.
        
        Args:
            tag_name: Tag name
            
        Returns:
            List of car IDs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT ct.car_id
                    FROM car_tags ct
                    JOIN tags t ON ct.tag_id = t.id
                    WHERE t.name = ?
                    """,
                    (tag_name,)
                )
                
                rows = cursor.fetchall()
                
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting cars with tag name '{tag_name}': {str(e)}")
            return []
    
    def get_cars_by_tags(self, tag_ids: List[int], require_all: bool = False) -> List[str]:
        """
        Get all car IDs with specific tags.
        
        Args:
            tag_ids: List of tag IDs
            require_all: If True, cars must have all tags. If False, cars must have any of the tags.
            
        Returns:
            List of car IDs
        """
        if not tag_ids:
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if require_all:
                    # Cars must have all tags
                    placeholders = ",".join(["?"] * len(tag_ids))
                    cursor.execute(
                        f"""
                        SELECT car_id
                        FROM car_tags
                        WHERE tag_id IN ({placeholders})
                        GROUP BY car_id
                        HAVING COUNT(DISTINCT tag_id) = ?
                        """,
                        tag_ids + [len(tag_ids)]
                    )
                else:
                    # Cars must have any of the tags
                    placeholders = ",".join(["?"] * len(tag_ids))
                    cursor.execute(
                        f"""
                        SELECT DISTINCT car_id
                        FROM car_tags
                        WHERE tag_id IN ({placeholders})
                        """,
                        tag_ids
                    )
                
                rows = cursor.fetchall()
                
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting cars with tags {tag_ids}: {str(e)}")
            return []
    
    def get_popular_tags(self, limit: int = 10) -> List[Tuple[Tag, int]]:
        """
        Get most popular tags by usage count.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of (tag, count) tuples
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.color, t.created_at, COUNT(ct.car_id) AS count
                    FROM tags t
                    JOIN car_tags ct ON t.id = ct.tag_id
                    GROUP BY t.id
                    ORDER BY count DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
                
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    tag = Tag(id=row[0], name=row[1], color=row[2])
                    tag.created_at = row[3]
                    result.append((tag, row[4]))
                return result
        except sqlite3.Error as e:
            logger.error(f"Error getting popular tags: {str(e)}")
            return []


# Create a singleton instance
tag_manager = TagManager() 