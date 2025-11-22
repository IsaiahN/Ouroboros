import sqlite3
import json
from datetime import datetime, timedelta

db_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\core_data.db"

def check_logs():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get logs from the last hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        print("Checking system logs for errors/warnings...")
        cursor.execute("""
            SELECT timestamp, level, logger_name, message, extra_data
            FROM system_logs
            WHERE timestamp >= ? AND (
                level IN ('ERROR', 'WARNING', 'CRITICAL') 
                OR message LIKE '%[GAME_TRACE]%'
                OR message LIKE '%[SEQUENCE REPLAY DEBUG]%'
            )
            ORDER BY timestamp DESC
            LIMIT 50
        """, (one_hour_ago,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No error/warning logs found in the last hour.")
        else:
            print(f"{'Timestamp':<20} | {'Level':<8} | {'Logger':<15} | {'Message'}")
            print("-" * 100)
            for row in rows:
                print(f"{row['timestamp'][:19]:<20} | {row['level']:<8} | {row['logger_name'][:15]:<15} | {row['message']}")
                if row['extra_data']:
                    try:
                        extra = json.loads(row['extra_data'])
                        print(f"  Extra: {extra}")
                    except:
                        print(f"  Extra: {row['extra_data']}")
            
    except Exception as e:
        print(f"Error checking logs: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_logs()
