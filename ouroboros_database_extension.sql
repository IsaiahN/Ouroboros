-- ============================================================================
-- OUROBOROS SYSTEM DATABASE SCHEMA EXTENSION
-- Extends core_database_schema.sql with evolutionary framework tables
-- Following Rule 2: Database-Only Storage - All Ouroboros data in SQLite
-- ============================================================================

-- [CHECKPOINT 1: DATABASE SCHEMA EXTENSION STARTED]
-- This file extends the existing database with Ouroboros evolutionary tables
-- Rule compliance: Database-only storage, no log files, real ARC data only

-- Enhanced agent management table
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    genome TEXT NOT NULL,              -- JSON strategy parameters
    generation INTEGER NOT NULL,
    parent_ids TEXT,                   -- JSON array of parent agent IDs
    specialization TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- ARC performance metrics (ARC-native rewards)
    total_games_played INTEGER DEFAULT 0,
    total_games_won INTEGER DEFAULT 0,
    total_score_achieved REAL DEFAULT 0.0,
    avg_score_per_game REAL DEFAULT 0.0,
    best_single_game_score REAL DEFAULT 0.0,
    avg_actions_per_game REAL DEFAULT 0.0,
    score_efficiency REAL DEFAULT 0.0,
    level_progressions_detected INTEGER DEFAULT 0,

    -- Evolution tracking
    mutation_count INTEGER DEFAULT 0,
    crossover_count INTEGER DEFAULT 0,
    last_performance_update TIMESTAMP,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    retirement_reason TEXT
);

-- Evolution cycle tracking (Claude Code decisions)
CREATE TABLE IF NOT EXISTS claude_evolution_decisions (
    decision_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Claude Code analysis
    population_analysis TEXT NOT NULL,      -- JSON analysis results
    evolution_strategy TEXT NOT NULL,       -- JSON strategy decisions
    reasoning TEXT NOT NULL,                -- Claude's reasoning for decisions

    -- Execution results
    agents_created INTEGER DEFAULT 0,
    agents_retired INTEGER DEFAULT 0,
    mutations_applied INTEGER DEFAULT 0,
    crossovers_performed INTEGER DEFAULT 0,

    -- Performance expectations
    expected_improvement_rate REAL,
    target_win_rate REAL,
    strategy_focus TEXT,                    -- 'exploration', 'exploitation', 'diversification'

    -- Results tracking
    actual_improvement_rate REAL,
    success_indicator BOOLEAN,
    notes TEXT
);

-- Agent ARC game performance (detailed tracking with ARC-native rewards)
CREATE TABLE IF NOT EXISTS agent_arc_performance (
    performance_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    game_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Game results (ARC-native rewards)
    final_score REAL NOT NULL,
    win_score_threshold REAL NOT NULL,
    win_achieved BOOLEAN NOT NULL,
    total_actions INTEGER NOT NULL,
    game_duration_seconds REAL,

    -- Performance metrics
    score_efficiency REAL NOT NULL,        -- score per action
    win_proximity REAL NOT NULL,           -- score / win_score
    level_progressions INTEGER DEFAULT 0,
    action_effectiveness REAL,

    -- Strategy tracking
    strategy_used TEXT NOT NULL,
    genome_config TEXT NOT NULL,           -- JSON genome at time of game
    action_sequence TEXT,                  -- JSON sequence of actions taken

    -- Reward calculation (evolutionary fitness)
    base_reward REAL NOT NULL,
    win_bonus REAL DEFAULT 0.0,
    efficiency_bonus REAL DEFAULT 0.0,
    level_progression_bonus REAL DEFAULT 0.0,
    total_evolutionary_reward REAL NOT NULL,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- Population diversity and health metrics
CREATE TABLE IF NOT EXISTS population_health_metrics (
    metric_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    measurement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Diversity measurements
    genetic_diversity_score REAL NOT NULL,
    strategy_distribution TEXT NOT NULL,    -- JSON distribution of agent types
    performance_variance REAL NOT NULL,

    -- Health indicators
    stagnation_indicator REAL NOT NULL,
    improvement_rate REAL NOT NULL,
    population_size INTEGER NOT NULL,
    active_agents INTEGER NOT NULL,

    -- Performance benchmarks
    best_win_rate REAL NOT NULL,
    average_win_rate REAL NOT NULL,
    worst_win_rate REAL NOT NULL,
    win_rate_std_dev REAL NOT NULL,

    -- Strategic analysis
    dominant_strategies TEXT,              -- JSON list of most successful strategies
    emerging_patterns TEXT,                -- JSON patterns Claude Code has identified
    recommendations TEXT                   -- JSON Claude Code recommendations
);

-- Claude Code memory and learning (LLM self-management per Rule 4)
CREATE TABLE IF NOT EXISTS claude_memory (
    memory_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,             -- 'successful_strategy', 'failed_approach', 'pattern_discovery'
    content TEXT NOT NULL,                 -- JSON memory content
    relevance_score REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,

    -- Memory linking
    related_agents TEXT,                   -- JSON array of related agent IDs
    related_decisions TEXT,                -- JSON array of related decision IDs
    context_tags TEXT,                     -- JSON array of context tags

    -- Memory validation
    validation_status TEXT DEFAULT 'unverified',  -- 'verified', 'contradicted', 'unverified'
    validation_evidence TEXT              -- JSON evidence for/against memory
);

-- Real-time ARC action tracking (Rule 7: Real Actions Only)
CREATE TABLE IF NOT EXISTS arc_action_tracking (
    action_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Action details
    action_type TEXT NOT NULL,
    action_data TEXT NOT NULL,             -- JSON action parameters
    coordinate_x INTEGER,                  -- For ACTION6 tracking (0-63 range)
    coordinate_y INTEGER,                  -- For ACTION6 tracking (0-63 range)

    -- API verification (Rule 7: Verify real actions sent to ARC games)
    api_request_sent BOOLEAN NOT NULL,
    api_response_received BOOLEAN NOT NULL,
    api_response_data TEXT,                -- JSON API response

    -- Effectiveness tracking
    score_before_action REAL,
    score_after_action REAL,
    score_delta REAL,
    immediate_reward REAL,

    -- Validation
    coordinate_valid BOOLEAN,              -- Within 0-63 range check
    action_accepted BOOLEAN,               -- ARC API accepted action
    error_message TEXT,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- ============================================================================
-- INDEXES FOR OUROBOROS PERFORMANCE
-- ============================================================================

-- Agent performance indexes
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_generation ON agents(generation);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_total_games_won ON agents(total_games_won);
CREATE INDEX IF NOT EXISTS idx_agents_score_efficiency ON agents(score_efficiency);

-- Evolution decisions indexes
CREATE INDEX IF NOT EXISTS idx_claude_decisions_generation ON claude_evolution_decisions(generation);
CREATE INDEX IF NOT EXISTS idx_claude_decisions_timestamp ON claude_evolution_decisions(decision_timestamp);
CREATE INDEX IF NOT EXISTS idx_claude_decisions_strategy_focus ON claude_evolution_decisions(strategy_focus);

-- Agent ARC performance indexes
CREATE INDEX IF NOT EXISTS idx_agent_arc_perf_agent_id ON agent_arc_performance(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_arc_perf_win_achieved ON agent_arc_performance(win_achieved);
CREATE INDEX IF NOT EXISTS idx_agent_arc_perf_timestamp ON agent_arc_performance(game_timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_arc_perf_total_reward ON agent_arc_performance(total_evolutionary_reward);

-- Population health indexes
CREATE INDEX IF NOT EXISTS idx_pop_health_generation ON population_health_metrics(generation);
CREATE INDEX IF NOT EXISTS idx_pop_health_timestamp ON population_health_metrics(measurement_timestamp);
CREATE INDEX IF NOT EXISTS idx_pop_health_improvement_rate ON population_health_metrics(improvement_rate);

-- Claude memory indexes
CREATE INDEX IF NOT EXISTS idx_claude_memory_type ON claude_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_claude_memory_relevance ON claude_memory(relevance_score);
CREATE INDEX IF NOT EXISTS idx_claude_memory_created_at ON claude_memory(created_at);

-- ARC action tracking indexes
CREATE INDEX IF NOT EXISTS idx_arc_action_agent_id ON arc_action_tracking(agent_id);
CREATE INDEX IF NOT EXISTS idx_arc_action_timestamp ON arc_action_tracking(action_timestamp);
CREATE INDEX IF NOT EXISTS idx_arc_action_coordinate_valid ON arc_action_tracking(coordinate_valid);
CREATE INDEX IF NOT EXISTS idx_arc_action_accepted ON arc_action_tracking(action_accepted);

-- ============================================================================
-- VIEWS FOR OUROBOROS ANALYSIS
-- ============================================================================

-- Current generation performance view
CREATE VIEW IF NOT EXISTS current_generation_performance AS
SELECT
    a.agent_id,
    a.agent_type,
    a.generation,
    a.total_games_played,
    a.total_games_won,
    CASE WHEN a.total_games_played > 0
         THEN CAST(a.total_games_won AS REAL) / a.total_games_played
         ELSE 0.0 END as win_rate,
    a.avg_score_per_game,
    a.score_efficiency,
    a.level_progressions_detected,
    a.is_active
FROM agents a
WHERE a.generation = (SELECT MAX(generation) FROM agents WHERE is_active = TRUE)
ORDER BY win_rate DESC, a.score_efficiency DESC;

-- Evolution progress view
CREATE VIEW IF NOT EXISTS evolution_progress AS
SELECT
    phm.generation,
    phm.population_size,
    phm.average_win_rate,
    phm.best_win_rate,
    phm.improvement_rate,
    phm.genetic_diversity_score,
    phm.stagnation_indicator,
    ced.strategy_focus,
    ced.decision_timestamp
FROM population_health_metrics phm
LEFT JOIN claude_evolution_decisions ced ON phm.generation = ced.generation
ORDER BY phm.generation DESC;

-- Top performing agents view
CREATE VIEW IF NOT EXISTS top_performing_agents AS
SELECT
    a.agent_id,
    a.agent_type,
    a.specialization,
    a.generation,
    CASE WHEN a.total_games_played > 0
         THEN CAST(a.total_games_won AS REAL) / a.total_games_played
         ELSE 0.0 END as win_rate,
    a.score_efficiency,
    a.avg_score_per_game,
    a.level_progressions_detected,
    a.created_at
FROM agents a
WHERE a.is_active = TRUE
ORDER BY win_rate DESC, a.score_efficiency DESC
LIMIT 10;

-- [CHECKPOINT 1 COMPLETED: DATABASE SCHEMA EXTENSION]
-- Next: Implement core coordinator and evolution engine components

-- ============================================================================
-- PATTERN LEARNING & ABSTRACTION EXTENSION (Rule 10: Integrated)
-- Tracks winning sequences, discovers patterns, learns abstractions
-- Critical for beating levels: learns HOW to beat each level type
-- ============================================================================

-- Winning action sequences (the gold standard - what actually worked)
CREATE TABLE IF NOT EXISTS winning_sequences (
    sequence_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    level_number INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- The winning sequence
    action_sequence TEXT NOT NULL,         -- JSON: ordered list of actions
    coordinate_sequence TEXT,              -- JSON: coordinates for ACTION6
    total_actions INTEGER NOT NULL,
    total_score REAL NOT NULL,
    efficiency_score REAL NOT NULL,        -- score / actions
    
    -- Game state context
    initial_frame TEXT NOT NULL,           -- JSON: starting frame state
    final_frame TEXT NOT NULL,             -- JSON: winning frame state
    frame_transitions TEXT,                -- JSON: key frame changes
    
    -- Abstraction tags (for pattern matching)
    pattern_tags TEXT,                     -- JSON: ['grid_clear', 'color_match', 'sequence_repeat']
    difficulty_level TEXT,                 -- 'easy', 'medium', 'hard'
    game_type TEXT,                        -- 'action6_only', 'mixed_actions', 'pattern_based'
    
    -- Reuse tracking
    times_referenced INTEGER DEFAULT 0,
    success_rate_when_reused REAL DEFAULT 0.0,
    last_referenced TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Discovered patterns (abstractions across multiple wins)
CREATE TABLE IF NOT EXISTS discovered_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_name TEXT NOT NULL,
    pattern_type TEXT NOT NULL,            -- 'action_sequence', 'coordinate_cluster', 'color_pattern'
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Pattern definition
    pattern_signature TEXT NOT NULL,       -- JSON: abstract pattern description
    concrete_examples TEXT NOT NULL,       -- JSON: array of sequence_ids that match
    occurrence_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 1,
    
    -- Effectiveness metrics
    success_rate REAL NOT NULL,            -- % of times pattern leads to win
    avg_score_achieved REAL NOT NULL,
    avg_efficiency REAL NOT NULL,
    confidence_score REAL NOT NULL,        -- statistical confidence
    
    -- Application context
    applicable_game_types TEXT,            -- JSON: which game types this works on
    
    -- Learning status
    validation_status TEXT DEFAULT 'hypothesis',  -- 'hypothesis', 'validated', 'invalidated'
    validation_games INTEGER DEFAULT 0,
    last_validated TIMESTAMP
);

-- Pattern application attempts
CREATE TABLE IF NOT EXISTS pattern_applications (
    application_id TEXT PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    sequence_id TEXT,
    game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Results
    success BOOLEAN NOT NULL,
    score_achieved REAL NOT NULL,
    actions_taken INTEGER NOT NULL,
    
    FOREIGN KEY (pattern_id) REFERENCES discovered_patterns(pattern_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Pattern learning indexes
CREATE INDEX IF NOT EXISTS idx_winning_sequences_game_id ON winning_sequences(game_id);
CREATE INDEX IF NOT EXISTS idx_winning_sequences_efficiency ON winning_sequences(efficiency_score);
CREATE INDEX IF NOT EXISTS idx_discovered_patterns_success_rate ON discovered_patterns(success_rate);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_success ON pattern_applications(success);

-- [CHECKPOINT: PATTERN LEARNING INTEGRATED]