import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()
columns = db.execute_query('PRAGMA table_info(agents)')
print("Agents table columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")
