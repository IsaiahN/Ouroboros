"""
Migration: Drop the unique index on winning_sequences that prevents multiple active sequences.

The design now allows up to 3 active sequences per game+level.
Auto-cleanup in core_gameplay.py keeps top 3 by success_rate, refs, and efficiency.

The old unique index (idx_winning_sequences_active) only allowed 1 active sequence per game+level,
causing UNIQUE constraint failures during INSERT.
"""

import sqlite3
import os

def run_migration():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
    
    print(f"[MIGRATE] Connecting to {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if index exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='idx_winning_sequences_active'
    """)
    result = cursor.fetchone()
    
    if result:
        print(f"[MIGRATE] Found unique index: {result[0]}")
        cursor.execute("DROP INDEX IF EXISTS idx_winning_sequences_active")
        conn.commit()
        print("[MIGRATE] SUCCESS: Dropped idx_winning_sequences_active")
    else:
        print("[MIGRATE] Index does not exist (already removed)")
    
    # Verify it's gone
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='idx_winning_sequences_active'
    """)
    result2 = cursor.fetchone()
    print(f"[MIGRATE] Verification - index exists: {result2 is not None}")
    
    conn.close()
    print("[MIGRATE] Done")

if __name__ == "__main__":
    run_migration()
