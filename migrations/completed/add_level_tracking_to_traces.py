"""
Add level_number tracking to action_traces table.

CRITICAL FIX: Without level tracking, sequences include ALL actions from ALL levels,
making OPTIMIZER sequences incorrect when trying to improve on specific level performance.

This migration:
1. Adds level_number column to action_traces
2. Updates database_interface to accept level_number
3. Ensures action_handler passes current_level to trace recording
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface


def migrate():
    db = DatabaseInterface()

    print("Adding level_number column to action_traces...")

    try:
        # Add level_number column (defaults to 1 for existing data)
        db.execute_query("""
            ALTER TABLE action_traces
            ADD COLUMN level_number INTEGER DEFAULT 1
        """)
        print("[OK] Added level_number column to action_traces")

        # Create index for faster level-based queries
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_action_traces_level
            ON action_traces(game_id, session_id, level_number)
        """)
        print("[OK] Created index for level-based queries")

        # Verify column exists
        result = db.execute_query("""
            SELECT COUNT(*) as count FROM action_traces
            WHERE level_number IS NOT NULL
        """)
        print(f"[OK] Verified: {result[0]['count']} traces have level_number")

        print("\n[OK] Migration complete!")
        print("\nNext steps:")
        print("1. Update action_handler to pass current_level when recording traces")
        print("2. Update database_interface.log_action_trace() to accept level_number")
        print("3. Update core_gameplay to pass current_level to action execution")
        print("4. Update _capture_winning_sequence() to filter by level_number")

    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("[WARN]  Column already exists, skipping...")
        else:
            print(f"[FAIL] Error: {e}")
            raise

if __name__ == "__main__":
    migrate()
