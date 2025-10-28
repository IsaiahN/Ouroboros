"""
AUTONOMOUS EVOLUTION AUTOMATION - QUICK REFERENCE
==================================================

The entire evolution process is now fully automated!

WHAT WAS CREATED:
-----------------
1. autonomous_evolution_runner.py - Core autonomous runner with full lifecycle management
2. run_evolution.py - Simple wrapper with preset modes
3. AUTOMATION_GUIDE.md - Complete documentation

HOW TO USE:
-----------

### SIMPLEST WAY (Just run this!)
```bash
python run_evolution.py
```

### DIFFERENT MODES
```bash
python run_evolution.py --fast       # Quick 30min cycles
python run_evolution.py --thorough   # Deep 90min cycles  
python run_evolution.py --quick      # 5 generation test
```

### ADVANCED CONTROL
```bash
python autonomous_evolution_runner.py \
    --population 15 \
    --games-per-gen 30 \
    --evolution-interval 45 \
    --max-generations 100 \
    --target-win-rate 0.60
```

WHAT IT DOES AUTOMATICALLY:
----------------------------
✓ Creates initial population (if needed)
✓ Runs evaluation games with real ARC API
✓ Analyzes performance after each cycle
✓ Evolves new generations based on results
✓ Monitors system health
✓ Handles errors gracefully
✓ Provides status updates
✓ Stops when target reached or max generations

STOPPING:
---------
Press Ctrl+C anytime for graceful shutdown with final summary

RESUMING:
---------
Just run the same command again - picks up where it left off!

MONITORING:
-----------
While running, check progress in another terminal:
```bash
python check_game_results.py
python performance_analyzer.py --analyze-population
python check_db.py
```

EXPECTED TIMELINE:
------------------
Standard Mode: 24-48 hours to 30-40% win rate
Fast Mode: 6-12 hours to 20-30% win rate  
Thorough Mode: 24-36 hours to 40-50% win rate

DATABASE:
---------
All data stored in core_data.db (Rule 2)
Auto-cleanup keeps size manageable
Typical size: 100-500 MB for full evolution run

RULE COMPLIANCE:
----------------
✓ Rule 1: PYTHONDONTWRITEBYTECODE=1 always set
✓ Rule 2: All data in database, no log files
✓ Rule 4: Claude Code autonomous coordination
✓ Rule 5: No test files - real games only
✓ Rule 6: No simulated games - real ARC API
✓ Rule 7: Real actions tracked and verified
✓ Rule 10: Pattern learning integrated

TROUBLESHOOTING:
----------------
Won't start? Check .env has valid ARC_API_KEY
Stuck at 0%? Normal - keep running, needs 50+ games
Database large? Auto-cleanup should handle it
Too slow? Use --fast mode
Bad data? Use --thorough mode

EXAMPLE OUTPUT:
---------------
🧬 AUTONOMOUS EVOLUTION RUNNER
================================================================================
Started: 2025-10-28 14:30:00
Initial Population: 10 agents
Games per Generation: 20
Max Generations: 50
Target Win Rate: 50.0%
Evolution Interval: 60 minutes
================================================================================

🚀 Starting autonomous evolution...
Press Ctrl+C to stop

🔄 EVOLUTION CYCLE #1
🎮 Running 20 evaluation games...
✓ Completed 20 games - Wins: 2/20 (10.0%)

📊 STATUS UPDATE - Generation 1
Runtime: 1.2 hours
Total Games: 40
Active Agents: 18
Win Rate: 10.00%
Avg Score: 35.50
Games/Hour: 33.3

🧬 Evolving Generation 2...
✓ Evolution complete - Created 8 new agents

... continues automatically until target or max generations ...

READY TO START:
---------------
python run_evolution.py

That's it! The system handles the rest autonomously! 🚀
"""

print(__doc__)
