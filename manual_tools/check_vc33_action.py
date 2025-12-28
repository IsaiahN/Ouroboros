"""Check action effectiveness for VC33."""
import sqlite3

conn = sqlite3.connect('core_data.db')
conn.row_factory = sqlite3.Row

print('=== Action Effectiveness for VC33 ===')
r = conn.execute("""
    SELECT * FROM action_effectiveness 
    WHERE game_id LIKE 'vc33%'
    ORDER BY action_number
    LIMIT 30
""").fetchall()
print(f'Found {len(r)} records')
for row in r:
    d = dict(row)
    print(f"Game: {d['game_id'][:15]}, Action: {d['action_number']}, "
          f"Rate: {d['success_rate']:.2f}, Impact: {d['avg_score_impact']:.2f}")

# The penalty 6.26 must come from somewhere - check sensation tables
print('\n=== Sensation Events for VC33 L3 ===')
try:
    r = conn.execute("""
        SELECT * FROM sensation_learning_events 
        WHERE game_id LIKE 'vc33%' AND level_number = 3
        ORDER BY event_id DESC
        LIMIT 10
    """).fetchall()
    print(f'Found {len(r)} sensation events')
    for row in r:
        print(dict(row))
except Exception as e:
    print(f'Error: {e}')

# Check action bias events
print('\n=== Action Bias Events for VC33 ===')
r = conn.execute("""
    SELECT * FROM action_bias_events 
    WHERE game_id LIKE 'vc33%'
    ORDER BY created_at DESC
    LIMIT 15
""").fetchall()
print(f'Found {len(r)} bias events')
for row in r:
    d = dict(row)
    print(f"Action: {d.get('action_code')}, Bias: {d.get('bias_value')}, "
          f"Reason: {d.get('reason', '')[:50]}")

conn.close()
