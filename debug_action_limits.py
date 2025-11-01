#!/usr/bin/env python3
"""Debug script to understand why action limits aren't working."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from adaptive_action_limits import AdaptiveActionLimits

db = DatabaseInterface()
limits = AdaptiveActionLimits(db)

print("\n" + "="*80)
print("ACTION LIMIT DEBUG")
print("="*80)

# Check what limits would be generated
print(f"\nAdaptive Limits Configuration:")
print(f"  MIN_TOTAL_ACTIONS: {limits.MIN_TOTAL_ACTIONS}")
print(f"  MAX_TOTAL_ACTIONS: {limits.MAX_TOTAL_ACTIONS}")
print(f"  Current total_actions: {limits.current_total_actions}")

# Test for generation 5
for gen in range(1, 6):
    actions_per_level, total_actions = limits.adjust_limits(gen)
    print(f"\n  Gen {gen}: {actions_per_level} per_level, {total_actions} total")

# Check recent games' action counts
print(f"\n" + "="*80)
print("RECENT GAMES ACTION COUNTS")
print("="*80)

games = db.execute_query("""
    SELECT game_id, total_actions, end_time
    FROM game_results
    WHERE end_time > datetime('now', '-2 hours')
    ORDER BY end_time DESC
    LIMIT 10
""")

if games:
    for r in games:
        game_id = r[0] if not isinstance(r, dict) else r['game_id']
        actions = r[1] if not isinstance(r, dict) else r['total_actions']
        end_time = r[2] if not isinstance(r, dict) else r['end_time']
        
        over_limit = "❌ WAY OVER" if actions > 10000 else ("⚠️ OVER" if actions > 3000 else "✅ OK")
        print(f"  {over_limit} {game_id[:20]:20s} | {actions:8d} actions | {end_time[:19]}")

# Check if there's a session override issue
print(f"\n" + "="*80)
print("CHECKING FOR OVERRIDE ISSUES")
print("="*80)

# Check game_session_manager default
from game_session_manager import GameSessionManager
print(f"\nGameSessionManager initialized with default config...")

# Check core_gameplay default
from core_gameplay import GameplayEngine
print(f"GameplayEngine initialized...")
engine = GameplayEngine("dummy_key")
print(f"\nDefault game_config:")
print(f"  max_actions_per_level: {engine.game_config.get('max_actions_per_level')}")
print(f"  max_total_actions: {engine.game_config.get('max_total_actions')}")

# Try configure
engine.configure(max_total_actions=3000)
print(f"\nAfter configure(max_total_actions=3000):")
print(f"  max_total_actions: {engine.game_config.get('max_total_actions')}")

print(f"\n" + "="*80)
print("HYPOTHESIS")
print("="*80)
print("""
If games are running to 200K+ actions despite:
1. Adaptive limits returning ≤3000
2. Configure() being called
3. Loop checking action_count < max_total_actions

Then the issue is likely:
- Config not being applied to the right engine instance
- Multiple engine instances (one configured, one not)
- Session manager creating its own engine
- Action count not being incremented properly

Need to check if autonomous_evolution_runner creates multiple GameplayEngine
instances and only configures one of them.
""")

print("="*80 + "\n")
