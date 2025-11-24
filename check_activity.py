import sqlite3
import time
import sys

def check_activity():
    conn = sqlite3.connect('core_data.db')
    cursor = conn.cursor()
    
    print("Monitoring for new games (Ctrl+C to stop)...")
    initial_count = cursor.execute("SELECT COUNT(*) FROM agent_arc_performance").fetchone()[0]
    print(f"Initial game count: {initial_count}")
    
    try:
        for _ in range(10):  # Check for 10 iterations (20 seconds)
            current_count = cursor.execute("SELECT COUNT(*) FROM agent_arc_performance").fetchone()[0]
            if current_count > initial_count:
                print(f"✅ NEW ACTIVITY! Games: {current_count} (+{current_count - initial_count})")
                # Get latest timestamp
                last_time = cursor.execute("SELECT MAX(game_timestamp) FROM agent_arc_performance").fetchone()[0]
                print(f"Latest game: {last_time}")
                return
            else:
                print(f"Waiting... ({current_count})")
            time.sleep(2)
            
        print("No new games detected in 20 seconds.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_activity()
