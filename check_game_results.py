"""Check game_results table for specific game."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

# Check game_results for the specific game
game_id = "lp85-d265526edbaa"
results = db.execute_query("""
    SELECT game_id, final_score, total_actions, win_detected, status, 
           level_completions, start_time, end_time
    FROM game_results 
    WHERE game_id = ?
    ORDER BY start_time DESC
""", (game_id,))

print(f"Game results for {game_id}:")
print(f"Total results found: {len(results)}\n")

for r in results:
    print(f"Game: {r['game_id']}")
    print(f"  Score: {r['final_score']}")
    print(f"  Actions: {r['total_actions']}")
    print(f"  Win Detected: {r['win_detected']}")
    print(f"  Status: {r['status']}")
    print(f"  Level Completions: {r['level_completions']}")
    print(f"  Start: {r['start_time']}")
    print(f"  End: {r['end_time']}")
    print()

# Check all game_results to see what games have wins
all_wins = db.execute_query("""
    SELECT game_id, final_score, total_actions, win_detected, level_completions 
    FROM game_results 
    WHERE win_detected = TRUE
    ORDER BY end_time DESC
    LIMIT 10
""")

print(f"\nAll games with wins detected (last 10):")
print(f"Total wins found: {len(all_wins)}\n")

for w in all_wins:
    print(f"Game: {w['game_id']}, Score: {w['final_score']}, Actions: {w['total_actions']}, Win: {w['win_detected']}, Levels: {w['level_completions']}")
