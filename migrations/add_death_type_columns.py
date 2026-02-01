"""
Migration: Add death type and death persona columns to agents table.

This migration adds columns needed for the Five Types of Death system:
- death_type: The predicted/actual death type (NATURAL_AGE, PERFORMANCE_CULL, etc.)
- death_persona: JSON storing death persona state if active
- social_relevance_score: How valued the agent's contributions are (prestige decay)
- learning_rate_effective: Current learning rate (vitality death detection)
- generations_since_contribution: Counter for prestige decay
- times_packages_queried_recent: Track how often packages are being used

Run with: python migrations/add_death_type_columns.py
"""

import os
import sqlite3
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_data.db')


def get_existing_columns(cursor, table_name):
    """Get list of existing columns in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def run_migration():
    """Add death type and death persona columns to agents table."""
    print(f"[MIGRATION] Connecting to database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("[MIGRATION] Database does not exist. Skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get existing columns
        existing_columns = get_existing_columns(cursor, 'agents')
        print(f"[MIGRATION] Found {len(existing_columns)} existing columns in agents table")

        # Define new columns to add
        new_columns = [
            ('death_type', 'TEXT DEFAULT NULL'),
            ('death_persona', 'TEXT DEFAULT NULL'),
            ('social_relevance_score', 'REAL DEFAULT 1.0'),
            ('learning_rate_effective', 'REAL DEFAULT 0.1'),
            ('generations_since_contribution', 'INTEGER DEFAULT 0'),
            ('times_packages_queried_recent', 'INTEGER DEFAULT 0'),
        ]

        # Add each column if it doesn't exist
        columns_added = 0
        for col_name, col_def in new_columns:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}"
                print(f"[MIGRATION] Adding column: {col_name}")
                cursor.execute(sql)
                columns_added += 1
            else:
                print(f"[MIGRATION] Column already exists: {col_name}")

        conn.commit()
        print(f"[MIGRATION] Complete! Added {columns_added} new columns.")

    except Exception as e:
        print(f"[MIGRATION] Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    run_migration()
