import sqlite3
import pandas as pd

def assess_results():
    conn = sqlite3.connect('core_data.db')
    
    print("=== ASSESSMENT REPORT ===\n")
    
    # 1. Check Strategy Logging
    print("1. Agent Strategy Logging (Last 100 Games):")
    try:
        df = pd.read_sql_query("""
            SELECT strategy_used, COUNT(*) as count 
            FROM agent_arc_performance 
            WHERE game_timestamp > datetime('now', '-24 hours')
            GROUP BY strategy_used
        """, conn)
        print(df)
        if not df.empty and 'agent_strategy' not in df['strategy_used'].values:
            print("SUCCESS: Real strategies are being logged!")
        elif df.empty:
            print("WARNING: No games found in last 24 hours.")
        else:
            print("FAILURE: Generic 'agent_strategy' still present.")
    except Exception as e:
        print(f"Error checking strategies: {e}")
        
    print("\n" + "-"*30 + "\n")
    
    # 2. Check Abstraction Metrics
    print("2. Abstraction Engine Usage:")
    try:
        # Check if table exists first
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='abstraction_metrics'")
        if not cursor.fetchone():
            print("FAILURE: abstraction_metrics table does not exist.")
        else:
            df_abs = pd.read_sql_query("SELECT * FROM abstraction_metrics", conn)
            if df_abs.empty:
                print("WARNING: abstraction_metrics table is empty.")
            else:
                print(f"SUCCESS: Found {len(df_abs)} entries in abstraction_metrics.")
                print(df_abs.head())
    except Exception as e:
        print(f"Error checking abstraction metrics: {e}")

    print("\n" + "-"*30 + "\n")

    # 3. Check System Logs for Abstraction
    print("3. Abstraction Logs:")
    try:
        logs = pd.read_sql_query("""
            SELECT message, timestamp 
            FROM system_logs 
            WHERE message LIKE '%Abstraction%' 
            AND timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
            LIMIT 10
        """, conn)
        if logs.empty:
            print("WARNING: No abstraction logs found.")
        else:
            print(f"Found {len(logs)} abstraction-related logs.")
            for _, row in logs.iterrows():
                print(f"{row['timestamp']}: {row['message']}")
    except Exception as e:
        print(f"Error checking logs: {e}")
        
    conn.close()

if __name__ == "__main__":
    assess_results()
