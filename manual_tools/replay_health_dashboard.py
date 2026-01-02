import os
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

DB_PATH = os.getenv('DATABASE_PATH', 'core_data.db')
LOOKBACK_HOURS = int(os.getenv('REPLAY_HEALTH_LOOKBACK_HOURS', '24'))


def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


def fetch_attempts(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT mode, role, COUNT(*) as cnt
        FROM attempts
        WHERE created_at >= ?
        GROUP BY mode, role
        ORDER BY cnt DESC
        """,
        (cutoff,),
    )
    return cur.fetchall()


def fetch_hook_failures(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT guard_code, hook_name, COUNT(*) as cnt
        FROM hook_failures
        WHERE timestamp >= ?
        GROUP BY guard_code, hook_name
        ORDER BY cnt DESC
        """,
        (cutoff,),
    )
    return cur.fetchall()


def fetch_guard_codes(conn):
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


def fetch_replay_pointers(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT COUNT(*) as ptrs
        FROM replay_index
        WHERE created_at >= ?
        """,
        (cutoff,),
    )
    row = cur.fetchone()
    return row['ptrs'] if row else 0


def fetch_resonance_counts(conn):
    cutoff = (datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)).isoformat()
    cur = conn.execute(
        """
        SELECT resonance_tags
        FROM action_proposals_log
        WHERE created_at >= ? AND resonance_tags IS NOT NULL
        """,
        (cutoff,),
    )
    counter = Counter()
    for row in cur.fetchall():
        tag = row['resonance_tags']
        if not tag:
            continue
        counter[tag] += 1
    return counter


def main():
    conn = connect(DB_PATH)
    print(f"Replay Health Dashboard (lookback {LOOKBACK_HOURS}h, db={DB_PATH})")
    print("-" * 72)

    attempts = fetch_attempts(conn)
    print("Attempts by mode/role:")
    for row in attempts:
        print(f"  {row['mode']}/{row['role']}: {row['cnt']}")
    if not attempts:
        print("  (none)")

    hooks = fetch_hook_failures(conn)
    print("\nHook failures by guard/hook:")
    for row in hooks:
        gc = row['guard_code'] or 'unknown'
        hn = row['hook_name'] or 'unknown'
        print(f"  {gc} / {hn}: {row['cnt']}")
    if not hooks:
        print("  (none)")

    guards = fetch_guard_codes(conn)
    print("\nGuard codes in attempts:")
    for row in guards:
        gc = row['guard_code'] or 'none'
        print(f"  {gc}: {row['cnt']}")
    if not guards:
        print("  (none)")

    ptrs = fetch_replay_pointers(conn)
    print(f"\nReplay pointers created: {ptrs}")

    resonance = fetch_resonance_counts(conn)
    print("\nResonance tags (top 10):")
    for tag, cnt in resonance.most_common(10):
        print(f"  {tag}: {cnt}")
    if not resonance:
        print("  (none)")

    conn.close()


if __name__ == "__main__":
    main()
