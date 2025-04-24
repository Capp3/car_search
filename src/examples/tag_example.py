#!/usr/bin/env python3
"""
Example script demonstrating how to use the tag system.

This script shows how to:
1. Create and manage tags
2. Associate tags with cars
3. Search for cars by tag(s)
4. Get tag statistics
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.tag_manager import tag_manager, Tag
from src.data.db_manager import db_manager
from src.examples.db_example import create_sample_cars

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_tag_safe(name: str, color: str = "#cccccc") -> Optional[Tag]:
    """Create a tag and ensure it has a valid ID."""
    tag = tag_manager.create_tag(name, color)
    if tag is None or tag.id is None:
        print(f"Failed to create tag '{name}'")
        return None
    return tag


def main():
    """Run the tag example script."""
    print(f"Database path: {db_manager.db_path}")
    
    # Ensure sample cars exist in the database
    sample_cars = create_sample_cars()
    db_manager.save_cars(sample_cars)
    
    # Example 1: Create tags
    print("\n=== Example 1: Create Tags ===")
    print("Creating tags...")
    
    # Create tags safely
    sedan_tag = create_tag_safe("Sedan", "#3498db")
    suv_tag = create_tag_safe("SUV", "#e74c3c")
    electric_tag = create_tag_safe("Electric", "#2ecc71")
    favorite_tag = create_tag_safe("Favorite", "#f1c40f")
    japanese_tag = create_tag_safe("Japanese", "#9b59b6")
    american_tag = create_tag_safe("American", "#e67e22")
    
    # Verify that all tags were created successfully
    all_tags = [sedan_tag, suv_tag, electric_tag, favorite_tag, japanese_tag, american_tag]
    if None in all_tags:
        print("Error: Failed to create some tags. Exiting.")
        return
    
    print(f"Created tags: {sedan_tag}, {suv_tag}, {electric_tag}, {favorite_tag}, {japanese_tag}, {american_tag}")
    
    # Now we know all tags are not None and have IDs
    # Use non-None assertion to tell type checker these are not None
    sedan_tag_id = sedan_tag.id
    suv_tag_id = suv_tag.id
    electric_tag_id = electric_tag.id
    favorite_tag_id = favorite_tag.id
    japanese_tag_id = japanese_tag.id
    american_tag_id = american_tag.id
    
    # Example 2: Associate tags with cars
    print("\n=== Example 2: Associate Tags with Cars ===")
    
    # Toyota Camry
    print("Adding tags to Toyota Camry...")
    tag_manager.add_tag_to_car("sample_1", sedan_tag_id)
    tag_manager.add_tag_to_car("sample_1", japanese_tag_id)
    tag_manager.add_tag_to_car("sample_1", favorite_tag_id)
    
    # Honda Accord
    print("Adding tags to Honda Accord...")
    tag_manager.add_tag_to_car("sample_2", sedan_tag_id)
    tag_manager.add_tag_to_car("sample_2", japanese_tag_id)
    
    # Tesla Model 3
    print("Adding tags to Tesla Model 3...")
    tag_manager.add_tag_to_car("sample_3", sedan_tag_id)
    tag_manager.add_tag_to_car("sample_3", electric_tag_id)
    tag_manager.add_tag_to_car("sample_3", american_tag_id)
    tag_manager.add_tag_to_car("sample_3", favorite_tag_id)
    
    # Example 3: Add a tag by name (will create if doesn't exist)
    print("\n=== Example 3: Add Tag by Name ===")
    print("Adding 'Luxury' tag to Tesla Model 3...")
    tag_manager.add_tag_to_car_by_name("sample_3", "Luxury")
    
    # Example 4: Get all tags for a car
    print("\n=== Example 4: Get All Tags for a Car ===")
    tesla_tags = tag_manager.get_car_tags("sample_3")
    print(f"Tags for Tesla Model 3:")
    for tag in tesla_tags:
        print(f"- {tag.name} ({tag.color})")
    
    # Example 5: Get all cars with a specific tag
    print("\n=== Example 5: Get Cars with Specific Tag ===")
    sedan_cars = tag_manager.get_cars_by_tag(sedan_tag_id)
    print(f"Found {len(sedan_cars)} cars with the 'Sedan' tag:")
    for car_id in sedan_cars:
        car = db_manager.get_car(car_id)
        if car:
            print(f"- {car.title}")
    
    # Example 6: Get all cars with a specific tag name
    print("\n=== Example 6: Get Cars with Specific Tag Name ===")
    favorite_cars = tag_manager.get_cars_by_tag_name("Favorite")
    print(f"Found {len(favorite_cars)} favorite cars:")
    for car_id in favorite_cars:
        car = db_manager.get_car(car_id)
        if car:
            print(f"- {car.title}")
    
    # Example 7: Get cars with multiple tags (any)
    print("\n=== Example 7: Get Cars with Multiple Tags (ANY) ===")
    tag_ids = [japanese_tag_id, american_tag_id]
    asian_american_cars = tag_manager.get_cars_by_tags(tag_ids, require_all=False)
    print(f"Found {len(asian_american_cars)} cars that are either Japanese or American:")
    for car_id in asian_american_cars:
        car = db_manager.get_car(car_id)
        if car:
            print(f"- {car.title}")
    
    # Example 8: Get cars with multiple tags (all)
    print("\n=== Example 8: Get Cars with Multiple Tags (ALL) ===")
    tag_ids = [sedan_tag_id, favorite_tag_id]
    favorite_sedans = tag_manager.get_cars_by_tags(tag_ids, require_all=True)
    print(f"Found {len(favorite_sedans)} favorite sedans:")
    for car_id in favorite_sedans:
        car = db_manager.get_car(car_id)
        if car:
            print(f"- {car.title}")
    
    # Example 9: Update tag
    print("\n=== Example 9: Update Tag ===")
    print(f"Updating tag '{favorite_tag.name}' to 'Must Have' with color '#ff9900'")
    updated = tag_manager.update_tag(favorite_tag_id, name="Must Have", color="#ff9900")
    if updated:
        updated_tag = tag_manager.get_tag(favorite_tag_id)
        print(f"Updated tag: {updated_tag}")
    else:
        print("Failed to update tag")
    
    # Example 10: Get all tags
    print("\n=== Example 10: Get All Tags ===")
    all_tags_list = tag_manager.get_all_tags()
    print(f"All tags ({len(all_tags_list)}):")
    for tag in all_tags_list:
        print(f"- {tag.name} ({tag.color})")
    
    # Example 11: Get popular tags
    print("\n=== Example 11: Get Popular Tags ===")
    popular_tags = tag_manager.get_popular_tags(limit=5)
    print("Popular tags:")
    for tag, count in popular_tags:
        print(f"- {tag.name}: {count} cars")
    
    # Example 12: Remove a tag from a car
    print("\n=== Example 12: Remove Tag from Car ===")
    print(f"Removing tag '{japanese_tag.name}' from Honda Accord")
    removed = tag_manager.remove_tag_from_car("sample_2", japanese_tag_id)
    if removed:
        print("Tag removed successfully")
        
        # Verify tags after removal
        honda_tags = tag_manager.get_car_tags("sample_2")
        print(f"Tags for Honda Accord after removal:")
        if honda_tags:
            for tag in honda_tags:
                print(f"- {tag.name}")
        else:
            print("No tags remaining")
    else:
        print("Failed to remove tag")
    
    # Example 13: Delete a tag
    print("\n=== Example 13: Delete Tag ===")
    print(f"Creating a temporary tag to delete...")
    temp_tag = create_tag_safe("Temporary", "#999999")
    
    if temp_tag:
        temp_tag_id = temp_tag.id
        print(f"Deleting tag '{temp_tag.name}'")
        deleted = tag_manager.delete_tag(temp_tag_id)
        if deleted:
            print("Tag deleted successfully")
        else:
            print("Failed to delete tag")
    else:
        print("Failed to create temporary tag")
    
    print("\nTag system demonstration complete!")


if __name__ == "__main__":
    main() 