-- ============================================================================
-- COMPLETE BITTERTRUTH-AI DATABASE SCHEMA
-- Combines core gameplay and Ouroboros evolutionary framework
-- Following Rule 2: Database-Only Storage - All data in SQLite
-- ============================================================================

-- ============================================================================
-- CORE GAME MECHANICS TABLES
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
    available_actions TEXT, -- JSON array of available actions at game start
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
-- OUROBOROS EVOLUTIONARY FRAMEWORK TABLES
-- ============================================================================

-- Enhanced agent management table
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    genome TEXT NOT NULL,              -- JSON strategy parameters (Layer 1: Static Genome)
    epigenetics TEXT,                  -- JSON epigenetic inheritance (Layer 2: Epigenetic)
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
    coordinate_x INTEGER,
    coordinate_y INTEGER,
    coordinate_valid BOOLEAN,

    -- API interaction (Rule 7 compliance)
    api_request_sent BOOLEAN DEFAULT FALSE,
    api_response_received BOOLEAN DEFAULT FALSE,
    api_response_time_ms INTEGER,
    action_accepted BOOLEAN,
    error_message TEXT,

    -- Action result
    frame_changed BOOLEAN DEFAULT FALSE,
    score_changed BOOLEAN DEFAULT FALSE,
    score_before REAL,
    score_after REAL,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- ============================================================================
-- PATTERN LEARNING & ABSTRACTION TABLES (Layer 3 - Community Knowledge)
-- ============================================================================

-- Winning action sequences (the gold standard - what actually worked)
CREATE TABLE IF NOT EXISTS winning_sequences (
    sequence_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    level_number INTEGER,
    agent_id TEXT NOT NULL,
    
    -- Sequence data
    action_sequence TEXT NOT NULL,         -- JSON array of actions
    coordinate_sequence TEXT,              -- JSON array of coordinates (for ACTION6)
    total_actions INTEGER NOT NULL,
    
    -- Context
    initial_frame TEXT,                    -- JSON initial game state
    final_frame TEXT,                      -- JSON final game state
    score_achieved REAL NOT NULL,
    win_achieved BOOLEAN NOT NULL,
    
    -- Performance metrics
    efficiency_score REAL NOT NULL,        -- score per action
    execution_time_seconds REAL,
    
    -- Discovery metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_discovered INTEGER NOT NULL,
    times_successfully_replayed INTEGER DEFAULT 0,
    times_attempted_replay INTEGER DEFAULT 0,
    
    -- Pattern tags for abstraction
    pattern_tags TEXT,                     -- JSON array of pattern identifiers
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Discovered patterns (abstractions across multiple wins)
CREATE TABLE IF NOT EXISTS discovered_patterns (
    pattern_id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,            -- 'action_sequence', 'coordinate_path', 'strategy'
    pattern_description TEXT NOT NULL,
    
    -- Pattern definition
    abstract_sequence TEXT NOT NULL,       -- JSON abstract representation
    required_preconditions TEXT,           -- JSON conditions for applicability
    expected_outcomes TEXT,                -- JSON expected results
    
    -- Performance tracking
    total_applications INTEGER DEFAULT 0,
    successful_applications INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_efficiency REAL DEFAULT 0.0,
    
    -- Meta information
    discovered_by_agent TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_discovered INTEGER NOT NULL,
    
    -- Pattern evolution
    parent_pattern_id TEXT,                -- For pattern refinement
    derived_from_sequences TEXT,           -- JSON array of sequence_ids
    
    -- Validation
    confidence_score REAL DEFAULT 0.5,
    times_validated INTEGER DEFAULT 0,
    last_validated TIMESTAMP,
    
    FOREIGN KEY (discovered_by_agent) REFERENCES agents(agent_id)
);

-- Pattern application attempts
CREATE TABLE IF NOT EXISTS pattern_applications (
    application_id TEXT PRIMARY KEY,
    pattern_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    
    -- Application details
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Results
    success BOOLEAN NOT NULL,
    score_achieved REAL,
    actions_taken INTEGER,
    
    -- Context
    preconditions_met TEXT,                -- JSON which preconditions were satisfied
    adaptation_required TEXT,              -- JSON any modifications made
    
    FOREIGN KEY (pattern_id) REFERENCES discovered_patterns(pattern_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Community memory: Sequence validation tracking (Layer 3 - Somatic/Community)
CREATE TABLE IF NOT EXISTS sequence_validation_attempts (
    validation_id TEXT PRIMARY KEY,
    sequence_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    
    -- Attempt details
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Results
    validation_success BOOLEAN NOT NULL,
    score_achieved REAL,
    actions_taken INTEGER,
    exact_match BOOLEAN DEFAULT FALSE,     -- Did sequence work exactly as recorded?
    
    -- Adaptation tracking
    modifications_made TEXT,               -- JSON any changes required
    failure_reason TEXT,                   -- If failed, why?
    
    -- Context similarity
    frame_similarity_score REAL,           -- How similar was initial state?
    context_match_score REAL,              -- Overall context similarity
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Sequence reputation scores (computed from validation attempts)
CREATE TABLE IF NOT EXISTS sequence_reputation (
    sequence_id TEXT PRIMARY KEY,
    
    -- Reputation metrics (Bayesian)
    total_validation_attempts INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    
    -- Calculated scores
    success_rate REAL DEFAULT 0.0,
    reliability_score REAL DEFAULT 0.5,    -- Bayesian: (successes + 2) / (total + 4)
    
    -- Usage tracking
    total_agents_attempted INTEGER DEFAULT 0,
    total_agents_succeeded INTEGER DEFAULT 0,
    
    -- Temporal tracking
    last_validation_attempt TIMESTAMP,
    last_successful_validation TIMESTAMP,
    generations_since_last_success INTEGER DEFAULT 0,
    
    -- Decay tracking
    reputation_decay_factor REAL DEFAULT 1.0,
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
);

-- ============================================================================
-- AGI-FOCUSED GAME DIVERSITY TRACKING
-- ============================================================================

-- Game diversity tracking per agent
CREATE TABLE IF NOT EXISTS agent_game_diversity (
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    first_played_generation INTEGER NOT NULL,
    times_played INTEGER DEFAULT 1,
    best_score REAL DEFAULT 0.0,
    win_achieved BOOLEAN DEFAULT FALSE,
    is_novel_game BOOLEAN DEFAULT TRUE,    -- Was this a new game for this agent?
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, game_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- AGI performance metrics (generalization focus)
CREATE TABLE IF NOT EXISTS agent_agi_metrics (
    agent_id TEXT PRIMARY KEY,
    
    -- Diversity metrics
    unique_games_played INTEGER DEFAULT 0,
    unique_games_won INTEGER DEFAULT 0,
    game_diversity_score REAL DEFAULT 0.0,
    
    -- Generalization metrics
    first_attempt_success_rate REAL DEFAULT 0.0,  -- Win rate on novel games
    transfer_learning_score REAL DEFAULT 0.0,      -- Performance on new games
    specialization_penalty REAL DEFAULT 0.0,       -- Penalty for narrow focus
    
    -- Adaptability
    avg_games_to_win REAL DEFAULT 0.0,            -- How fast does agent learn?
    novel_game_performance REAL DEFAULT 0.0,       -- Avg score on unseen games
    
    -- AGI fitness (combines everything)
    agi_fitness_score REAL DEFAULT 0.0,
    
    -- Temporal tracking
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Game exposure tracking (prevent overfitting)
CREATE TABLE IF NOT EXISTS game_exposure_history (
    game_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    times_played INTEGER DEFAULT 0,
    times_won INTEGER DEFAULT 0,
    unique_agents_played INTEGER DEFAULT 0,
    is_retired BOOLEAN DEFAULT FALSE,      -- Has this game been overused?
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, generation)
);

-- ============================================================================
-- META-LEARNING EXTENSION - Learn to Learn Capability
-- ============================================================================

-- Learned visual primitives (building blocks for reasoning)
CREATE TABLE IF NOT EXISTS visual_primitives (
    primitive_id TEXT PRIMARY KEY,
    primitive_type TEXT NOT NULL,          -- 'shape', 'color_pattern', 'spatial_relation', 'transformation'
    primitive_definition TEXT NOT NULL,    -- JSON definition
    agent_id TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    times_observed INTEGER DEFAULT 1,
    times_used_successfully INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Learned transformation rules (abstract IF-THEN rules)
CREATE TABLE IF NOT EXISTS learned_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,               -- 'visual', 'spatial', 'logical', 'sequential'
    
    -- Rule definition
    preconditions TEXT NOT NULL,           -- JSON conditions that trigger rule
    transformations TEXT NOT NULL,         -- JSON transformations to apply
    expected_outcomes TEXT NOT NULL,       -- JSON expected results
    
    -- Learning context
    agent_id TEXT NOT NULL,
    learned_from_games TEXT NOT NULL,      -- JSON array of game_ids
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_learned INTEGER NOT NULL,
    
    -- Performance tracking
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.5,
    
    -- Transfer learning
    transferred_to_novel_games INTEGER DEFAULT 0,
    transferred_successfully INTEGER DEFAULT 0,
    transfer_success_rate REAL DEFAULT 0.0,
    
    -- Abstraction level
    abstraction_level INTEGER DEFAULT 1,   -- 1=concrete, 5=highly abstract
    generality_score REAL DEFAULT 0.0,     -- How broadly applicable?
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Rule transfer attempts (learning history)
CREATE TABLE IF NOT EXISTS rule_transfers (
    transfer_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    source_game_id TEXT NOT NULL,          -- Where rule was learned
    target_game_id TEXT NOT NULL,          -- Where rule was applied
    agent_id TEXT NOT NULL,
    
    -- Transfer details
    transfer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Context similarity
    context_similarity REAL NOT NULL,      -- How similar were the games?
    precondition_match REAL NOT NULL,      -- How well did preconditions match?
    
    -- Results
    transfer_successful BOOLEAN NOT NULL,
    performance_improvement REAL,          -- Score improvement vs baseline
    
    -- Adaptation
    rule_adapted BOOLEAN DEFAULT FALSE,
    adaptations_made TEXT,                 -- JSON modifications
    
    FOREIGN KEY (rule_id) REFERENCES learned_rules(rule_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Meta-learning metrics per agent (learning to learn)
CREATE TABLE IF NOT EXISTS agent_meta_learning (
    agent_id TEXT PRIMARY KEY,
    
    -- Rule library
    total_rules_learned INTEGER DEFAULT 0,
    active_rules INTEGER DEFAULT 0,
    rule_diversity_score REAL DEFAULT 0.0,
    
    -- Transfer performance
    total_transfer_attempts INTEGER DEFAULT 0,
    successful_transfers INTEGER DEFAULT 0,
    transfer_success_rate REAL DEFAULT 0.0,
    
    -- Learning speed
    avg_actions_to_learn_rule REAL DEFAULT 0.0,
    avg_games_to_learn_rule REAL DEFAULT 0.0,
    learning_rate REAL DEFAULT 0.0,
    
    -- Abstraction capability
    avg_rule_generality REAL DEFAULT 0.0,
    max_abstraction_level INTEGER DEFAULT 1,
    
    -- Meta-fitness (learning to learn score)
    meta_fitness_score REAL DEFAULT 0.0,
    
    -- Temporal tracking
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Curriculum stage tracking (4-stage learning progression)
CREATE TABLE IF NOT EXISTS curriculum_progress (
    agent_id TEXT NOT NULL,
    stage_number INTEGER NOT NULL,         -- 1=Foundation, 2=Pattern, 3=Abstraction, 4=Transfer
    
    -- Stage status
    stage_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stage_completed TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    
    -- Stage metrics
    games_in_stage INTEGER DEFAULT 0,
    wins_in_stage INTEGER DEFAULT 0,
    rules_learned_in_stage INTEGER DEFAULT 0,
    
    -- Progression criteria
    mastery_score REAL DEFAULT 0.0,        -- 0.0 to 1.0
    ready_for_next_stage BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (agent_id, stage_number),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Game session visual analysis (store frame analyses for rule learning)
CREATE TABLE IF NOT EXISTS game_visual_analysis (
    analysis_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    
    -- Frame data
    frame_number INTEGER NOT NULL,
    frame_data TEXT NOT NULL,              -- JSON frame state
    
    -- Visual analysis
    detected_primitives TEXT,              -- JSON array of primitive_ids
    detected_patterns TEXT,                -- JSON patterns observed
    spatial_relationships TEXT,            -- JSON spatial analysis
    
    -- Transformation analysis
    transformation_from_prev TEXT,         -- JSON what changed from previous frame
    likely_action TEXT,                    -- Inferred action that caused change
    
    -- Rule induction
    triggered_rule_ids TEXT,               -- JSON rules that matched this context
    used_in_rule_id TEXT,                  -- If this frame was used to learn a rule
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id),
    FOREIGN KEY (used_in_rule_id) REFERENCES learned_rules(rule_id)
);

-- ============================================================================
-- NETWORK INTELLIGENCE & ECOSYSTEM HEALTH TRACKING
-- ============================================================================

-- Ecosystem health snapshots (network vital signs)
CREATE TABLE IF NOT EXISTS ecosystem_health_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Knowledge metrics (the "database as organism")
    total_sequences INTEGER DEFAULT 0,
    total_patterns INTEGER DEFAULT 0,
    total_learned_rules INTEGER DEFAULT 0,
    unique_games_solved INTEGER DEFAULT 0,
    knowledge_diversity_index REAL DEFAULT 0.0,  -- Shannon entropy of pattern distribution
    
    -- Information flow metrics (the "metabolism")
    sequences_created_this_gen INTEGER DEFAULT 0,
    sequences_validated_this_gen INTEGER DEFAULT 0,
    sequences_reused_this_gen INTEGER DEFAULT 0,
    rules_learned_this_gen INTEGER DEFAULT 0,
    rules_transferred_this_gen INTEGER DEFAULT 0,
    knowledge_creation_rate REAL DEFAULT 0.0,  -- New discoveries per agent-game
    validation_rate REAL DEFAULT 0.0,  -- Successful validations / total attempts
    
    -- Resilience metrics (the "immune system")
    critical_sequences_count INTEGER DEFAULT 0,  -- Sequences with >80% reliability
    orphan_sequences_count INTEGER DEFAULT 0,  -- Sequences with 0 validations
    redundancy_index REAL DEFAULT 0.0,  -- Avg validations per sequence
    knowledge_backup_ratio REAL DEFAULT 0.0,  -- % of knowledge with multiple agent carriers
    
    -- Population metrics (temporary expressions)
    active_agents INTEGER DEFAULT 0,
    agent_diversity_index REAL DEFAULT 0.0,
    avg_agent_lifespan_generations REAL DEFAULT 0.0,
    agent_turnover_rate REAL DEFAULT 0.0,
    
    -- Metabolic health indicators
    network_growth_rate REAL DEFAULT 0.0,  -- Knowledge growth vs population growth
    innovation_vs_exploitation REAL DEFAULT 0.5,  -- New vs reused sequences ratio
    transfer_learning_rate REAL DEFAULT 0.0,  -- Successful rule transfers per agent
    system_entropy REAL DEFAULT 0.0,  -- Overall disorder measure
    
    -- Overall health assessment
    health_status TEXT DEFAULT 'unknown',  -- 'critical', 'poor', 'fair', 'good', 'excellent'
    health_score REAL DEFAULT 0.0  -- 0.0 to 1.0
);

-- Knowledge redundancy tracking (viral backup system)
CREATE TABLE IF NOT EXISTS knowledge_redundancy (
    sequence_id TEXT PRIMARY KEY,
    
    -- Redundancy metrics
    total_agent_carriers INTEGER DEFAULT 0,  -- How many agents can execute this?
    active_agent_carriers INTEGER DEFAULT 0,  -- How many are still active?
    generation_spread INTEGER DEFAULT 0,  -- How many generations have seen this?
    
    -- Backup status
    is_backed_up BOOLEAN DEFAULT FALSE,  -- Multiple carriers exist
    backup_count INTEGER DEFAULT 0,
    last_backup_generation INTEGER,
    
    -- Risk assessment
    risk_of_loss REAL DEFAULT 1.0,  -- 1.0 = high risk, 0.0 = well protected
    criticality_score REAL DEFAULT 0.0,  -- Based on success rate and usage
    is_viral_core BOOLEAN DEFAULT FALSE,  -- Part of critical knowledge base?
    
    -- Temporal tracking
    first_discovered_generation INTEGER NOT NULL,
    last_used_generation INTEGER,
    generations_since_last_use INTEGER DEFAULT 0,
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
);

-- Rule redundancy tracking (abstract knowledge backup)
CREATE TABLE IF NOT EXISTS rule_redundancy (
    rule_id TEXT PRIMARY KEY,
    
    -- Redundancy metrics
    total_agent_carriers INTEGER DEFAULT 0,
    active_agent_carriers INTEGER DEFAULT 0,
    independent_discoveries INTEGER DEFAULT 0,  -- How many agents learned this independently?
    
    -- Backup status
    is_backed_up BOOLEAN DEFAULT FALSE,
    backup_count INTEGER DEFAULT 0,
    
    -- Risk assessment
    risk_of_loss REAL DEFAULT 1.0,
    criticality_score REAL DEFAULT 0.0,
    is_viral_core BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (rule_id) REFERENCES learned_rules(rule_id)
);

-- Network knowledge graph (relationships between knowledge pieces)
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    edge_id TEXT PRIMARY KEY,
    
    -- Edge definition
    source_knowledge_id TEXT NOT NULL,  -- sequence_id or rule_id or pattern_id
    target_knowledge_id TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'sequence', 'rule', 'pattern'
    target_type TEXT NOT NULL,
    
    -- Relationship type
    edge_type TEXT NOT NULL,  -- 'derives_from', 'depends_on', 'contradicts', 'reinforces'
    relationship_strength REAL DEFAULT 1.0,
    
    -- Discovery
    discovered_by_agent TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation INTEGER NOT NULL,
    
    -- Validation
    times_observed INTEGER DEFAULT 1,
    confidence REAL DEFAULT 0.5,
    
    FOREIGN KEY (discovered_by_agent) REFERENCES agents(agent_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Core game mechanics indexes
CREATE INDEX IF NOT EXISTS idx_training_sessions_mode ON training_sessions(mode);
CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);
CREATE INDEX IF NOT EXISTS idx_training_sessions_start_time ON training_sessions(start_time);

CREATE INDEX IF NOT EXISTS idx_game_results_session_id ON game_results(session_id);
CREATE INDEX IF NOT EXISTS idx_game_results_status ON game_results(status);
CREATE INDEX IF NOT EXISTS idx_game_results_final_score ON game_results(final_score);

CREATE INDEX IF NOT EXISTS idx_action_traces_session_id ON action_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_action_traces_game_id ON action_traces(game_id);
CREATE INDEX IF NOT EXISTS idx_action_traces_timestamp ON action_traces(timestamp);

CREATE INDEX IF NOT EXISTS idx_action_effectiveness_game_id ON action_effectiveness(game_id);
CREATE INDEX IF NOT EXISTS idx_action_effectiveness_action_number ON action_effectiveness(action_number);
CREATE INDEX IF NOT EXISTS idx_action_effectiveness_success_rate ON action_effectiveness(success_rate);

CREATE INDEX IF NOT EXISTS idx_score_history_session_id ON score_history(session_id);
CREATE INDEX IF NOT EXISTS idx_score_history_game_id ON score_history(game_id);
CREATE INDEX IF NOT EXISTS idx_score_history_timestamp ON score_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_logger_name ON system_logs(logger_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_session_id ON system_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_game_id ON system_logs(game_id);

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

-- Pattern learning indexes
CREATE INDEX IF NOT EXISTS idx_winning_sequences_game_id ON winning_sequences(game_id);
CREATE INDEX IF NOT EXISTS idx_winning_sequences_efficiency ON winning_sequences(efficiency_score);
CREATE INDEX IF NOT EXISTS idx_discovered_patterns_success_rate ON discovered_patterns(success_rate);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_success ON pattern_applications(success);
CREATE INDEX IF NOT EXISTS idx_sequence_validation_attempts_agent ON sequence_validation_attempts(agent_id);
CREATE INDEX IF NOT EXISTS idx_sequence_validation_attempts_sequence ON sequence_validation_attempts(sequence_id);
CREATE INDEX IF NOT EXISTS idx_sequence_reputation_success_rate ON sequence_reputation(success_rate DESC);

-- AGI diversity indexes
CREATE INDEX IF NOT EXISTS idx_agent_game_diversity_agent ON agent_game_diversity(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_game_diversity_novel ON agent_game_diversity(is_novel_game);
CREATE INDEX IF NOT EXISTS idx_agent_agi_metrics_fitness ON agent_agi_metrics(agi_fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_game_exposure_retired ON game_exposure_history(is_retired);

-- Meta-learning indexes
CREATE INDEX IF NOT EXISTS idx_visual_primitives_agent ON visual_primitives(agent_id);
CREATE INDEX IF NOT EXISTS idx_visual_primitives_type ON visual_primitives(primitive_type);
CREATE INDEX IF NOT EXISTS idx_visual_primitives_success ON visual_primitives(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_learned_rules_agent ON learned_rules(agent_id);
CREATE INDEX IF NOT EXISTS idx_learned_rules_confidence ON learned_rules(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_learned_rules_transferred ON learned_rules(transferred_successfully);
CREATE INDEX IF NOT EXISTS idx_learned_rules_generality ON learned_rules(generality_score DESC);

CREATE INDEX IF NOT EXISTS idx_rule_transfers_rule ON rule_transfers(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_transfers_successful ON rule_transfers(transfer_successful);
CREATE INDEX IF NOT EXISTS idx_rule_transfers_timestamp ON rule_transfers(transfer_timestamp);

CREATE INDEX IF NOT EXISTS idx_agent_meta_learning_fitness ON agent_meta_learning(meta_fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_agent_meta_learning_transfer_rate ON agent_meta_learning(transfer_success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_curriculum_progress_agent ON curriculum_progress(agent_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_progress_stage ON curriculum_progress(stage_number);
CREATE INDEX IF NOT EXISTS idx_curriculum_progress_completed ON curriculum_progress(stage_completed);

CREATE INDEX IF NOT EXISTS idx_game_visual_analysis_agent ON game_visual_analysis(agent_id);
CREATE INDEX IF NOT EXISTS idx_game_visual_analysis_game ON game_visual_analysis(game_id);

-- Ecosystem health indexes
CREATE INDEX IF NOT EXISTS idx_ecosystem_health_generation ON ecosystem_health_snapshots(generation);
CREATE INDEX IF NOT EXISTS idx_ecosystem_health_timestamp ON ecosystem_health_snapshots(snapshot_timestamp);
CREATE INDEX IF NOT EXISTS idx_ecosystem_health_status ON ecosystem_health_snapshots(health_status);
CREATE INDEX IF NOT EXISTS idx_ecosystem_health_score ON ecosystem_health_snapshots(health_score DESC);

CREATE INDEX IF NOT EXISTS idx_knowledge_redundancy_criticality ON knowledge_redundancy(criticality_score DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_redundancy_viral_core ON knowledge_redundancy(is_viral_core);
CREATE INDEX IF NOT EXISTS idx_knowledge_redundancy_risk ON knowledge_redundancy(risk_of_loss DESC);

CREATE INDEX IF NOT EXISTS idx_rule_redundancy_criticality ON rule_redundancy(criticality_score DESC);
CREATE INDEX IF NOT EXISTS idx_rule_redundancy_viral_core ON rule_redundancy(is_viral_core);

CREATE INDEX IF NOT EXISTS idx_knowledge_graph_source ON knowledge_graph_edges(source_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graph_target ON knowledge_graph_edges(target_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_graph_type ON knowledge_graph_edges(edge_type);

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

-- Current generation performance view
CREATE VIEW IF NOT EXISTS current_generation_performance AS
SELECT
    a.agent_id,
    a.agent_type,
    a.generation,
    a.total_games_played,
    a.total_games_won,
    CASE 
        WHEN a.total_games_played > 0 THEN (a.total_games_won * 1.0 / a.total_games_played)
        ELSE 0.0
    END as win_rate,
    a.avg_score_per_game,
    a.score_efficiency,
    a.is_active
FROM agents a
WHERE a.generation = (SELECT MAX(generation) FROM agents WHERE is_active = TRUE)
ORDER BY win_rate DESC, a.score_efficiency DESC;

-- Evolution progress view
CREATE VIEW IF NOT EXISTS evolution_progress AS
SELECT
    phm.generation,
    phm.population_size,
    phm.best_win_rate,
    phm.average_win_rate,
    phm.improvement_rate,
    phm.genetic_diversity_score,
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
    a.generation,
    a.total_games_played,
    a.total_games_won,
    CASE 
        WHEN a.total_games_played > 0 THEN (a.total_games_won * 1.0 / a.total_games_played)
        ELSE 0.0
    END as win_rate,
    a.avg_score_per_game,
    a.score_efficiency,
    a.created_at
FROM agents a
WHERE a.is_active = TRUE
ORDER BY win_rate DESC, a.score_efficiency DESC
LIMIT 10;
