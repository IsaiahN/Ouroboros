"""
Migration: Add game_type column to terminal_patterns table
Date: 2025-12-29
Purpose: Enable cross-session terminal pattern matching

The original design stored patterns with game_id (e.g., "sp80-abc123"), 
but each session gets a NEW game_id, so patterns never matched!

Fix: Add game_type column (e.g., "sp80") and query by that instead.
"""

import sqlite3
import os

def migrate():
    """Add game_type column and backfill from existing game_id values."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
    
    if not os.path.exists(db_path):
        print("[SKIP] Database not found - migration will be applied on first run")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(terminal_patterns)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'game_type' in columns:
            print("[OK] game_type column already exists")
        else:
            # Add the column
            print("[MIGRATE] Adding game_type column to terminal_patterns...")
            cursor.execute("ALTER TABLE terminal_patterns ADD COLUMN game_type TEXT")
            
            # Backfill from game_id (extract type from 'sp80-abc123' -> 'sp80')
            print("[MIGRATE] Backfilling game_type from existing game_id values...")
            cursor.execute("""
                UPDATE terminal_patterns 
                SET game_type = CASE 
                    WHEN INSTR(game_id, '-') > 0 THEN SUBSTR(game_id, 1, INSTR(game_id, '-') - 1)
                    ELSE game_id
                END
                WHERE game_type IS NULL
            """)
            
            # Create new index for faster lookups
            print("[MIGRATE] Creating index on game_type...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_terminal_patterns_lookup_v2
                ON terminal_patterns (game_type, level_number, frame_hash, is_active)
            """)
            
            conn.commit()
            
            # Report results
            cursor.execute("SELECT COUNT(*) FROM terminal_patterns WHERE game_type IS NOT NULL")
            count = cursor.fetchone()[0]
            print(f"[OK] Migration complete - {count} patterns updated with game_type")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
