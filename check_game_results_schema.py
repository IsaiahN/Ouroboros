"""Check game_results schema"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from database_interface import DatabaseInterface

db = DatabaseInterface()
cols = db.execute_query('PRAGMA table_info(game_results)')
print("game_results columns:")
for c in cols:
    print(f"  {c['name']}: {c['type']}")
