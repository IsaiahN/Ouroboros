"""
Migration: Add remaining consciousness tables from agent_consciousness_synthesis.md

Tables added:
1. abstraction_quality - Transfer quality tracking
2. persona_theory_bindings - Persona-theory binding for lifecycle management

This is v2 of the consciousness tables migration, adding tables that were
specified in the architecture document but not included in v1.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "core_data.db"


def run_migration():
    """Create the remaining consciousness system tables."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    tables_created = 0
    indexes_created = 0
    
    # Table 1: abstraction_quality - Transfer quality tracking
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abstraction_quality (
                quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT NOT NULL,
                
                -- Transfer attempts
                source_game_type TEXT NOT NULL,
                target_game_type TEXT NOT NULL,
                target_level INTEGER,
                
                -- Outcome
                transfer_succeeded BOOLEAN,
                actions_to_success INTEGER,
                adaptation_required TEXT,
                
                -- Quality metrics
                is_memorization BOOLEAN DEFAULT FALSE,
                is_abstraction BOOLEAN DEFAULT FALSE,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        tables_created += 1
        print("[OK] Created table: abstraction_quality")
    except Exception as e:
        print(f"[SKIP] abstraction_quality: {e}")
    
    # Table 2: persona_theory_bindings - Bind personas to theories
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persona_theory_bindings (
                binding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id TEXT NOT NULL,
                theory_id TEXT NOT NULL,
                bound_at_action INTEGER,
                agent_id TEXT,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(persona_id, theory_id)
            )
        """)
        tables_created += 1
        print("[OK] Created table: persona_theory_bindings")
    except Exception as e:
        print(f"[SKIP] persona_theory_bindings: {e}")
    
    # Create indexes
    index_definitions = [
        ("idx_abstraction_quality_lesson", "abstraction_quality", "lesson_id"),
        ("idx_abstraction_quality_target", "abstraction_quality", "target_game_type"),
        ("idx_abstraction_quality_transfer", "abstraction_quality", "transfer_succeeded"),
        ("idx_persona_bindings_persona", "persona_theory_bindings", "persona_id"),
        ("idx_persona_bindings_theory", "persona_theory_bindings", "theory_id"),
        ("idx_persona_bindings_agent", "persona_theory_bindings", "agent_id"),
    ]
    
    for idx_name, table, column in index_definitions:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            indexes_created += 1
            print(f"[OK] Created index: {idx_name}")
        except Exception as e:
            print(f"[SKIP] {idx_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== Migration Complete ===")
    print(f"Tables created: {tables_created}")
    print(f"Indexes created: {indexes_created}")
    
    return tables_created, indexes_created


if __name__ == "__main__":
    run_migration()
