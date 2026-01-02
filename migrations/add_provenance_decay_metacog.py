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

    added = []

    try:
        # Metacog tables: add provenance + decay/credibility
        for table in (
            "metacognitive_assumptions",
            "metacognitive_eliminations",
            "metacognitive_failure_patterns",
            "metacognitive_insights",
            "metacognitive_predictions",
        ):
            if table_exists(cursor, table):
                if add_column_if_missing(cursor, table, "source_attempt_id", "source_attempt_id TEXT"):
                    added.append(f"{table}.source_attempt_id")
                if add_column_if_missing(cursor, table, "source_mode", "source_mode TEXT"):
                    added.append(f"{table}.source_mode")
                if add_column_if_missing(cursor, table, "last_observed_generation", "last_observed_generation INTEGER DEFAULT 0"):
                    added.append(f"{table}.last_observed_generation")
                if add_column_if_missing(cursor, table, "decay_score", "decay_score REAL DEFAULT 0.0"):
                    added.append(f"{table}.decay_score")
                if add_column_if_missing(cursor, table, "reliability", "reliability REAL DEFAULT 0.5"):
                    added.append(f"{table}.reliability")
                if add_column_if_missing(cursor, table, "consensus", "consensus REAL DEFAULT 0.0"):
                    added.append(f"{table}.consensus")

        # Gap registry and interventions: provenance + decay + attempt FK
        if table_exists(cursor, "gap_registry"):
            if add_column_if_missing(cursor, "gap_registry", "attempt_id", "attempt_id TEXT"):
                added.append("gap_registry.attempt_id")
            if add_column_if_missing(cursor, "gap_registry", "source_mode", "source_mode TEXT"):
                added.append("gap_registry.source_mode")
            if add_column_if_missing(cursor, "gap_registry", "generation", "generation INTEGER"):
                added.append("gap_registry.generation")
            if add_column_if_missing(cursor, "gap_registry", "role", "role TEXT"):
                added.append("gap_registry.role")
            if add_column_if_missing(cursor, "gap_registry", "last_observed_generation", "last_observed_generation INTEGER DEFAULT 0"):
                added.append("gap_registry.last_observed_generation")
            if add_column_if_missing(cursor, "gap_registry", "decay_score", "decay_score REAL DEFAULT 0.0"):
                added.append("gap_registry.decay_score")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_gap_registry_attempt ON gap_registry(attempt_id)"
            )
        if table_exists(cursor, "interventions"):
            if add_column_if_missing(cursor, "interventions", "attempt_id", "attempt_id TEXT"):
                added.append("interventions.attempt_id")
            if add_column_if_missing(cursor, "interventions", "source_mode", "source_mode TEXT"):
                added.append("interventions.source_mode")
            if add_column_if_missing(cursor, "interventions", "generation", "generation INTEGER"):
                added.append("interventions.generation")
            if add_column_if_missing(cursor, "interventions", "role", "role TEXT"):
                added.append("interventions.role")
            if add_column_if_missing(cursor, "interventions", "last_observed_generation", "last_observed_generation INTEGER DEFAULT 0"):
                added.append("interventions.last_observed_generation")
            if add_column_if_missing(cursor, "interventions", "decay_score", "decay_score REAL DEFAULT 0.0"):
                added.append("interventions.decay_score")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_interventions_attempt ON interventions(attempt_id)"
            )

        # Oracle observations: provenance + credibility/decay
        if table_exists(cursor, "oracle_observations"):
            if add_column_if_missing(cursor, "oracle_observations", "source_attempt_id", "source_attempt_id TEXT"):
                added.append("oracle_observations.source_attempt_id")
            if add_column_if_missing(cursor, "oracle_observations", "source_mode", "source_mode TEXT"):
                added.append("oracle_observations.source_mode")
            if add_column_if_missing(cursor, "oracle_observations", "confidence", "confidence REAL DEFAULT 0.5"):
                added.append("oracle_observations.confidence")
            if add_column_if_missing(cursor, "oracle_observations", "last_observed_generation", "last_observed_generation INTEGER DEFAULT 0"):
                added.append("oracle_observations.last_observed_generation")
            if add_column_if_missing(cursor, "oracle_observations", "decay_score", "decay_score REAL DEFAULT 0.0"):
                added.append("oracle_observations.decay_score")

        # Valence associations: provenance + decay
        if table_exists(cursor, "valence_associations"):
            if add_column_if_missing(cursor, "valence_associations", "source_attempt_id", "source_attempt_id TEXT"):
                added.append("valence_associations.source_attempt_id")
            if add_column_if_missing(cursor, "valence_associations", "source_mode", "source_mode TEXT"):
                added.append("valence_associations.source_mode")
            if add_column_if_missing(cursor, "valence_associations", "last_observed_generation", "last_observed_generation INTEGER DEFAULT 0"):
                added.append("valence_associations.last_observed_generation")
            if add_column_if_missing(cursor, "valence_associations", "decay_score", "decay_score REAL DEFAULT 0.0"):
                added.append("valence_associations.decay_score")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_valence_associations_attempt ON valence_associations(source_attempt_id)"
            )

        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        print(f"[ERROR] Migration failed: {exc}")
        sys.exit(1)
    finally:
        conn.close()

    print("[OK] Provenance/decay migration completed")
    if added:
        print("  Columns added: " + ", ".join(added))
    else:
        print("  No changes applied (already up to date)")


if __name__ == "__main__":
    print("=" * 72)
    print("Provenance + Decay for Metacog/Observer Tables")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("DB: core_data.db")
    print("=" * 72)
    run_migration()
