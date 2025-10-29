import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from database_interface import DatabaseInterface

db = DatabaseInterface()

tables = ['agent_arc_performance', 'winning_sequences', 'learned_rules', 'curriculum_progress']

for table in tables:
    try:
        columns = db.execute_query(f'PRAGMA table_info({table})')
        print(f"\n{table}:")
        for col in columns:
            print(f"  {col['name']}: {col['type']}")
    except:
        print(f"\n{table}: TABLE DOES NOT EXIST")
