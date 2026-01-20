import sqlite3

db = sqlite3.connect('core_data.db')
db.row_factory = sqlite3.Row

print('='*70)
print('LS20 DISCOVERIES & KEY EVENTS')
print('='*70)

# Get discovery logs
discoveries = db.execute('''
    SELECT timestamp, message
    FROM system_logs
    WHERE message LIKE '%ls20%' 
    AND (message LIKE '%DISCOVERY%' OR message LIKE '%controls%' OR message LIKE '%WIN%' OR message LIKE '%LEVEL%' OR message LIKE '%hypothesis%' OR message LIKE '%pattern%')
    ORDER BY timestamp DESC
    LIMIT 300
''').fetchall()

print('\n--- DISCOVERIES ---')
for d in discoveries:
    msg = d['message']
    # Clean up the message
    if ' - ' in msg:
        msg = msg.split(' - ')[-1]
    print(f"{d['timestamp'][:19]}: {msg[:100]}")

# Get action reasoning logs
print('\n' + '='*70)
print('ACTION REASONING LOGS')  
print('='*70)

cols = db.execute('PRAGMA table_info(action_reasoning_logs)').fetchall()
print('Columns:', [c[1] for c in cols][:10])

reasoning = db.execute('''
    SELECT * FROM action_reasoning_logs
    WHERE game_id LIKE '%ls20%'
    ORDER BY log_id DESC
    LIMIT 200
''').fetchall()

for r in reasoning:
    print(f"\n{r['timestamp'][:19]} | Action: {r['action_taken']}")
    if r['cods_operator']:
        print(f"  CODS: {r['cods_operator']}")
    if r['reasoning_summary']:
        print(f"  Reasoning: {r['reasoning_summary'][:80]}")

if not reasoning:
    print('No action reasoning logs for ls20')

# Check consciousness logs
print('\n' + '='*70)
print('CONSCIOUSNESS/DELIBERATION LOGS')
print('='*70)

consciousness = db.execute('''
    SELECT timestamp, message
    FROM system_logs
    WHERE message LIKE '%ls20%'
    AND (message LIKE '%deliberat%' OR message LIKE '%I-THREAD%' OR message LIKE '%STREAM%' OR message LIKE '%conflict%' OR message LIKE '%CODS%' OR message LIKE '%primitive%' OR message LIKE '%theory%')
    ORDER BY timestamp DESC
    LIMIT 300
''').fetchall()

for c in consciousness:
    msg = c['message']
    if ' - ' in msg:
        msg = msg.split(' - ')[-1]
    print(f"{c['timestamp'][:19]}: {msg[:90]}")

if not consciousness:
    print('No consciousness logs for ls20')
