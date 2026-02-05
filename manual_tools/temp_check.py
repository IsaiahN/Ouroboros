"""Check action traces and decision reasons from recent gameplay."""

import json
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get table schema for action_traces
print("=== ACTION_TRACES TABLE SCHEMA ===")
cursor.execute("PRAGMA table_info(action_traces)")
for col in cursor.fetchall():
    print(f"  {col['name']:30} {col['type']}")

# Count records
cursor.execute('SELECT COUNT(*) FROM action_traces')
total = cursor.fetchone()[0]
print(f"\n=== ACTION TRACES: {total} records ===")

# Recent traces
print("\nRecent 10 action traces:")
cursor.execute('''
    SELECT game_id, action_num, action_taken, score_before, score_after,
           level_before, level_after, is_game_over, timestamp
    FROM action_traces
    ORDER BY timestamp DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    game = row['game_id'][:20] if row['game_id'] else '?'
    print(f"  [{row['action_num']:3d}] {row['action_taken']:8s} | {game} | score: {row['score_before']}->{row['score_after']} | level: {row['level_before']}->{row['level_after']}")

conn.close()
