import sqlite3
import pandas as pd

def inspect_db():
    conn = sqlite3.connect('core_data.db')
    try:
        # Check last 5 entries in agent_arc_performance
        print("Last 5 entries in agent_arc_performance:")
        df = pd.read_sql_query("SELECT * FROM agent_arc_performance ORDER BY rowid DESC LIMIT 5", conn)
        print(df)
        
        # Check timestamp format
        if not df.empty:
            print("\nTimestamp format sample:", df['game_timestamp'].iloc[0])
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_db()
