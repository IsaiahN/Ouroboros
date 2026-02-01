#!/usr/bin/env python3
"""
Migration: Add SYMBOLIC MECHANICS tables for symbolic puzzle support.

Tables:
1. symbolic_state_hypotheses - Key/lock object tracking
2. tool_effect_hypotheses - Tool transformation effects
3. ui_layout_hypotheses - HUD detection and parsing
4. remote_effect_hypotheses - Action-at-distance causation
5. goal_structure_hypotheses - Compound goal decomposition

From LS20 DEFEAT PLAN (renamed to SYMBOLIC MECHANICS for universal applicability).
"""
import os
import sqlite3
from datetime import datetime


def migrate(db_path: str = "core_data.db"):
    """Apply the symbolic mechanics migration."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[MIGRATION] Adding SYMBOLIC MECHANICS tables...")

    # 1. Symbolic state tracking for key/lock puzzles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbolic_state_hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            level_number INTEGER,
            object_id TEXT NOT NULL,
            object_role TEXT,  -- 'key', 'lock', 'gate', 'tool', 'unknown'
            region_bbox TEXT,  -- JSON: [x1, y1, x2, y2]
            shape_signature TEXT,
            dominant_color INTEGER,
            orientation TEXT,
            discovered_by_agent TEXT,
            discovery_generation INTEGER,
            confidence REAL DEFAULT 0.5,
            validation_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created symbolic_state_hypotheses table")

    # 2. Tool effect hypotheses for transformation puzzles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_effect_hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            tool_signature TEXT,  -- Visual signature of tool object
            tool_position TEXT,  -- JSON: [x, y]
            effect_type TEXT,  -- 'shape_increment', 'color_rotate', 'orientation_rotate', 'unknown'
            target_attribute TEXT,  -- 'shape', 'color', 'orientation'
            transformation_rule TEXT,  -- JSON: {"from": X, "to": Y}
            observation_count INTEGER DEFAULT 1,
            success_rate REAL DEFAULT 0.0,
            discovered_by_agent TEXT,
            discovery_generation INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created tool_effect_hypotheses table")

    # 3. UI layout hypotheses for HUD detection
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ui_layout_hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            ui_region TEXT,  -- JSON: [x1, y1, x2, y2]
            indicator_type TEXT,  -- 'health_dots', 'life_squares', 'score_counter', 'timer'
            indicator_color INTEGER,
            meaning TEXT,  -- 'remaining_actions', 'remaining_lives', 'score'
            max_value INTEGER,  -- Maximum observed count
            depletes_on TEXT,  -- 'action', 'damage', 'time'
            refills_on TEXT,  -- 'pickup_purple', 'level_complete', 'never'
            confidence REAL DEFAULT 0.5,
            observation_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created ui_layout_hypotheses table")

    # 4. Remote effect hypotheses for action-at-distance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remote_effect_hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            level_number INTEGER,
            trigger_position TEXT,  -- JSON: [x, y] where agent acted
            trigger_object TEXT,  -- Object overlapped
            effect_region TEXT,  -- JSON: [x1, y1, x2, y2] where change occurred
            effect_type TEXT,  -- 'symbolic_change', 'gate_open', 'spawn', 'destroy'
            causal_chain TEXT,  -- JSON: ["step1", "step2", ...]
            observation_count INTEGER DEFAULT 1,
            reliability REAL DEFAULT 0.3,
            discovered_by_agent TEXT,
            discovery_generation INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created remote_effect_hypotheses table")

    # 5. Goal structure hypotheses for compound goals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_structure_hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_type TEXT NOT NULL,
            goal_type TEXT,  -- 'reach', 'match', 'collect', 'survive', 'transform'
            is_compound BOOLEAN DEFAULT FALSE,
            sub_goals TEXT,  -- JSON: [{"type": "match_shape", "target": X}, ...]
            completion_condition TEXT,  -- JSON: {"key_matches_lock": true}
            dependency_order TEXT,  -- JSON: ["sub_goal_1", "sub_goal_2"]
            confidence REAL DEFAULT 0.5,
            win_validated BOOLEAN DEFAULT FALSE,
            observation_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created goal_structure_hypotheses table")

    # Create indexes for fast lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbolic_state_game ON symbolic_state_hypotheses(game_type, level_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbolic_state_role ON symbolic_state_hypotheses(object_role, is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_effect_game ON tool_effect_hypotheses(game_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_effect_type ON tool_effect_hypotheses(effect_type, is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_layout_game ON ui_layout_hypotheses(game_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_remote_effect_game ON remote_effect_hypotheses(game_type, level_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_remote_effect_type ON remote_effect_hypotheses(effect_type, is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_structure_game ON goal_structure_hypotheses(game_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goal_structure_type ON goal_structure_hypotheses(goal_type, is_active)")
    print("[OK] Created indexes")

    conn.commit()
    conn.close()

    print(f"[MIGRATION] SYMBOLIC MECHANICS tables added to {db_path}")
    return True


if __name__ == "__main__":
    # Default to current directory's core_data.db
    db_path = os.environ.get("DATABASE_PATH", "core_data.db")
    migrate(db_path)
