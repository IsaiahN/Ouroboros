import sqlite3
from datetime import datetime

DB_PATH = "core_data.db"


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        if not column_exists(conn, "attempts", "scorecard_id"):
            conn.execute("ALTER TABLE attempts ADD COLUMN scorecard_id TEXT")
            conn.commit()
            print(f"[OK] Added scorecard_id to attempts at {datetime.now()}")
        else:
            print("[SKIP] scorecard_id already exists on attempts")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
