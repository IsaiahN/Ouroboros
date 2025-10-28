# Autonomous Evolution Runner - Real GameplayEngine Integration

## ✅ COMPLETED: No More Fake Gameplay

The `autonomous_evolution_runner.py` has been updated to use **REAL** ARC AGI 3 API calls following all Ouroboros rules.

## Key Changes Made

### 1. Real GameplayEngine Integration
- ✅ Imported `GameplayEngine` from `core_gameplay.py`
- ✅ Uses `async with GameplayEngine(api_key, db_path)` for real game sessions
- ✅ Calls `engine.play_single_game(game_id)` for actual ARC API interactions
- ✅ No mock data, no simulated games - 100% real

### 2. Max Actions Per Level = 200 (As Requested)
```python
engine.configure(
    strategy='balanced',
    max_actions_per_level=200,  # ✅ SET TO 200
    max_actions_per_game=max_actions,
    enable_random_exploration=True,
    enable_pattern_learning=True
)
```

### 3. Real Agent Creation
- ✅ Uses `AgentFactory.create_agent()` with real genomes
- ✅ Creates 4 agent types: pattern_specialist, score_optimizer, exploration_agent, win_focused_agent
- ✅ Random genome initialization with proper parameters

### 4. Real Evolution Using EvolutionaryEngine
- ✅ Uses `CrossoverOperations.crossover_genomes()` for breeding
- ✅ Uses `MutationStrategies.mutate_genome()` for mutations
- ✅ Adaptive strategy: exploration → diversification → exploitation
- ✅ Prunes worst performers when population grows too large

### 5. Real ARC Rewards Processing
- ✅ Uses `ARCRLVRFramework.process_arc_rewards()` after each game
- ✅ Stores agent performance in database
- ✅ Uses `PerformanceAnalyzer` for population analysis

## Compliance with Ouroboros Rules

### ✅ Rule 1: No Pycache
- Environment variable set: `PYTHONDONTWRITEBYTECODE=1`

### ✅ Rule 2: Database-Only Storage
- All game results stored in database
- Uses `DatabaseLogHandler` for logging
- No file-based logging

### ✅ Rule 3: No Orphaned Code
- Removed all placeholder `coordinator.create_initial_population()` calls
- Removed all placeholder `coordinator.run_evaluation_cycle()` calls
- Removed all placeholder `coordinator.evolve_population()` calls
- Clean integration with existing components

### ✅ Rule 4: LLM Self-Management
- Autonomous decision making in `analyze_and_evolve()`
- Strategy focus determined by performance analysis
- Evolution continues without human intervention

### ✅ Rule 5: No Test Files
- Uses real ARC games from API
- No mock or test data

### ✅ Rule 6: No Simulated Games
- All games use real ARC AGI 3 API
- API endpoint: `https://three.arcprize.org/api/`

### ✅ Rule 7: Real Actions Only
- Every action sent to real ARC API via `GameplayEngine`
- Action tracking in `arc_action_tracking` table
- Verifiable API requests and responses

### ✅ Rule 8: Max Actions Per Level = 200
- Set explicitly in `engine.configure(max_actions_per_level=200)`
- Enforced by `core_gameplay.py`

## Method Implementations

### `initialize_population()` - REAL
```python
- Creates agents using AgentFactory.create_agent()
- Random genomes with proper ARC-relevant parameters
- Stores in database immediately
- No fake data
```

### `run_evaluation_games()` - REAL
```python
- Gets active agents from database
- Uses GameplayEngine(api_key) for real games
- Calls await engine.play_single_game(game_id)
- Processes ARC rewards via ARCRLVRFramework
- Stores all results in database
- Returns real statistics
```

### `analyze_and_evolve()` - REAL
```python
- Uses PerformanceAnalyzer.analyze_population_performance()
- Selects breeding pairs from top performers
- Crossover using CrossoverOperations.crossover_genomes()
- Mutation using MutationStrategies.mutate_genome()
- Creates new agents via AgentFactory
- Prunes worst performers when needed
```

## Running the System

### Quick Start
```powershell
# Run with defaults (10 agents, 20 games/gen, 50 generations)
python run_evolution.py

# Quick test (5 agents, 10 games/gen, 10 generations)
python run_evolution.py --mode quick

# Thorough evolution (20 agents, 50 games/gen, 100 generations)
python run_evolution.py --mode thorough
```

### Direct Usage
```powershell
python -c "import asyncio; from autonomous_evolution_runner import AutonomousEvolutionRunner; runner = AutonomousEvolutionRunner(initial_population_size=10, games_per_generation=20, max_generations=50); asyncio.run(runner.run())"
```

### With Custom Parameters
```python
from autonomous_evolution_runner import AutonomousEvolutionRunner
import asyncio

runner = AutonomousEvolutionRunner(
    db_path="core_data.db",
    initial_population_size=15,      # Start with 15 agents
    games_per_generation=30,         # 30 games per generation
    max_generations=100,             # Up to 100 generations
    target_win_rate=0.50,           # Stop at 50% win rate
    evolution_interval_minutes=60,   # Evolve every hour
    health_check_interval=10        # Health check every 10 games
)

asyncio.run(runner.run())
```

## Verification

### Check Real Actions Being Sent
```python
from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check recent actions sent to API
recent_actions = db.execute_query("""
    SELECT action_type, coordinate_x, coordinate_y,
           api_request_sent, api_response_received,
           action_accepted, error_message
    FROM arc_action_tracking 
    WHERE action_timestamp > datetime('now', '-1 hour')
    ORDER BY action_timestamp DESC
    LIMIT 20
""")

print(f"Actions sent to API: {len(recent_actions)}")
for action in recent_actions:
    print(f"  {action['action_type']} @ ({action['coordinate_x']}, {action['coordinate_y']}) - "
          f"Sent: {action['api_request_sent']}, Received: {action['api_response_received']}")
```

### Check Game Results
```python
# Verify real game results
game_results = db.execute_query("""
    SELECT game_id, final_score, win_achieved, actions_taken
    FROM game_results 
    ORDER BY game_end_time DESC 
    LIMIT 10
""")

print(f"Recent games: {len(game_results)}")
for game in game_results:
    print(f"  Game {game['game_id']}: Score {game['final_score']}, "
          f"Win: {game['win_achieved']}, Actions: {game['actions_taken']}")
```

### Check Agent Performance
```python
# Verify agents are learning
agents = db.execute_query("""
    SELECT agent_id, avg_score_per_game, total_games_won, 
           total_games_played, score_efficiency
    FROM agents 
    WHERE is_active = 1
    ORDER BY avg_score_per_game DESC
""")

print(f"Active agents: {len(agents)}")
for agent in agents:
    win_rate = agent['total_games_won'] / max(agent['total_games_played'], 1)
    print(f"  {agent['agent_id']}: Avg Score {agent['avg_score_per_game']:.2f}, "
          f"Win Rate {win_rate:.1%}, Efficiency {agent['score_efficiency']:.3f}")
```

## What Was Removed (Fake Code)

### ❌ REMOVED: Placeholder Coordinator Methods
```python
# OLD FAKE CODE - REMOVED
await self.coordinator.create_initial_population(population_size=10)
await self.coordinator.run_evaluation_cycle(games_per_agent=2)
await self.coordinator.evolve_population(generation=1, performance_data={})
```

### ✅ REPLACED WITH: Real Implementations
```python
# NEW REAL CODE
- AgentFactory.create_agent() for agent creation
- GameplayEngine.play_single_game() for real games
- CrossoverOperations.crossover_genomes() for breeding
- MutationStrategies.mutate_genome() for mutations
```

## Monitoring

### Watch Live Progress
```powershell
# The runner prints real-time status:
# - Agent creation progress
# - Game-by-game results (score, actions, duration)
# - Population statistics
# - Evolution decisions
# - Health checks
```

### Database Monitoring
```python
# Monitor database growth (real data accumulating)
import os
db_size_mb = os.path.getsize("core_data.db") / (1024 * 1024)
print(f"Database size: {db_size_mb:.2f} MB")

# Check log count
stats = db.get_database_stats()
print(f"System logs: {stats['system_logs_count']}")
print(f"Game results: {stats['game_results_count']}")
```

## Summary

**NO MORE FAKE GAMEPLAY!**

Every operation now uses:
- ✅ Real ARC AGI 3 API calls
- ✅ Real GameplayEngine
- ✅ Real agent genomes
- ✅ Real evolution (crossover + mutation)
- ✅ Real performance analysis
- ✅ Real database storage

**Max actions per level: 200** (as requested)

The system is now **production-ready** for autonomous evolution with real ARC games.
