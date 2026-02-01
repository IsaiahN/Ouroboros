import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

"""Add CHECK-like triggers to enforce modes and booleans without table rebuild.

Safe for existing data; aborts invalid INSERT/UPDATE.
"""

import sqlite3

DB_PATH = "core_data.db"

ALLOWED_MODES = ("LIVE", "REPLAY_VALIDATION", "EVAL", "LEGACY")


def create_trigger(conn: sqlite3.Connection, name: str, sql: str) -> None:
    try:
        conn.execute(sql)
        print(f"[OK] Trigger {name}")
    except sqlite3.Error as exc:
        if "already exists" in str(exc).lower():
            print(f"[SKIP] Trigger {name} exists")
        else:
            print(f"[WARN] Trigger {name} skipped: {exc}")


def run() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    mode_list = ",".join(f"'{m}'" for m in ALLOWED_MODES)

    create_trigger(
        conn,
        "tr_attempts_mode_check",
        f"""
        CREATE TRIGGER tr_attempts_mode_check
        BEFORE INSERT ON attempts
        WHEN NEW.mode NOT IN ({mode_list})
        BEGIN
            SELECT RAISE(ABORT, 'invalid mode for attempts');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_attempts_mode_check_update",
        f"""
        CREATE TRIGGER tr_attempts_mode_check_update
        BEFORE UPDATE ON attempts
        WHEN NEW.mode NOT IN ({mode_list})
        BEGIN
            SELECT RAISE(ABORT, 'invalid mode for attempts');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_attempts_guard_flags",
        """
        CREATE TRIGGER tr_attempts_guard_flags
        BEFORE INSERT ON attempts
        WHEN NEW.guard_budget_ok NOT IN (0,1)
          OR NEW.guard_role_ok NOT IN (0,1)
          OR NEW.guard_mode_ok NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid guard flag for attempts');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_attempts_guard_flags_update",
        """
        CREATE TRIGGER tr_attempts_guard_flags_update
        BEFORE UPDATE ON attempts
        WHEN NEW.guard_budget_ok NOT IN (0,1)
          OR NEW.guard_role_ok NOT IN (0,1)
          OR NEW.guard_mode_ok NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid guard flag for attempts');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_action_proposals_mode_check",
        f"""
        CREATE TRIGGER tr_action_proposals_mode_check
        BEFORE INSERT ON action_proposals_log
        WHEN NEW.mode NOT IN ({mode_list})
        BEGIN
            SELECT RAISE(ABORT, 'invalid mode for action_proposals_log');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_action_proposals_mode_check_update",
        f"""
        CREATE TRIGGER tr_action_proposals_mode_check_update
        BEFORE UPDATE ON action_proposals_log
        WHEN NEW.mode NOT IN ({mode_list})
        BEGIN
            SELECT RAISE(ABORT, 'invalid mode for action_proposals_log');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_winning_sequences_active",
        """
        CREATE TRIGGER tr_winning_sequences_active
        BEFORE INSERT ON winning_sequences
        WHEN NEW.is_active NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid is_active for winning_sequences');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_winning_sequences_active_update",
        """
        CREATE TRIGGER tr_winning_sequences_active_update
        BEFORE UPDATE ON winning_sequences
        WHEN NEW.is_active NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid is_active for winning_sequences');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_winning_sequences_full_game_active",
        """
        CREATE TRIGGER tr_winning_sequences_full_game_active
        BEFORE INSERT ON winning_sequences_full_game
        WHEN NEW.is_active NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid is_active for winning_sequences_full_game');
        END;
        """,
    )

    create_trigger(
        conn,
        "tr_winning_sequences_full_game_active_update",
        """
        CREATE TRIGGER tr_winning_sequences_full_game_active_update
        BEFORE UPDATE ON winning_sequences_full_game
        WHEN NEW.is_active NOT IN (0,1)
        BEGIN
            SELECT RAISE(ABORT, 'invalid is_active for winning_sequences_full_game');
        END;
        """,
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run()
