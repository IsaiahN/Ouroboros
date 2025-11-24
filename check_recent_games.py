#!/usr/bin/env python3
"""Check recent game activity"""

from database_interface import DatabaseInterface

db = DatabaseInterface('core_data.db')

# Check last 10 games
print("Last 10 games played:")
results = db.execute_query("""
    SELECT scorecard_id, game_id, created_at, final_score 
    FROM game_results 
    ORDER BY created_at DESC 
    LIMIT 10
""")

for row in results:
    print(f"  {row['scorecard_id']}: {row['game_id']} (score: {row['final_score']}) - {row['created_at']}")

# Count games by day
print("\nGames per day (last 7 days):")
daily = db.execute_query("""
    SELECT DATE(created_at) as day, COUNT(*) as count
    FROM game_results
    WHERE created_at >= datetime('now', '-7 days')
    GROUP BY DATE(created_at)
    ORDER BY day DESC
""")

for row in daily:
    print(f"  {row['day']}: {row['count']} games")

# Check if any games are stuck
print("\nActive game sessions (not completed):")
active = db.execute_query("""
    SELECT game_id, agent_id, session_id, created_at
    FROM game_sessions
    WHERE end_time IS NULL
    ORDER BY created_at DESC
    LIMIT 5
""")

if active:
    for row in active:
        print(f"  {row['game_id']} by {row['agent_id']}: started {row['created_at']}")
else:
    print("  None")
