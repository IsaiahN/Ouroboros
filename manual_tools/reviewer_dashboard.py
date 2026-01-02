import os
import sqlite3
from datetime import datetime, timedelta

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

DB_PATH = os.getenv('DATABASE_PATH', 'core_data.db')
LOOKBACK_HOURS = int(os.getenv('REVIEW_LOOKBACK_HOURS', '24'))


def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def fetch_guard_summary(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT guard_code, COUNT(*) as cnt
        FROM attempts
        WHERE created_at >= ?
        GROUP BY guard_code
        ORDER BY cnt DESC
        """,
        (cutoff,),
    )
    return cur.fetchall()


def fetch_hook_failures(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT hook_name, guard_code, COUNT(*) as cnt
        FROM hook_failures
        WHERE timestamp >= ?
        GROUP BY hook_name, guard_code
        ORDER BY cnt DESC
        """,
        (cutoff,),
    )
    return cur.fetchall()


def fetch_recent_sequences(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT game_id, level_number, COUNT(*) as cnt
        FROM winning_sequences
        WHERE discovered_at >= ?
        GROUP BY game_id, level_number
        ORDER BY cnt DESC
        LIMIT 20
        """,
        (cutoff,),
    )
    return cur.fetchall()


def main():
    conn = connect(DB_PATH)
    print(f"Reviewer Dashboard (lookback {LOOKBACK_HOURS}h, db={DB_PATH})")
    print("-" * 72)

    guards = fetch_guard_summary(conn)
    print("Guard codes in attempts:")
    for row in guards:
        gc = row['guard_code'] or 'none'
        print(f"  {gc}: {row['cnt']}")
    if not guards:
        print("  (none)")

    hooks = fetch_hook_failures(conn)
    print("\nHook failures:")
    for row in hooks:
        gc = row['guard_code'] or 'unknown'
        hn = row['hook_name'] or 'unknown'
        print(f"  {hn} / {gc}: {row['cnt']}")
    if not hooks:
        print("  (none)")

    seqs = fetch_recent_sequences(conn)
    print("\nRecent sequences added:")
    for row in seqs:
        print(f"  {row['game_id']} L{row['level_number']}: {row['cnt']}")
    if not seqs:
        print("  (none)")

    conn.close()


if __name__ == "__main__":
    main()
