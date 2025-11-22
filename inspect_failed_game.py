import sqlite3
import json

db_path = r"C:\Users\Admin\Documents\GitHub\BitterTruth-AI\core_data.db"
game_id = "ft09-b8377d4b7815"

def inspect_game():
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"Inspecting Game: {game_id}")
        cursor.execute("SELECT * FROM game_results WHERE game_id = ?", (game_id,))
        row = cursor.fetchone()
        
        if row:
            for key in row.keys():
                print(f"{key}: {row[key]}")
        else:
            print("Game not found in database.")
            
        print("\nChecking logs for this game:")
        cursor.execute("SELECT * FROM system_logs WHERE message LIKE ? OR extra_data LIKE ?", (f"%{game_id}%", f"%{game_id}%"))
        logs = cursor.fetchall()
        for log in logs:
            print(f"{log['timestamp']} | {log['level']} | {log['message']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    inspect_game()
