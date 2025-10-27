import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface
import json

db = DatabaseInterface()

print("=== Searching for Wins ===\n")

# Look for wins in game_results
print("=== Games with Wins Detected ===")
wins = db.execute_query("""
    SELECT game_id, session_id, final_score, total_actions, start_time, end_time
    FROM game_results 
    WHERE win_detected = 1 OR status = 'WIN'
    ORDER BY start_time DESC
    LIMIT 10
""")

if wins:
    print(f"Found {len(wins)} wins!")
    for w in wins:
        print(f"\nGame: {w['game_id']}")
        print(f"  Session: {w['session_id']}")
        print(f"  Score: {w['final_score']}")
        print(f"  Actions: {w['total_actions']}")
        print(f"  Time: {w['start_time']}")
else:
    print("No wins found in game_results")

# Look for high scores
print("\n=== Top Scoring Games ===")
top_scores = db.execute_query("""
    SELECT game_id, session_id, final_score, total_actions, status
    FROM game_results 
    WHERE final_score > 0
    ORDER BY final_score DESC
    LIMIT 10
""")

if top_scores:
    print(f"Found {len(top_scores)} games with score > 0:")
    for game in top_scores:
        print(f"  {game['game_id']}: Score={game['final_score']}, Actions={game['total_actions']}, Status={game['status']}")
else:
    print("No games with positive scores found")

# Look for level completions in action_traces
print("\n=== Level Completions (from action traces) ===")
level_ups = db.execute_query("""
    SELECT session_id, game_id, score_after, timestamp
    FROM action_traces 
    WHERE score_change > 50
    ORDER BY timestamp DESC
    LIMIT 10
""")

if level_ups:
    print(f"Found {len(level_ups)} significant score increases (possible level completions):")
    for level in level_ups:
        print(f"  Session: {level['session_id']}")
        print(f"  Game: {level['game_id']}")
        print(f"  Score: {level['score_after']}")
        print(f"  Time: {level['timestamp']}")
else:
    print("No significant score increases found")

# Search for the specific session ID pattern
print("\n=== Searching for Session Pattern '5e2a1998' ===")
pattern_search = db.execute_query("""
    SELECT DISTINCT session_id 
    FROM action_traces 
    WHERE session_id LIKE ?
    LIMIT 20
""", ('%5e2a1998%',))

if pattern_search:
    print(f"Found {len(pattern_search)} matching sessions:")
    for s in pattern_search:
        print(f"  {s['session_id']}")
        
    # Get details of first match
    if pattern_search:
        session_id = pattern_search[0]['session_id']
        print(f"\n=== Details for {session_id} ===")
        
        # Get action summary
        summary = db.execute_query("""
            SELECT 
                COUNT(*) as total_actions,
                MAX(score_after) as max_score,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM action_traces 
            WHERE session_id = ?
        """, (session_id,))
        
        if summary:
            s = summary[0]
            print(f"Total Actions: {s['total_actions']}")
            print(f"Max Score: {s['max_score']}")
            print(f"Start: {s['start_time']}")
            print(f"End: {s['end_time']}")
            
        # Get game progression
        games = db.execute_query("""
            SELECT DISTINCT game_id, MAX(score_after) as max_score
            FROM action_traces 
            WHERE session_id = ?
            GROUP BY game_id
            ORDER BY MIN(timestamp)
        """, (session_id,))
        
        print(f"\nGames played: {len(games)}")
        for g in games:
            print(f"  {g['game_id']}: Max Score = {g['max_score']}")
else:
    print("No matching sessions found")

# Look in system logs for game completion or win messages
print("\n=== Looking for Win/Completion Messages in Logs ===")
win_logs = db.execute_query("""
    SELECT message, timestamp 
    FROM system_logs 
    WHERE message LIKE '%WIN%' OR message LIKE '%completed%level%' OR message LIKE '%score%100%'
    ORDER BY timestamp DESC
    LIMIT 20
""")

if win_logs:
    print(f"Found {len(win_logs)} relevant log entries:")
    for log in win_logs[:10]:
        print(f"  {log['timestamp']}: {log['message'][:120]}")
