"""Check VC33 game data."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

# Check winning sequences for vc33
print('=== VC33 Winning Sequences ===')
r = conn.execute("""
    SELECT sequence_id, level_number, total_score,
           substr(action_sequence, 1, 300) as actions_preview
    FROM winning_sequences 
    WHERE game_type = 'vc33' 
    ORDER BY level_number
    LIMIT 10
""").fetchall()
for row in r:
    print(dict(row))

print()
print('=== VC33 Selectable Objects ===')
r2 = conn.execute("""
    SELECT * FROM object_selection_state 
    WHERE game_type = 'vc33'
    ORDER BY level_number
""").fetchall()
for row in r2:
    print(dict(row))

print()
print('=== VC33 Control Hypotheses ===')
r3 = conn.execute("""
    SELECT * FROM network_object_control_hypotheses 
    WHERE game_type = 'vc33'
    ORDER BY level_number
    LIMIT 10
""").fetchall()
for row in r3:
    print(dict(row))

conn.close()
