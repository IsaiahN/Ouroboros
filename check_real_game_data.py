import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime, timedelta

db = DatabaseInterface()

# Check recent games
recent = db.execute_query("""
    SELECT COUNT(*) as total, 
           SUM(CASE WHEN final_score > 0 THEN 1 ELSE 0 END) as scored,
           MAX(final_score) as best_score,
           AVG(final_score) as avg_score
    FROM game_results 
    WHERE end_time >= datetime('now', '-9 hours')
""")

r = recent[0]
print(f"\n[DATABASE CHECK] Games in last 9 hours:")
print(f"  Total Games: {r['total']}")
print(f"  Games with Score > 0: {r['scored']}")
print(f"  Best Score: {r['best_score']}")
avg = r['avg_score'] if r['avg_score'] else 0
print(f"  Avg Score: {avg:.2f}")

# Check agent performance
agents_with_games = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM agents 
    WHERE total_games_played > 0 AND is_active = TRUE
""")

print(f"\n  Active agents with games: {agents_with_games[0]['count']}")

# Check network snapshots
snapshots = db.execute_query("""
    SELECT COUNT(*) as count FROM ecosystem_health_snapshots
""")

print(f"  Network snapshots captured: {snapshots[0]['count']}")

print("\n" + "="*60)
print("CONCLUSION:")
if r['total'] == 0:
    print("  ⚠️  NO GAMES COMPLETED in last 9 hours!")
    print("  The runner might have been paused or stuck.")
elif r['total'] > 0:
    print(f"  ✓ {r['total']} games completed - runner's counter was wrong")
    print(f"  Database has the real data!")
