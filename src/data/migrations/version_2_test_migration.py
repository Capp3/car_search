"""
Migration 2: Test migration

Created at: 2025-04-24T15:44:46
"""

import sqlite3
from src.data.migration import Migration

# Create migration
migration = Migration(2, "Test migration")

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
