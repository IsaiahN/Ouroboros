import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from database_interface import DatabaseInterface

db = DatabaseInterface()
schema = db.execute_query('PRAGMA table_info(game_results)')
print('game_results columns:')
for col in schema:
    print(f"  {col['name']} ({col['type']})")
