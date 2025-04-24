"""
Data access layer for the Car Search application.

This package provides functionality to retrieve car data from various sources,
including web scraping and external APIs.
"""

from .autotrader import AutoTraderScraper
from .car_apis import car_data_manager, CarDataManager, SmartcarAPI, EdmundsAPI
from .db_manager import db_manager, DatabaseManager
from .migration import Migration, MigrationManager, get_migration_manager, initialize_migrations
from .tag_manager import tag_manager, Tag, TagManager
from .filtering import filter_manager, FilterManager, FilterQueryBuilder, FilterExpression

# Initialize migrations
# This needs to happen after all modules are imported to avoid circular imports
def _init_migrations():
    """Initialize the migration system."""
    # First, import all migration modules without applying them
    import importlib
    import pkgutil
    import sys
    from pathlib import Path
    
    migrations_dir = Path(__file__).parent / "migrations"
    if migrations_dir.exists():
        # First import all migration modules
        for _, name, _ in pkgutil.iter_modules([str(migrations_dir)]):
            if name.startswith("version_"):
                try:
                    importlib.import_module(f"src.data.migrations.{name}")
                except Exception as e:
                    print(f"Error importing migration {name}: {e}")
    
        # Now register all migrations
        # We need to get all migration modules and call their register function
        for _, name, _ in pkgutil.iter_modules([str(migrations_dir)]):
            if name.startswith("version_"):
                try:
                    module = importlib.import_module(f"src.data.migrations.{name}")
                    if hasattr(module, 'register'):
                        module.register()
                except Exception as e:
                    print(f"Error registering migration {name}: {e}")
    
    # Initialize the migration manager
    return initialize_migrations()

# Initialize the migration manager
migration_manager = _init_migrations()

__all__ = [
    "AutoTraderScraper",
    "car_data_manager",
    "CarDataManager",
    "SmartcarAPI",
    "EdmundsAPI",
    "db_manager",
    "DatabaseManager",
    "migration_manager",
    "Migration",
    "MigrationManager",
    "get_migration_manager",
    "initialize_migrations",
    "tag_manager",
    "Tag",
    "TagManager",
    "filter_manager",
    "FilterManager",
    "FilterQueryBuilder",
    "FilterExpression"
]
