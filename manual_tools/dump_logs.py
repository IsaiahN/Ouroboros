import sqlite3
import pandas as pd

def dump_logs():
    conn = sqlite3.connect('core_data.db')
    try:
        # Get columns
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(system_logs)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        logs = pd.read_sql_query("SELECT * FROM system_logs WHERE logger_name != 'schema_auto_maintenance' ORDER BY timestamp DESC LIMIT 20", conn)
        print(logs)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    dump_logs()
