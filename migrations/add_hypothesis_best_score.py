import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""Migration: Add best_score_achieved column to network_object_control_hypotheses.

TIER 5 - SELECTION: Hypotheses compete by outcome, not just validation count.
When multiple hypotheses exist for the same game/level, we rank them by
the best score any agent achieved while using that hypothesis.

This enables:
- High-performing hypotheses rise to the top of query results
- Agents naturally gravitate toward hypotheses that produce wins
- Poor hypotheses sink even if technically "validated"
"""
import sqlite3

conn = sqlite3.connect('core_data.db')

# Check current columns
cols = [c[1] for c in conn.execute('PRAGMA table_info(network_object_control_hypotheses)').fetchall()]
print('Current columns:', cols)

# Add best_score_achieved column if missing
if 'best_score_achieved' not in cols:
    try:
        conn.execute('ALTER TABLE network_object_control_hypotheses ADD COLUMN best_score_achieved INTEGER DEFAULT 0')
        print('  Added: best_score_achieved')
    except Exception as e:
        print(f'  Skip best_score_achieved: {e}')
else:
    print('  best_score_achieved already exists')

conn.commit()
conn.close()
print('[OK] Schema updated - hypothesis competition by outcome enabled')
