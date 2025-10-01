-- ============================================================================
-- CORE GAME MECHANICS DATABASE SCHEMA
-- This schema contains only the essential tables needed for basic gameplay
-- No architect, governor, or director-specific tables included
-- ============================================================================

-- System sessions and training runs
CREATE TABLE IF NOT EXISTS training_sessions (
    session_id TEXT PRIMARY KEY,
    game_id TEXT, -- Optional game_id for session context
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    total_actions INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_games INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    avg_score REAL DEFAULT 0.0,
    energy_level REAL DEFAULT 100.0,
    memory_operations INTEGER DEFAULT 0,
    sleep_cycles INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual game results within sessions
CREATE TABLE IF NOT EXISTS game_results (
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL, -- 'completed', 'failed', 'timeout', 'cancelled'
    final_score REAL DEFAULT 0.0,
    total_actions INTEGER DEFAULT 0,
    actions_taken TEXT, -- JSON array of action numbers
    win_detected BOOLEAN DEFAULT FALSE,
    level_completions INTEGER DEFAULT 0,
    frame_changes INTEGER DEFAULT 0,
    coordinate_attempts INTEGER DEFAULT 0,
    coordinate_successes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, session_id),
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- Action traces for detailed analysis
CREATE TABLE IF NOT EXISTS action_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    action_number INTEGER DEFAULT 0, -- Allow 0 for unknown actions
    coordinates TEXT, -- JSON coordinates for Action 6
    timestamp TIMESTAMP NOT NULL,
    frame_before TEXT, -- JSON frame data
    frame_after TEXT, -- JSON frame data
    frame_changed BOOLEAN DEFAULT FALSE,
    score_before REAL DEFAULT 0.0,
    score_after REAL DEFAULT 0.0,
    score_change REAL DEFAULT 0.0,
    response_data TEXT, -- JSON API response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- Action effectiveness tracking
CREATE TABLE IF NOT EXISTS action_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    action_number INTEGER NOT NULL,
    attempts INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_score_impact REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Score tracking for performance analysis
CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    action_number INTEGER NOT NULL,
    score REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- Global counters for system state
CREATE TABLE IF NOT EXISTS global_counters (
    counter_name TEXT PRIMARY KEY,
    counter_value INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- System logs table for all application logging
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT NOT NULL,
    logger_name TEXT NOT NULL,
    message TEXT NOT NULL,
    module TEXT,
    function_name TEXT,
    line_number INTEGER,
    session_id TEXT,
    game_id TEXT,
    process_id INTEGER,
    thread_id INTEGER,
    extra_data TEXT -- JSON for additional context
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Training sessions indexes
CREATE INDEX IF NOT EXISTS idx_training_sessions_mode ON training_sessions(mode);
CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);
CREATE INDEX IF NOT EXISTS idx_training_sessions_start_time ON training_sessions(start_time);

-- Game results indexes
CREATE INDEX IF NOT EXISTS idx_game_results_session_id ON game_results(session_id);
CREATE INDEX IF NOT EXISTS idx_game_results_status ON game_results(status);
CREATE INDEX IF NOT EXISTS idx_game_results_final_score ON game_results(final_score);

-- Action traces indexes
CREATE INDEX IF NOT EXISTS idx_action_traces_session_id ON action_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_action_traces_game_id ON action_traces(game_id);
CREATE INDEX IF NOT EXISTS idx_action_traces_timestamp ON action_traces(timestamp);

-- Action effectiveness indexes
CREATE INDEX IF NOT EXISTS idx_action_effectiveness_game_id ON action_effectiveness(game_id);
CREATE INDEX IF NOT EXISTS idx_action_effectiveness_action_number ON action_effectiveness(action_number);
CREATE INDEX IF NOT EXISTS idx_action_effectiveness_success_rate ON action_effectiveness(success_rate);

-- Score history indexes
CREATE INDEX IF NOT EXISTS idx_score_history_session_id ON score_history(session_id);
CREATE INDEX IF NOT EXISTS idx_score_history_game_id ON score_history(game_id);
CREATE INDEX IF NOT EXISTS idx_score_history_timestamp ON score_history(timestamp);

-- System logs indexes
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_logger_name ON system_logs(logger_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_session_id ON system_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_game_id ON system_logs(game_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Recent sessions view
CREATE VIEW IF NOT EXISTS recent_sessions AS
SELECT
    session_id,
    mode,
    status,
    total_actions,
    total_wins,
    total_games,
    win_rate,
    avg_score,
    start_time,
    end_time
FROM training_sessions
WHERE start_time >= datetime('now', '-7 days')
ORDER BY start_time DESC;

-- Action effectiveness summary view
CREATE VIEW IF NOT EXISTS action_effectiveness_summary AS
SELECT
    action_number,
    COUNT(*) as game_count,
    SUM(attempts) as total_attempts,
    SUM(successes) as total_successes,
    AVG(success_rate) as avg_success_rate,
    AVG(avg_score_impact) as avg_score_impact
FROM action_effectiveness
GROUP BY action_number
ORDER BY avg_success_rate DESC;

-- ============================================================================
-- ALGORITHMIC EVOLUTION SYSTEM TABLES
-- ============================================================================

-- Algorithm Population Storage
CREATE TABLE IF NOT EXISTS algorithm_population (
    algorithm_id TEXT PRIMARY KEY,
    algorithm_type TEXT NOT NULL, -- 'GP', 'VAE_generated', 'hybrid'
    algorithm_data TEXT NOT NULL, -- JSON serialized AST/DAG
    generation INTEGER DEFAULT 0,
    parent_ids TEXT, -- JSON array of parent algorithm IDs
    fitness_score REAL DEFAULT 0.0,
    games_evaluated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_evaluated TIMESTAMP
);

-- Algorithm Performance Tracking
CREATE TABLE IF NOT EXISTS algorithm_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    final_score REAL NOT NULL,
    actions_taken INTEGER NOT NULL,
    win_detected BOOLEAN DEFAULT FALSE,
    evaluation_context TEXT, -- JSON metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithm_population(algorithm_id),
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- VAE Model States
CREATE TABLE IF NOT EXISTS vae_models (
    model_id TEXT PRIMARY KEY,
    model_state BLOB, -- Serialized model weights
    latent_dimensions INTEGER NOT NULL,
    training_epoch INTEGER DEFAULT 0,
    validation_loss REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Multi-Armed Bandit Arms
CREATE TABLE IF NOT EXISTS mab_arms (
    arm_id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    total_pulls INTEGER DEFAULT 0,
    total_reward REAL DEFAULT 0.0,
    avg_reward REAL DEFAULT 0.0,
    confidence_interval REAL DEFAULT 1.0,
    last_pulled TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithm_population(algorithm_id)
);

-- Evolution History Tracking
CREATE TABLE IF NOT EXISTS evolution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation INTEGER NOT NULL,
    population_size INTEGER NOT NULL,
    best_fitness REAL NOT NULL,
    avg_fitness REAL NOT NULL,
    diversity_metric REAL,
    operations_performed TEXT, -- JSON array of GP operations
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EVOLUTION SYSTEM INDEXES
-- ============================================================================

-- Algorithm population indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_population_type ON algorithm_population(algorithm_type);
CREATE INDEX IF NOT EXISTS idx_algorithm_population_generation ON algorithm_population(generation);
CREATE INDEX IF NOT EXISTS idx_algorithm_population_fitness ON algorithm_population(fitness_score);
CREATE INDEX IF NOT EXISTS idx_algorithm_population_evaluated ON algorithm_population(last_evaluated);

-- Algorithm performance indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_performance_algorithm_id ON algorithm_performance(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_performance_game_id ON algorithm_performance(game_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_performance_session_id ON algorithm_performance(session_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_performance_timestamp ON algorithm_performance(timestamp);

-- VAE models indexes
CREATE INDEX IF NOT EXISTS idx_vae_models_epoch ON vae_models(training_epoch);
CREATE INDEX IF NOT EXISTS idx_vae_models_created ON vae_models(created_at);

-- MAB arms indexes
CREATE INDEX IF NOT EXISTS idx_mab_arms_algorithm_id ON mab_arms(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_mab_arms_avg_reward ON mab_arms(avg_reward);
CREATE INDEX IF NOT EXISTS idx_mab_arms_last_pulled ON mab_arms(last_pulled);

-- Evolution history indexes
CREATE INDEX IF NOT EXISTS idx_evolution_history_generation ON evolution_history(generation);
CREATE INDEX IF NOT EXISTS idx_evolution_history_timestamp ON evolution_history(timestamp);

-- ============================================================================
-- EVOLUTION SYSTEM VIEWS
-- ============================================================================

-- Top performing algorithms view
CREATE VIEW IF NOT EXISTS top_algorithms AS
SELECT
    ap.algorithm_id,
    ap.algorithm_type,
    ap.generation,
    ap.fitness_score,
    ap.games_evaluated,
    COUNT(perf.id) as total_evaluations,
    AVG(perf.final_score) as avg_score,
    SUM(CASE WHEN perf.win_detected THEN 1 ELSE 0 END) as wins,
    (SUM(CASE WHEN perf.win_detected THEN 1 ELSE 0 END) * 1.0 / COUNT(perf.id)) as win_rate
FROM algorithm_population ap
LEFT JOIN algorithm_performance perf ON ap.algorithm_id = perf.algorithm_id
GROUP BY ap.algorithm_id
HAVING COUNT(perf.id) >= 5  -- Only algorithms with sufficient evaluations
ORDER BY ap.fitness_score DESC, win_rate DESC;

-- Recent evolution progress view
CREATE VIEW IF NOT EXISTS evolution_progress AS
SELECT
    generation,
    population_size,
    best_fitness,
    avg_fitness,
    diversity_metric,
    timestamp
FROM evolution_history
WHERE timestamp >= datetime('now', '-30 days')
ORDER BY generation DESC;

-- ============================================================================
-- SEEDED ALGORITHMS AND ROUTINES EXTENSION
-- ============================================================================

-- Add columns to existing algorithm_population table for seeded algorithms
-- Note: These will be added via ALTER statements in database_interface.py for safety

-- Algorithm routines for game-type specific sequences
CREATE TABLE IF NOT EXISTS algorithm_routines (
    routine_id TEXT PRIMARY KEY,
    game_type TEXT NOT NULL, -- Extracted from game_id prefix (e.g., "vc33")
    routine_name TEXT NOT NULL,
    algorithm_sequence TEXT NOT NULL, -- JSON array of algorithm_ids in execution order
    switch_conditions TEXT, -- JSON array of conditions for switching algorithms
    success_rate REAL DEFAULT 0.0,
    games_tested INTEGER DEFAULT 0,
    levels_completed INTEGER DEFAULT 0,
    avg_actions_per_level REAL DEFAULT 0.0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seeded algorithm metadata for tracking adaptation quality
CREATE TABLE IF NOT EXISTS seeded_algorithms_meta (
    algorithm_id TEXT PRIMARY KEY,
    original_name TEXT NOT NULL,
    category TEXT NOT NULL,
    adaptability_score REAL DEFAULT 0.5, -- How well we expect it to adapt (0-1)
    complexity_level TEXT DEFAULT 'moderate', -- 'simple', 'moderate', 'complex'
    adaptation_notes TEXT,
    games_tested INTEGER DEFAULT 0,
    avg_performance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithm_population(algorithm_id)
);

-- Game type performance tracking
CREATE TABLE IF NOT EXISTS game_type_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_type TEXT NOT NULL,
    algorithm_id TEXT,
    routine_id TEXT,
    levels_completed INTEGER DEFAULT 0,
    total_actions INTEGER DEFAULT 0,
    avg_actions_per_level REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 0.0,
    games_played INTEGER DEFAULT 1,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithm_population(algorithm_id),
    FOREIGN KEY (routine_id) REFERENCES algorithm_routines(routine_id)
);

-- ============================================================================
-- SEEDED ALGORITHMS INDEXES
-- ============================================================================

-- Algorithm routines indexes
CREATE INDEX IF NOT EXISTS idx_algorithm_routines_game_type ON algorithm_routines(game_type);
CREATE INDEX IF NOT EXISTS idx_algorithm_routines_success_rate ON algorithm_routines(success_rate);
CREATE INDEX IF NOT EXISTS idx_algorithm_routines_last_used ON algorithm_routines(last_used);

-- Seeded algorithms meta indexes
CREATE INDEX IF NOT EXISTS idx_seeded_algorithms_category ON seeded_algorithms_meta(category);
CREATE INDEX IF NOT EXISTS idx_seeded_algorithms_adaptability ON seeded_algorithms_meta(adaptability_score);
CREATE INDEX IF NOT EXISTS idx_seeded_algorithms_performance ON seeded_algorithms_meta(avg_performance);

-- Game type performance indexes
CREATE INDEX IF NOT EXISTS idx_game_type_performance_type ON game_type_performance(game_type);
CREATE INDEX IF NOT EXISTS idx_game_type_performance_algorithm ON game_type_performance(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_game_type_performance_routine ON game_type_performance(routine_id);
CREATE INDEX IF NOT EXISTS idx_game_type_performance_success ON game_type_performance(success_rate);

-- ============================================================================
-- SEEDED ALGORITHMS VIEWS
-- ============================================================================

-- Best performing algorithms by category
CREATE VIEW IF NOT EXISTS top_seeded_algorithms AS
SELECT
    sam.algorithm_id,
    sam.original_name,
    sam.category,
    sam.adaptability_score,
    sam.avg_performance,
    ap.fitness_score,
    ap.generation,
    COUNT(gtp.id) as games_tested_total
FROM seeded_algorithms_meta sam
JOIN algorithm_population ap ON sam.algorithm_id = ap.algorithm_id
LEFT JOIN game_type_performance gtp ON sam.algorithm_id = gtp.algorithm_id
GROUP BY sam.algorithm_id
ORDER BY sam.avg_performance DESC, ap.fitness_score DESC;

-- Best routines by game type
CREATE VIEW IF NOT EXISTS top_game_routines AS
SELECT
    ar.game_type,
    ar.routine_id,
    ar.routine_name,
    ar.success_rate,
    ar.games_tested,
    ar.levels_completed,
    ar.avg_actions_per_level,
    COUNT(gtp.id) as performance_records
FROM algorithm_routines ar
LEFT JOIN game_type_performance gtp ON ar.routine_id = gtp.routine_id
GROUP BY ar.routine_id
HAVING ar.games_tested >= 3  -- Only routines with sufficient testing
ORDER BY ar.success_rate DESC, ar.avg_actions_per_level ASC;