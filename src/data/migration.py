"""
Data migration system for the Car Search application.

This module provides functionality for managing database schema migrations
in a structured and version-controlled way.
"""

import os
import logging
import sqlite3
import importlib
import pkgutil
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from pathlib import Path

from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class Migration:
    """
    Represents a single database migration.
    
    Each migration has an upgrade and downgrade function that manipulate the database schema.
    """
    
    def __init__(self, version: int, description: str):
        """
        Initialize a migration.
        
        Args:
            version: Migration version number (should be sequential)
            description: Short description of what the migration does
        """
        self.version = version
        self.description = description
        self.upgrade_fn: Optional[Callable[[sqlite3.Connection], None]] = None
        self.downgrade_fn: Optional[Callable[[sqlite3.Connection], None]] = None
    
    def upgrade(self, fn: Callable[[sqlite3.Connection], None]) -> Callable:
        """
        Decorator to register an upgrade function.
        
        Args:
            fn: Function that performs the upgrade
            
        Returns:
            The decorated function
        """
        self.upgrade_fn = fn
        return fn
    
    def downgrade(self, fn: Callable[[sqlite3.Connection], None]) -> Callable:
        """
        Decorator to register a downgrade function.
        
        Args:
            fn: Function that performs the downgrade
            
        Returns:
            The decorated function
        """
        self.downgrade_fn = fn
        return fn


class MigrationManager:
    """
    Manages database migrations.
    
    This class keeps track of available migrations, the current database version,
    and can apply migrations to upgrade or downgrade the database.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the migration manager.
        
        Args:
            db_path: Path to the SQLite database file.
                    If None, uses the default path from config.
        """
        if db_path is None:
            db_dir = str(settings.app.data_dir)
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "car_search.db")
        
        self.db_path = db_path
        self.migrations: Dict[int, Migration] = {}
        # Don't automatically load migrations to avoid circular imports
        # This will be called separately during initialization
    
    def _load_migrations(self) -> None:
        """
        Load all available migrations from the migrations package.
        """
        try:
            # Use a more flexible approach to import migrations
            migrations_dir = Path(__file__).parent / "migrations"
            if not migrations_dir.exists():
                logger.warning("No migrations directory found. Create src/data/migrations/ to store migrations.")
                return
                
            # Walk through the migrations directory and import all modules
            for file_path in migrations_dir.glob("version_*.py"):
                module_name = file_path.stem
                try:
                    # Import the migration module
                    module_path = f"src.data.migrations.{module_name}"
                    importlib.import_module(module_path)
                except ImportError as e:
                    logger.error(f"Error importing migration {module_name}: {str(e)}")
            
            logger.info(f"Loaded {len(self.migrations)} migrations")
        except Exception as e:
            logger.error(f"Error loading migrations: {str(e)}")
    
    def register_migration(self, migration: Migration) -> None:
        """
        Register a migration with the manager.
        
        Args:
            migration: The migration to register
        """
        if migration.version in self.migrations:
            logger.warning(f"Migration version {migration.version} already registered, overwriting")
        
        self.migrations[migration.version] = migration
        logger.debug(f"Registered migration version {migration.version}: {migration.description}")
    
    def get_current_version(self) -> int:
        """
        Get the current database schema version.
        
        Returns:
            Current version number, or 0 if no version info exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if schema_info table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'"
                )
                if not cursor.fetchone():
                    return 0
                
                # Get version info
                cursor.execute("SELECT version FROM schema_info LIMIT 1")
                result = cursor.fetchone()
                
                return result[0] if result else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting current database version: {str(e)}")
            return 0
    
    def get_migrations_to_apply(self, target_version: Optional[int] = None) -> List[Tuple[int, bool]]:
        """
        Get a list of migrations that need to be applied to reach the target version.
        
        Args:
            target_version: Target version to migrate to.
                           If None, uses the latest available version.
                           
        Returns:
            List of (version, is_upgrade) tuples indicating migrations to apply
        """
        current_version = self.get_current_version()
        
        if target_version is None:
            if not self.migrations:
                return []
            target_version = max(self.migrations.keys())
        
        # Determine if we're upgrading or downgrading
        if current_version == target_version:
            return []
        elif current_version < target_version:
            # Upgrading - apply all migrations from current+1 to target
            return [(v, True) for v in range(current_version + 1, target_version + 1)
                   if v in self.migrations]
        else:
            # Downgrading - apply all migrations from current down to target+1 in reverse
            return [(v, False) for v in range(current_version, target_version, -1)
                   if v in self.migrations]
    
    def _ensure_schema_info(self, conn: sqlite3.Connection) -> None:
        """
        Ensure the schema_info table exists.
        
        Args:
            conn: SQLite connection
        """
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
                (0, datetime.now().isoformat())
            )
            conn.commit()
    
    def _update_version(self, conn: sqlite3.Connection, version: int) -> None:
        """
        Update the schema version in the database.
        
        Args:
            conn: SQLite connection
            version: New version number
        """
        cursor = conn.cursor()
        
        # Update schema version
        cursor.execute(
            "UPDATE schema_info SET version = ?, created_at = ?",
            (version, datetime.now().isoformat())
        )
        conn.commit()
        logger.info(f"Updated schema version to {version}")
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """
        Migrate the database to the target version.
        
        Args:
            target_version: Target version to migrate to.
                           If None, migrates to the latest available version.
                           
        Returns:
            True if migrations were applied successfully, False otherwise
        """
        try:
            migrations_to_apply = self.get_migrations_to_apply(target_version)
            
            if not migrations_to_apply:
                logger.info("Database is already at the target version")
                return True
            
            current_version = self.get_current_version()
            
            if target_version is None:
                target_version = max(self.migrations.keys())
            
            logger.info(f"Migrating database from version {current_version} to {target_version}")
            
            # Apply migrations in sequence
            with sqlite3.connect(self.db_path) as conn:
                # Ensure schema_info table exists
                self._ensure_schema_info(conn)
                
                for version, is_upgrade in migrations_to_apply:
                    migration = self.migrations.get(version)
                    
                    if not migration:
                        logger.warning(f"Migration version {version} not found, skipping")
                        continue
                    
                    if is_upgrade:
                        if migration.upgrade_fn:
                            logger.info(f"Applying migration {version}: {migration.description}")
                            migration.upgrade_fn(conn)
                            self._update_version(conn, version)
                        else:
                            logger.warning(f"Migration {version} has no upgrade function, skipping")
                    else:
                        if migration.downgrade_fn:
                            logger.info(f"Reverting migration {version}: {migration.description}")
                            migration.downgrade_fn(conn)
                            self._update_version(conn, version - 1)
                        else:
                            logger.warning(f"Migration {version} has no downgrade function, skipping")
            
            final_version = self.get_current_version()
            logger.info(f"Migration complete. Database is now at version {final_version}")
            
            return final_version == target_version
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            return False


def create_migration(description: str) -> Optional[str]:
    """
    Create a new migration file with the given description.
    
    Args:
        description: Short description of what the migration does
        
    Returns:
        Path to the created migration file, or None if creation failed
    """
    try:
        # Get migration manager
        migration_manager = get_migration_manager()
        
        # Determine the next version number
        next_version = 1
        if migration_manager.migrations:
            next_version = max(migration_manager.migrations.keys()) + 1
        
        # Create migrations directory if it doesn't exist
        migrations_dir = Path(__file__).parent / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        migrations_init = migrations_dir / "__init__.py"
        if not migrations_init.exists():
            with open(migrations_init, "w") as f:
                f.write('"""Migration package for database schema changes."""\n')
        
        # Create the migration file
        filename = f"version_{next_version}_{description.lower().replace(' ', '_')}.py"
        file_path = migrations_dir / filename
        
        with open(file_path, "w") as f:
            f.write(f'''"""
Migration {next_version}: {description}

Created at: {datetime.now().isoformat(timespec='seconds')}
"""

import sqlite3
from src.data.migration import Migration

# Create migration
migration = Migration({next_version}, "{description}")

@migration.upgrade
def upgrade(conn: sqlite3.Connection) -> None:
    """
    Upgrade the database schema.
    
    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()
    
    # TODO: Implement the upgrade logic here
    # Example:
    # cursor.execute("""
    #     CREATE TABLE new_table (
    #         id INTEGER PRIMARY KEY,
    #         name TEXT NOT NULL
    #     )
    # """)

@migration.downgrade
def downgrade(conn: sqlite3.Connection) -> None:
    """
    Downgrade the database schema.
    
    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()
    
    # TODO: Implement the downgrade logic here
    # Example:
    # cursor.execute("DROP TABLE IF EXISTS new_table")

# Instead of directly importing and using migration_manager here,
# we'll define a function that can be called during initialization
def register():
    """Register this migration with the migration manager."""
    from src.data.migration import get_migration_manager
    migration_manager = get_migration_manager()
    migration_manager.register_migration(migration)
''')
        
        logger.info(f"Created migration file: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Error creating migration file: {str(e)}")
        return None


# Create a function to get or create the migration manager
# This breaks the circular dependency by allowing migrations to import
# just what they need (the Migration class) and then register later
_migration_manager_instance = None

def get_migration_manager() -> MigrationManager:
    """
    Get the migration manager instance.
    
    Returns:
        The migration manager singleton instance
    """
    global _migration_manager_instance
    if _migration_manager_instance is None:
        _migration_manager_instance = MigrationManager()
    return _migration_manager_instance

def initialize_migrations():
    """
    Initialize the migration system by loading all available migrations.
    This should be called after all modules are imported.
    """
    manager = get_migration_manager()
    manager._load_migrations()
    return manager

# For backwards compatibility with existing code
migration_manager = get_migration_manager() 