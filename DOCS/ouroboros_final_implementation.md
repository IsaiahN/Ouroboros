# Ouroboros System Implementation - Claude Code Coordinator

**Created**: 2025-10-19
**Last Updated**: 2025-12-03
**Status**: Phase 0-5 + Phase 4.5 (Sensation Engine) COMPLETE
**Purpose**: Complete Ouroboros evolutionary framework integrated with existing ARC AGI 3 codebase
**Coordinator**: Claude Code as autonomous LLM coordinator

## LLM Operating Rules

**Claude Code operates the entire system according to these non-negotiable rules:**

### Rule 1: Always Disable Pycache
- Set `PYTHONDONTWRITEBYTECODE=1` in all environments
- Never allow .pyc files to be generated
- Keep Python environment clean

### Rule 2: Database-Only Storage
- ALL data stored in SQLite database, never use log files
- Never create .log files or any file-based logging
- Every operation, decision, and result goes into database tables
- If existing code uses file logging, convert to database storage

### Rule 3: No Orphaned Code
- Never leave old code behind when making changes
- Properly delete, move, or integrate all existing functionality
- Clean integration means enhancing existing files, not replacing them
- Every line of old code must be accounted for

### Rule 4: LLM Self-Management
- Claude Code manages the entire system autonomously
- All evolutionary decisions made by Claude Code analyzing database data
- System designed to run without human intervention once started
- Claude Code coordinates all agents, evolution, and optimization

### Rule 5: No Test Files
- Never create test files - waste of LLM tokens
- Always test with live ARC AGI 3 data
- Use real game results for all validation and testing

### Rule 6: No Simulated Games
- Never create simulated or mock ARC games
- Always use real ARC AGI 3 API calls
- Waste of time and tokens to generate fake game data

### Rule 7: Real Actions Only
- Always verify that real actions are being sent to ARC games
- Monitor API calls to ensure actual game interaction
- Never substitute mock or simulated actions

## System Overview

**Claude Code** serves as the central LLM coordinator running the Ouroboros evolutionary framework on autopilot. The system enhances the existing BitterTruth-AI ARC AGI 3 codebase with autonomous evolution capabilities while preserving all current functionality.

### Core Architecture

```
Claude Code Coordinator
├── Population Manager          # Manages agent populations in database
├── Evolution Engine           # Handles crossover, mutation, selection
├── ARC RLVR Framework        # Processes ARC-native rewards
├── Agent Factory             # Creates specialized agents
├── Sensation Engine          # Phase 4.5: Emotional Intelligence & Navigation
└── Performance Analyzer      # Analyzes ARC game performance data
```

**Integration Points with Existing Code:**
- Enhances `core_gameplay.py` with agent callback system
- Extends `action_handler.py` with evolutionary action selection
- Uses existing `database_interface.py` for all storage operations
- Builds on existing `core_database_schema.sql` with new tables
- Integrates with `main_runner.py` CLI with new evolution commands

## Core Components

### 1. Claude Code Coordinator (`ouroboros_coordinator.py`)

**Purpose**: Central LLM that runs everything on autopilot

```python
class OuroborosCoordinator:
    """Claude Code LLM coordinator for autonomous Ouroboros operation"""

    def __init__(self, database_interface):
        self.db = database_interface
        self.population_manager = PopulationManager(database_interface)
        self.evolution_engine = EvolutionaryEngine(database_interface)
        self.arc_rlvr = ARCRLVRFramework(database_interface)
        self.performance_analyzer = PerformanceAnalyzer(database_interface)

    def run_autonomous_evolution(self):
        """Main coordination loop - Claude Code runs this autonomously"""
        while True:
            # 1. Analyze current ARC performance data from database
            performance_data = self.performance_analyzer.analyze_population_performance()

            # 2. Make evolution decisions based on ARC results
            evolution_strategy = self._determine_evolution_strategy(performance_data)

            # 3. Execute evolution cycle
            new_agents = self.evolution_engine.evolve_population(evolution_strategy)

            # 4. Deploy agents for ARC game testing
            self._deploy_agents_for_testing(new_agents)

            # 5. Store all decisions and results in database
            self._log_evolution_cycle_to_database(evolution_strategy, new_agents)

    def _determine_evolution_strategy(self, performance_data):
        """Claude Code analyzes ARC performance and decides evolution strategy"""
        # Analyze win rates, score efficiency, level progression
        # Make strategic decisions about which traits to favor
        # Return evolution parameters for next generation
```

**Key Responsibilities:**
- Autonomous operation without human intervention
- Analysis of ARC performance patterns from database
- Strategic evolution decisions based on game results
- Coordination of all system components
- Database logging of all decisions and results

### 2. Evolution Engine (`evolutionary_engine.py`)

**Purpose**: Handles agent breeding, mutation, and selection based on ARC performance

```python
class EvolutionaryEngine:
    """Executes evolution operations based on Claude Code decisions"""

    def __init__(self, database_interface):
        self.db = database_interface
        self.crossover_ops = CrossoverOperations()
        self.mutation_strategies = MutationStrategies()

    def evolve_population(self, evolution_strategy):
        """Execute evolution cycle using ARC performance data"""
        # 1. Load current population from database
        current_population = self._load_population_from_database()

        # 2. Calculate ARC-based fitness scores
        fitness_scores = self._calculate_arc_fitness(current_population)

        # 3. Select breeding pairs based on ARC performance
        breeding_pairs = self._select_breeding_pairs(fitness_scores)

        # 4. Generate offspring through crossover
        offspring = self._generate_offspring(breeding_pairs)

        # 5. Apply mutations to explore strategy space
        mutated_offspring = self._apply_mutations(offspring, evolution_strategy)

        # 6. Update population in database
        new_population = self._update_population_database(mutated_offspring)

        return new_population

    def _calculate_arc_fitness(self, population):
        """Calculate fitness based on ARC game performance only"""
        fitness_scores = {}
        for agent in population:
            # Get ARC performance from database
            arc_performance = self.db.get_agent_arc_performance(agent.id)

            # Calculate fitness: 70% win rate, 20% score efficiency, 10% consistency
            fitness = (
                arc_performance['win_rate'] * 0.7 +
                arc_performance['score_efficiency'] * 0.2 +
                arc_performance['consistency_score'] * 0.1
            )
            fitness_scores[agent.id] = fitness

        return fitness_scores
```

### 3. ARC RLVR Framework (`arc_rlvr_framework.py`)

**Purpose**: Processes ARC-native rewards for evolutionary feedback

```python
class ARCRLVRFramework:
    """Reasoning, Learning, Validation, Revision using ARC-native rewards"""

    def __init__(self, database_interface):
        self.db = database_interface

    def process_arc_rewards(self, agent_id, game_session_results):
        """Process ARC game results into evolutionary feedback"""

        # Extract ARC-native rewards
        arc_rewards = {
            'game_win': game_session_results.get('win_detected', False),
            'score_achieved': game_session_results.get('final_score', 0),
            'win_score_threshold': game_session_results.get('win_score', 0),
            'actions_taken': game_session_results.get('total_actions', 0),
            'level_progressions': game_session_results.get('level_changes', 0)
        }

        # Calculate derived metrics
        score_efficiency = arc_rewards['score_achieved'] / max(arc_rewards['actions_taken'], 1)
        win_proximity = arc_rewards['score_achieved'] / max(arc_rewards['win_score_threshold'], 1)

        # Store in database for evolution analysis
        reward_data = {
            'agent_id': agent_id,
            'win_bonus': 100.0 if arc_rewards['game_win'] else 0.0,
            'score_efficiency': score_efficiency,
            'win_proximity': win_proximity,
            'level_progression_bonus': arc_rewards['level_progressions'] * 10.0,
            'total_reward': self._calculate_total_reward(arc_rewards, score_efficiency, win_proximity)
        }

        self.db.store_arc_reward_data(agent_id, reward_data)
        return reward_data

    def _calculate_total_reward(self, arc_rewards, score_efficiency, win_proximity):
        """Calculate total evolutionary reward from ARC performance"""
        base_reward = arc_rewards['score_achieved']
        win_bonus = 100.0 if arc_rewards['game_win'] else 0.0
        efficiency_bonus = score_efficiency * 10.0
        proximity_bonus = win_proximity * 20.0
        level_bonus = arc_rewards['level_progressions'] * 10.0

        return base_reward + win_bonus + efficiency_bonus + proximity_bonus + level_bonus
        return base_reward + win_bonus + efficiency_bonus + proximity_bonus + level_bonus

### 3.5. Sensation Engine (`sensation_engine.py`) - Phase 4.5

**Purpose**: Provides "Emotional Intelligence" to agents, allowing them to "feel" the game state and bias navigation actions based on past experiences with similar objects.

```python
class SensationEngine:
    """Phase 4.5: Emotional Intelligence for Agents"""

    def __init__(self, database_interface):
        self.db = database_interface

    def process_sensation(self, agent_id, game_state, nearby_objects):
        """
        1. Perceive objects
        2. Recall associated sensations (fear, excitement, curiosity)
        3. Update internal navigation state (-1.0 to +1.0)
        4. Bias next action selection
        """
        # ... implementation details ...
        return action_bias_weights
```

**Key Features:**
- **Object-Sensation Mapping**: Agents learn to associate game objects (colors, shapes) with outcomes.
- **Navigation State**: A floating point value (-1.0 to 1.0) representing the agent's current "mood".
- **Action Biasing**: "Fear" promotes caution/retreat; "Excitement" promotes exploration/interaction.
- **Integration**: Fully integrated into `core_gameplay.py` and `agent_factory.py`.


### 4. Agent Factory (`agent_factory.py`)

**Purpose**: Creates specialized agents that integrate with existing GameplayEngine

```python
class AgentFactory:
    """Creates ARC-specialized agents using existing codebase integration"""

    def __init__(self, database_interface):
        self.db = database_interface

    def create_agent(self, agent_type, genome):
        """Create agent that uses existing ActionHandler and GameplayEngine"""

        agent_types = {
            'pattern_specialist': self._create_pattern_specialist,
            'score_optimizer': self._create_score_optimizer,
            'exploration_agent': self._create_exploration_agent,
            'win_focused_agent': self._create_win_focused_agent
        }

        if agent_type not in agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent = agent_types[agent_type](genome)

        # Store agent in database
        self.db.store_agent(agent)

        return agent

    def _create_pattern_specialist(self, genome):
        """Agent specializing in ARC pattern recognition"""
        return ARCAgent(
            agent_id=self._generate_agent_id(),
            agent_type='pattern_specialist',
            genome=genome,
            specialization_config={
                'pattern_recognition_sensitivity': genome.get('pattern_sensitivity', 0.7),
                'coordinate_exploration_pattern': genome.get('coord_pattern', 'spiral'),
                'action_diversity_preference': genome.get('action_diversity', 0.6)
            }
        )

    def _create_score_optimizer(self, genome):
        """Agent focused on ARC score maximization"""
        return ARCAgent(
            agent_id=self._generate_agent_id(),
            agent_type='score_optimizer',
            genome=genome,
            specialization_config={
                'score_optimization_priority': genome.get('score_priority', 0.8),
                'action_efficiency_preference': genome.get('efficiency_pref', 0.7),
                'win_focus_threshold': genome.get('win_threshold', 0.85)
            }
        )
```

### 5. Performance Analyzer (`performance_analyzer.py`)

**Purpose**: Analyzes ARC performance data for Claude Code decision-making

```python
class PerformanceAnalyzer:
    """Analyzes ARC performance data for evolutionary decisions"""

    def __init__(self, database_interface):
        self.db = database_interface

    def analyze_population_performance(self):
        """Analyze current population's ARC performance for Claude Code"""

        # Get all agents and their ARC performance
        population_data = self.db.get_population_performance_data()

        analysis = {
            'population_stats': self._calculate_population_statistics(population_data),
            'top_performers': self._identify_top_performers(population_data),
            'performance_trends': self._analyze_performance_trends(population_data),
            'strategy_effectiveness': self._analyze_strategy_effectiveness(population_data),
            'diversity_metrics': self._calculate_diversity_metrics(population_data)
        }

        # Store analysis in database for Claude Code reference
        self.db.store_performance_analysis(analysis)

        return analysis

    def _calculate_population_statistics(self, population_data):
        """Calculate key ARC performance statistics"""
        win_rates = [agent['win_rate'] for agent in population_data]
        avg_scores = [agent['avg_score'] for agent in population_data]

        return {
            'average_win_rate': sum(win_rates) / len(win_rates),
            'best_win_rate': max(win_rates),
            'worst_win_rate': min(win_rates),
            'average_score': sum(avg_scores) / len(avg_scores),
            'score_variance': self._calculate_variance(avg_scores),
            'population_size': len(population_data)
        }
```

## Database Schema Extensions

### Extended Database Schema

```sql
-- Enhanced agent management
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    genome TEXT NOT NULL,              -- JSON strategy parameters
    generation INTEGER NOT NULL,
    parent_ids TEXT,                   -- JSON array of parent agent IDs
    specialization TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- ARC performance metrics
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
CREATE TABLE claude_evolution_decisions (
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

-- Agent ARC game performance (detailed tracking)
CREATE TABLE agent_arc_performance (
    performance_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    game_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Game results
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

    -- Reward calculation
    base_reward REAL NOT NULL,
    win_bonus REAL DEFAULT 0.0,
    efficiency_bonus REAL DEFAULT 0.0,
    level_progression_bonus REAL DEFAULT 0.0,
    total_evolutionary_reward REAL NOT NULL,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
);

-- Population diversity and health metrics
CREATE TABLE population_health_metrics (
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

-- Claude Code memory and learning
CREATE TABLE claude_memory (
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

-- Real-time ARC action tracking
CREATE TABLE arc_action_tracking (
    action_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Action details
    action_type TEXT NOT NULL,
    action_data TEXT NOT NULL,             -- JSON action parameters
    coordinate_x INTEGER,                  -- For ACTION6 tracking
    coordinate_y INTEGER,                  -- For ACTION6 tracking

    -- API verification
    api_request_sent BOOLEAN NOT NULL,
    api_response_received BOOLEAN NOT NULL,
    api_response_data TEXT,                -- JSON API response

    -- Effectiveness tracking
    score_before_action REAL,
    score_after_action REAL,
    score_delta REAL,
    immediate_reward REAL,

    -- Validation
    coordinate_valid BOOLEAN,              -- Within 0-63 range
    action_accepted BOOLEAN,               -- ARC API accepted action
    error_message TEXT,

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

## Integration with Existing Codebase

### Enhanced `core_gameplay.py`

**Integration Points:**
- Add `agent_callback` parameter to `play_single_game()`
- Integrate agent genome-based strategy selection
- Add hooks for agent performance tracking
- Maintain all existing API integration

```python
# Enhanced method signature
async def play_single_game(self, game_id: str,
                          agent_callback: Optional[Callable] = None,
                          agent_genome: Optional[Dict] = None) -> Dict[str, Any]:
    """Enhanced to support agent-based gameplay while preserving existing functionality"""

    # Existing game initialization code preserved
    # ...

    # New: Agent-driven strategy selection
    if agent_genome:
        strategy = self._select_strategy_from_genome(agent_genome)
    else:
        strategy = self.current_strategy  # Existing fallback

    # New: Agent callback for action selection
    if agent_callback:
        action = agent_callback(game_state, available_actions, agent_genome)
    else:
        action = self._select_action(game_state, available_actions)  # Existing logic

    # Existing action execution and API calls preserved
    # ...

    # New: Track performance for evolution
    if agent_callback:
        self._track_agent_performance(agent_genome.get('agent_id'), game_results)

    return game_results
```

### Enhanced `action_handler.py`

**Integration Points:**
- Add `EvolutionaryActionSelector` class
- Integrate ARC reward signal tracking
- Maintain existing ACTION6 coordinate handling
- Add immediate reward calculation

```python
class EvolutionaryActionSelector:
    """Evolutionary action selection that uses existing ActionHandler"""

    def __init__(self, action_handler, database_interface):
        self.action_handler = action_handler  # Use existing ActionHandler
        self.db = database_interface

    def select_action_for_agent(self, agent_genome, game_state, available_actions):
        """Select action based on agent genome using existing action mechanisms"""

        # Use genome parameters to influence existing strategy selection
        strategy_weights = {
            'exploration': agent_genome.get('exploration_weight', 0.3),
            'conservative': agent_genome.get('conservative_bias', 0.2),
            'score_focus': agent_genome.get('score_optimization_priority', 0.7)
        }

        # Use existing action selection but with agent-specific weights
        action = self.action_handler.smart_action_selection(
            game_state,
            available_actions,
            strategy_preferences=strategy_weights
        )

        # Track action for evolution analysis
        self._track_action_for_evolution(agent_genome['agent_id'], action, game_state)

        return action

    def track_arc_reward_signals(self, agent_id, score_before, score_after,
                                win_detected, level_change):
        """Track immediate ARC rewards for evolutionary feedback"""

        reward_data = {
            'agent_id': agent_id,
            'score_delta': score_after - score_before,
            'win_bonus': 100.0 if win_detected else 0.0,
            'level_bonus': 10.0 if level_change else 0.0,
            'immediate_reward': self._calculate_immediate_reward(
                score_after - score_before, win_detected, level_change
            )
        }

        # Store in database for Claude Code analysis
        self.db.store_immediate_reward_signal(reward_data)
        return reward_data
```

### Enhanced `main_runner.py`

**New Evolution Commands:**

```python
# New command group for evolution
@click.group()
def evolve():
    """Evolution commands for Ouroboros system"""
    pass

@evolve.command()
@click.option('--generations', default=10, help='Number of evolution cycles to run')
@click.option('--population-size', default=20, help='Agent population size')
def run(generations, population_size):
    """Run autonomous evolution cycles with Claude Code coordination"""
    coordinator = OuroborosCoordinator(db_interface)
    coordinator.run_evolution_cycles(generations, population_size)

@evolve.command()
def analyze():
    """Analyze current population performance"""
    analyzer = PerformanceAnalyzer(db_interface)
    analysis = analyzer.analyze_population_performance()
    display_analysis_results(analysis)

@evolve.command()
@click.option('--agent-id', required=True, help='Agent ID to analyze')
def agent_details(agent_id):
    """Detailed analysis of specific agent performance"""
    analyzer = PerformanceAnalyzer(db_interface)
    details = analyzer.analyze_agent_details(agent_id)
    display_agent_details(details)

# Integration with existing commands
@main.command()
@click.option('--with-evolution', is_flag=True, help='Enable evolution during gameplay')
def play(with_evolution):
    """Enhanced play command with optional evolution"""
    if with_evolution:
        # Use agent-driven gameplay
        coordinator = OuroborosCoordinator(db_interface)
        coordinator.run_agent_gameplay_session()
    else:
        # Use existing gameplay logic
        run_existing_gameplay()
```

## Autonomous Operation Protocol

### Claude Code Operating Procedure

**1. System Initialization**
```python
def initialize_ouroboros_system():
    """Claude Code initializes the complete Ouroboros system"""

    # Set environment variables
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    # Initialize database with extended schema
    db = DatabaseInterface()
    db.initialize_ouroboros_schema()

    # Create initial agent population
    coordinator = OuroborosCoordinator(db)
    coordinator.create_initial_population()

    # Begin autonomous operation
    coordinator.run_autonomous_evolution()
```

**2. Continuous Evolution Loop**
```python
def run_autonomous_evolution(self):
    """Main loop - Claude Code operates autonomously"""

    cycle_count = 0
    while True:
        cycle_count += 1

        # 1. Analyze current state
        performance_data = self.performance_analyzer.analyze_population_performance()

        # 2. Make strategic decisions
        strategy = self._determine_evolution_strategy(performance_data)

        # 3. Execute evolution
        new_generation = self.evolution_engine.evolve_population(strategy)

        # 4. Deploy for testing
        test_results = self._test_generation_with_arc(new_generation)

        # 5. Update database with all results
        self._store_cycle_results(cycle_count, strategy, test_results)

        # 6. Self-assessment and adjustment
        self._assess_system_health()

        # 7. Optional pause or continue based on performance
        if self._should_pause_evolution(test_results):
            self._log_pause_decision()
            break
```

**3. Decision Making Framework**
```python
def _determine_evolution_strategy(self, performance_data):
    """Claude Code analyzes data and makes strategic decisions"""

    # Analyze population health
    if performance_data['population_stats']['average_win_rate'] < 0.1:
        strategy_focus = 'exploration'  # Need more diverse strategies
    elif performance_data['diversity_metrics']['genetic_diversity'] < 0.3:
        strategy_focus = 'diversification'  # Population too homogeneous
    elif performance_data['performance_trends']['improvement_rate'] > 0.05:
        strategy_focus = 'exploitation'  # Good strategies, refine them
    else:
        strategy_focus = 'balanced'  # Maintain current approach

    # Determine specific evolution parameters
    evolution_strategy = {
        'focus': strategy_focus,
        'mutation_rate': self._calculate_optimal_mutation_rate(performance_data),
        'crossover_rate': self._calculate_optimal_crossover_rate(performance_data),
        'selection_pressure': self._calculate_selection_pressure(performance_data),
        'population_adjustments': self._determine_population_adjustments(performance_data)
    }

    # Store decision reasoning in database
    self.db.store_evolution_decision(evolution_strategy, performance_data)

    return evolution_strategy
```

## Success Metrics and Monitoring

### Performance Indicators

**Primary Metrics (ARC-Native):**
- Population average win rate improvement
- Best individual agent win rate
- Score efficiency trends (score per action)
- Level progression detection rates
- Consistency across multiple games

**System Health Metrics:**
- Population genetic diversity
- Evolution cycle completion time
- Database performance and integrity
- API interaction success rates
- Memory usage and system stability

**Claude Code Decision Quality:**
- Decision-to-improvement correlation
- Strategy effectiveness validation
- Prediction accuracy for evolution outcomes
- System self-correction frequency

### Monitoring and Alerts

```python
def _assess_system_health(self):
    """Claude Code monitors system health autonomously"""

    health_metrics = {
        'database_performance': self._check_database_performance(),
        'api_success_rate': self._check_arc_api_health(),
        'evolution_effectiveness': self._check_evolution_progress(),
        'memory_usage': self._check_system_resources(),
        'population_health': self._check_population_diversity()
    }

    # Store health assessment
    self.db.store_system_health_assessment(health_metrics)

    # Take corrective action if needed
    if any(metric['status'] == 'critical' for metric in health_metrics.values()):
        self._initiate_system_recovery()

    return health_metrics
```

## Conclusion

This implementation transforms the existing BitterTruth-AI codebase into a fully autonomous Ouroboros system with Claude Code as the central coordinator. The system operates according to strict rules ensuring database-only storage, real ARC data usage, and clean code integration.

**Key Features:**
- **Autonomous Operation**: Claude Code manages everything without human intervention
- **ARC-Native Evolution**: Evolution driven entirely by real ARC game performance
- **Database-First**: All data, decisions, and results stored in SQLite database
- **Clean Integration**: Enhances existing code rather than replacing it
- **Real Data Only**: No test files, simulations, or mock data
- **Self-Management**: System monitors and adjusts itself based on performance

**Implementation Priority:**
1. Database schema extension
2. Core coordinator and evolution engine
3. Integration with existing gameplay engine
4. ARC RLVR framework implementation
5. Performance monitoring and health assessment
6. Autonomous operation deployment

The result is a self-evolving AI system that continuously improves ARC AGI 3 performance through verifiable evolutionary processes, with Claude Code serving as the intelligent coordinator ensuring optimal operation and continuous improvement.