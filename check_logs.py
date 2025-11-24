import sqlite3
import time

def check_logs():
    conn = sqlite3.connect('core_data.db')
    cursor = conn.cursor()
    
    print("Checking System Logs (Last 5 mins):")
    try:
        cursor.execute("""
            SELECT message, timestamp 
            FROM system_logs 
            WHERE timestamp > datetime('now', '-5 minutes') 
            ORDER BY timestamp DESC 
            LIMIT 50
        """)
        rows = cursor.fetchall()
        if not rows:
            print("No recent logs found.")
        else:
            for r in rows:
                print(f"{r[1]}: {r[0]}")
                
        # Specific check for abstraction
        print("\nChecking for Abstraction Init:")
        cursor.execute("""
            SELECT message, timestamp 
            FROM system_logs 
            WHERE message LIKE '%Abstraction engine initialized%'
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            print(f"✅ FOUND: {row[1]}: {row[0]}")
        else:
            print("❌ NOT FOUND: Abstraction init message missing")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_logs()
