# Action Limits Configuration

## Current Status

### ✅ Max Actions Per Level: IMPLEMENTED

The system respects max actions per level in `core_gameplay.py`:

**Default Configuration:**
```python
'max_actions_per_level': 100  # Max actions PER LEVEL
'max_actions_per_game': 1000  # Max actions TOTAL (across all levels)
```

**How It Works:**
- Each game can have multiple levels
- Each level has its own action counter
- When `max_actions_per_level` is reached:
  - Level times out
  - Game moves to next level (if available)
  - Or game ends if no more levels

### Example from `start_evolution.py`:

```python
# Configure engine before playing
max_actions = random.randint(200, 300)

engine.configure(
    strategy='balanced',
    max_actions_per_game=max_actions,     # Total limit
    max_actions_per_level=100,            # Per-level limit (optional)
    enable_random_exploration=True
)

# Play game - will respect both limits
result = await engine.play_single_game(game_id)
```

## Configuration Options

### Per-Level Limit (Default: 100)
Controls how many actions before a level times out:

```python
engine.configure(max_actions_per_level=50)   # Faster, less thorough
engine.configure(max_actions_per_level=150)  # Slower, more exploration
engine.configure(max_actions_per_level=200)  # Very thorough per level
```

### Total Game Limit (Default: 1000)
Controls total actions across all levels:

```python
engine.configure(max_actions_per_game=100)   # Quick evaluation
engine.configure(max_actions_per_game=300)   # Standard (start_evolution.py)
engine.configure(max_actions_per_game=1000)  # Deep exploration
```

## Recommendations for Evolution

### Fast Evaluation (Quick testing)
```python
engine.configure(
    max_actions_per_level=50,
    max_actions_per_game=100
)
```
- 2-3 levels max per game
- Fast feedback for evolution
- Good for initial generations

### Standard Evaluation (Balanced)
```python
engine.configure(
    max_actions_per_level=100,  # Default
    max_actions_per_game=300    # What start_evolution.py uses
)
```
- 3-4 levels per game
- Good balance of speed and thoroughness
- Recommended for most evolution cycles

### Deep Evaluation (Thorough)
```python
engine.configure(
    max_actions_per_level=150,
    max_actions_per_game=500
)
```
- 3-4 levels per game
- More exploration per level
- Better for later generations

### Full Evaluation (Maximum effort)
```python
engine.configure(
    max_actions_per_level=200,
    max_actions_per_game=1000
)
```
- 5+ levels per game
- Maximum exploration
- Use for final evaluation of best agents

## Why This Matters for Evolution

### Level Progression = Skill Indicator
- Agents that complete levels show real skill
- Not just random luck
- Level progression tracked in database:
  ```python
  'level_completions': <count>
  'level_progressions_detected': <count>
  ```

### Action Efficiency = Fitness Metric
- Score per action matters
- Agents that win quickly are better
- Evolution favors efficient agents:
  ```python
  score_efficiency = final_score / actions_taken
  ```

### Multi-Level Games = Better Data
- Single level: Hard to differentiate agents
- Multiple levels: Clear skill progression
- More data points for evolution

## Current Implementation Status

### ✅ Working in `start_evolution.py`
```python
max_actions = random.randint(200, 300)
engine.configure(max_actions_per_game=max_actions)
```

### ⚠️ Needs Update in `autonomous_evolution_runner.py`

The autonomous runner currently has placeholder methods:
```python
# This doesn't actually exist yet:
results = await self.coordinator.run_evaluation_cycle(
    games_per_agent=num_games // max(self.db.get_active_agent_count(), 1)
)
```

**Should be implemented similar to `start_evolution.py`:**
```python
async with GameplayEngine(api_key, db_path=db.db_path) as engine:
    # Configure action limits
    engine.configure(
        max_actions_per_level=100,
        max_actions_per_game=300,
        strategy='balanced'
    )
    
    # Play games
    for game in available_games:
        result = await engine.play_single_game(game['id'])
        # Process results...
```

## Recommended Configuration for Autonomous Runner

When `autonomous_evolution_runner.py` is fully implemented:

### Early Generations (0-10)
```python
max_actions_per_level=50    # Fast evaluation
max_actions_per_game=150    # Quick cycles
```

### Middle Generations (10-30)
```python
max_actions_per_level=100   # Standard
max_actions_per_game=300    # Balanced
```

### Late Generations (30+)
```python
max_actions_per_level=150   # Thorough
max_actions_per_game=500    # Deep evaluation
```

### Adaptive Configuration
The runner could adjust based on population performance:
```python
if average_win_rate < 0.05:
    # Early stage - fast iterations
    max_actions_per_level = 50
    max_actions_per_game = 150
elif average_win_rate < 0.20:
    # Improving - standard evaluation
    max_actions_per_level = 100
    max_actions_per_game = 300
else:
    # Advanced - thorough evaluation
    max_actions_per_level = 150
    max_actions_per_game = 500
```

## Summary

✅ **YES** - The system respects max actions per level (default: 100)  
✅ **YES** - Configurable via `engine.configure()`  
✅ **YES** - Currently working in `start_evolution.py`  
⚠️ **NEEDS IMPLEMENTATION** - In `autonomous_evolution_runner.py`  

**The core system is ready, the autonomous runner needs the actual GameplayEngine integration!**
