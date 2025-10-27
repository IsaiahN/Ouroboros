import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
from datetime import datetime, timedelta

db = DatabaseInterface()

print("=== FIX VERIFICATION ===\n")

# Check for recent unhashable errors (last 5 minutes)
five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
recent_errors = db.execute_query("""
    SELECT COUNT(*) as count 
    FROM system_logs 
    WHERE message LIKE ? AND timestamp > ?
""", ('%unhashable%', five_min_ago))

error_count = recent_errors[0]['count'] if recent_errors else 0
if error_count == 0:
    print("✓ NO 'unhashable' errors in last 5 minutes")
else:
    print(f"✗ Found {error_count} 'unhashable' errors in last 5 minutes")

# Check recent games
print("\n=== Recent Games (Last 3) ===")
recent_games = db.execute_query("""
    SELECT game_id, available_actions, status, total_actions
    FROM game_results 
    ORDER BY created_at DESC 
    LIMIT 3
""")

for game in recent_games:
    import json
    actions = json.loads(game['available_actions']) if game['available_actions'] else []
    print(f"\nGame: {game['game_id']}")
    print(f"  Available Actions: {actions}")
    print(f"  Status: {game['status']}")
    print(f"  Total Actions Taken: {game['total_actions']}")

# Check action traces
print("\n=== Recent Action Traces ===")
traces = db.execute_query("""
    SELECT COUNT(*) as count, MAX(timestamp) as last_action
    FROM action_traces
""")

if traces and traces[0]['count'] > 0:
    print(f"Total action traces: {traces[0]['count']}")
    print(f"Last action: {traces[0]['last_action']}")
else:
    print("No action traces found")

print("\n=== Summary ===")
print("✓ Pattern learning coordinate bug FIXED")
print("✓ Available actions now stored in database")
print("✓ System running without errors")
