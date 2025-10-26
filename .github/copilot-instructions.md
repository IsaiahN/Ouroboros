# GitHub Copilot Instructions for BitterTruth-AI Ouroboros System

**Project**: BitterTruth-AI - Autonomous ARC AGI 3 Evolution System
**Coordinator**: Claude Code as autonomous LLM coordinator

## Critical Operating Rules

These rules are non-negotiable and must be followed at all times when working on this codebase.

### Rule 1: Always Disable Pycache
- Set `PYTHONDONTWRITEBYTECODE=1` in all environments
- Never allow .pyc files to be generated
- Keep Python environment clean
- All scripts must set this environment variable before executing Python code

### Rule 2: Database-Only Storage
- ALL data stored in SQLite database, never use log files
- Never create .log files or any file-based logging
- Every operation, decision, and result goes into database tables
- If existing code uses file logging, convert to database storage
- Use `database_logger.py` with `DatabaseLogHandler` for all logging needs

### Rule 3: No Orphaned Code
- Never leave old code behind when making changes
- Properly delete, move, or integrate all existing functionality
- Clean integration means enhancing existing files, not replacing them
- Every line of old code must be accounted for
- When refactoring, ensure all references are updated

### Rule 4: LLM Self-Management
- Claude Code manages the entire system autonomously
- All evolutionary decisions made by Claude Code analyzing database data
- System designed to run without human intervention once started
- Claude Code coordinates all agents, evolution, and optimization
- Autonomous operation is the primary design goal

### Rule 5: No Test Files
- **Never create test files - waste of LLM tokens**
- Always test with live ARC AGI 3 data
- Use real game results for all validation and testing
- Run actual games instead of creating test scripts
- If verification is needed, use the existing CLI commands with real data

### Rule 6: No Simulated Games
- Never create simulated or mock ARC games
- Always use real ARC AGI 3 API calls
- Waste of time and tokens to generate fake game data
- All game interactions must go through the real API at https://three.arcprize.org
- No mock responses or fake game states

### Rule 7: Real Actions Only
- Always verify that real actions are being sent to ARC games
- Monitor API calls to ensure actual game interaction
- Never substitute mock or simulated actions
- All ACTION1-ACTION7 commands must be sent to the real ARC API
- Track API responses to verify actions were received and processed

## Rule 8: 
Whenever creating an implementation or change, Test the new implementation on the current main active fun script, and then scan the terminal for errors, bugs, and anything else and then fix the issue and rescan, retest etc. you should automatically start and stop the terminal runs etc. until you can get a clean verifiable run with actions sent, and scores updated, and real scorecard ids etc.

### Rule 9: Dont create summary md files unless asked

## Architecture Guidelines

### Database-First Design
- All state stored in `core_data.db` SQLite database
- Use `database_interface.py` for all database operations
- Extended Ouroboros schema in `ouroboros_database_extension.sql`
- No file-based persistence except database file itself

### Integration Philosophy
- Enhance existing files rather than creating new ones
- Use existing `GameplayEngine`, `ActionHandler`, `GameSessionManager`
- Extend functionality through callbacks and optional parameters
- Maintain backward compatibility with existing CLI commands

### ARC API Integration
- Base URL: `https://three.arcprize.org`
- All endpoints prefixed with `/api/`
- Use `arc_api_client.py` for all API interactions
- Store API responses in database for analysis

### Autonomous Evolution
- `ouroboros_coordinator.py` is the central orchestrator
- Claude Code makes all evolutionary decisions
- Decisions based on database analysis of real game performance
- No human intervention required once system is started

## Code Style

### Naming Conventions
- Classes: `PascalCase` (e.g., `OuroborosCoordinator`)
- Functions/Methods: `snake_case` (e.g., `run_autonomous_evolution`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_ACTIONS_PER_GAME`)
- Private methods: `_leading_underscore` (e.g., `_determine_evolution_strategy`)

### Documentation
- All classes have comprehensive docstrings
- Methods include Args, Returns, and purpose description
- Complex algorithms have inline comments explaining logic
- Database operations document table and column usage

### Error Handling
- Use try-except blocks for API calls and database operations
- Log errors to database using `DatabaseLogHandler`
- Raise specific exceptions with meaningful messages
- Never silently fail - always log to database

## Key Files and Their Purposes

### Core System Files
- `ouroboros_coordinator.py` - Central LLM coordinator for autonomous operation
- `evolutionary_engine.py` - Handles agent breeding, mutation, selection
- `arc_rlvr_framework.py` - Processes ARC-native rewards for evolution
- `agent_factory.py` - Creates specialized agents with different strategies
- `performance_analyzer.py` - Analyzes ARC performance data for decisions

### Existing Integration Points
- `core_gameplay.py` - Main game loop, enhanced with agent callbacks
- `action_handler.py` - Action execution, extended with evolutionary selection
- `game_session_manager.py` - Session management, tracks agent performance
- `database_interface.py` - Database operations, extended for Ouroboros
- `arc_api_client.py` - ARC API client, all real game interactions

### Database Files
- `core_database_schema.sql` - Original schema for game tracking
- `ouroboros_database_extension.sql` - Extended schema for evolution system
- `database_logger.py` - Database-based logging system
- `core_data.db` - SQLite database file (created at runtime)

## Development Workflow

1. **Always start with database**: Plan database schema changes first
2. **Enhance, don't replace**: Modify existing files rather than creating new ones
3. **Test with real data**: Use actual ARC games, never create test files
4. **Store everything**: All results, decisions, and actions go in database
5. **Verify real actions**: Check that API calls are actually being made

## Common Tasks

### Adding New Functionality
1. Determine which existing file to enhance
2. Design database schema for new data
3. Implement functionality using existing patterns
4. Test with real ARC games
5. Store all results in database

### Debugging Issues
1. Query database for relevant data
2. Check system_logs table for error messages
3. Verify API calls in arc_action_tracking table
4. Analyze agent_arc_performance for game results
5. Never create debug test files - use real games

### Running Evolution
```bash
# Start autonomous evolution (Claude Code coordinates)
python start_evolution.py

# Run games for agent evaluation
python run_continuous_games.py --games 10

# Check database for results
python -c "from database_interface import DatabaseInterface; db = DatabaseInterface(); print(db.get_agents())"
```

## Ouroboros System Operation (Post-Implementation)

### Evolution Commands

Once the Ouroboros system is fully implemented, use these commands:

```bash
# Start autonomous evolution cycles
python ouroboros_coordinator.py --generations 10 --population-size 20

# Analyze current population performance
python performance_analyzer.py --analyze-population

# View specific agent details
python performance_analyzer.py --agent-id <agent_id>

# Run agent-driven gameplay session
python core_gameplay.py --with-evolution --agent-id <agent_id>

# Check system health
python ouroboros_coordinator.py --health-check
```

### Database Queries for Analysis

Query the database to understand system state:

```python
# Get all active agents
from database_interface import DatabaseInterface
db = DatabaseInterface()
agents = db.execute_query("SELECT * FROM agents WHERE is_active = TRUE")

# Check recent evolution decisions
decisions = db.execute_query("""
    SELECT * FROM claude_evolution_decisions 
    ORDER BY decision_timestamp DESC 
    LIMIT 10
""")

# View top performing agents
top_agents = db.execute_query("""
    SELECT agent_id, avg_score_per_game, total_games_won, score_efficiency
    FROM agents 
    WHERE is_active = TRUE
    ORDER BY avg_score_per_game DESC 
    LIMIT 10
""")

# Analyze population health
health = db.execute_query("""
    SELECT * FROM population_health_metrics 
    ORDER BY measurement_timestamp DESC 
    LIMIT 1
""")

# Track real actions being sent to API
actions = db.execute_query("""
    SELECT * FROM arc_action_tracking 
    WHERE api_request_sent = TRUE 
    ORDER BY action_timestamp DESC 
    LIMIT 20
""")
```

### Key System Components

**Core Files (Post-Implementation):**
- `ouroboros_coordinator.py` - Central LLM coordinator, autonomous operation
- `evolutionary_engine.py` - Agent breeding, mutation, selection
- `arc_rlvr_framework.py` - ARC-native reward processing
- `agent_factory.py` - Creates specialized agent types
- `performance_analyzer.py` - Population performance analysis

**Agent Types:**
- `pattern_specialist` - Focuses on ARC pattern recognition
- `score_optimizer` - Maximizes score efficiency
- `exploration_agent` - Explores diverse strategies
- `win_focused_agent` - Prioritizes game wins

**Integration Points:**
- `core_gameplay.py` - Enhanced with agent callbacks and genome-based strategy
- `action_handler.py` - Extended with evolutionary action selection
- `game_session_manager.py` - Tracks agent performance per session
- `database_interface.py` - All Ouroboros tables and operations

### ARC Performance Metrics

**Primary Fitness Calculation:**
```
fitness = (win_rate * 0.7) + (score_efficiency * 0.2) + (consistency * 0.1)
```

**Score Efficiency:**
```
score_efficiency = score_achieved / actions_taken
```

**Win Proximity:**
```
win_proximity = score_achieved / win_score_threshold
```

**Total Evolutionary Reward:**
```
total_reward = base_score + win_bonus(100) + efficiency_bonus + proximity_bonus + level_bonus(10/level)
```

### Evolution Strategy Focus

Claude Code determines strategy based on population analysis:

- **Exploration** - Average win rate < 10%, need diverse strategies
- **Diversification** - Genetic diversity < 30%, population too homogeneous  
- **Exploitation** - Improvement rate > 5%, refine successful strategies
- **Balanced** - Default, maintain current approach

### Monitoring System Health

**Critical Health Indicators:**
- Database performance and integrity
- API interaction success rates (Rule 7 compliance)
- Population genetic diversity
- Evolution cycle effectiveness
- Memory usage and system stability

**When System Health is Critical:**
- Claude Code initiates automatic system recovery
- Stores recovery actions in `system_logs` table
- Adjusts evolution parameters to stabilize population
- May pause evolution cycles until health restored

### Real Action Verification (Rule 7)

Always verify real actions are being sent to ARC API:

```python
# Check arc_action_tracking table
recent_actions = db.execute_query("""
    SELECT action_type, coordinate_x, coordinate_y,
           api_request_sent, api_response_received,
           action_accepted, error_message
    FROM arc_action_tracking 
    WHERE action_timestamp > datetime('now', '-1 hour')
    ORDER BY action_timestamp DESC
""")

# Verify API success rate
api_health = db.execute_query("""
    SELECT 
        COUNT(*) as total_actions,
        SUM(CASE WHEN api_request_sent THEN 1 ELSE 0 END) as requests_sent,
        SUM(CASE WHEN api_response_received THEN 1 ELSE 0 END) as responses_received,
        SUM(CASE WHEN action_accepted THEN 1 ELSE 0 END) as actions_accepted
    FROM arc_action_tracking
    WHERE action_timestamp > datetime('now', '-1 hour')
""")
```

### Claude Code Memory System

The system maintains learning memory in `claude_memory` table:

**Memory Types:**
- `successful_strategy` - Strategies that achieved high performance
- `failed_approach` - Approaches that performed poorly
- `pattern_discovery` - Patterns observed in ARC game behavior

**Memory Validation:**
- `verified` - Confirmed by multiple game sessions
- `contradicted` - Contradicted by new evidence
- `unverified` - Not yet validated

Query recent memories:
```python
memories = db.execute_query("""
    SELECT memory_type, content, relevance_score, validation_status
    FROM claude_memory 
    ORDER BY created_at DESC 
    LIMIT 20
""")
```

### Debugging and Troubleshooting

**If evolution stalls:**
1. Check `population_health_metrics` for stagnation_indicator
2. Review `claude_evolution_decisions` for strategy focus
3. Increase mutation_rate or change to 'exploration' focus
4. Query `agent_arc_performance` for performance trends

**If API errors increase:**
1. Check `arc_action_tracking` for error_message patterns
2. Verify `coordinate_valid` field (must be TRUE for ACTION6)
3. Ensure api_request_sent and api_response_received are TRUE
4. Review system_logs for API client errors

**If no games being played:**
1. Verify agents exist: `SELECT COUNT(*) FROM agents WHERE is_active = TRUE`
2. Check game results: `SELECT * FROM game_results ORDER BY game_end_time DESC LIMIT 10`
3. Review coordinator logs in system_logs table
4. Ensure coordinator loop is running with proper database connection

## Remember

- **No test files** - Use real ARC games
- **Database only** - No file logging
- **Real actions** - Verify API calls in arc_action_tracking table
- **Clean integration** - Enhance existing code
- **Autonomous design** - Claude Code coordinates everything
- **Agent-driven** - All gameplay uses agent genomes and callbacks
- **Fitness = ARC performance** - 70% win rate, 20% efficiency, 10% consistency
- **Monitor health** - Check population_health_metrics regularly
- **Verify actions** - Always confirm API requests/responses in database

These rules ensure the system operates efficiently, uses tokens wisely, and maintains clean, verifiable operation with real ARC AGI 3 data.
