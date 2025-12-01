#!/usr/bin/env python3
"""Review evolution test results"""

import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Get recent games from last hour (test was just run)
cutoff = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

results = conn.execute('''
    SELECT game_id, total_actions, level_completions, final_score, status, start_time
    FROM game_results 
    WHERE start_time > ?
    ORDER BY start_time DESC
    LIMIT 10
''', (cutoff,)).fetchall()

print("=" * 80)
print("RECENT TEST EVOLUTION RESULTS (Last Hour)")
print("=" * 80)
for r in results:
    print(f"{r['game_id']}: {r['total_actions']} actions, "
          f"{r['level_completions']} levels, Score={r['final_score']}, "
          f"Status={r['status']}")

# Summary stats
total_games = len(results)
avg_actions = sum(r['total_actions'] for r in results) / total_games if total_games > 0 else 0
total_levels = sum(r['level_completions'] for r in results)
success_count = sum(1 for r in results if r['level_completions'] > 0)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total games: {total_games}")
print(f"Average actions: {avg_actions:.0f}")
print(f"Total levels completed: {total_levels}")
print(f"Games with progress: {success_count}/{total_games}")
print(f"Success rate: {success_count/total_games*100:.1f}%" if total_games > 0 else "N/A")

conn.close()
