import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

game_id = 'lp85-d265526edbaa'
session_id = '5e2a1998-2019-4ec3-8614-42fd01f7fbb0-1'

print(f"=== Investigating Real Win ===")
print(f"Game: {game_id}")
print(f"Session: {session_id}\n")

# Check game_results
print("=== Game Results ===")
game_results = db.execute_query("""
    SELECT * FROM game_results 
    WHERE game_id LIKE ?
    ORDER BY start_time DESC
""", (f'%{game_id}%',))

if game_results:
    print(f"Found {len(game_results)} result(s):")
    for r in game_results:
        print(f"\nGame: {r['game_id']}")
        print(f"  Session: {r['session_id']}")
        print(f"  Status: {r['status']}")
        print(f"  Final Score: {r['final_score']}")
        print(f"  Total Actions: {r['total_actions']}")
        print(f"  Win Detected: {r['win_detected']}")
        print(f"  Start Time: {r['start_time']}")
        if r.get('available_actions'):
            try:
                actions = json.loads(r['available_actions'])
                print(f"  Available Actions: {actions}")
            except:
                print(f"  Available Actions: {r['available_actions']}")
else:
    print("No game_results found")

# Check action_traces
print("\n=== Action Traces Summary ===")
trace_summary = db.execute_query("""
    SELECT 
        session_id,
        COUNT(*) as total_actions,
        MIN(score_before) as min_score,
        MAX(score_after) as max_score,
        SUM(CASE WHEN frame_changed = 1 THEN 1 ELSE 0 END) as frame_changes,
        SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as score_increases,
        MIN(timestamp) as first_action,
        MAX(timestamp) as last_action
    FROM action_traces 
    WHERE game_id LIKE ?
    GROUP BY session_id
    ORDER BY first_action
""", (f'%{game_id}%',))

if trace_summary:
    for trace in trace_summary:
        print(f"\nSession: {trace['session_id']}")
        print(f"  Total Actions: {trace['total_actions']}")
        print(f"  Score Range: {trace['min_score']} → {trace['max_score']}")
        print(f"  Frame Changes: {trace['frame_changes']}")
        print(f"  Score Increases: {trace['score_increases']}")
        print(f"  Duration: {trace['first_action']} to {trace['last_action']}")
else:
    print("No action traces found")

# Get detailed action progression
print("\n=== Score Progression (showing key moments) ===")
score_changes = db.execute_query("""
    SELECT action_number, score_before, score_after, score_change, 
           frame_changed, timestamp
    FROM action_traces 
    WHERE game_id LIKE ? AND (score_change != 0 OR frame_changed = 1)
    ORDER BY timestamp
    LIMIT 50
""", (f'%{game_id}%',))

if score_changes:
    print(f"Found {len(score_changes)} significant actions:")
    for action in score_changes:
        changed = "📺" if action['frame_changed'] else "  "
        print(f"  {changed} ACTION{action['action_number']} - Score: {action['score_before']:.1f}→{action['score_after']:.1f} (Δ{action['score_change']:+.1f})")
else:
    print("No score changes found")

# Check last 30 actions to see what happened at the end
print("\n=== Last 30 Actions (to see why it stopped) ===")
last_actions = db.execute_query("""
    SELECT action_number, score_before, score_after, score_change, 
           frame_changed, coordinates, timestamp
    FROM action_traces 
    WHERE game_id LIKE ?
    ORDER BY timestamp DESC
    LIMIT 30
""", (f'%{game_id}%',))

if last_actions:
    print("Most recent actions (in reverse):")
    for i, action in enumerate(last_actions[:15]):
        changed = "✓" if action['frame_changed'] else " "
        coords = ""
        if action.get('coordinates'):
            try:
                c = json.loads(action['coordinates'])
                coords = f" at {c}"
            except:
                pass
        print(f"  {15-i:2d}. ACTION{action['action_number']}{coords} - Score: {action['score_after']:.0f} [{changed}]")
else:
    print("No actions found")

# Check if there's a winning sequence captured
print("\n=== Winning Sequence Check ===")
winning_seq = db.execute_query("""
    SELECT * FROM winning_sequences 
    WHERE game_id LIKE ?
""", (f'%{game_id}%',))

if winning_seq:
    print(f"✓ Winning sequence captured! {len(winning_seq)} sequence(s)")
    for seq in winning_seq:
        print(f"  Sequence ID: {seq['sequence_id']}")
        print(f"  Total Actions: {seq['total_actions']}")
        print(f"  Score: {seq['total_score']}")
        print(f"  Efficiency: {seq['efficiency_score']:.3f}")
        print(f"  Pattern Tags: {seq['pattern_tags']}")
else:
    print("⚠ No winning sequence captured in database")

# Check system logs for this game
print("\n=== System Logs ===")
logs = db.execute_query("""
    SELECT level, message, timestamp 
    FROM system_logs 
    WHERE message LIKE ?
    ORDER BY timestamp DESC
    LIMIT 20
""", (f'%{game_id}%',))

if logs:
    print(f"Found {len(logs)} log entries:")
    for log in logs[:10]:
        print(f"  [{log['level']}] {log['message'][:150]}")
else:
    print("No logs found for this game")

print("\n=== ANALYSIS ===")
if trace_summary and len(trace_summary) > 0:
    trace = trace_summary[0]
    if trace['max_score'] > 0:
        print(f"✓ CONFIRMED WIN! Max score reached: {trace['max_score']}")
        print(f"  Actions taken: {trace['total_actions']}")
        print(f"  Frame changes: {trace['frame_changes']}")
        
        if not winning_seq:
            print("\n⚠ WARNING: Win achieved but NOT captured by pattern learning!")
            print("  This means the win detection logic may have missed it")
            print("  or the game ended before capture could complete")
