#!/usr/bin/env python3
"""Analyze what can be safely cleaned up."""
import sqlite3
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

print('='*60)
print('CLEANUP ANALYSIS - What can we safely delete?')
print('='*60)

# Database size
db_size = os.path.getsize('core_data.db') / (1024*1024*1024)
print(f'\nDATABASE SIZE: {db_size:.2f} GB / 10 GB limit')

# 1. Zero-score game results
c.execute('SELECT COUNT(*) FROM game_results WHERE final_score = 0')
zero_games = c.fetchone()[0]
print(f'\n1. ZERO-SCORE GAME RESULTS: {zero_games:,}')

# 2. System logs 
c.execute('SELECT COUNT(*) FROM system_logs')
logs = c.fetchone()[0]
print(f'2. SYSTEM_LOGS: {logs:,}')

# 3. Sensation learning events
c.execute('SELECT COUNT(*) FROM sensation_learning_events')
sens = c.fetchone()[0]
print(f'3. SENSATION_LEARNING_EVENTS: {sens:,}')

# 4. Score history
c.execute('SELECT COUNT(*) FROM score_history')
scores = c.fetchone()[0]
print(f'4. SCORE_HISTORY: {scores:,}')

# 5. Navigation state history
c.execute('SELECT COUNT(*) FROM navigation_state_history')
nav = c.fetchone()[0]
print(f'5. NAVIGATION_STATE_HISTORY: {nav:,}')

# 6. Action traces
c.execute('SELECT COUNT(*) FROM action_traces')
traces = c.fetchone()[0]
print(f'6. ACTION_TRACES: {traces:,}')

# 7. Database logs
c.execute('SELECT COUNT(*) FROM database_logs')
db_logs = c.fetchone()[0]
print(f'7. DATABASE_LOGS: {db_logs:,}')

# Check what tables are largest
print('\n' + '='*60)
print('TOP 10 LARGEST TABLES BY ROW COUNT:')
print('='*60)
c.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
''')
tables = [r[0] for r in c.fetchall()]
table_sizes = []
for t in tables:
    c.execute(f'SELECT COUNT(*) FROM "{t}"')
    cnt = c.fetchone()[0]
    if cnt > 0:
        table_sizes.append((t, cnt))
table_sizes.sort(key=lambda x: x[1], reverse=True)
for t, cnt in table_sizes[:10]:
    print(f'  {t}: {cnt:,}')

conn.close()
