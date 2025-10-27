import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

print("=== Most Recent Actions ===")
traces = db.execute_query("""
    SELECT session_id, game_id, action_number, coordinates, frame_changed, score_change
    FROM action_traces 
    ORDER BY timestamp DESC 
    LIMIT 30
""")

if traces:
    current_session = None
    for t in traces:
        if t['session_id'] != current_session:
            print(f"\nSession: {t['session_id']}")
            print(f"Game: {t['game_id']}")
            current_session = t['session_id']
        
        coords = f" at {t['coordinates']}" if t['coordinates'] else ""
        print(f"  ACTION{t['action_number']}{coords} - Changed: {t['frame_changed']}, Score Δ: {t['score_change']}")
else:
    print("No action traces found")

print("\n=== Action Traces Summary ===")
summary = db.execute_query("""
    SELECT 
        COUNT(*) as total_actions,
        COUNT(DISTINCT session_id) as total_sessions,
        COUNT(DISTINCT game_id) as total_games,
        SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frame_changes,
        SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as score_improvements
    FROM action_traces
""")

if summary:
    s = summary[0]
    print(f"Total Actions: {s['total_actions']}")
    print(f"Total Sessions: {s['total_sessions']}")
    print(f"Total Games: {s['total_games']}")
    print(f"Frame Changes: {s['frame_changes']}")
    print(f"Score Improvements: {s['score_improvements']}")
