"""
Migration: Add controlled_color column to network_object_control_hypotheses

Issue: INSERT uses 'controlled_color' and 'discovered_generation' columns
but they don't exist in the schema.

The table has 'discovery_generation' but we need 'discovered_generation' alias too.
"""
import sqlite3
import os

def run_migration():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(network_object_control_hypotheses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        changes_made = []
        
        # Add controlled_color column if missing
        if 'controlled_color' not in columns:
            cursor.execute("""
                ALTER TABLE network_object_control_hypotheses 
                ADD COLUMN controlled_color INTEGER DEFAULT 0
            """)
            changes_made.append("controlled_color")
            print("[OK] Added 'controlled_color' column")
        else:
            print("[SKIP] 'controlled_color' column already exists")
        
        # Add discovered_generation alias column if missing
        # (schema has discovery_generation, but code uses discovered_generation)
        if 'discovered_generation' not in columns:
            cursor.execute("""
                ALTER TABLE network_object_control_hypotheses 
                ADD COLUMN discovered_generation INTEGER DEFAULT 0
            """)
            changes_made.append("discovered_generation")
            print("[OK] Added 'discovered_generation' column")
        else:
            print("[SKIP] 'discovered_generation' column already exists")
        
        # Copy data from discovery_generation to discovered_generation if both exist
        if 'discovery_generation' in columns and 'discovered_generation' in changes_made:
            cursor.execute("""
                UPDATE network_object_control_hypotheses 
                SET discovered_generation = discovery_generation 
                WHERE discovered_generation IS NULL OR discovered_generation = 0
            """)
            print("[OK] Copied data from discovery_generation to discovered_generation")
        
        conn.commit()
        print(f"Migration complete. Changes: {changes_made or 'none needed'}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()
