import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import sqlite3

c = sqlite3.connect('core_data.db')
rows = c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for r in rows:
    n = r[0]
    if any(k in n for k in ['rout', 'trace', 'decision', 'epistemic', 'action_trace', 'game_result']):
        cnt = c.execute(f"SELECT COUNT(*) FROM [{n}]").fetchone()[0]
        print(f"  {n}: {cnt} rows")
c.close()
