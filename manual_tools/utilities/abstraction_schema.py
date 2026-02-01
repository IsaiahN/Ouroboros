import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Abstraction Database Schema
============================

All database tables for the Sequence Abstraction Engine.
Creates tables only if ENABLE_ABSTRACTION is true.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from abstraction_config import is_abstraction_enabled
import logging

logger = logging.getLogger(__name__)


SQL_SCHEMAS = {
    'detected_objects': """
        CREATE TABLE IF NOT EXISTS detected_objects (
            object_id TEXT PRIMARY KEY,
            game_id TEXT,
            level_number INTEGER,
            frame_index INTEGER,
            properties TEXT,
            detected_at TEXT
        )
    """,
    
    'object_tracks': """
        CREATE TABLE IF NOT EXISTS object_tracks (
            track_id TEXT PRIMARY KEY,
            game_id TEXT,
            level_number INTEGER,
            object_sequence TEXT,
            lifecycle TEXT,
            created_at TEXT
        )
    """,
    
    'action_effects': """
        CREATE TABLE IF NOT EXISTS action_effects (
            effect_id TEXT PRIMARY KEY,
            game_id TEXT,
            level_number INTEGER,
            action_type TEXT,
            affected_objects TEXT,
            frame_before INTEGER,
            frame_after INTEGER,
            analyzed_at TEXT
        )
    """,
    
    'causal_chains': """
        CREATE TABLE IF NOT EXISTS causal_chains (
            chain_id TEXT PRIMARY KEY,
            game_id TEXT,
            level_number INTEGER,
            action_sequence TEXT,
            outcome TEXT,
            confidence REAL,
            learned_at TEXT
        )
    """,
    
    'movement_patterns': """
        CREATE TABLE IF NOT EXISTS movement_patterns (
            pattern_id TEXT PRIMARY KEY,
            pattern_type TEXT,
            template TEXT,
            example_sequences TEXT,
            frequency INTEGER,
            success_rate REAL,
            created_at TEXT
        )
    """,
    
    'sequence_concepts': """
        CREATE TABLE IF NOT EXISTS sequence_concepts (
            concept_id TEXT PRIMARY KEY,
            sequence_id TEXT,
            layout_signature TEXT,
            goal_type TEXT,
            strategy_type TEXT,
            constraints TEXT,
            abstraction_level INTEGER,
            created_at TEXT,
            FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
        )
    """,
    
    'abstraction_metrics': """
        CREATE TABLE IF NOT EXISTS abstraction_metrics (
            metric_id TEXT PRIMARY KEY,
            abstraction_level INTEGER,
            match_method TEXT,
            success_count INTEGER,
            failure_count INTEGER,
            avg_similarity_score REAL,
            measured_at TEXT
        )
    """
}


def create_abstraction_tables(db_path="core_data.db"):
    """
    Create all abstraction tables.
    
    Only creates if ENABLE_ABSTRACTION is true.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    if not is_abstraction_enabled():
        logger.info("Abstraction disabled, skipping table creation")
        return False
    
    db = DatabaseInterface(db_path)
    
    try:
        for table_name, schema in SQL_SCHEMAS.items():
            logger.info(f"Creating table: {table_name}")
            db.execute_query(schema)
        
        # Create indices for performance
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_sequence_concepts_seq 
            ON sequence_concepts(sequence_id)
        """)
        
        db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_detected_objects_game 
            ON detected_objects(game_id, level_number)
        """)
        
        logger.info("[OK] All abstraction tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create abstraction tables: {e}")
        return False


def verify_abstraction_schema(db_path="core_data.db"):
    """Verify all abstraction tables exist."""
    if not is_abstraction_enabled():
        return False
    
    db = DatabaseInterface(db_path)
    
    for table_name in SQL_SCHEMAS.keys():
        result = db.execute_query("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        if not result:
            logger.error(f"Missing table: {table_name}")
            return False
    
    logger.info("[OK] All abstraction tables verified")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("ABSTRACTION DATABASE SCHEMA SETUP")
    print("=" * 70)
    
    if not is_abstraction_enabled():
        print("\n[WARN]  ENABLE_ABSTRACTION is false")
        print("Set environment variable: ENABLE_ABSTRACTION=true")
        print("\nSkipping table creation (backwards compatible)")
    else:
        print("\n[OK] ENABLE_ABSTRACTION is true")
        print("\nCreating tables...")
        
        if create_abstraction_tables():
            print("\n[OK] Schema created successfully")
            
            if verify_abstraction_schema():
                print("[OK] Schema verified")
            else:
                print("[FAIL] Schema verification failed")
        else:
            print("\n[FAIL] Schema creation failed")
