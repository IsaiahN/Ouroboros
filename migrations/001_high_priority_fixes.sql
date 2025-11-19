-- High Priority Fixes: Database Schema Updates
-- This script implements:
-- 1. winning_sequences table (for partial/level wins)
-- 2. winning_sequences_full_game table (for full game wins - protected sequences)
-- 3. social_rule_adherence column for agents table (Exploiter 50/50 split)

-- =================================================================
-- FIX #3: Full Game Sequence Table Separation
-- =================================================================
-- Purpose: Protect full game wins from being overwritten by partial wins

-- Table for partial wins (individual levels)
CREATE TABLE IF NOT EXISTS winning_sequences (
    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    sequence_data TEXT NOT NULL, -- JSON: list of actions
    total_actions INTEGER NOT NULL,
    final_score REAL NOT NULL,
    agent_id TEXT,
    generation INTEGER,
    is_full_game_win BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate sequences for same game/level
    UNIQUE(game_id, level_number, sequence_data)
);

-- Table for FULL GAME wins (protected, never overwritten)
CREATE TABLE IF NOT EXISTS winning_sequences_full_game (
    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL UNIQUE, -- One entry per game
    total_levels_completed INTEGER NOT NULL,
    sequence_data TEXT NOT NULL, -- JSON: full game sequence
    total_actions INTEGER NOT NULL,
    final_score REAL NOT NULL,
    agent_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    agent_mode TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full game wins are immutable once stored
    CHECK(total_levels_completed >= 1)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_winning_sequences_game ON winning_sequences(game_id, level_number);
CREATE INDEX IF NOT EXISTS idx_winning_sequences_full_game ON winning_sequences_full_game(game_id);

-- =================================================================
-- FIX #4: Exploiter 50/50 Split (Social Rule Adherence)
-- =================================================================
-- Purpose: Create bimodal distribution of Exploiters:
--   - 50% Sociopaths (social_rule_adherence = 0.0-0.2)
--   - 50% Conformists (social_rule_adherence = 0.8-1.0)

-- Add social_rule_adherence column to agents table if it doesn't exist
-- Note: SQLite doesn't support ALTER TABLE IF NOT EXISTS, so we check first

-- This will be executed via Python to handle the conditional logic
-- ALTER TABLE agents ADD COLUMN social_rule_adherence REAL DEFAULT 0.5;

COMMIT;
