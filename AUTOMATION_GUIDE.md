# Autonomous Evolution System - User Guide

## Overview

The autonomous evolution system automates the entire lifecycle of evolving AI agents to play ARC AGI 3 games. It handles:

1. ✅ **Population Initialization** - Creates diverse agents with random strategies
2. ✅ **Game Evaluation** - Runs real ARC games to test performance
3. ✅ **Performance Analysis** - Analyzes which strategies work best
4. ✅ **Evolution** - Breeds better agents from successful parents
5. ✅ **Continuous Improvement** - Repeats until target achieved

## Quick Start

### Option 1: Simplest Way (Recommended)

```bash
# Just run this - it handles everything!
python run_evolution.py
```

That's it! The system will:
- Create 10 initial agents if none exist
- Run 20 games per evolution cycle
- Evolve every 60 minutes
- Continue until 50% win rate or 50 generations

### Option 2: Different Modes

```bash
# Fast mode: Quick iterations, less thorough
python run_evolution.py --fast

# Thorough mode: More games per cycle, better data
python run_evolution.py --thorough

# Quick test: Just 5 generations to see it work
python run_evolution.py --quick
```

### Option 3: Custom Configuration

```bash
# Full control over all parameters
python autonomous_evolution_runner.py \
    --population 15 \
    --games-per-gen 30 \
    --evolution-interval 45 \
    --max-generations 100 \
    --target-win-rate 0.60
```

## What Happens When You Run It

### Phase 1: Initialization (First Run Only)
```
🧬 Creating initial population (10 agents)...
  Agent 1/10: pattern_specialist - gen0_agent_0
  Agent 2/10: score_optimizer - gen0_agent_1
  ...
✓ Created 10 agents
```

### Phase 2: Evaluation Games
```
🎮 Running 20 evaluation games...
  Game 1: lp85-d265526edbaa (100 actions)
    Score: 0.0, Actions: 100, Duration: 14.1s
  ...
✓ Completed 20 games
  Wins: 0/20 (0.0%)
  Avg Score: 0.00
```

### Phase 3: Performance Analysis
```
🧠 Analyzing population performance...
  Population: 10 agents
  Avg Win Rate: 0.00%
  Best Win Rate: 0.00%
```

### Phase 4: Evolution
```
🧬 Evolving Generation 1...
  Selected 2 parents for breeding
  Created 5 offspring through crossover
  Applied 3 mutations for diversity
✓ Evolution complete - Created 8 new agents
```

### Phase 5: Status Report
```
📊 STATUS UPDATE - Generation 1
================================================================================
Runtime: 1.2 hours
Total Games: 40
Active Agents: 18
Win Rate: 5.00%
Avg Score: 12.50
Games/Hour: 33.3
================================================================================
```

The system repeats Phases 2-5 automatically until:
- Target win rate achieved (default: 50%)
- Max generations reached (default: 50)
- You press Ctrl+C to stop

## Configuration Options

### Simple Mode Presets

| Mode | Population | Games/Gen | Interval | Max Gens | Best For |
|------|-----------|-----------|----------|----------|----------|
| **Standard** (default) | 10 | 20 | 60 min | 50 | Balanced evolution |
| **Fast** | 8 | 10 | 30 min | 30 | Quick iterations |
| **Thorough** | 15 | 50 | 90 min | 20 | High-quality data |
| **Quick Test** | 5 | 10 | 15 min | 5 | Testing/demo |

### Advanced Parameters

```bash
python autonomous_evolution_runner.py \
    --population <int>           # Initial number of agents (default: 10)
    --games-per-gen <int>        # Games per evolution cycle (default: 20)
    --evolution-interval <int>   # Minutes between evolutions (default: 60)
    --max-generations <int>      # Maximum generations (default: 50)
    --target-win-rate <float>    # Win rate target 0.0-1.0 (default: 0.50)
    --db-path <str>              # Database file path (default: core_data.db)
```

## Monitoring Progress

### Real-Time Output

The runner prints status updates after each cycle:

```
📊 STATUS UPDATE - Generation 3
================================================================================
Runtime: 3.5 hours
Total Games: 140
Active Agents: 25
Win Rate: 12.50%
Avg Score: 45.00
Games/Hour: 40.0
================================================================================
```

### Check Database Anytime

While the runner is active, you can check progress in another terminal:

```bash
# View recent games
python check_game_results.py

# Check agent performance
python performance_analyzer.py --analyze-population

# Database size
python -c "import os; s = os.path.getsize('core_data.db'); print(f'DB: {s/1024/1024:.2f} MB')"

# View top agents
python performance_analyzer.py --top-agents 10
```

### System Health Checks

The runner automatically monitors:
- ✓ Active agent count
- ✓ Database size
- ✓ Log count (auto-cleanup at 100K)
- ✓ Games played per hour
- ✓ Evolution progress

If issues are detected, it will print warnings:
```
⚠️  System Health Issues:
  - Database large: 950 MB
  - High log count - cleanup may be needed
```

## Stopping and Resuming

### Graceful Stop

Press `Ctrl+C` to stop gracefully:

```
⏸️  Interrupted by user

📈 FINAL SUMMARY
================================================================================
Total Runtime: 5.50 hours
Total Games: 220
Final Generation: 4
Games/Hour: 40.0

Final Performance:
  Win Rate: 15.00%
  Best Win Rate: 25.00%
  Avg Score: 52.30
  Population: 30 agents

Top 3 Agents:
  1. agent_gen4_abc123: 25.00% win rate, 78.50 avg score
  2. agent_gen3_def456: 20.00% win rate, 65.20 avg score
  3. agent_gen4_ghi789: 18.00% win rate, 60.10 avg score
================================================================================

✓ Autonomous evolution runner stopped
Database: core_data.db

To resume: python autonomous_evolution_runner.py
================================================================================
```

### Resume Later

Just run it again - it picks up where it left off:

```bash
python run_evolution.py
```

Output:
```
✓ Found 30 existing agents, skipping initialization
🚀 Starting autonomous evolution...
```

## Expected Timeline

### Fast Mode (~6-12 hours)
- 30 generations @ 30 min each
- 8 agents, 10 games/gen
- Total: ~300 games
- Expected final win rate: 20-30%

### Standard Mode (~24-48 hours)
- 50 generations @ 60 min each
- 10 agents, 20 games/gen
- Total: ~1000 games
- Expected final win rate: 30-40%

### Thorough Mode (~24-36 hours)
- 20 generations @ 90 min each
- 15 agents, 50 games/gen
- Total: ~1000 games
- Expected final win rate: 40-50%

## Troubleshooting

### Runner Won't Start

```bash
# Check API key
cat .env | grep ARC_API_KEY

# Verify database
python verify_database.py

# Check for errors
python check_errors.py
```

### No Progress / Stuck at 0%

**Cause:** Initial random strategies are all bad

**Solution:** Let it run longer - need 50+ games to see patterns
```bash
# Keep running, it will improve
# Or manually inject better agents
python agent_factory.py --create-smart-agents 5
```

### Database Getting Large

**Cause:** Too many logs

**Solution:** Auto-cleanup should handle it, but you can force:
```bash
# Check size
ls -lh core_data.db

# Manual cleanup if needed
python -c "from database_interface import DatabaseInterface; db = DatabaseInterface(); db.execute_query('DELETE FROM system_logs WHERE timestamp < datetime(\"now\", \"-1 day\")')"

# Vacuum
python -c "from database_interface import DatabaseInterface; db = DatabaseInterface(); db._get_connection().execute('VACUUM')"
```

### Evolution Too Slow

```bash
# Use fast mode
python run_evolution.py --fast

# Or reduce games per generation
python autonomous_evolution_runner.py --games-per-gen 10
```

### Evolution Too Fast / Bad Data

```bash
# Use thorough mode
python run_evolution.py --thorough

# Or increase interval
python autonomous_evolution_runner.py --evolution-interval 120
```

## Under the Hood

The autonomous runner orchestrates these components:

1. **DatabaseInterface** - Stores all data (Rule 2)
2. **OuroborosCoordinator** - Claude Code's autonomous manager (Rule 4)
3. **GameplayEngine** - Runs real ARC games (Rules 6 & 7)
4. **PerformanceAnalyzer** - Analyzes what works
5. **EvolutionaryEngine** - Breeds better agents
6. **ARCRLVRFramework** - ARC-native reward processing

All following Copilot Instructions rules:
- ✓ Rule 1: No pycache
- ✓ Rule 2: Database-only storage
- ✓ Rule 4: LLM self-management
- ✓ Rule 5: No test files
- ✓ Rule 6: No simulated games
- ✓ Rule 7: Real actions only
- ✓ Rule 10: Pattern learning integrated

## Example Session

```bash
$ python run_evolution.py --quick

⚡ QUICK TEST - 5 generations
============================================================
Configuration:
  Initial Population: 5 agents
  Games per Generation: 10
  Evolution Interval: 15 minutes
  Max Generations: 5
  Target Win Rate: 50%
============================================================

🧬 AUTONOMOUS EVOLUTION RUNNER
================================================================================
Started: 2025-10-28 14:30:00
Initial Population: 5 agents
Games per Generation: 10
Max Generations: 5
Target Win Rate: 50.0%
Evolution Interval: 15 minutes
================================================================================

✓ Found 5 existing agents, skipping initialization

🚀 Starting autonomous evolution...
Press Ctrl+C to stop

================================================================================
🔄 EVOLUTION CYCLE #1
================================================================================

🎮 Running 10 evaluation games...
... [games running] ...
✓ Completed 10 games
  Wins: 1/10 (10.0%)
  Avg Score: 25.50

📊 STATUS UPDATE - Generation 0
================================================================================
Runtime: 0.3 hours
Total Games: 10
Active Agents: 5
Win Rate: 10.00%
Avg Score: 25.50
Games/Hour: 33.3
================================================================================

🧠 Analyzing population performance...
  Population: 5 agents
  Avg Win Rate: 10.00%
  Best Win Rate: 20.00%

🧬 Evolving Generation 1...
✓ Evolution complete - Created 4 new agents

... [continues for 5 generations] ...

^C
⏸️  Interrupted by user

📈 FINAL SUMMARY
================================================================================
Total Runtime: 1.50 hours
Total Games: 50
Final Generation: 5
Games/Hour: 33.3

Final Performance:
  Win Rate: 22.00%
  Best Win Rate: 40.00%
  Avg Score: 65.00
  Population: 9 agents

Top 3 Agents:
  1. agent_gen5_a: 40.00% win rate, 95.00 avg score
  2. agent_gen4_b: 30.00% win rate, 78.00 avg score
  3. agent_gen5_c: 25.00% win rate: 70.00 avg score
================================================================================

✓ Autonomous evolution runner stopped
```

## Best Practices

1. **Start with Standard Mode** - Good balance for first run
2. **Let it run overnight** - Evolution takes time
3. **Monitor occasionally** - Check status every few hours
4. **Don't interrupt during games** - Wait for cycle to complete
5. **Back up database periodically** - `cp core_data.db core_data.db.backup`
6. **Check disk space** - Database grows ~100 MB per 1000 games
7. **Use thorough mode for final push** - When close to target

## Success Metrics

After 24-48 hours, you should see:
- ✓ Win rate improving each generation
- ✓ Best agents hitting 20-40% win rate
- ✓ Average score increasing steadily
- ✓ Population size growing to 20-50 agents
- ✓ Genetic diversity maintaining 30-70%

If not seeing progress after 100+ games:
- Check that API is working (real games being played)
- Verify actions are being sent (Rule 7 verification)
- Consider increasing mutation rate
- Try different initial agent types

## Advanced Usage

### Run Multiple Instances

You can run multiple evolution processes with different databases:

```bash
# Terminal 1: Fast exploration
python autonomous_evolution_runner.py --db-path fast_evolution.db --games-per-gen 10

# Terminal 2: Thorough evaluation  
python autonomous_evolution_runner.py --db-path thorough_evolution.db --games-per-gen 50
```

Then compare results and merge best agents!

### Custom Evolution Strategy

Edit `ouroboros_coordinator.py` to adjust:
- Parent selection criteria
- Crossover methods
- Mutation rates
- Fitness calculations

### Integration with Other Tools

The runner works alongside:
```bash
# While runner is active, monitor in another terminal
watch -n 60 'python check_game_results.py | tail -20'

# Real-time log streaming
tail -f <(python -c "from database_logger import get_recent_logs; logs = get_recent_logs(limit=50); [print(l) for l in logs]")
```

---

**Ready to evolve?**

```bash
python run_evolution.py
```

Let the autonomous evolution begin! 🧬🚀
