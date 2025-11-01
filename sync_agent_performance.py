"""Manually sync existing agent_arc_performance data to agents table"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("\n=== SYNCING AGENT PERFORMANCE ===\n")

# Check before sync
before = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE total_games_played > 0
""")
print(f"[BEFORE] Agents with games > 0: {before[0]['count']}")

# Run sync
print("\n[SYNCING] Running sync_agent_performance_to_agents_table()...")
agents_updated = db.sync_agent_performance_to_agents_table()
print(f"[OK] Updated {agents_updated} agents")

# Check after sync
after = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE total_games_played > 0
""")
print(f"\n[AFTER] Agents with games > 0: {after[0]['count']}")

# Show top agents
top = db.execute_query("""
    SELECT 
        agent_id,
        agent_type,
        generation,
        total_games_played,
        total_games_won,
        avg_score_per_game,
        score_efficiency
    FROM agents
    WHERE total_games_played > 0
    ORDER BY avg_score_per_game DESC, total_games_played DESC
    LIMIT 10
""")

print(f"\n[TOP AGENTS] By avg levels per game:")
for i, a in enumerate(top, 1):
    print(f"  {i}. {a['agent_id'][:16]} Gen{a['generation']} ({a['agent_type'][:12]})")
    print(f"      {a['total_games_played']} games, {a['total_games_won']} wins, "
          f"{a['avg_score_per_game']:.3f} avg levels, eff={a['score_efficiency']:.5f}")

print("\n=== SYNC COMPLETE ===\n")
