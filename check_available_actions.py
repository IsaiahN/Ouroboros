import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

print("=== Recent Games with Available Actions ===")
results = db.execute_query("""
    SELECT game_id, available_actions, status, final_score 
    FROM game_results 
    ORDER BY created_at DESC 
    LIMIT 10
""")

for r in results:
    actions = r['available_actions']
    if actions:
        try:
            actions = json.loads(actions) if isinstance(actions, str) else actions
            print(f"Game: {r['game_id']}")
            print(f"  Available Actions: {actions}")
            print(f"  Status: {r['status']}, Score: {r['final_score']}")
        except:
            print(f"Game: {r['game_id']}")
            print(f"  Available Actions: {actions} (raw)")
    else:
        print(f"Game: {r['game_id']} - No available_actions stored")
