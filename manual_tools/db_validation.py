import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

"""DB validation helper: checks modes/booleans and PRAGMA settings.
Run manually to surface bad rows without rewriting tables.
"""

import sqlite3

DB_PATH = "core_data.db"
ALLOWED_MODES = {"LIVE", "REPLAY_VALIDATION", "EVAL", "LEGACY"}


def fetchall(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def check_modes(conn):
    bad_attempts = fetchall(
        conn,
        "SELECT attempt_id, mode FROM attempts WHERE mode NOT IN ({})".format(
            ",".join("?" for _ in ALLOWED_MODES)
        ),
        tuple(ALLOWED_MODES),
    )
    bad_actions = fetchall(
        conn,
        "SELECT id, mode FROM action_proposals_log WHERE mode NOT IN ({})".format(
            ",".join("?" for _ in ALLOWED_MODES)
        ),
        tuple(ALLOWED_MODES),
    )
    return bad_attempts, bad_actions


def check_booleans(conn):
    bad_attempts = fetchall(
        conn,
        """
        SELECT attempt_id, guard_budget_ok, guard_role_ok, guard_mode_ok
        FROM attempts
        WHERE guard_budget_ok NOT IN (0,1)
           OR guard_role_ok NOT IN (0,1)
           OR guard_mode_ok NOT IN (0,1)
        """,
    )
    bad_ws = fetchall(
        conn,
        "SELECT sequence_id, is_active FROM winning_sequences WHERE is_active NOT IN (0,1)",
    )
    bad_wsg = fetchall(
        conn,
        "SELECT sequence_id, is_active FROM winning_sequences_full_game WHERE is_active NOT IN (0,1)",
    )
    return bad_attempts, bad_ws, bad_wsg


def check_pragmas(conn):
    foreign_keys = fetchall(conn, "PRAGMA foreign_keys;")[0].get("foreign_keys")
    journal_mode = fetchall(conn, "PRAGMA journal_mode;")[0].get("journal_mode")
    return foreign_keys, journal_mode


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    foreign_keys, journal_mode = check_pragmas(conn)
    print(f"PRAGMA foreign_keys={foreign_keys}, journal_mode={journal_mode}")

    bad_attempts_mode, bad_actions_mode = check_modes(conn)
    bad_attempts_bool, bad_ws_bool, bad_wsg_bool = check_booleans(conn)

    if not any([bad_attempts_mode, bad_actions_mode, bad_attempts_bool, bad_ws_bool, bad_wsg_bool]):
        print("[OK] No invalid modes or booleans found")
    else:
        if bad_attempts_mode:
            print("[FAIL] attempts invalid modes:", bad_attempts_mode)
        if bad_actions_mode:
            print("[FAIL] action_proposals_log invalid modes:", bad_actions_mode)
        if bad_attempts_bool:
            print("[FAIL] attempts guard flags invalid:", bad_attempts_bool)
        if bad_ws_bool:
            print("[FAIL] winning_sequences is_active invalid:", bad_ws_bool)
        if bad_wsg_bool:
            print("[FAIL] winning_sequences_full_game is_active invalid:", bad_wsg_bool)

    conn.close()


if __name__ == "__main__":
    main()
