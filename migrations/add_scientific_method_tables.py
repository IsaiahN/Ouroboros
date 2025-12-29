"""
Migration: Add Scientific Method Engine tables
Created: 2025-12-29
Purpose: Create tables for autonomous theory formation, testing, and generalization.

Tables created:
- agent_theories: Stores theories formed by agents (object danger, action effects, goals, etc.)
- theory_experiments: Tracks experiments designed to test theories
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "core_data.db"


def run_migration():
    """Create the scientific method tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create agent_theories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_theories (
                theory_id TEXT PRIMARY KEY,
                theory_type TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                
                -- Theory content
                description TEXT NOT NULL,
                formal_statement TEXT NOT NULL,
                predictions TEXT,
                
                -- Evidence
                supporting_observations TEXT,
                contradicting_observations TEXT,
                
                -- Confidence and status
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'proposed',
                tests_conducted INTEGER DEFAULT 0,
                tests_successful INTEGER DEFAULT 0,
                
                -- Generalization
                generalized_from TEXT,
                child_theories TEXT,
                
                -- Network sharing
                shared_to_network INTEGER DEFAULT 0,
                network_validations INTEGER DEFAULT 0,
                
                -- Metadata
                created_at TEXT,
                last_tested_at TEXT,
                discovered_by_agent TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        print("[OK] Created agent_theories table")
        
        # Create index for efficient lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_theories_lookup
            ON agent_theories (game_type, level_number, status, is_active)
        """)
        print("[OK] Created agent_theories index")
        
        # Create theory_experiments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theory_experiments (
                experiment_id TEXT PRIMARY KEY,
                theory_id TEXT NOT NULL,
                
                hypothesis TEXT,
                prediction TEXT,
                preconditions TEXT,
                test_action TEXT,
                expected_result TEXT,
                
                actual_result TEXT,
                prediction_matched INTEGER,
                
                executed_at TEXT,
                executed_by_agent TEXT,
                
                FOREIGN KEY (theory_id) REFERENCES agent_theories(theory_id)
            )
        """)
        print("[OK] Created theory_experiments table")
        
        # Create index for experiment lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_theory_experiments_theory
            ON theory_experiments (theory_id)
        """)
        print("[OK] Created theory_experiments index")
        
        conn.commit()
        print("\n[SUCCESS] Scientific Method tables created successfully!")
        
        # Show table counts
        cursor.execute("SELECT COUNT(*) FROM agent_theories")
        theory_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM theory_experiments")
        exp_count = cursor.fetchone()[0]
        
        print(f"\nCurrent counts:")
        print(f"  - agent_theories: {theory_count}")
        print(f"  - theory_experiments: {exp_count}")
        
    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Scientific Method Engine - Table Migration")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    run_migration()
