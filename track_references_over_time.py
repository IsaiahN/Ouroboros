#!/usr/bin/env python3
"""Check when seq_4d2a times_referenced hit 10+"""

import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Get all games using lp85, ordered by time
games = conn.execute('''
    SELECT game_id, start_time, level_completions, total_actions
    FROM game_results
    WHERE game_id LIKE "lp85%"
    ORDER BY start_time ASC
''').fetchall()

print(f"Total lp85 games: {len(games)}\n")

# Pruning times
pruning_times = [
    ("Gen 239", "2025-11-25T10:53:08"),
    ("Gen 240", "2025-11-25T12:37:39"),
    ("Gen 241", "2025-11-25T12:54:03"),
]

seq_created = "2025-11-25T09:53:13"
print(f"seq_4d2a created: {seq_created}\n")

# Count references over time
count = 0
for game in games:
    game_time = game['start_time']
    count += 1
    
    # Check if this crosses pruning threshold
    if count == 10:
        print(f"✓ 10th reference: {game_time}")
    
    # Check relative to pruning runs
    for gen, prune_time in pruning_times:
        if game_time > seq_created and game_time < prune_time and count == len([g for g in games if g['start_time'] < prune_time]):
            print(f"  At {gen} ({prune_time}): {count} references")

# Final count
print(f"\nCurrent references: {count}")

# More precise: what was the state at each pruning?
print("\n" + "=" * 80)
print("REFERENCES AT EACH PRUNING RUN:")
print("=" * 80)

for gen, prune_time in pruning_times:
    refs_at_time = len([g for g in games if g['start_time'] < prune_time])
    status = "✓ Should prune" if refs_at_time >= 10 else "✗ Too few refs"
    print(f"{gen} ({prune_time}): {refs_at_time} references {status}")

conn.close()
