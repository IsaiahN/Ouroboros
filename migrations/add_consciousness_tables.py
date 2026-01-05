"""
Migration: Add Consciousness System Tables
From: agent_consciousness_synthesis.md

Tables added:
- consciousness_logs: Per-action consciousness loop execution logs
- theory_transitions: Theory stage lifecycle transitions  
- working_theories: Working theory lifecycle tracking
- metacognitive_questions: Questions generated during gameplay (Q1-Q9)
- theory_action_links: Which actions tested which theories
"""
import sqlite3
import os

DB_PATH = 'core_data.db'

TABLES = [
    # Consciousness loop execution logs (CRITICAL for benchmarks)
    """
    CREATE TABLE IF NOT EXISTS consciousness_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        game_id TEXT NOT NULL,
        action_number INTEGER NOT NULL,
        
        -- What was logged
        log_type TEXT NOT NULL,            -- 'stream_confusion', 'observer_spawn', 'theory_transition', 'cross_transfer', 'surprise'
        log_text TEXT NOT NULL,            -- Human-readable consciousness report
        
        -- Stream weights at time of log
        w_a REAL,                          -- Private memory weight
        w_b REAL,                          -- Collective wisdom weight
        
        -- Context
        current_theory_stage TEXT,
        surprise_score REAL,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Theory stage transitions (for lifecycle visibility)
    """
    CREATE TABLE IF NOT EXISTS theory_transitions (
        transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        game_type TEXT NOT NULL,
        level_number INTEGER,
        
        from_stage TEXT NOT NULL,
        to_stage TEXT NOT NULL,
        action_number INTEGER NOT NULL,
        
        -- What triggered the transition
        trigger_reason TEXT,               -- 'evidence_accumulated', 'contradiction', 'transfer_success'
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Working theory lifecycle tracking
    """
    CREATE TABLE IF NOT EXISTS working_theories (
        theory_id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        game_type TEXT NOT NULL,
        level_number INTEGER NOT NULL,
        
        -- Theory content
        hypothesis TEXT NOT NULL,
        hypothesis_type TEXT,              -- 'control', 'goal', 'physics', 'trigger'
        stage TEXT DEFAULT 'speculating',  -- speculating, exploring, hypothesis_formed, partial_confirmation, contradicted, confident, transferred
        
        -- Evidence tracking
        evidence_for INTEGER DEFAULT 0,
        evidence_against INTEGER DEFAULT 0,
        contradictions_json TEXT,          -- JSON array of contradictions
        
        -- Last action this theory was active
        last_action INTEGER,
        
        -- Timestamps
        formed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        -- Source tracking
        source_observations TEXT           -- JSON of observations that led to theory
    )
    """,
    
    # Questions generated during gameplay
    """
    CREATE TABLE IF NOT EXISTS metacognitive_questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT,
        game_id TEXT,
        level_number INTEGER,
        action_number INTEGER,
        
        -- Question content
        question_type TEXT NOT NULL,       -- Q1-Q9 from framework
        query TEXT NOT NULL,
        urgency TEXT DEFAULT 'medium',     -- low, medium, high, critical
        
        -- Enforcement (questions with teeth)
        blocks_action BOOLEAN DEFAULT FALSE,
        score_modifier REAL DEFAULT 1.0,
        allowed_actions TEXT,              -- JSON array of allowed action types when blocked
        
        -- Resolution
        answered BOOLEAN DEFAULT FALSE,
        answer TEXT,
        led_to_theory_revision BOOLEAN DEFAULT FALSE,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Theory-action links (which actions tested which theories)
    """
    CREATE TABLE IF NOT EXISTS theory_action_links (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT,
        theory_id TEXT NOT NULL,
        action_number INTEGER NOT NULL,
        game_id TEXT NOT NULL,
        
        -- Prediction vs outcome
        predicted_outcome TEXT,
        actual_outcome TEXT,
        matched BOOLEAN,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_consciousness_logs_agent_game ON consciousness_logs(agent_id, game_id)",
    "CREATE INDEX IF NOT EXISTS idx_consciousness_logs_type ON consciousness_logs(log_type)",
    "CREATE INDEX IF NOT EXISTS idx_theory_transitions_agent ON theory_transitions(agent_id, game_type)",
    "CREATE INDEX IF NOT EXISTS idx_working_theories_agent_game ON working_theories(agent_id, game_type, level_number)",
    "CREATE INDEX IF NOT EXISTS idx_working_theories_stage ON working_theories(stage)",
    "CREATE INDEX IF NOT EXISTS idx_metacognitive_questions_agent ON metacognitive_questions(agent_id, game_id)",
    "CREATE INDEX IF NOT EXISTS idx_metacognitive_questions_type ON metacognitive_questions(question_type)",
    "CREATE INDEX IF NOT EXISTS idx_theory_action_links_theory ON theory_action_links(theory_id)",
]

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Running consciousness system migration...")
    
    # Create tables
    for table_sql in TABLES:
        try:
            cursor.execute(table_sql)
            # Extract table name for logging
            table_name = table_sql.split('CREATE TABLE IF NOT EXISTS ')[1].split('(')[0].strip()
            print(f"  [OK] Created table: {table_name}")
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    # Create indexes
    for idx_sql in INDEXES:
        try:
            cursor.execute(idx_sql)
            idx_name = idx_sql.split('CREATE INDEX IF NOT EXISTS ')[1].split(' ON')[0].strip()
            print(f"  [OK] Created index: {idx_name}")
        except Exception as e:
            print(f"  [ERROR] Index: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nMigration complete!")
    return True

if __name__ == "__main__":
    run_migration()
