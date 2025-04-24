#!/usr/bin/env python3
"""
Database migration CLI tool.

This module provides a command-line interface for managing database migrations.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the src package
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.data.migration import get_migration_manager, initialize_migrations

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run the migration CLI."""
    parser = argparse.ArgumentParser(description="Manage database migrations")
    subparsers = parser.add_subparsers(dest="command", help="Migration command")
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("description", help="Short description of the migration")
    
    # Apply migrations command
    apply_parser = subparsers.add_parser("apply", help="Apply migrations")
    apply_parser.add_argument("--version", "-v", type=int, help="Target version to migrate to", default=None)
    
    # Info command
    subparsers.add_parser("info", help="Show migration information")
    
    args = parser.parse_args()
    
    # Initialize migrations - this ensures all migrations are loaded
    migration_manager = initialize_migrations()
    
    if args.command == "create":
        # Import create_migration here to avoid circular imports
        from src.data.migration import create_migration
        file_path = create_migration(args.description)
        if file_path:
            print(f"Created migration file: {file_path}")
            print(f"Edit the file to implement your migration.")
        else:
            print("Failed to create migration file")
            return 1
    
    elif args.command == "apply":
        current_version = migration_manager.get_current_version()
        target_version = args.version
        
        if target_version is None:
            # Find latest available version
            if migration_manager.migrations:
                target_version = max(migration_manager.migrations.keys())
            else:
                print("No migrations available to apply")
                return 0
        
        if current_version == target_version:
            print(f"Database is already at version {current_version}")
            return 0
        
        print(f"Migrating database from version {current_version} to {target_version}")
        
        if migration_manager.migrate(target_version):
            print(f"Migration completed successfully")
            return 0
        else:
            print(f"Migration failed")
            return 1
    
    elif args.command == "info":
        current_version = migration_manager.get_current_version()
        print(f"Current database version: {current_version}")
        
        print("\nAvailable migrations:")
        if not migration_manager.migrations:
            print("  No migrations available")
        else:
            for version, migration in sorted(migration_manager.migrations.items()):
                status = "APPLIED" if version <= current_version else "PENDING"
                print(f"  {version}: {migration.description} [{status}]")
            
            if migration_manager.migrations:
                latest_version = max(migration_manager.migrations.keys())
                if current_version < latest_version:
                    print(f"\nDatabase is {latest_version - current_version} version(s) behind")
    
    else:
        parser.print_help()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 