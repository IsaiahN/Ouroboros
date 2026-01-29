"""Verify counterfactual tables are dropped."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%counterfactual%'")
tables = c.fetchall()
print(f"Remaining counterfactual tables: {tables if tables else 'NONE'}")
conn.close()
