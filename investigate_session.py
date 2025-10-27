import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

session_id = '5e2a1998-2019-4ec3-8614-42fd01f7fbb0-1'

print(f"=== Investigating Session: {session_id} ===\n")

# Check training sessions
print("=== Training Session Info ===")
sessions = db.execute_query("""
    SELECT * FROM training_sessions 
    WHERE session_id = ?
""", (session_id,))

if sessions:
    s = sessions[0]
    print(f"Session ID: {s['session_id']}")
    print(f"Start Time: {s['start_time']}")
    print(f"End Time: {s['end_time']}")
    print(f"Status: {s['status']}")
    print(f"Total Games: {s['total_games']}")
    print(f"Total Wins: {s['total_wins']}")
    print(f"Total Actions: {s['total_actions']}")
else:
    print("No training session found")

# Check game results
print("\n=== Game Results ===")
games = db.execute_query("""
    SELECT * FROM game_results 
    WHERE session_id = ?
    ORDER BY start_time
""", (session_id,))

print(f"Found {len(games)} game(s) in this session:")
for i, game in enumerate(games, 1):
    print(f"\nGame {i}: {game['game_id']}")
    print(f"  Status: {game['status']}")
    print(f"  Final Score: {game['final_score']}")
    print(f"  Total Actions: {game['total_actions']}")
    print(f"  Win Detected: {game['win_detected']}")
    if game.get('available_actions'):
        actions = json.loads(game['available_actions']) if isinstance(game['available_actions'], str) else game['available_actions']
        print(f"  Available Actions: {actions}")

# Check action traces to see what happened
print("\n=== Action Trace Analysis ===")
traces = db.execute_query("""
    SELECT game_id, COUNT(*) as action_count, 
           MAX(score_after) as max_score,
           SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frame_changes,
           MIN(timestamp) as first_action,
           MAX(timestamp) as last_action
    FROM action_traces 
    WHERE session_id = ?
    GROUP BY game_id
    ORDER BY first_action
""", (session_id,))

for trace in traces:
    print(f"\nGame: {trace['game_id']}")
    print(f"  Actions: {trace['action_count']}")
    print(f"  Max Score: {trace['max_score']}")
    print(f"  Frame Changes: {trace['frame_changes']}")
    print(f"  First Action: {trace['first_action']}")
    print(f"  Last Action: {trace['last_action']}")

# Check the last few actions to see what state we were in
print("\n=== Last 20 Actions ===")
last_actions = db.execute_query("""
    SELECT action_number, score_before, score_after, score_change, 
           frame_changed, timestamp
    FROM action_traces 
    WHERE session_id = ?
    ORDER BY timestamp DESC
    LIMIT 20
""", (session_id,))

for action in reversed(last_actions):
    changed = "✓" if action['frame_changed'] else " "
    print(f"  ACTION{action['action_number']} - Score: {action['score_before']:.0f}→{action['score_after']:.0f} (Δ{action['score_change']:+.0f}) [{changed}]")

# Check system logs for this session
print("\n=== System Logs (Key Events) ===")
logs = db.execute_query("""
    SELECT level, message, timestamp 
    FROM system_logs 
    WHERE message LIKE ?
    ORDER BY timestamp DESC
    LIMIT 30
""", (f'%{session_id[:8]}%',))

if logs:
    print(f"Found {len(logs)} relevant log entries (showing first 10):")
    for log in logs[:10]:
        print(f"  [{log['level']}] {log['message'][:150]}")
else:
    # Try searching for the game ID instead
    if games:
        game_id = games[0]['game_id']
        print(f"Searching for logs related to game: {game_id}")
        logs = db.execute_query("""
            SELECT level, message, timestamp 
            FROM system_logs 
            WHERE message LIKE ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (f'%{game_id}%',))
        for log in logs[:10]:
            print(f"  [{log['level']}] {log['message'][:150]}")

print("\n=== Analysis ===")
if games and len(games) > 0:
    first_game = games[0]
    if first_game['win_detected'] or first_game['final_score'] > 0:
        print("✓ Level completed successfully!")
        print(f"  Final Score: {first_game['final_score']}")
        if len(games) == 1:
            print("⚠ Only 1 game played - system stopped after first level")
            print("  This suggests the game may have ended or an error occurred")
        else:
            print(f"✓ System continued - {len(games)} levels attempted")
