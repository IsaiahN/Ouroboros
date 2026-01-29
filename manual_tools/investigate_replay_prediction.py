import sqlite3
conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

print('=== Replay Learning Investigation ===')

# List replay tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'replay%'")
print('\nReplay-related tables:')
for r in cur.fetchall():
    print(f'  {r[0]}')

# Check replay_learning_events
cur.execute("SELECT COUNT(*) FROM replay_learning_events")
print(f'\nTotal replay_learning_events: {cur.fetchone()[0]}')

cur.execute("""
    SELECT game_type, 
           COUNT(*) as events,
           AVG(prediction_correct) as avg_correct
    FROM replay_learning_events 
    GROUP BY game_type
""")
print('\nEvents by game_type:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} events, {r[2]*100:.1f}% correct' if r[2] else f'  {r[0]}: {r[1]} events')

# Check inferred patterns (actual table name)
try:
    cur.execute("""
        SELECT game_type, pattern_type, pattern_data
        FROM replay_inferred_patterns
        LIMIT 10
    """)
    print('\nStored inferred patterns:')
    for r in cur.fetchall():
        print(f'  {r[0]}: {r[1]} -> {r[2][:50]}...')
except Exception as e:
    print(f'\nCould not query inferred patterns: {e}')

conn.close()
