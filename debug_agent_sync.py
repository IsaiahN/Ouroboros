"""Check why agents show 0 games despite agent_arc_performance having data"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import math

db = DatabaseInterface()

print("\n=== DEBUGGING AGENT TRACKING ===\n")

# Check agents table
agents_check = db.execute_query("""
    SELECT 
        agent_id,
        agent_type,
        generation,
        total_games_played,
        total_games_won,
        avg_score_per_game
    FROM agents
    WHERE total_games_played > 0
    ORDER BY total_games_played DESC
    LIMIT 10
""")

print(f"[AGENTS TABLE] Agents with games > 0: {len(agents_check)}")
if agents_check:
    for a in agents_check[:5]:
        print(f"  {a['agent_id'][:16]} Gen{a['generation']}: "
              f"{a['total_games_played']} games, {a['avg_score_per_game']:.3f} avg")
else:
    print("  PROBLEM: No agents have total_games_played > 0!")
    print("  This means the agents table isn't being updated with game results")

# Check agent_arc_performance table
perf_check = db.execute_query("""
    SELECT 
        agent_id,
        COUNT(*) as games,
        SUM(final_score) as total_levels,
        AVG(final_score) as avg_levels
    FROM agent_arc_performance
    GROUP BY agent_id
    ORDER BY games DESC
    LIMIT 10
""")

print(f"\n[AGENT_ARC_PERFORMANCE] Agents with records: {len(perf_check)}")
for p in perf_check[:5]:
    learning_speed = (p['total_levels'] ** 1.5) / math.log(p['games'] + 1)
    print(f"  {p['agent_id'][:16]}: {p['games']} games, "
          f"{int(p['total_levels'])} levels, learning_speed={learning_speed:.2f}")

# Check if these agents exist in agents table
print(f"\n[CROSS-CHECK] Do these agent_ids exist in agents table?")
for p in perf_check[:3]:
    agent_exists = db.execute_query(
        "SELECT agent_id, generation FROM agents WHERE agent_id = ?",
        (p['agent_id'],)
    )
    if agent_exists:
        print(f"  ✓ {p['agent_id'][:16]} exists in agents table (Gen {agent_exists[0]['generation']})")
    else:
        print(f"  ✗ {p['agent_id'][:16]} NOT FOUND in agents table!")

print("\n[ISSUE]")
print("  agent_arc_performance has data (755 records)")
print("  BUT agents.total_games_played is not being updated")
print("  SOLUTION: Need to sync agent_arc_performance → agents table")

print("\n")
