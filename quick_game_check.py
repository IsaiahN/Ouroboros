#!/usr/bin/env python3
"""Quick check of game diversity"""
from database_interface import DatabaseInterface

db = DatabaseInterface()

# Games in last hour
recent = db.execute_query("""
    SELECT game_id, COUNT(*) as count 
    FROM agent_arc_performance 
    WHERE game_timestamp > datetime('now', '-1 hour')
    GROUP BY game_id 
    ORDER BY count DESC
""")

print("Games played in last hour:")
if recent:
    for r in recent:
        print(f"  {r['game_id'][:4]}: {r['count']} plays")
else:
    print("  No recent games")

# Check if all 6 games represented
all_games = set([r['game_id'] for r in recent]) if recent else set()
expected = ['vc33', 'as66', 'ft09', 'ls20', 'lp85', 'sp80']
print(f"\nGame diversity: {len(all_games)}/6 unique games")
for game in expected:
    status = "✅" if any(g.startswith(game) for g in all_games) else "❌"
    print(f"  {status} {game}")
