"""Drop orphaned counterfactual tables that are no longer used."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core_data.db')

print("Connecting to database...")
conn = sqlite3.connect(db_path, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")  # Better for concurrent access
c = conn.cursor()

tables_to_drop = ['counterfactual_learnings', 'counterfactual_scenarios']

for table in tables_to_drop:
    try:
        # Check if table exists and get count
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"  {table}: {count} records")
        
        # Drop it
        c.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"  [OK] Dropped {table}")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print(f"  {table}: already gone")
        else:
            print(f"  [ERROR] {table}: {e}")
    except Exception as e:
        print(f"  [ERROR] {table}: {e}")

conn.commit()
conn.close()
print("\nDone!")
