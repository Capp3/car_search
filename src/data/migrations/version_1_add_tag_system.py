"""
Migration 1: Add tag system

Created at: 2023-08-10T12:00:00
"""

import sqlite3
from src.data.migration import Migration

# Create migration
migration = Migration(1, "Add tag system")

@migration.upgrade
def upgrade(conn: sqlite3.Connection) -> None:
    """
    Upgrade the database schema to add tag tables.
    
    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()
    
    # Create tags table
    cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#cccccc',
            created_at TEXT NOT NULL
        )
    """)
    
    # Create car_tags join table
    cursor.execute("""
        CREATE TABLE car_tags (
            car_id TEXT,
            tag_id INTEGER,
            created_at TEXT NOT NULL,
            PRIMARY KEY (car_id, tag_id),
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX idx_tags_name ON tags(name)")
    cursor.execute("CREATE INDEX idx_car_tags_tag_id ON car_tags(tag_id)")

@migration.downgrade
def downgrade(conn: sqlite3.Connection) -> None:
    """
    Downgrade the database schema by removing tag tables.
    
    Args:
        conn: SQLite connection
    """
    cursor = conn.cursor()
    
    # Drop car_tags table first (due to foreign key constraints)
    cursor.execute("DROP TABLE IF EXISTS car_tags")
    
    # Drop tags table
    cursor.execute("DROP TABLE IF EXISTS tags")

# Instead of directly importing and using migration_manager here,
# we'll define a function that can be called during initialization
def register():
    """Register this migration with the migration manager."""
    from src.data.migration import get_migration_manager
    migration_manager = get_migration_manager()
    migration_manager.register_migration(migration) 