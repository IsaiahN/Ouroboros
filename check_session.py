import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

session_id = '72e615b3-2e54-4a25-bc45-d7794e12cbf6'

# Check game_results for this session
print("=== Game Results ===")
results = db.execute_query("""
    SELECT game_id, final_score, total_actions, end_time 
    FROM game_results 
    WHERE session_id = ? 
    ORDER BY created_at DESC 
    LIMIT 5
""", (session_id,))
print(f"Found {len(results)} game results")
for r in results:
    print(f"  Game: {r['game_id']}, Score: {r['final_score']}, Actions: {r['total_actions']}")

# Check arc_action_tracking
print("\n=== Action Tracking ===")
actions = db.execute_query("""
    SELECT action_type, coordinate_x, coordinate_y, 
           api_request_sent, api_response_received, action_accepted,
           error_message
    FROM arc_action_tracking 
    ORDER BY action_timestamp DESC
    LIMIT 20
""")
print(f"Found {len(actions)} total actions")
for a in actions:
    print(f"  {a['action_type']} at ({a['coordinate_x']}, {a['coordinate_y']}) - Sent: {a['api_request_sent']}, Response: {a['api_response_received']}, Accepted: {a['action_accepted']}")
    if a['error_message']:
        print(f"    Error: {a['error_message']}")

# Check action_traces for the session
print("\n=== Action Traces ===")
traces = db.execute_query("""
    SELECT game_id, action_number, coordinates, frame_changed, score_change, timestamp
    FROM action_traces 
    WHERE session_id = ?
    ORDER BY timestamp DESC
    LIMIT 20
""", (session_id,))
print(f"Found {len(traces)} action traces for this session")
for t in traces:
    coords = f" at {t['coordinates']}" if t['coordinates'] else ""
    print(f"  ACTION{t['action_number']}{coords} - Changed: {t['frame_changed']}, Score Δ: {t['score_change']}")

# Check system logs for errors
print("\n=== Recent System Logs ===")
logs = db.execute_query("""
    SELECT level, message 
    FROM system_logs 
    WHERE message LIKE ? OR message LIKE ?
    ORDER BY timestamp DESC 
    LIMIT 15
""", (f'%{session_id[:8]}%', '%ACTION%'))
print(f"Found {len(logs)} relevant logs")
for log in logs[:10]:
    print(f"  [{log['level']}] {log['message'][:150]}")
