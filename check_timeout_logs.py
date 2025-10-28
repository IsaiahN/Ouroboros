import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("Checking for level timeout messages...")
print()

logs = db.execute_query("""
    SELECT message, timestamp 
    FROM system_logs 
    WHERE message LIKE '%timed out%' 
       OR message LIKE '%continuing with remaining%'
       OR message LIKE '%Ending game%'
    ORDER BY timestamp DESC 
    LIMIT 10
""")

if logs:
    for log in logs:
        print(f"[{log['timestamp']}]")
        print(f"  {log['message'][:150]}")
        print()
else:
    print("No timeout messages found")

# Also check game results
print("\nRecent games:")
games = db.execute_query("""
    SELECT game_id, status, total_actions, final_score 
    FROM game_results 
    ORDER BY end_time DESC 
    LIMIT 5
""")

for game in games:
    print(f"  {game['game_id'][:24]}: {game['status']:12s} - {game['total_actions']:3d} actions, score {game['final_score']:.2f}")
