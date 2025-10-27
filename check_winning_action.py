import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

# Get the winning action
action = db.execute_query("""
    SELECT * FROM action_traces 
    WHERE game_id = ? AND score_after = 1.0 
    LIMIT 1
""", ('lp85-d265526edbaa',))

if action:
    a = action[0]
    print("=== Winning Action Details ===")
    print(f"Action Number: {a['action_number']}")
    print(f"Score Before: {a['score_before']}")
    print(f"Score After: {a['score_after']}")
    print(f"Score Change: {a['score_change']}")
    print(f"Coordinates: {a['coordinates']}")
    print(f"Frame Changed: {a['frame_changed']}")
    print(f"Timestamp: {a['timestamp']}")
    
    if a.get('response_data'):
        try:
            response = json.loads(a['response_data'])
            print(f"\nAPI Response:")
            print(f"  State: {response.get('state')}")
            print(f"  Available Actions: {response.get('available_actions')}")
            print(f"  Action Input: {response.get('action_input')}")
        except Exception as e:
            print(f"\nCouldn't parse response: {e}")
            print(f"Raw: {a['response_data'][:200]}")
    
    # Get the next action to see what happened
    print("\n=== Next Actions After Win ===")
    next_actions = db.execute_query("""
        SELECT action_number, score_before, score_after, response_data
        FROM action_traces 
        WHERE game_id = ? AND timestamp > ?
        ORDER BY timestamp
        LIMIT 5
    """, ('lp85-d265526edbaa', a['timestamp']))
    
    if next_actions:
        print(f"Found {len(next_actions)} actions after the win")
        for na in next_actions:
            print(f"  ACTION{na['action_number']}: Score {na['score_before']} → {na['score_after']}")
            if na.get('response_data'):
                try:
                    r = json.loads(na['response_data'])
                    print(f"    State: {r.get('state')}")
                except:
                    pass
    else:
        print("⚠ NO ACTIONS after the win! System stopped immediately after scoring.")
        
else:
    print("Winning action not found")
