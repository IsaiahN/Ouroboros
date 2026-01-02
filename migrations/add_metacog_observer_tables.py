import os
import sqlite3
import sys
from datetime import datetime

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"  # Rule 1: Disable pycache

DB_PATH = "core_data.db"


def add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, definition: str) -> bool:
    """Add a column to a table if it does not already exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column in columns:
        return False
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
    return True


def run_migration() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")

    created_tables = []
    added_columns = []

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS theory_versions (
                version_id TEXT PRIMARY KEY,
                theory_id TEXT NOT NULL,
                version_number INTEGER DEFAULT 1,
                change_summary TEXT,
                assumptions TEXT,
                supporting_evidence TEXT,
                contradicting_evidence TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by_agent TEXT,
                status TEXT DEFAULT 'draft',
                FOREIGN KEY (theory_id) REFERENCES agent_theories(theory_id)
            )
            """
        )
        created_tables.append("theory_versions")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_theory_versions_theory
            ON theory_versions (theory_id, version_number DESC)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS theory_elimination_events (
                elimination_id TEXT PRIMARY KEY,
                theory_id TEXT,
                reason TEXT,
                evidence TEXT,
                eliminated_by_agent TEXT,
                eliminated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                outcome TEXT,
                FOREIGN KEY (theory_id) REFERENCES agent_theories(theory_id)
            )
            """
        )
        created_tables.append("theory_elimination_events")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_theory_elimination_theory
            ON theory_elimination_events (theory_id)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS concept_library (
                concept_id TEXT PRIMARY KEY,
                concept_name TEXT NOT NULL,
                description TEXT,
                example_games TEXT,
                peer_review_status TEXT DEFAULT 'proposed',
                peer_reviewer TEXT,
                peer_reviewed_at TEXT,
                reliability_score REAL DEFAULT 0.5,
                source_attempt_id TEXT,
                source_mode TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        created_tables.append("concept_library")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_concept_library_review
            ON concept_library (peer_review_status, reliability_score DESC)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_biographies (
                biography_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                attempt_id TEXT,
                generation INTEGER,
                role TEXT,
                game_type TEXT,
                level_number INTEGER,
                timeline TEXT,
                mental_model_snapshot TEXT,
                wa_adoptions TEXT,
                wb_adoptions TEXT,
                wa_rejections TEXT,
                wb_rejections TEXT,
                struggles TEXT,
                blind_spots TEXT,
                learning_events TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
                FOREIGN KEY (attempt_id) REFERENCES attempts(attempt_id)
            )
            """
        )
        created_tables.append("agent_biographies")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_agent_biographies_agent
            ON agent_biographies (agent_id, generation)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_struggle_indicators (
                indicator_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                attempt_id TEXT,
                game_type TEXT,
                level_number INTEGER,
                indicator_type TEXT,
                severity TEXT,
                signals TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
                FOREIGN KEY (attempt_id) REFERENCES attempts(attempt_id)
            )
            """
        )
        created_tables.append("agent_struggle_indicators")
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_agent_struggle_indicators_agent
            ON agent_struggle_indicators (agent_id, created_at)
            """
        )

        if add_column_if_missing(cursor, "code_proposals", "pr_url", "pr_url TEXT"):
            added_columns.append("code_proposals.pr_url")
        if add_column_if_missing(cursor, "code_proposals", "pr_status", "pr_status TEXT"):
            added_columns.append("code_proposals.pr_status")
        if add_column_if_missing(cursor, "code_proposals", "pr_number", "pr_number TEXT"):
            added_columns.append("code_proposals.pr_number")
        if add_column_if_missing(cursor, "code_proposals", "commit_sha", "commit_sha TEXT"):
            added_columns.append("code_proposals.commit_sha")

        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        print(f"[ERROR] Migration failed: {exc}")
        sys.exit(1)
    finally:
        conn.close()

    print("[OK] Migration completed")
    if created_tables:
        print(f"  Tables ensured: {', '.join(created_tables)}")
    if added_columns:
        print(f"  Columns added: {', '.join(added_columns)}")
    if not created_tables and not added_columns:
        print("  No changes applied (already up to date)")


if __name__ == "__main__":
    print("=" * 72)
    print("Metacog + Observer Tables Migration")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("DB: core_data.db")
    print("=" * 72)
    run_migration()
