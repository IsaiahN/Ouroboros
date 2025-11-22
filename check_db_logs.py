import sys
import io
import os
import sqlite3

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_logs():
    db_path = "core_data.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"--- System Logs (Last 20) ---")
        cursor.execute("SELECT timestamp, level, message FROM system_logs ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        
        for row in rows:
            try:
                print(f"[{row['timestamp']}] {row['level']}: {row['message']}")
            except Exception:
                print(f"[{row['timestamp']}] {row['level']}: <unicode error>")
            
        print(f"\n--- Recent Game Results ---")
        cursor.execute("SELECT game_id, status, final_score, end_time FROM game_results ORDER BY end_time DESC LIMIT 5")
        rows = cursor.fetchall()
        if not rows:
            print("No game results found.")
        for row in rows:
            print(f"[{row['end_time']}] {row['game_id']}: {row['status']} (Score: {row['final_score']})")
            
        conn.close()
        
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    check_logs()
