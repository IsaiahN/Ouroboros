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

-- Community memory: Sequence validation tracking (Layer 3 - Somatic/Community)
-- Tracks which agents tried which sequences and whether they worked
-- This enables communal learning while requiring individual validation
CREATE TABLE IF NOT EXISTS sequence_validation_attempts (
    validation_id TEXT PRIMARY KEY,
    sequence_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation results
    validation_success BOOLEAN NOT NULL,       -- Did sequence work for this agent?
    partial_success BOOLEAN DEFAULT FALSE,     -- Got partway through sequence
    actions_completed INTEGER DEFAULT 0,       -- How many actions from sequence worked
    total_actions_in_sequence INTEGER NOT NULL,
    
    -- Performance
    score_achieved REAL DEFAULT 0.0,
    efficiency_vs_original REAL DEFAULT 1.0,   -- This agent's efficiency / original efficiency
    
    -- Context
    agent_epigenetics TEXT,                    -- JSON: agent's epigenetic state during attempt
    failure_reason TEXT,                       -- If failed, why? 'state_mismatch', 'invalid_action', etc.
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Sequence reputation scores (computed from validation attempts)
-- Updated periodically to track community consensus on sequence quality
CREATE TABLE IF NOT EXISTS sequence_reputation (
    sequence_id TEXT PRIMARY KEY,
    
    -- Validation statistics
    total_validation_attempts INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    failed_validations INTEGER DEFAULT 0,
    partial_validations INTEGER DEFAULT 0,
    
    -- Reputation metrics
    success_rate REAL DEFAULT 0.0,              -- successful / total
    reliability_score REAL DEFAULT 0.5,         -- Bayesian confidence-adjusted score
    agent_diversity INTEGER DEFAULT 1,          -- How many different agents tried it
    
    -- Temporal tracking
    recent_success_rate REAL DEFAULT 0.0,       -- Last 10 attempts only
    trending TEXT DEFAULT 'stable',             -- 'improving', 'declining', 'stable'
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
);

-- Pattern learning indexes
CREATE INDEX IF NOT EXISTS idx_winning_sequences_game_id ON winning_sequences(game_id);
CREATE INDEX IF NOT EXISTS idx_winning_sequences_efficiency ON winning_sequences(efficiency_score);
CREATE INDEX IF NOT EXISTS idx_discovered_patterns_success_rate ON discovered_patterns(success_rate);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_success ON pattern_applications(success);
CREATE INDEX IF NOT EXISTS idx_sequence_validation_attempts_agent ON sequence_validation_attempts(agent_id);
CREATE INDEX IF NOT EXISTS idx_sequence_validation_attempts_sequence ON sequence_validation_attempts(sequence_id);
CREATE INDEX IF NOT EXISTS idx_sequence_reputation_success_rate ON sequence_reputation(success_rate DESC);

-- ============================================================================
-- AGI-FOCUSED GAME DIVERSITY TRACKING
-- Tracks agent performance across diverse games for generalization testing
-- Following AGI goal: generalize to 100s of unseen games, not specialize
-- ============================================================================

-- Game diversity tracking per agent
CREATE TABLE IF NOT EXISTS agent_game_diversity (
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    first_attempt_score REAL DEFAULT 0.0,
    best_score REAL DEFAULT 0.0,
    last_attempt_score REAL DEFAULT 0.0,
    is_novel_game BOOLEAN DEFAULT TRUE,        -- First time this agent saw this game
    few_shot_improvement REAL DEFAULT 0.0,     -- Score improvement from attempt 1 to 2
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id, game_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- AGI performance metrics (generalization focus)
CREATE TABLE IF NOT EXISTS agent_agi_metrics (
    agent_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    
    -- Diversity metrics
    unique_games_played INTEGER DEFAULT 0,
    unique_games_scored INTEGER DEFAULT 0,      -- Games with ANY score > 0
    game_diversity_ratio REAL DEFAULT 0.0,      -- scored/played ratio
    
    -- Generalization metrics
    novel_game_performance REAL DEFAULT 0.0,    -- Avg score on first-time games
    novel_games_attempted INTEGER DEFAULT 0,
    novel_games_scored INTEGER DEFAULT 0,
    
    -- Few-shot learning metrics
    few_shot_improvement_avg REAL DEFAULT 0.0,  -- Avg improvement attempt 1→2
    few_shot_success_rate REAL DEFAULT 0.0,     -- % games improved on 2nd try
    
    -- Anti-overfitting metrics
    max_repeats_on_single_game INTEGER DEFAULT 0,
    overfitting_penalty REAL DEFAULT 0.0,       -- Penalty if too focused on one game
    
    -- AGI fitness score (50% novel + 30% few-shot + 20% diversity)
    agi_fitness_score REAL DEFAULT 0.0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Game exposure tracking (prevent overfitting)
CREATE TABLE IF NOT EXISTS game_exposure_history (
    game_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    times_played INTEGER DEFAULT 0,
    unique_agents_played INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0.0,
    best_score REAL DEFAULT 0.0,
    is_retired BOOLEAN DEFAULT FALSE,           -- Retired if played too much
    retirement_reason TEXT,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, generation)
);

-- AGI diversity indexes
CREATE INDEX IF NOT EXISTS idx_agent_game_diversity_agent ON agent_game_diversity(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_game_diversity_novel ON agent_game_diversity(is_novel_game);
CREATE INDEX IF NOT EXISTS idx_agent_agi_metrics_fitness ON agent_agi_metrics(agi_fitness_score DESC);
CREATE INDEX IF NOT EXISTS idx_game_exposure_retired ON game_exposure_history(is_retired);

-- [CHECKPOINT: PATTERN LEARNING INTEGRATED]
-- [CHECKPOINT: AGI GAME DIVERSITY TRACKING ADDED]

-- ============================================================================
-- META-LEARNING EXTENSION - Learn to Learn Capability
-- Stores learned visual primitives, transformation rules, and meta-learning metrics
-- Enables true generalization to unseen levels through rule induction
-- ============================================================================

-- Learned visual primitives (building blocks for reasoning)
CREATE TABLE IF NOT EXISTS visual_primitives (
    primitive_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    primitive_type TEXT NOT NULL,          -- 'symmetry_detector', 'pattern_finder', 'color_analyzer'
    primitive_name TEXT NOT NULL,
    learned_parameters TEXT NOT NULL,      -- JSON: parameters/weights for this primitive
    success_rate REAL DEFAULT 0.0,
    times_used INTEGER DEFAULT 0,
    avg_confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Learned transformation rules (abstract IF-THEN rules)
CREATE TABLE IF NOT EXISTS learned_rules (
    rule_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    source_game_id TEXT NOT NULL,          -- Game where rule was learned
    rule_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Rule definition
    preconditions TEXT NOT NULL,           -- JSON: visual conditions that must be met
    action_template TEXT NOT NULL,         -- JSON: sequence of actions to take
    expected_outcome TEXT NOT NULL,        -- 'win', 'progress', 'score_increase'
    
    -- Confidence and success tracking
    confidence REAL DEFAULT 0.5,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,         -- success / (success + failure)
    
    -- Transfer learning
    applicable_games TEXT,                 -- JSON: list of game_ids where rule works
    transferred_successfully BOOLEAN DEFAULT 0,
    transfer_attempts INTEGER DEFAULT 0,
    successful_transfers INTEGER DEFAULT 0,
    
    -- Rule characteristics
    visual_signature TEXT,                 -- Compact signature for quick matching
    complexity_level TEXT,                 -- 'simple', 'moderate', 'complex'
    generality_score REAL DEFAULT 0.0,     -- How many games rule works on
    
    last_updated TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Rule transfer attempts (learning history)
CREATE TABLE IF NOT EXISTS rule_transfers (
    transfer_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    source_game_id TEXT NOT NULL,
    target_game_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    transfer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Transfer results
    transfer_successful BOOLEAN NOT NULL,
    confidence_before REAL NOT NULL,
    confidence_after REAL,
    score_achieved REAL,
    actions_taken INTEGER,
    
    -- Analysis
    match_confidence REAL,                 -- How well preconditions matched
    execution_quality REAL,                -- How well actions were executed
    actual_result TEXT,                    -- 'full_win', 'partial_success', 'no_progress', 'failure'
    failure_reason TEXT,
    
    FOREIGN KEY (rule_id) REFERENCES learned_rules(rule_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Meta-learning metrics per agent (learning to learn)
CREATE TABLE IF NOT EXISTS agent_meta_learning (
    agent_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    
    -- Rule acquisition
    total_rules_learned INTEGER DEFAULT 0,
    rules_created_this_gen INTEGER DEFAULT 0,
    avg_rules_per_game REAL DEFAULT 0.0,
    
    -- Transfer learning
    successful_transfers INTEGER DEFAULT 0,
    failed_transfers INTEGER DEFAULT 0,
    transfer_success_rate REAL DEFAULT 0.0,
    
    -- Generalization capability
    avg_rule_generality REAL DEFAULT 0.0,  -- Avg games each rule works on
    novel_game_success_rate REAL DEFAULT 0.0,
    learning_rate REAL DEFAULT 0.0,        -- How fast agent learns new rules
    
    -- Meta-fitness (30% of total fitness in diversity mode)
    meta_fitness_score REAL DEFAULT 0.0,
    
    -- Visual reasoning capability
    visual_primitives_learned INTEGER DEFAULT 0,
    visual_understanding_score REAL DEFAULT 0.0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Curriculum stage tracking (4-stage learning progression)
CREATE TABLE IF NOT EXISTS curriculum_progress (
    agent_id TEXT NOT NULL,
    stage_number INTEGER NOT NULL,         -- 1: specialization, 2: near_transfer, 3: diversification, 4: generalization
    stage_name TEXT NOT NULL,
    entered_stage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exited_stage TIMESTAMP,
    
    -- Stage requirements
    required_win_rate REAL NOT NULL,
    achieved_win_rate REAL DEFAULT 0.0,
    required_transfer_rate REAL,
    achieved_transfer_rate REAL DEFAULT 0.0,
    
    -- Stage performance
    games_played_in_stage INTEGER DEFAULT 0,
    games_won_in_stage INTEGER DEFAULT 0,
    rules_learned_in_stage INTEGER DEFAULT 0,
    successful_transfers_in_stage INTEGER DEFAULT 0,
    
    -- Advancement
    stage_completed BOOLEAN DEFAULT FALSE,
    completion_timestamp TIMESTAMP,
    
    PRIMARY KEY (agent_id, stage_number),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Game session visual analysis (store frame analyses for rule learning)
CREATE TABLE IF NOT EXISTS game_visual_analysis (
    analysis_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    frame_number INTEGER NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Frame data
    frame_data TEXT NOT NULL,              -- JSON: the actual frame
    
    -- Visual features (from visual_reasoning_engine)
    symmetry_detected TEXT,                -- JSON: symmetry types and confidence
    patterns_found TEXT,                   -- JSON: repeating patterns
    colors_analyzed TEXT,                  -- JSON: color distribution
    shapes_detected TEXT,                  -- JSON: shape information
    spatial_relations TEXT,                -- JSON: relationships between objects
    complexity_metrics TEXT,               -- JSON: complexity scores
    
    -- Transformation suggestions
    likely_transformations TEXT,           -- JSON: suggested actions based on visual analysis
    
    -- Used for rule learning
    used_in_rule_id TEXT,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (used_in_rule_id) REFERENCES learned_rules(rule_id)
);

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

-- [CHECKPOINT: META-LEARNING DATABASE SCHEMA ADDED]
-- Next: Implement meta-learning fitness calculation in evolutionary_engine.py

-- ============================================================================
-- NETWORK INTELLIGENCE & ECOSYSTEM HEALTH TRACKING
-- Treats the DATABASE as the primary organism, agents as temporary components
-- Tracks network-level health: knowledge diversity, information flow, resilience
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
    discovery_timestamp TIMESTAMP,
    discovery_generation INTEGER,
    
    -- Backup metrics (how many agents know this)
    agents_who_know INTEGER DEFAULT 1,  -- How many agents have used this successfully
    agent_carriers TEXT,  -- JSON: list of agent IDs who successfully used this
    validation_attempts INTEGER DEFAULT 0,
    successful_validations INTEGER DEFAULT 0,
    
    -- Criticality assessment
    games_solved_by_this INTEGER DEFAULT 0,  -- How many unique games
    alternative_solutions_exist INTEGER DEFAULT 0,  -- Redundancy at game level
    criticality_score REAL DEFAULT 0.0,  -- How critical is this to network survival
    is_viral_core BOOLEAN DEFAULT FALSE,  -- Essential knowledge that must not be lost
    
    -- Persistence tracking
    generations_survived INTEGER DEFAULT 0,  -- How many generations has this knowledge persisted
    last_used_generation INTEGER DEFAULT 0,
    last_used_timestamp TIMESTAMP,
    risk_of_loss REAL DEFAULT 1.0,  -- Probability of being forgotten (0=safe, 1=at risk)
    
    -- Network contribution
    times_taught_to_others INTEGER DEFAULT 0,
    network_enrichment_value REAL DEFAULT 0.0,
    
    FOREIGN KEY (sequence_id) REFERENCES winning_sequences(sequence_id)
);

-- Rule redundancy tracking (abstract knowledge backup)
CREATE TABLE IF NOT EXISTS rule_redundancy (
    rule_id TEXT PRIMARY KEY,
    discovery_timestamp TIMESTAMP,
    discovery_generation INTEGER,
    
    -- Backup metrics
    agents_who_discovered INTEGER DEFAULT 1,
    agent_carriers TEXT,  -- JSON: list of agent IDs who independently discovered this
    independent_discoveries INTEGER DEFAULT 1,
    
    -- Criticality for network
    games_applicable_to INTEGER DEFAULT 0,
    transfer_success_count INTEGER DEFAULT 0,
    criticality_score REAL DEFAULT 0.0,
    is_viral_core BOOLEAN DEFAULT FALSE,
    
    -- Persistence
    generations_survived INTEGER DEFAULT 0,
    last_used_generation INTEGER DEFAULT 0,
    risk_of_loss REAL DEFAULT 1.0,
    
    FOREIGN KEY (rule_id) REFERENCES learned_rules(rule_id)
);

-- Network knowledge graph (relationships between knowledge pieces)
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    edge_id TEXT PRIMARY KEY,
    source_knowledge_id TEXT NOT NULL,
    target_knowledge_id TEXT NOT NULL,
    source_knowledge_type TEXT NOT NULL,  -- 'sequence', 'pattern', 'rule'
    target_knowledge_type TEXT NOT NULL,
    edge_type TEXT NOT NULL,  -- 'builds_on', 'contradicts', 'generalizes', 'specializes'
    
    -- Edge strength
    confidence REAL DEFAULT 0.5,
    evidence_count INTEGER DEFAULT 1,
    
    -- Discovery
    discovered_by_agent TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discovered_generation INTEGER,
    
    -- Validation
    validated BOOLEAN DEFAULT FALSE,
    validation_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (discovered_by_agent) REFERENCES agents(agent_id)
);

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

-- [CHECKPOINT: NETWORK INTELLIGENCE DATABASE SCHEMA ADDED]
-- Network-centric view now possible: track ecosystem as primary organism
