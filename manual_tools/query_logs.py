import sqlite3

db = sqlite3.connect('core_data.db')
db.row_factory = sqlite3.Row

# Find all tables
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
log_tables = [t[0] for t in tables if 'log' in t[0].lower()]
print('Log tables:', log_tables)

# Check system_logs schema
print('\n=== system_logs schema ===')
cols = db.execute('PRAGMA table_info(system_logs)').fetchall()
for c in cols:
    print(f'  {c[1]} ({c[2]})')

# Get recent ls20 logs
print('\n' + '='*70)
print('RECENT LS20 CONSOLE LOGS (last 8 hours)')
print('='*70)

logs = db.execute('''
    SELECT timestamp, level, module, message
    FROM system_logs
    WHERE (message LIKE '%ls20%' OR module LIKE '%ls20%')
    ORDER BY timestamp DESC
    LIMIT 500
''').fetchall()

for log in logs:
    ts = log['timestamp']
    lvl = log['level']
    mod = log['module'][:20] if log['module'] else ''
    msg = log['message'][:100] if log['message'] else ''
    print(f'{ts} [{lvl}] {mod}: {msg}')

if not logs:
    print('No ls20 logs in last 8 hours')
    
    # Try getting ANY recent logs
    print('\n=== Most recent logs (any game) ===')
    recent = db.execute('''
        SELECT timestamp, level, module, message
        FROM system_logs
        ORDER BY timestamp DESC
        LIMIT 200
    ''').fetchall()
    
    for log in recent:
        ts = log['timestamp']
        msg = log['message'][:120] if log['message'] else ''
        print(f'{ts}: {msg}')
