#!/usr/bin/env python3
"""
Investigate why games end early with NOT_FINISHED state
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

print("=" * 80)
print("🔍 INVESTIGATING EARLY GAME ENDINGS")
print("=" * 80)
print()

db = DatabaseInterface()

# Get recent games with their action counts and final states
games = db.execute_query("""
    SELECT 
        gr.game_id,
        gr.final_score,
        gr.win_detected,
        gr.status,
        gr.total_actions as gr_total_actions,
        gr.end_time,
        ap.total_actions,
        ap.level_progressions,
        ap.win_proximity,
        ap.win_achieved
    FROM game_results gr
    JOIN agent_arc_performance ap ON gr.game_id = ap.game_id
    WHERE gr.end_time >= datetime('now', '-2 hours')
    ORDER BY gr.end_time DESC
    LIMIT 30
""")

print("RECENT GAMES (Last 2 hours):")
print("-" * 80)
print()
print("Game ID                      | Actions | Score  | Status       | Win? | Proximity")
print("-" * 80)

games_under_200 = []
games_with_progress = []

for game in games:
    game_id = game['game_id'][:24]
    actions = game['total_actions']
    score = game['final_score']
    levels = game['level_progressions']
    status = game['status'][:12]
    win = '✓' if game['win_achieved'] else '✗'
    proximity = game['win_proximity']
    
    print(f"{game_id:24s} | {actions:7d} | {score:6.2f} | {status:12s} | {win:4s} | {proximity:8.4f}")
    
    # Track games that ended before 200 actions
    if actions < 200:
        games_under_200.append({
            'game_id': game['game_id'],
            'actions': actions,
            'score': score,
            'levels': levels
        })
    
    # Track games with progress (score > 0 or levels > 0)
    if score > 0 or levels > 0:
        games_with_progress.append({
            'game_id': game['game_id'],
            'actions': actions,
            'score': score,
            'levels': levels
        })

print()
print("=" * 80)
print("📊 ANALYSIS")
print("=" * 80)
print()

total_games = len(games)
games_under_200_count = len(games_under_200)
games_with_progress_count = len(games_with_progress)

print(f"Total games analyzed: {total_games}")
print(f"Games ending before 200 actions: {games_under_200_count} ({games_under_200_count/max(total_games,1)*100:.1f}%)")
print(f"Games with progress (score/levels): {games_with_progress_count} ({games_with_progress_count/max(total_games,1)*100:.1f}%)")

# Check if games with progress tend to end early
if games_with_progress:
    avg_actions_with_progress = sum(g['actions'] for g in games_with_progress) / len(games_with_progress)
    print(f"\nAvg actions in games WITH progress: {avg_actions_with_progress:.1f}")

if games_under_200:
    progress_games_under_200 = [g for g in games_under_200 if g['score'] > 0 or g['levels'] > 0]
    print(f"\nGames that ended <200 actions BUT had progress: {len(progress_games_under_200)}")
    
    if progress_games_under_200:
        print("\nThese games made progress but ended early:")
        for g in progress_games_under_200[:5]:
            print(f"  - {g['game_id'][:24]}: {g['actions']} actions, score {g['score']:.2f}, {g['levels']} levels")

print()
print("=" * 80)
print("🔍 CHECKING GAME STATE TRACKING")
print("=" * 80)
print()

# Check if we're storing game state properly
print("Looking for games with NOT_FINISHED state in recent hour...")

# Note: game state might not be in game_results, need to check system_logs or other tracking
state_logs = db.execute_query("""
    SELECT message, timestamp
    FROM system_logs
    WHERE message LIKE '%NOT_FINISHED%'
       OR message LIKE '%game state%'
       OR message LIKE '%Game ended%'
    ORDER BY timestamp DESC
    LIMIT 10
""")

if state_logs:
    print("\nRecent state-related log messages:")
    for log in state_logs:
        print(f"  [{log['timestamp']}] {log['message'][:100]}")
else:
    print("  (No NOT_FINISHED messages found in recent logs)")

print()
print("=" * 80)
