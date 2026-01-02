import os
import sqlite3
import sys
from datetime import datetime

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Rule 1: disable pycache

DB_PATH = "core_data.db"


def table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migration() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")

    created = False

    try:
        if not table_exists(cursor, "intrinsic_milestones"):
            cursor.execute(
                """
                CREATE TABLE intrinsic_milestones (
                    milestone_id TEXT PRIMARY KEY,
                    attempt_id TEXT,
                    agent_id TEXT,
                    game_type TEXT,
                    level_number INTEGER,
                    hypothesis TEXT NOT NULL,
                    expected_signal TEXT,
                    observed_signal TEXT,
                    outcome TEXT,
                    status TEXT DEFAULT 'pending',
                    milestone_tag TEXT,
                    confidence REAL DEFAULT 0.5,
                    evidence TEXT,
                    source_attempt_id TEXT,
                    source_mode TEXT,
                    generation INTEGER,
                    last_observed_generation INTEGER DEFAULT 0,
                    decay_score REAL DEFAULT 0.0,
                    reliability REAL DEFAULT 0.5,
                    consensus REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_intrinsic_milestones_attempt ON intrinsic_milestones(attempt_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_intrinsic_milestones_game_level ON intrinsic_milestones(game_type, level_number)"
            )
            created = True

        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        print(f"[ERROR] Migration failed: {exc}")
        sys.exit(1)
    finally:
        conn.close()

    print("=" * 72)
    print("Intrinsic Milestones / Thought Experiment Scaffold")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DB: {DB_PATH}")
    if created:
        print("[OK] intrinsic_milestones table created (idempotent)")
    else:
        print("[OK] No changes applied (already present)")


if __name__ == "__main__":
    run_migration()
