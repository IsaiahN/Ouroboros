#!/usr/bin/env python3
"""List all death/danger related tables."""
import sqlite3

conn = sqlite3.connect('core_data.db')
cur = conn.cursor()

cur.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table'
    AND (name LIKE '%death%' OR name LIKE '%danger%' OR name LIKE '%terminal%' OR name LIKE '%threat%')
""")
tables = [r[0] for r in cur.fetchall()]
print("Death/Danger related tables:")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    count = cur.fetchone()[0]
    print(f"  {t}: {count} rows")

conn.close()
