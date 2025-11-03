import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from database_interface import DatabaseInterface

db = DatabaseInterface()
tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("Database Tables:")
for t in tables:
    print(f"  - {t['name']}")
