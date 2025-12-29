"""
Migration: Add dangerous_objects and action_triggered_dangers tables
Date: 2025-12-29
Purpose: Pattern-based danger detection for death zone system

New tables:
1. dangerous_objects - Track WHAT (by color) killed agents, not just WHERE
2. action_triggered_dangers - Track when actions SPAWN dangerous situations

Also adds new columns to death_zones for challenge tracking.
"""

import sqlite3
import os

def migrate():
    """Add new tables and columns for pattern-based danger detection."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
    
    if not os.path.exists(db_path):
        print("[SKIP] Database not found - migration will be applied on first run")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Add challenge tracking columns to death_zones
        print("[MIGRATE] Adding challenge tracking columns to death_zones...")
        
        columns_to_add = [
            ("last_challenged_at", "TEXT"),
            ("challenge_count", "INTEGER DEFAULT 0"),
            ("last_validated_at", "TEXT"),
            ("generations_since_death", "INTEGER DEFAULT 0")
        ]
        
        cursor.execute("PRAGMA table_info(death_zones)")
        existing_cols = {col[1] for col in cursor.fetchall()}
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE death_zones ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name}")
        
        # 2. Create dangerous_objects table
        print("[MIGRATE] Creating dangerous_objects table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dangerous_objects (
                object_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                object_color INTEGER NOT NULL,
                object_size INTEGER DEFAULT 1,
                contact_type TEXT DEFAULT 'collision',
                
                fatal_action INTEGER,
                player_color INTEGER,
                
                kill_count INTEGER DEFAULT 1,
                safe_contact_count INTEGER DEFAULT 0,
                danger_score REAL DEFAULT 0.8,
                
                suspected_instances INTEGER DEFAULT 0,
                confirmed_kills INTEGER DEFAULT 0,
                
                discovered_at TEXT,
                last_kill_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dangerous_objects_lookup
            ON dangerous_objects (game_type, level_number, object_color, is_active)
        """)
        
        # 3. Create action_triggered_dangers table
        print("[MIGRATE] Creating action_triggered_dangers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_triggered_dangers (
                trigger_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                trigger_action INTEGER NOT NULL,
                trigger_x INTEGER,
                trigger_y INTEGER,
                
                spawned_color INTEGER,
                spawned_positions TEXT,
                
                actions_until_death INTEGER DEFAULT 1,
                
                occurrence_count INTEGER DEFAULT 1,
                danger_score REAL DEFAULT 0.7,
                
                discovered_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        conn.commit()
        print("[OK] Migration complete - pattern-based danger detection enabled")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
