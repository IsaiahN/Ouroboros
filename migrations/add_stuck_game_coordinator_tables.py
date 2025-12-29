"""
Migration: Add Stuck Game Coordinator Tables
=============================================
Creates tables for the new intelligent intervention system that
replaces the broken frustration quorum.
"""

import sqlite3
import os
import sys

def run_migration(db_path: str = 'core_data.db'):
    """Run the migration to add stuck game coordinator tables."""
    print(f"[MIGRATION] Adding stuck game coordinator tables to {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. stuck_game_interventions - Track intelligent interventions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stuck_game_interventions (
            intervention_id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            game_type TEXT NOT NULL,
            generation INTEGER NOT NULL,
            
            -- Analysis
            bottleneck_level INTEGER,
            agents_stuck INTEGER,
            total_agents INTEGER,
            stuck_ratio REAL,
            
            -- Knowledge synthesis
            death_zones_found INTEGER DEFAULT 0,
            dangerous_objects_found INTEGER DEFAULT 0,
            theories_found INTEGER DEFAULT 0,
            hypotheses_found INTEGER DEFAULT 0,
            
            -- Gaps identified
            knowledge_gaps TEXT,  -- JSON list
            
            -- Interventions applied
            interventions_applied TEXT,  -- JSON list
            action_budget_boost REAL DEFAULT 0,
            investigators_assigned INTEGER DEFAULT 0,
            experiments_requested INTEGER DEFAULT 0,
            
            -- Outcome tracking
            resolved BOOLEAN DEFAULT FALSE,
            resolution_generation INTEGER,
            breakthrough_action TEXT,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    """)
    print("  [OK] stuck_game_interventions table created")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stuck_game_lookup
        ON stuck_game_interventions (game_type, resolved, generation)
    """)
    print("  [OK] Index created for stuck_game_interventions")
    
    # 2. game_specific_config - Per-game configuration from coordinator
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_specific_config (
            game_type TEXT,
            config_key TEXT,
            config_value TEXT,
            updated_at TIMESTAMP,
            PRIMARY KEY (game_type, config_key)
        )
    """)
    print("  [OK] game_specific_config table created")
    
    # 3. queued_experiments - Experiments queued by coordinator for scientific method engine
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queued_experiments (
            experiment_id TEXT PRIMARY KEY,
            game_type TEXT,
            description TEXT,
            priority TEXT DEFAULT 'NORMAL',
            executed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK] queued_experiments table created")
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_queued_experiments_lookup
        ON queued_experiments (game_type, executed, priority)
    """)
    print("  [OK] Index created for queued_experiments")
    
    # 4. knowledge_synthesis - Synthesized knowledge for stuck games
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_synthesis (
            synthesis_id TEXT PRIMARY KEY,
            game_type TEXT,
            level INTEGER,
            synthesis_data TEXT,  -- JSON with combined knowledge
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK] knowledge_synthesis table created")
    
    conn.commit()
    conn.close()
    
    print("[MIGRATION] Stuck game coordinator tables migration complete!")


if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'core_data.db'
    run_migration(db_path)
