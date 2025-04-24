#!/usr/bin/env python3
"""
Example script demonstrating how to use the database migration system.

This script shows how to:
1. Create a new migration
2. Apply migrations
3. Get information about the migration status
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.migration import migration_manager, create_migration
from src.data.db_manager import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run the migration example script."""
    print(f"Database path: {db_manager.db_path}")
    
    # Example 1: Get database schema version
    print("\n=== Example 1: Get Database Schema Version ===")
    current_version = migration_manager.get_current_version()
    print(f"Current database schema version: {current_version}")
    
    # Example 2: List available migrations
    print("\n=== Example 2: List Available Migrations ===")
    if not migration_manager.migrations:
        print("No migrations available")
    else:
        for version, migration in sorted(migration_manager.migrations.items()):
            status = "APPLIED" if version <= current_version else "PENDING"
            print(f"Migration {version}: {migration.description} [{status}]")
    
    # Example 3: Create a new migration (commented out to avoid creating multiple migrations)
    print("\n=== Example 3: Create a New Migration ===")
    print("To create a new migration, you would run:")
    print("  file_path = create_migration('Add new feature XYZ')")
    print("This will generate a new migration file that you can edit to implement your changes.")
    
    # Example 4: Apply migrations
    print("\n=== Example 4: Apply Migrations ===")
    # Only run this if there are pending migrations
    pending_migrations = migration_manager.get_migrations_to_apply()
    if not pending_migrations:
        print("No pending migrations to apply")
    else:
        print(f"Found {len(pending_migrations)} pending migration(s)")
        print("To apply all pending migrations, you would run:")
        print("  migration_manager.migrate()")
        
        # Example of how to apply a specific version
        print("\nTo migrate to a specific version (e.g., version 2):")
        print("  migration_manager.migrate(target_version=2)")
    
    # Example 5: How migrations work
    print("\n=== Example 5: How Migrations Work ===")
    print("1. Each migration has an upgrade and downgrade function.")
    print("2. The upgrade function applies schema changes to move forward.")
    print("3. The downgrade function reverses those changes.")
    print("4. Migrations are tracked in the database schema_info table.")
    print("\nWhen you migrate, the system:")
    print("1. Checks the current version.")
    print("2. Determines which migrations need to be applied.")
    print("3. Applies each migration in sequence.")
    print("4. Updates the version in the schema_info table.")
    
    # Example 6: Using the migration command-line tool
    print("\n=== Example 6: Using the Migration Command-Line Tool ===")
    print("The migration system includes a command-line tool that can be used to:")
    print("1. Create new migrations: python -m src.cli.migrate create 'Add new feature'")
    print("2. Apply migrations: python -m src.cli.migrate apply")
    print("3. Show migration info: python -m src.cli.migrate info")


if __name__ == "__main__":
    main() 