import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

"""Add hot-path indices for attempts, sequences, and lesson tables.

Adds indices to reduce scan costs on common filters:
- winning_sequences: (game_id, level_number, is_active)
- winning_sequences_full_game: (game_id, level_number, is_active)
- sequence_validation_attempts: (sequence_id, agent_id)
- attempts: (mode, role, game_id, level)
- action_proposals_log: (attempt_id, step_idx)
- lesson_interpretations: (game_id, level)
"""

import sqlite3

DB_PATH = "core_data.db"


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def create_index(conn: sqlite3.Connection, sql: str, name: str) -> None:
    try:
        conn.execute(sql)
        print(f"[OK] Index {name}")
    except sqlite3.Error as exc:
        print(f"[WARN] Index {name} skipped: {exc}")


def run() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    if table_exists(conn, "winning_sequences"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_winning_sequences_game_level_active"
            " ON winning_sequences(game_id, level_number, is_active)",
            "idx_winning_sequences_game_level_active",
        )

    if table_exists(conn, "winning_sequences_full_game"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_winning_sequences_full_game_game_active"
            " ON winning_sequences_full_game(game_id, is_active)",
            "idx_winning_sequences_full_game_game_active",
        )

    if table_exists(conn, "sequence_validation_attempts"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_sequence_validation_attempts_seq_agent"
            " ON sequence_validation_attempts(sequence_id, agent_id)",
            "idx_sequence_validation_attempts_seq_agent",
        )

    if table_exists(conn, "attempts"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_attempts_mode_role_game_level"
            " ON attempts(mode, role, game_id, level)",
            "idx_attempts_mode_role_game_level",
        )

    if table_exists(conn, "action_proposals_log"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_action_proposals_attempt_step"
            " ON action_proposals_log(attempt_id, step_idx)",
            "idx_action_proposals_attempt_step",
        )

    if table_exists(conn, "lesson_interpretations"):
        create_index(
            conn,
            "CREATE INDEX IF NOT EXISTS idx_lesson_interpretations_game_level"
            " ON lesson_interpretations(game_id, level)",
            "idx_lesson_interpretations_game_level",
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run()
