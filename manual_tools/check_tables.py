import sqlite3
conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

tables = [
    'frontier_checkpoints', 
    'game_lessons_learned', 
    'frame_embeddings', 
    'level_sequence_usage',
    'action_traces',
    'position_death_patterns',
    'winning_sequences'
]

print("=== Table existence check ===")
for t in tables:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'")
    if cur.fetchone():
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'  {t}: {cur.fetchone()[0]} rows')
    else:
        print(f'  {t}: NOT FOUND')

# Check level_sequence_usage columns if exists
print("\n=== level_sequence_usage schema ===")
try:
    cur.execute("PRAGMA table_info(level_sequence_usage)")
    cols = cur.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
except Exception as e:
    print(f"  Error: {e}")

# Check if action_traces has the columns we need
print("\n=== action_traces schema (sample) ===")
cur.execute("PRAGMA table_info(action_traces)")
cols = cur.fetchall()
for col in cols[:10]:
    print(f"  {col[1]} ({col[2]})")
print(f"  ... ({len(cols)} total columns)")
