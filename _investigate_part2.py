"""Part 2 - game_results and rung tracking investigation."""
import json
import sqlite3

conn = sqlite3.connect('core_data.db')
c = conn.cursor()

# Check game_results schema
print("=== game_results schema ===")
cols = [(r[1], r[2]) for r in c.execute('PRAGMA table_info(game_results)')]
for name, typ in cols:
    print(f"  {name}: {typ}")

# Also check deliberation tables
print("\n=== Tables with rung/decision data ===")
tables = c.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table' AND (
        name LIKE '%deliber%' OR name LIKE '%rung%' OR name LIKE '%decision%'
        OR name LIKE '%routing%' OR name LIKE '%cognitive%'
    )
""").fetchall()
for (t,) in tables:
    cnt = c.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    cols = [r[1] for r in c.execute(f"PRAGMA table_info([{t}])")]
    print(f"  {t}: {cnt} rows")
    print(f"    columns: {cols}")

conn.close()
