import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

"""Add attempts/event spine tables, provenance tags, and indices.
- attempts, hook_failures, action_proposals_log, attention_windows,
  theory_validation_states, lesson_interpretations, replay_index,
  gap_registry, interventions, competence_metrics, peer_teaching_graph,
  code_proposals
- provenance columns on sequences/operators
- Two-Streams fields and indices
"""

import sqlite3
from datetime import datetime

DB_PATH = "core_data.db"


def table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def column_exists(conn, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(c[1] == column for c in cols)


def create_table(conn, sql: str, name: str):
    if table_exists(conn, name):
        print(f"[SKIP] {name} exists")
        return
    conn.execute(sql)
    print(f"[OK] Created {name}")


def add_column(conn, table: str, column: str, ddl: str):
    if column_exists(conn, table, column):
        print(f"[SKIP] {table}.{column} exists")
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
    print(f"[OK] Added {table}.{column}")


def create_index(conn, sql: str, name: str):
    try:
        conn.execute(sql)
        print(f"[OK] Index {name}")
    except sqlite3.IntegrityError as exc:
        print(f"[WARN] Index {name} skipped due to integrity error: {exc}")
    except sqlite3.Error as exc:
        print(f"[WARN] Index {name} skipped: {exc}")


def seed_validation_states(conn):
    states = ["PENDING", "TOO_EARLY", "INVALID_SETUP", "VALIDATED", "CONTRADICTED"]
    if not table_exists(conn, "theory_validation_states"):
        return
    for state in states:
        conn.execute(
            "INSERT OR IGNORE INTO theory_validation_states(state) VALUES (?)",
            (state,),
        )
    print("[OK] Seeded theory_validation_states")


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")

    # Phase 1 tables
    create_table(
        conn,
        """
        CREATE TABLE attempts (
          attempt_id TEXT PRIMARY KEY,
          game_id TEXT NOT NULL,
          level INTEGER,
          agent_id TEXT,
          role TEXT NOT NULL,
          mode TEXT NOT NULL CHECK (mode IN ('LIVE','REPLAY_VALIDATION','EVAL')),
          generation INTEGER,
          actions_used INTEGER,
          actions_budget INTEGER,
          game_actions_used INTEGER,
          game_actions_budget INTEGER,
          levels_completed INTEGER,
          score REAL,
          time_ms INTEGER,
          succeeded INTEGER,
          source_sequence_id TEXT,
          source_mode TEXT,
          w_A_weight REAL,
          w_B_weight REAL,
          w_R_weight REAL,
          scorecard_id TEXT,
          guard_budget_ok INTEGER,
          guard_role_ok INTEGER,
          guard_mode_ok INTEGER,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "attempts",
    )

    create_table(
        conn,
        """
        CREATE TABLE hook_failures (
          id INTEGER PRIMARY KEY,
          attempt_id TEXT,
          hook_name TEXT,
          hook_phase TEXT,
          exception_type TEXT,
          message TEXT,
          stack_hash TEXT,
          auto_disabled_flag INTEGER,
          game_id TEXT,
          level INTEGER,
          agent_id TEXT,
          generation INTEGER,
          guard_code TEXT,
          timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "hook_failures",
    )

    create_table(
        conn,
        """
        CREATE TABLE action_proposals_log (
          id INTEGER PRIMARY KEY,
          attempt_id TEXT NOT NULL,
          step_idx INTEGER NOT NULL,
          available_actions TEXT,
          proposals TEXT,
          chosen_action TEXT,
          chosen_reason TEXT,
          w_A REAL,
          w_B REAL,
          w_R REAL,
          resonance_tags TEXT,
          role_compliance TEXT,
          theory_validation_state TEXT,
          attention_window_id TEXT,
          mode TEXT NOT NULL CHECK (mode IN ('LIVE','REPLAY_VALIDATION','EVAL')),
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "action_proposals_log",
    )

    create_table(
        conn,
        """
        CREATE TABLE attention_windows (
          id TEXT PRIMARY KEY,
          attempt_id TEXT NOT NULL,
          step_idx INTEGER NOT NULL,
          bbox TEXT,
          salient_cue TEXT,
          cluster_size INTEGER,
          prior_flag TEXT,
          frame_id TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "attention_windows",
    )

    create_table(
        conn,
        """
        CREATE TABLE theory_validation_states (
          state TEXT PRIMARY KEY
        )
        """,
        "theory_validation_states",
    )

    create_table(
        conn,
        """
        CREATE TABLE lesson_interpretations (
          id INTEGER PRIMARY KEY,
          attempt_id TEXT NOT NULL,
          game_id TEXT,
          level INTEGER,
          interpretation TEXT,
          explains_examples INTEGER,
          fails_examples INTEGER,
          confidence REAL,
          contradictions TEXT,
          coverage_notes TEXT,
          resonance_tags TEXT,
          source_mode TEXT,
          reasoning_tags TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "lesson_interpretations",
    )

    create_table(
        conn,
        """
        CREATE TABLE replay_index (
          id INTEGER PRIMARY KEY,
          attempt_id TEXT NOT NULL,
          scorecard_id TEXT,
          replay_id TEXT,
          arc_game_id TEXT,
          agent_type TEXT,
          tags TEXT,
          local_recording_path TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "replay_index",
    )

    create_table(
        conn,
        """
        CREATE TABLE gap_registry (
          id INTEGER PRIMARY KEY,
          gap_type TEXT NOT NULL,
          root_cause TEXT,
          severity TEXT,
          affected_population INTEGER,
          status TEXT,
          concept_id TEXT,
          detected_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "gap_registry",
    )

    create_table(
        conn,
        """
        CREATE TABLE interventions (
          id INTEGER PRIMARY KEY,
          gap_id INTEGER NOT NULL,
          intervention_type TEXT NOT NULL,
          resources TEXT,
          success_criteria TEXT,
          rollback_conditions TEXT,
          outcome_status TEXT,
          outcome_metrics TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (gap_id) REFERENCES gap_registry(id)
        )
        """,
        "interventions",
    )

    create_table(
        conn,
        """
        CREATE TABLE competence_metrics (
          id INTEGER PRIMARY KEY,
          agent_id TEXT NOT NULL,
          generation INTEGER,
          game_id TEXT,
          level INTEGER,
          prediction_accuracy REAL,
          theory_coherence REAL,
          transfer_rate REAL,
          explanation_quality REAL,
          metacog_calibration REAL,
          recovery_rate REAL,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "competence_metrics",
    )

    create_table(
        conn,
        """
        CREATE TABLE peer_teaching_graph (
          id INTEGER PRIMARY KEY,
          teacher_agent_id TEXT NOT NULL,
          learner_agent_id TEXT NOT NULL,
          concept_id TEXT,
          outcome TEXT,
          adoption_success INTEGER,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "peer_teaching_graph",
    )

    create_table(
        conn,
        """
        CREATE TABLE code_proposals (
          id INTEGER PRIMARY KEY,
          branch_name TEXT NOT NULL,
          gap_id INTEGER,
          description TEXT,
          risk TEXT,
          impact TEXT,
          tests TEXT,
          canary_metrics TEXT,
          status TEXT,
          mode TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "code_proposals",
    )

    # Phase 2 columns: provenance and Two-Streams
    add_column(conn, "winning_sequences", "source_attempt_id", "source_attempt_id TEXT")
    add_column(conn, "winning_sequences", "source_mode", "source_mode TEXT")
    add_column(conn, "winning_sequences_full_game", "source_attempt_id", "source_attempt_id TEXT")
    add_column(conn, "winning_sequences_full_game", "source_mode", "source_mode TEXT")
    add_column(conn, "viral_information_packages", "source_attempt_id", "source_attempt_id TEXT")
    add_column(conn, "viral_information_packages", "source_mode", "source_mode TEXT")
    add_column(conn, "network_object_control_hypotheses", "source_attempt_id", "source_attempt_id TEXT")
    add_column(conn, "network_object_control_hypotheses", "source_mode", "source_mode TEXT")

    add_column(conn, "winning_sequences", "w_A", "w_A REAL")
    add_column(conn, "winning_sequences", "w_B", "w_B REAL")
    add_column(conn, "winning_sequences", "w_R", "w_R REAL")
    add_column(conn, "action_proposals_log", "w_A_mix", "w_A_mix REAL")
    add_column(conn, "action_proposals_log", "w_B_mix", "w_B_mix REAL")
    add_column(conn, "action_proposals_log", "w_R_mix", "w_R_mix REAL")

    # Indices and unique constraints
    create_index(
        conn,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_winning_sequences_active "
        "ON winning_sequences(game_id, level_number) WHERE is_active = 1",
        "idx_winning_sequences_active",
    )
    create_index(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_winning_sequences_full_game_game "
        "ON winning_sequences_full_game(game_id)",
        "idx_winning_sequences_full_game_game",
    )
    create_index(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_attempts_mode_role_game_level "
        "ON attempts(mode, role, game_id, level)",
        "idx_attempts_mode_role_game_level",
    )
    create_index(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_action_proposals_attempt_step "
        "ON action_proposals_log(attempt_id, step_idx)",
        "idx_action_proposals_attempt_step",
    )
    create_index(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_replay_index_attempt ON replay_index(attempt_id)",
        "idx_replay_index_attempt",
    )
    create_index(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_replay_index_replay ON replay_index(replay_id, arc_game_id)",
        "idx_replay_index_replay",
    )

    seed_validation_states(conn)

    conn.commit()
    conn.close()
    print("\n[SUCCESS] attempts/event spine migration applied at", datetime.now())


if __name__ == "__main__":
    run()
