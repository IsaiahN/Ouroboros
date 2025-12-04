import sqlite3
import json
from datetime import datetime

db_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\core_data.db"

def check_results():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Checking recent game results...")
        cursor.execute("""
            SELECT game_id, session_id, level_completions, final_score, total_actions, created_at, end_time
            FROM game_results
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No game results found.")
            return

        print(f"{'Game ID':<10} | {'Session ID':<10} | {'Levels':<6} | {'Score':<6} | {'Actions':<7} | {'Created At'}")
        print("-" * 80)
        
        for row in rows:
            print(f"{row['game_id'][:8]:<10} | {row['session_id'][:8]:<10} | {row['level_completions']:<6} | {row['final_score']:<6} | {row['total_actions']:<7} | {row['created_at']}")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_results()
