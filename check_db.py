import sqlite3
import os

db_path = 'core_data.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for Ouroboros tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Total tables: {len(tables)}")
    print(f"Tables: {tables}")
    
    # Check specifically for Ouroboros tables
    ouroboros_tables = ['agents', 'claude_evolution_decisions', 'agent_arc_performance', 
                       'population_health_metrics', 'claude_memory', 'arc_action_tracking']
    
    found_ouroboros = [t for t in ouroboros_tables if t in tables]
    missing_ouroboros = [t for t in ouroboros_tables if t not in tables]
    
    print(f"\nOuroboros tables found: {found_ouroboros}")
    print(f"Ouroboros tables missing: {missing_ouroboros}")
    
    conn.close()
else:
    print("Database does not exist yet")
