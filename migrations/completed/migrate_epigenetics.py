"""
Migration script to add epigenetics column to agents table
Following Rule 2: Database-only storage
"""

import os
import sqlite3

from database_interface import DatabaseInterface


def migrate_database():
    """Add epigenetics column to agents table if it doesn't exist"""

    db = DatabaseInterface()

    print("Checking if epigenetics column exists...")

    with db._get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(agents)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'epigenetics' in columns:
            print("✓ Epigenetics column already exists")
            return

        print("Adding epigenetics column to agents table...")

        try:
            conn.execute("""
                ALTER TABLE agents
                ADD COLUMN epigenetics TEXT
            """)
            conn.commit()
            print("✓ Successfully added epigenetics column")

            # Verify the column was added
            cursor = conn.execute("PRAGMA table_info(agents)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'epigenetics' in columns:
                print("✓ Migration verified - epigenetics column exists")
            else:
                print("✗ Migration failed - column not found after addition")

        except sqlite3.OperationalError as e:
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("EPIGENETICS DATABASE MIGRATION")
    print("=" * 60)
    migrate_database()
    print("=" * 60)
    print("Migration complete")
