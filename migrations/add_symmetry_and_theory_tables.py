"""
Database Migration: Add Property Symmetry and Theory History Tables
Date: 2026-01-07
Purpose: Support causation testing, property symmetry, and theory refinement
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_interface import DatabaseInterface
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Add pending_symmetry_experiments and working_theory_history tables."""
    db = DatabaseInterface()
    
    try:
        # Create pending_symmetry_experiments table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS pending_symmetry_experiments (
                experiment_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                reference_color INTEGER NOT NULL,
                property_type TEXT NOT NULL,
                action TEXT,
                direction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE,
                results TEXT
            )
        """)
        logger.info("[MIGRATION] Created pending_symmetry_experiments table")
        
        # Create working_theory_history table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS working_theory_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                theory_text TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                evidence_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                invalidated_at TIMESTAMP NULL
            )
        """)
        logger.info("[MIGRATION] Created working_theory_history table")
        
        # Add indexes for performance
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_symmetry_exp_game 
            ON pending_symmetry_experiments(game_type, level_number)
        """)
        
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_theory_hist_agent_game
            ON working_theory_history(agent_id, game_type, level_number)
        """)
        
        logger.info("[MIGRATION] Migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"[MIGRATION] Failed: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
