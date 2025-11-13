"""
HARDCODED LIMITS AUDIT - BitterTruth-AI Ouroboros System

Found hardcoded limits and recommendations for adaptive scaling:

═══════════════════════════════════════════════════════════════════════════════
CRITICAL: NEEDS ADAPTIVE SCALING
═══════════════════════════════════════════════════════════════════════════════

1. ❌ games_per_generation = 20 (autonomous_evolution_runner.py line 72)
   PROBLEM: Fixed 20 games per generation regardless of population size
   SOLUTION: Scale with population - games_per_generation = TARGET_POPULATION
   IMPACT: High - affects evolution throughput and agent evaluation
   
   Recommendation:
   - Small population (60 agents): 60 games/generation (full coverage)
   - Large population (1000 agents): 1000 games/generation (full coverage)
   - Ensures every agent gets evaluated roughly once per generation


2. ❌ initial_population_size = 10 (autonomous_evolution_runner.py line 71)
   PROBLEM: Always starts with 10 agents regardless of available games
   SOLUTION: Scale with game types - initial_pop = len(game_types) * 2
   IMPACT: Medium - affects startup population diversity
   
   Recommendation:
   - 6 game types: 12 initial agents (2 per type)
   - 50 game types: 100 initial agents (2 per type)
   - Ensures each game type has specialists from start


═══════════════════════════════════════════════════════════════════════════════
IMPORTANT: CONSIDER ADAPTIVE SCALING
═══════════════════════════════════════════════════════════════════════════════

3. ⚠️ Adaptive Action Limits (adaptive_action_limits.py)
   Current: MIN_ACTIONS_PER_LEVEL = 200, MAX = 3000
   Current: MIN_TOTAL_ACTIONS = 1000, MAX = 10000
   PROBLEM: Fixed ranges may not suit all game complexities
   SOLUTION: Could scale based on game difficulty metrics
   IMPACT: Low-Medium - affects game completion rates
   
   Current system already adapts within these ranges based on performance.
   These are safety bounds to prevent runaway action counts.
   ✅ ACCEPTABLE AS-IS for now


4. ⚠️ max_repeats_per_game = 5 (autonomous_evolution_runner.py line 906)
   PROBLEM: Fixed limit in diversity mode
   SOLUTION: Could scale with game difficulty or population
   IMPACT: Low - only affects diversity mode (agi_mode)
   
   ✅ ACCEPTABLE AS-IS - prevents game spamming


═══════════════════════════════════════════════════════════════════════════════
ACCEPTABLE: REASONABLE FIXED LIMITS
═══════════════════════════════════════════════════════════════════════════════

5. ✅ NO_PROGRESS_RESET_THRESHOLD = 1000 (core_gameplay.py line 245)
   Purpose: Hard reset after 1000 no-progress actions
   ✅ REASONABLE - Safety limit to prevent infinite loops
   

6. ✅ API_RESET_THRESHOLD = 1000 (core_gameplay.py line 250)
   Purpose: API reset after 1000 no-progress actions (optimizer mode)
   ✅ REASONABLE - Safety limit for stuck states


7. ✅ STUCK_STATE_THRESHOLD = 100 (core_gameplay.py line 254)
   Purpose: Detect stuck games (100 actions no change)
   ✅ REASONABLE - Quick detection of futile actions


8. ✅ MAX_API_RESETS_PER_LEVEL = 2 (core_gameplay.py line 249)
   Purpose: Limit API resets per level
   ✅ REASONABLE - Prevents reset spam


9. ✅ min_actions_needed = 100 (game_session_manager.py line 225)
   Purpose: Minimum actions to make game attempt reasonable
   ✅ REASONABLE - Ensures meaningful game attempts


10. ✅ Collective reasoning: 3-5 agents (collective_reasoning_engine.py)
    min_agents_for_collective = 3
    max_agents_for_collective = 5
    ✅ REASONABLE - Small focused group for ensemble intelligence


11. ✅ API retry logic: max_retries = 3 (arc_api_client.py line 209)
    ✅ REASONABLE - Standard retry pattern


12. ✅ ANTI-GAMING thresholds (core_gameplay.py lines 1601-1602)
    min_action_improvement = 5 if same_agent else 3
    min_efficiency_multiplier = 1.10 if same_agent else 1.05
    ✅ REASONABLE - Prevents sequence spam while allowing improvements


═══════════════════════════════════════════════════════════════════════════════
RECOMMENDED CHANGES - PRIORITY ORDER
═══════════════════════════════════════════════════════════════════════════════

PRIORITY 1: games_per_generation (HIGH IMPACT)
──────────────────────────────────────────────────
Make games_per_generation adaptive:

Current:
    self.games_per_generation = games_per_generation  # Default 20

Recommended:
    # If not explicitly set, scale with target population
    if games_per_generation is None:
        self.games_per_generation = ADAPTIVE_TARGET_POPULATION
    else:
        self.games_per_generation = games_per_generation
        
Benefits:
- Full population coverage each generation
- 60 agents → 60 games (vs current 20)
- 1000 agents → 1000 games (vs current 20)
- Better evaluation of entire population


PRIORITY 2: initial_population_size (MEDIUM IMPACT)
──────────────────────────────────────────────────
Make initial population scale with game types:

Current:
    initial_population_size: int = 10

Recommended:
    initial_population_size: int = None  # Auto-calculate
    
    # In __init__:
    if initial_population_size is None:
        # Calculate based on available game types (done at runtime)
        self.initial_population_size = 10  # Fallback
    else:
        self.initial_population_size = initial_population_size
    
    # In _create_initial_population:
    # Update to use detected game count
    detected_game_types = len(game_types)  # From API
    actual_initial_pop = detected_game_types * 2
    
Benefits:
- 6 game types → 12 initial agents (2 per type)
- 50 game types → 100 initial agents (2 per type)
- Better initial coverage and diversity


═══════════════════════════════════════════════════════════════════════════════
IMPLEMENTATION NOTES
═══════════════════════════════════════════════════════════════════════════════

games_per_generation:
- Already have self._current_target_population set during evaluation
- Simply use that value instead of hardcoded games_per_generation
- Add command-line override to maintain manual control option

initial_population_size:
- More complex: game types not known until first API call
- Could start with default 10, then breed to target after first gen
- OR: Make first API call during initialization to detect game count
- Second option preferred for proper startup scaling


═══════════════════════════════════════════════════════════════════════════════
SUMMARY
═══════════════════════════════════════════════════════════════════════════════

Total Hardcoded Limits Found: 12

Status:
✅ Acceptable as-is: 8 limits (safety bounds, reasonable fixed values)
⚠️ Consider future improvement: 2 limits (low-medium impact)
❌ SHOULD FIX: 2 limits (high-medium impact on scaling)

Priority Fixes:
1. games_per_generation → Adaptive (= TARGET_POPULATION)
2. initial_population_size → Adaptive (= game_types * 2)

These two changes will complete the adaptive scaling system and allow
the Ouroboros system to scale from 6 games to 1000+ games without any
manual configuration changes.
"""

print(__doc__)
