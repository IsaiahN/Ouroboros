"""
Issue 2 & 3 Fixes: Game Diversity + Pruning

1. Round-robin game distribution per generation
2. Fix pruning to be more aggressive
"""
from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

print("=" * 100)
print("ISSUE 2: GAME DIVERSITY FIX")
print("=" * 100)

# Get available game types
game_types = ['vc33', 'as66', 'ft09', 'sp80', 'ls20', 'lp85']

print(f"\nAvailable game types: {game_types}")
print(f"Total: {len(game_types)} game types")

print("""
IMPLEMENTATION PLAN:

1. Round-Robin Distribution:
   - Each generation, divide agents evenly among game types
   - If 50 agents, each game type gets ~8 agents
   - Rotate starting game type each generation

2. Code Changes in autonomous_evolution_runner.py:
   
   Line ~780 (in _evaluate_population):
   ```python
   # NEW: Round-robin game distribution
   game_types = ['vc33', 'as66', 'ft09', 'sp80', 'ls20', 'lp85']
   agents_per_game_type = max(1, len(active_agents) // len(game_types))
   
   # Rotate starting point each generation (prevents bias)
   start_offset = self.current_generation % len(game_types)
   rotated_game_types = game_types[start_offset:] + game_types[:start_offset]
   
   for agent_idx, agent in enumerate(active_agents):
       # Assign game type based on agent index (round-robin)
       assigned_game_type = rotated_game_types[agent_idx % len(rotated_game_types)]
       
       # Filter available_games to only this game type
       agent_games = [g for g in available_games 
                      if g.get('id', g.get('game_id', '')).startswith(assigned_game_type)]
       
       # Select specific games (existing logic can handle this)
       agent_games = self._assign_agent_to_optimal_task(
           agent_id=agent_id,
           agent_mode=agent_mode,
           available_games=[{'id': gid} for gid in agent_games],
           games_per_agent=games_per_agent
       )
   ```

3. Fallback for Dormant Specialists:
   - If no active agents know a game type, activate dormant specialists
   - Check last prestige decay and reactivate if needed
""")

print("\n" + "=" * 100)
print("ISSUE 3: PRUNING FIX")
print("=" * 100)

# Check current pruning settings
agents = db.execute_query("""
    SELECT 
        generation,
        COUNT(*) as total,
        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
    FROM agents
    GROUP BY generation
    ORDER BY generation DESC
    LIMIT 15
""")

print("\nCurrent agent counts (last 15 generations):")
print("Gen | Total | Active | Inactive")
print("----|-------|--------|----------")
for a in agents:
    inactive = a['total'] - a['active']
    print(f"{a['generation']:3d} | {a['total']:5d} | {a['active']:6d} | {inactive:8d}")

avg_total = sum(a['total'] for a in agents) / len(agents)
avg_active = sum(a['active'] for a in agents) / len(agents)

print(f"\nAverage per generation:")
print(f"  Total: {avg_total:.1f}")
print(f"  Active: {avg_active:.1f}")

print(f"""
PROBLEM ANALYSIS:
- Average {avg_total:.0f} agents per generation (HIGH!)
- Recent generations have 50 active agents
- Pruning target is 100 agents, but only pruning worst 100 of 200 checked
- POPULATION_MULTIPLIER might be too high

SOLUTION:

1. More Aggressive Pruning Target:
   Line ~1310 in autonomous_evolution_runner.py:
   ```python
   # OLD:
   target_pruned = min(100, population_size - self.initial_population_size * POPULATION_MULTIPLIER)
   
   # NEW: Prune down to target population size
   TARGET_POPULATION = 50  # Keep 50 active agents per generation
   target_pruned = max(0, population_size - TARGET_POPULATION)
   ```

2. Check More Agents for Pruning:
   Line ~1308:
   ```python
   # OLD:
   worst_performers = analysis.get('top_performers', [])[-200:]
   
   # NEW: Check all agents (sorted worst first)
   worst_performers = analysis.get('top_performers', [])[::-1]  # Reverse to get worst first
   ```

3. Ensure Pruning Actually Happens:
   - Current code stops after pruning target_pruned agents
   - This is correct, but target_pruned calculation is wrong
   - Fix the calculation to be more aggressive

4. Add Generation Cleanup:
   ```python
   # After pruning, clean up very old inactive agents (optional)
   # Keep last 10 generations of inactive agents for analysis
   min_generation_to_keep = self.current_generation - 10
   
   deleted = db.execute_query('''
       DELETE FROM agents 
       WHERE is_active = 0 
         AND generation < ?
   ''', (min_generation_to_keep,))
   ```

EXPECTED RESULTS AFTER FIX:
- Each generation: ~50 active agents (down from 173 avg)
- Game diversity: Each game type gets ~8 agents
- Cleaner database: Old inactive agents pruned after 10 generations
""")

print("\n" + "=" * 100)
print("READY TO IMPLEMENT")
print("=" * 100)
print("Apply these changes to autonomous_evolution_runner.py")
