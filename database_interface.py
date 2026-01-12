import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Core Database Interface

Handles all database operations for core game mechanics.
Provides clean interface for storing and retrieving game data.
No architect, governor, or director-specific functionality.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
import threading
import uuid
import shutil
import os
import weakref

logger = logging.getLogger(__name__)


class DatabaseInterface:
    """Core database interface for game mechanics."""

    def __init__(self, db_path: str = "core_data.db"):
        """Initialize database interface.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        # Ensure connections close even if caller forgets (prevents ResourceWarning)
        self._finalizer = weakref.finalize(self, DatabaseInterface._finalize_cleanup, weakref.ref(self))
        # Initialize base schema
        self._initialize_database_from_template()
        # Persona submodeling tables must exist even on legacy databases
        self._ensure_persona_tables()
        # Role transition tracking tables must exist for adaptive action limits
        self._ensure_role_transition_tables()

    @staticmethod
    def _finalize_cleanup(self_ref: weakref.ReferenceType):
        inst = self_ref()
        if inst is None:
            return
        try:
            inst.close()
        except Exception:
            pass

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enforce referential integrity on every connection (Phase 0: foreign_keys=ON)
            try:
                self._local.connection.execute("PRAGMA foreign_keys=ON")
            except Exception as e:
                logger.warning(f"Failed to enable foreign_keys pragma: {e}")
            # Enable WAL mode for better concurrent access
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            # Aggressive WAL checkpointing to prevent data loss on force-close
            # Checkpoint every 1000 pages (~4MB) instead of default 1000 pages
            self._local.connection.execute("PRAGMA wal_autocheckpoint=100")  # 400KB
            # Synchronous mode NORMAL for better crash recovery (still fast)
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection

    def _initialize_database_from_template(self):
        """Initialize database from schema if it doesn't exist."""
        if not os.path.exists(self.db_path):
            # Create database from schema file
            self._create_database_from_schema()
        else:
            logger.debug(f"Database already exists: {self.db_path}")

    def _create_database_from_schema(self):
        """Create database using the schema file."""
        schema_path = Path(__file__).parent / "complete_database_schema.sql"

        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Database schema file not found: {schema_path}")

        with self._get_connection() as conn:
            # Read and execute schema
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()

        logger.info(f"Database initialized from schema: {self.db_path}")

    def _ensure_database_exists(self):
        """Ensure database exists with schema (maintained for backward compatibility)."""
        self._create_database_from_schema()

    # --------------------------------------------------------------------
    # Persona Submodeling (profiles, proposals, outcomes, reliability)
    # --------------------------------------------------------------------
    def _ensure_persona_tables(self) -> None:
        """Create persona tables if missing (idempotent)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_profiles (
                    persona_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    persona_type TEXT,
                    role TEXT,
                    stage INTEGER,
                    world_model TEXT,
                    bias_vector TEXT,
                    bias_risk REAL,
                    bias_abstraction REAL,
                    bias_symbolic REAL,
                    persistence_class TEXT DEFAULT 'tactical',
                    lifetime_exposures INTEGER DEFAULT 0,
                    reliability_global REAL DEFAULT 0.5,
                    novelty_bias REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    persona_id TEXT NOT NULL,
                    agent_id TEXT,
                    persona_type TEXT,
                    game_id TEXT,
                    session_id TEXT,
                    level_number INTEGER,
                    step_idx INTEGER,
                    problem_signature TEXT,
                    world_model TEXT,
                    self_identity_snapshot TEXT,
                    action TEXT,
                    rationale_embedding TEXT,
                    confidence REAL DEFAULT 0.5,
                    safety_flag INTEGER DEFAULT 0,
                    novelty_flag INTEGER DEFAULT 0,
                    surprise_score REAL,
                    observer_flags TEXT,
                    synthesis_source TEXT,
                    scorer_score REAL,
                    chosen INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (persona_id) REFERENCES persona_profiles(persona_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    persona_id TEXT,
                    agent_id TEXT,
                    game_id TEXT,
                    level_number INTEGER,
                    delta_score REAL,
                    delta_actions INTEGER,
                    outcome_score REAL,
                    safety_incident INTEGER DEFAULT 0,
                    surprise_score REAL,
                    stuck_flag INTEGER DEFAULT 0,
                    observer_flags TEXT,
                    observer_stuckness REAL,
                    observer_control_loss REAL,
                    observer_confidence_trend TEXT,
                    observer_pattern_tag TEXT,
                    observer_suggested_approach TEXT,
                    observer_veto_unsafe INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES persona_proposals(proposal_id),
                    FOREIGN KEY (persona_id) REFERENCES persona_profiles(persona_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_context_reliability (
                    persona_id TEXT NOT NULL,
                    problem_signature TEXT NOT NULL,
                    reliability_score REAL DEFAULT 0.5,
                    sample_count INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (persona_id, problem_signature),
                    FOREIGN KEY (persona_id) REFERENCES persona_profiles(persona_id)
                )
                """
            )

            # Add new columns if missing (backfill-friendly)
            try:
                cursor.execute("ALTER TABLE persona_profiles ADD COLUMN persistence_class TEXT DEFAULT 'tactical'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE persona_profiles ADD COLUMN lifetime_exposures INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE persona_profiles ADD COLUMN persona_type TEXT")
            except Exception:
                pass
            for col in [
                "bias_risk REAL",
                "bias_abstraction REAL",
                "bias_symbolic REAL"
            ]:
                try:
                    cursor.execute(f"ALTER TABLE persona_profiles ADD COLUMN {col}")
                except Exception:
                    pass

            # Add new columns to proposals/outcomes as needed
            for col_stmt in [
                "persona_type TEXT",
                "synthesis_source TEXT",
                "scorer_score REAL"
            ]:
                try:
                    cursor.execute(f"ALTER TABLE persona_proposals ADD COLUMN {col_stmt}")
                except Exception:
                    pass
            for col_stmt in [
                "observer_stuckness REAL",
                "observer_control_loss REAL",
                "observer_confidence_trend TEXT",
                "observer_pattern_tag TEXT",
                "observer_suggested_approach TEXT",
                "observer_veto_unsafe INTEGER"
            ]:
                try:
                    cursor.execute(f"ALTER TABLE persona_outcomes ADD COLUMN {col_stmt}")
                except Exception:
                    pass

            # Observer logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_observer_logs (
                    log_id TEXT PRIMARY KEY,
                    proposal_id TEXT,
                    persona_id TEXT,
                    agent_id TEXT,
                    problem_signature TEXT,
                    stuckness_level REAL,
                    control_loss REAL,
                    confidence_trend TEXT,
                    pattern_tag TEXT,
                    suggested_approach TEXT,
                    veto_unsafe INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES persona_proposals(proposal_id),
                    FOREIGN KEY (persona_id) REFERENCES persona_profiles(persona_id)
                )
                """
            )

            # Hindsight relabeling table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_hindsight (
                    hindsight_id TEXT PRIMARY KEY,
                    original_proposal_id TEXT NOT NULL,
                    alternative_persona_id TEXT,
                    agent_id TEXT,
                    problem_signature TEXT,
                    estimated_outcome REAL,
                    retrospective_credit REAL,
                    surprise_score REAL,
                    observer_flags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_proposal_id) REFERENCES persona_proposals(proposal_id)
                )
                """
            )

            # Persona metrics (lightweight monitoring)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS persona_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    problem_signature TEXT,
                    synthesis_used INTEGER,
                    observer_veto INTEGER,
                    micro_cf_used INTEGER,
                    hindsight_updates INTEGER,
                    core_ratio REAL,
                    diversity_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()
        except Exception as exc:
            logger.debug(f"Persona table initialization skipped: {exc}")

    def _ensure_role_transition_tables(self) -> None:
        """Create role transition tracking tables if missing (idempotent)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS role_transition_attempts (
                    transition_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    from_role TEXT,
                    to_role TEXT,
                    success_probability REAL,
                    was_successful BOOLEAN,
                    atp_cost REAL,
                    generation INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_role_transition_agent_gen
                ON role_transition_attempts(agent_id, generation)
                """
            )

            conn.commit()
        except Exception as exc:
            logger.error(f"Error ensuring role transition tables: {exc}")

    def upsert_persona_profile(
        self,
        persona_id: str,
        agent_id: Optional[str],
        role: Optional[str] = None,
        persona_type: Optional[str] = None,
        stage: Optional[int] = None,
        world_model: Optional[str] = None,
        bias_vector: Optional[str] = None,
        bias_risk: Optional[float] = None,
        bias_abstraction: Optional[float] = None,
        bias_symbolic: Optional[float] = None,
        persistence_class: Optional[str] = None,
        lifetime_exposures: Optional[int] = None,
        reliability_global: Optional[float] = None,
        novelty_bias: Optional[float] = None,
        stream_type: Optional[str] = None,  # FIX #9: 'A', 'B', or 'neutral'
    ) -> None:
        """Insert or update a persona profile."""
        reliability_value = reliability_global if reliability_global is not None else 0.5
        novelty_value = novelty_bias if novelty_bias is not None else 0.0
        persistence_value = persistence_class if persistence_class is not None else None
        exposures_value = lifetime_exposures if lifetime_exposures is not None else None
        stream_type_value = stream_type if stream_type is not None else 'neutral'  # FIX #9
        
        # FIX #9: Ensure stream_type column exists (ALTER TABLE is idempotent if column exists)
        conn = self._get_connection()
        try:
            conn.execute("ALTER TABLE persona_profiles ADD COLUMN stream_type TEXT DEFAULT 'neutral'")
        except Exception:
            pass  # Column already exists
        
        with conn:
            conn.execute(
                """
                INSERT INTO persona_profiles (
                    persona_id, agent_id, role, stage, world_model, bias_vector,
                    persona_type, bias_risk, bias_abstraction, bias_symbolic,
                    persistence_class, lifetime_exposures, reliability_global, novelty_bias, 
                    stream_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(persona_id) DO UPDATE SET
                    agent_id=excluded.agent_id,
                    role=COALESCE(excluded.role, persona_profiles.role),
                    persona_type=COALESCE(excluded.persona_type, persona_profiles.persona_type),
                    stage=COALESCE(excluded.stage, persona_profiles.stage),
                    world_model=COALESCE(excluded.world_model, persona_profiles.world_model),
                    bias_vector=COALESCE(excluded.bias_vector, persona_profiles.bias_vector),
                    bias_risk=COALESCE(excluded.bias_risk, persona_profiles.bias_risk),
                    bias_abstraction=COALESCE(excluded.bias_abstraction, persona_profiles.bias_abstraction),
                    bias_symbolic=COALESCE(excluded.bias_symbolic, persona_profiles.bias_symbolic),
                    persistence_class=COALESCE(excluded.persistence_class, persona_profiles.persistence_class),
                    lifetime_exposures=COALESCE(excluded.lifetime_exposures, persona_profiles.lifetime_exposures),
                    reliability_global=COALESCE(excluded.reliability_global, persona_profiles.reliability_global),
                    novelty_bias=COALESCE(excluded.novelty_bias, persona_profiles.novelty_bias),
                    stream_type=COALESCE(excluded.stream_type, persona_profiles.stream_type),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    persona_id,
                    agent_id,
                    role,
                    persona_type,
                    stage,
                    world_model,
                    bias_vector,
                    bias_risk,
                    bias_abstraction,
                    bias_symbolic,
                    persistence_value,
                    exposures_value,
                    reliability_value,
                    novelty_value,
                    stream_type_value,
                ),
            )

    def log_persona_proposal(self, payload: Dict[str, Any]) -> str:
        """Persist a persona proposal and return proposal_id."""
        proposal_id = payload.get('proposal_id') or f"pp_{uuid.uuid4().hex[:12]}"
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO persona_proposals (
                    proposal_id, persona_id, agent_id, persona_type, game_id, session_id, level_number, step_idx,
                    problem_signature, world_model, self_identity_snapshot, action, rationale_embedding,
                    confidence, safety_flag, novelty_flag, surprise_score, observer_flags, synthesis_source,
                    scorer_score, chosen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    payload.get('persona_id'),
                    payload.get('agent_id'),
                    payload.get('persona_type'),
                    payload.get('game_id'),
                    payload.get('session_id'),
                    payload.get('level_number'),
                    payload.get('step_idx'),
                    payload.get('problem_signature'),
                    payload.get('world_model'),
                    payload.get('self_identity_snapshot'),
                    payload.get('action'),
                    payload.get('rationale_embedding'),
                    payload.get('confidence', 0.5),
                    1 if payload.get('safety_flag') else 0,
                    1 if payload.get('novelty_flag') else 0,
                    payload.get('surprise_score'),
                    payload.get('observer_flags'),
                    payload.get('synthesis_source'),
                    payload.get('scorer_score'),
                    1 if payload.get('chosen') else 0,
                ),
            )
        return proposal_id

    def log_persona_outcome(self, payload: Dict[str, Any]) -> str:
        """Persist outcome for a persona proposal."""
        outcome_id = payload.get('outcome_id') or f"po_{uuid.uuid4().hex[:12]}"
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO persona_outcomes (
                    outcome_id, proposal_id, persona_id, agent_id, game_id, level_number,
                    delta_score, delta_actions, outcome_score, safety_incident, surprise_score,
                    stuck_flag, observer_flags, observer_stuckness, observer_control_loss,
                    observer_confidence_trend, observer_pattern_tag, observer_suggested_approach,
                    observer_veto_unsafe
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome_id,
                    payload.get('proposal_id'),
                    payload.get('persona_id'),
                    payload.get('agent_id'),
                    payload.get('game_id'),
                    payload.get('level_number'),
                    payload.get('delta_score'),
                    payload.get('delta_actions'),
                    payload.get('outcome_score'),
                    1 if payload.get('safety_incident') else 0,
                    payload.get('surprise_score'),
                    1 if payload.get('stuck_flag') else 0,
                    payload.get('observer_flags'),
                    payload.get('observer_stuckness'),
                    payload.get('observer_control_loss'),
                    payload.get('observer_confidence_trend'),
                    payload.get('observer_pattern_tag'),
                    payload.get('observer_suggested_approach'),
                    1 if payload.get('observer_veto_unsafe') else 0,
                ),
            )
        return outcome_id

    def log_observer_output(self, payload: Dict[str, Any]) -> str:
        """Persist rich observer outputs for a proposal/outcome."""
        log_id = payload.get('log_id') or f"ob_{uuid.uuid4().hex[:12]}"
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO persona_observer_logs (
                    log_id, proposal_id, persona_id, agent_id, problem_signature,
                    stuckness_level, control_loss, confidence_trend, pattern_tag,
                    suggested_approach, veto_unsafe
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    payload.get('proposal_id'),
                    payload.get('persona_id'),
                    payload.get('agent_id'),
                    payload.get('problem_signature'),
                    payload.get('stuckness_level'),
                    payload.get('control_loss'),
                    payload.get('confidence_trend'),
                    payload.get('pattern_tag'),
                    payload.get('suggested_approach'),
                    1 if payload.get('veto_unsafe') else 0,
                ),
            )
        return log_id

    def log_persona_hindsight(self, payload: Dict[str, Any]) -> str:
        """Persist hindsight relabeling / counterfactual credit."""
        hindsight_id = payload.get('hindsight_id') or f"ph_{uuid.uuid4().hex[:12]}"
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO persona_hindsight (
                    hindsight_id, original_proposal_id, alternative_persona_id, agent_id,
                    problem_signature, estimated_outcome, retrospective_credit, surprise_score,
                    observer_flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    hindsight_id,
                    payload.get('original_proposal_id'),
                    payload.get('alternative_persona_id'),
                    payload.get('agent_id'),
                    payload.get('problem_signature'),
                    payload.get('estimated_outcome'),
                    payload.get('retrospective_credit'),
                    payload.get('surprise_score'),
                    payload.get('observer_flags'),
                ),
            )
        return hindsight_id

    def log_persona_metrics(self, payload: Dict[str, Any]) -> None:
        """Persist lightweight persona metrics snapshot."""
        conn = self._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO persona_metrics (
                    agent_id, problem_signature, synthesis_used, observer_veto, micro_cf_used,
                    hindsight_updates, core_ratio, diversity_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.get('agent_id'),
                    payload.get('problem_signature'),
                    1 if payload.get('synthesis_used') else 0,
                    1 if payload.get('observer_veto') else 0,
                    1 if payload.get('micro_cf_used') else 0,
                    payload.get('hindsight_updates') or 0,
                    payload.get('core_ratio'),
                    payload.get('diversity_count'),
                ),
            )

    def update_persona_context_reliability(
        self,
        persona_id: str,
        problem_signature: str,
        delta_score: Optional[float] = None,
        safety_incident: bool = False,
    ) -> None:
        """Incrementally update context-conditional reliability."""
        conn = self._get_connection()
        with conn:
            row = conn.execute(
                "SELECT reliability_score, sample_count FROM persona_context_reliability WHERE persona_id=? AND problem_signature=?",
                (persona_id, problem_signature),
            ).fetchone()
            reliability = 0.5
            samples = 0
            if row:
                reliability = row['reliability_score'] or 0.5
                samples = row['sample_count'] or 0

            # Simple update rule: positive delta nudges up, safety incident nudges down
            adjustment = 0.0
            if delta_score is not None:
                if delta_score > 0:
                    adjustment += 0.05
                elif delta_score < 0:
                    adjustment -= 0.05
            if safety_incident:
                adjustment -= 0.1

            new_reliability = max(0.0, min(1.0, reliability + adjustment))
            conn.execute(
                """
                INSERT INTO persona_context_reliability (persona_id, problem_signature, reliability_score, sample_count, last_updated)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(persona_id, problem_signature) DO UPDATE SET
                    reliability_score=?,
                    sample_count=persona_context_reliability.sample_count + 1,
                    last_updated=CURRENT_TIMESTAMP
                """,
                (
                    persona_id,
                    problem_signature,
                    new_reliability,
                    samples + 1,
                    new_reliability,
                ),
            )

    def get_action_effectiveness(self, game_id: str) -> list:
        """Get action effectiveness data for a game (stub - not yet implemented).
        
        Args:
            game_id: Game ID
            
        Returns:
            Empty list (feature not implemented)
        """
        logger.debug(f"get_action_effectiveness called for {game_id} (stub)")
        return []
    
    def get_action_traces(self, game_id=None, limit=100):
        """Get action traces (stub - returns empty for now)."""
        return []
    
    def get_score_history(self, game_id: str) -> list:
        """Get score history (stub - returns empty for now)."""
        return []
    
    def close(self):
        """Close database connections and checkpoint WAL."""
        if hasattr(self._local, 'connection'):
            try:
                # Force WAL checkpoint to ensure all data is written to main DB file
                # TRUNCATE mode empties the WAL file after checkpoint
                self._local.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._local.connection.commit()
                logger.info("WAL checkpoint completed before closing database")
            except Exception as e:
                logger.warning(f"WAL checkpoint failed (non-critical): {e}")
            finally:
                self._local.connection.close()
                delattr(self._local, 'connection')
        # Detach finalizer now that we handled cleanup explicitly
        if hasattr(self, '_finalizer'):
            try:
                self._finalizer.detach()
            except Exception:
                pass

    def checkpoint_wal(self):
        """
        Force a WAL checkpoint to persist all pending writes to main database file.
        
        This should be called:
        - Before creating checkpoints/backups
        - During graceful shutdown
        - Periodically during long-running operations
        
        Returns:
            bool: True if checkpoint successful, False otherwise
        """
        try:
            conn = self._get_connection()
            # TRUNCATE mode: checkpoint and empty the WAL file
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.commit()
            logger.debug("WAL checkpoint completed")
            return True
        except Exception as e:
            logger.warning(f"WAL checkpoint failed: {e}")
            return False

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def create_session(self, session_id: Optional[str] = None, mode: str = "gameplay",
                      game_id: Optional[str] = None) -> str:
        """Create a new training session.

        Args:
            session_id: Optional session ID, will generate if not provided
            mode: Session mode (default: "gameplay")
            game_id: Optional game ID for session context

        Returns:
            Created session ID
        """
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status
                ) VALUES (?, ?, ?, ?, 'running')
            """, (session_id, game_id, datetime.now(), mode))
            conn.commit()

        logger.info(f"Created session: {session_id}")
        return session_id

    def end_session(self, session_id: str):
        """End a training session.

        Args:
            session_id: Session ID to end
        """
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE training_sessions
                SET end_time = ?, status = 'completed'
                WHERE session_id = ?
            """, (datetime.now(), session_id))
            conn.commit()

        logger.info(f"Ended session: {session_id}")

    def update_session_stats(self, session_id: str, stats: Dict[str, Any]):
        """Update session statistics.

        Args:
            session_id: Session ID to update
            stats: Dictionary of stats to update
        """
        valid_fields = {
            'total_actions', 'total_wins', 'total_games',
            'win_rate', 'avg_score', 'energy_level',
            'memory_operations', 'sleep_cycles'
        }

        # Filter stats to only include valid fields
        filtered_stats = {k: v for k, v in stats.items() if k in valid_fields}

        if not filtered_stats:
            return

        # Build dynamic update query
        set_clause = ", ".join([f"{field} = ?" for field in filtered_stats.keys()])
        query = f"UPDATE training_sessions SET {set_clause} WHERE session_id = ?"

        with self._get_connection() as conn:
            conn.execute(query, list(filtered_stats.values()) + [session_id])
            conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session data or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM training_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    # ========================================================================
    # GAME RESULTS
    # ========================================================================

    def save_game_result(self, game_data: Dict[str, Any]):
        """Save game result to database.

        Args:
            game_data: Dictionary containing game result data
        """
        required_fields = ['game_id', 'session_id', 'status']
        if not all(field in game_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")

        with self._get_connection() as conn:
            # BUG FIX (2025-12-27): Preserve original start_time when updating game result
            # Previously INSERT OR REPLACE would overwrite start_time with datetime.now()
            # when finishing a game, making start_time == end_time
            existing_start_time = None
            if 'start_time' not in game_data:
                cursor = conn.execute("""
                    SELECT start_time FROM game_results 
                    WHERE game_id = ? AND session_id = ?
                """, (game_data['game_id'], game_data['session_id']))
                row = cursor.fetchone()
                if row:
                    existing_start_time = row[0]
            
            # Use existing start_time if found, otherwise use provided or now()
            start_time = game_data.get('start_time') or existing_start_time or datetime.now()
            
            conn.execute("""
                INSERT OR REPLACE INTO game_results (
                    game_id, session_id, scorecard_id, start_time, end_time, status,
                    final_score, total_actions, actions_taken, available_actions, win_detected,
                    level_completions, frame_changes, coordinate_attempts,
                    coordinate_successes, generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['game_id'],
                game_data['session_id'],
                game_data.get('scorecard_id'),  # Store ARC scorecard ID
                start_time,  # Fixed: preserve original start_time
                game_data.get('end_time', datetime.now()),
                game_data['status'],
                game_data.get('final_score', 0.0),
                game_data.get('total_actions', 0),
                json.dumps(game_data.get('actions_taken', [])),
                json.dumps(game_data.get('available_actions', [])),
                game_data.get('win_detected', False),
                game_data.get('level_completions', 0),
                game_data.get('frame_changes', 0),
                game_data.get('coordinate_attempts', 0),
                game_data.get('coordinate_successes', 0),
                game_data.get('generation')  # Generation for cleanup tracking
            ))
            conn.commit()

        logger.debug(f"Saved game result: {game_data['game_id']}")

    def get_game_results(self, session_id: Optional[str] = None, game_id: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get game results.

        Args:
            session_id: Optional session ID filter
            game_id: Optional game ID filter
            limit: Maximum number of results to return

        Returns:
            List of game result dictionaries
        """
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if game_id:
            conditions.append("game_id = ?")
            params.append(game_id)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM game_results
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)

            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # ACTION TRACES
    # ========================================================================

    def log_level_sequence_usage(self, session_id: str, game_id: str, agent_id: str, 
                                  level_number: int, used_sequence: bool, 
                                  sequence_id: Optional[str] = None, 
                                  exploration_mode: Optional[str] = None):
        """Log whether agent used a sequence or explored for a level.
        
        Args:
            session_id: Training session ID
            game_id: Game ID
            agent_id: Agent ID
            level_number: Level number
            used_sequence: True if used existing sequence, False if explored
            sequence_id: Sequence ID if used_sequence=True
            exploration_mode: Exploration strategy if used_sequence=False
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO level_sequence_usage (
                    session_id, game_id, agent_id, level_number,
                    used_sequence, sequence_id, exploration_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, game_id, agent_id, level_number,
                used_sequence, sequence_id, exploration_mode
            ))
            conn.commit()

    def save_action_trace(self, trace_data: Dict[str, Any]):
        """Save action trace to database.

        Args:
            trace_data: Dictionary containing action trace data
        """
        required_fields = ['session_id', 'game_id', 'timestamp']
        if not all(field in trace_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")

        # Generate frame hash for state-aware queries
        frame_hash = None
        if trace_data.get('frame_before'):
            try:
                import hashlib
                frame_data = trace_data['frame_before']
                if isinstance(frame_data, list):
                    # Create a simple hash from frame data
                    frame_str = str(frame_data)[:1000]  # Truncate for performance
                    frame_hash = hashlib.md5(frame_str.encode()).hexdigest()[:16]
            except Exception:
                pass

        # Imagination telemetry (optional fields, used if columns are present)
        budget_total = trace_data.get('budget_total')
        budget_spend = trace_data.get('budget_spend')
        context_mode = trace_data.get('context_mode')
        grounding_score = trace_data.get('grounding_score')
        question_tier = trace_data.get('question_tier')
        persona_proposal_count = trace_data.get('persona_proposal_count')
        counterfactual_rollouts_used = trace_data.get('counterfactual_rollouts_used')
        synthesis_enabled = trace_data.get('synthesis_enabled')
        existential_mode_active = trace_data.get('existential_mode_active')
        imagination_unlock_event = trace_data.get('imagination_unlock_event')

        with self._get_connection() as conn:
            # Ensure new telemetry columns exist before inserting
            self._ensure_action_trace_columns(conn)
            # Try with frame_hash column (new schema)
            try:
                conn.execute("""
                    INSERT INTO action_traces (
                        session_id, game_id, action_number, coordinates,
                        timestamp, frame_before, frame_after, frame_changed,
                        score_before, score_after, score_change, response_data,
                        level_number, resulted_in_game_over, frame_hash,
                        budget_total, budget_spend, context_mode, grounding_score,
                        question_tier, persona_proposal_count, counterfactual_rollouts_used,
                        synthesis_enabled, existential_mode_active, imagination_unlock_event
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trace_data['session_id'],
                    trace_data['game_id'],
                    trace_data.get('action_number', 0),
                    json.dumps(trace_data.get('coordinates')) if trace_data.get('coordinates') else None,
                    trace_data['timestamp'],
                    json.dumps(trace_data.get('frame_before')) if trace_data.get('frame_before') else None,
                    json.dumps(trace_data.get('frame_after')) if trace_data.get('frame_after') else None,
                    trace_data.get('frame_changed', False),
                    trace_data.get('score_before', 0.0),
                    trace_data.get('score_after', 0.0),
                    trace_data.get('score_change', 0.0),
                    json.dumps(trace_data.get('response_data')) if trace_data.get('response_data') else None,
                    trace_data.get('level_number', 1),  # Default to level 1 if not specified
                    trace_data.get('resulted_in_game_over', False),  # Q5: terminal failure tracking
                    frame_hash,  # State signature for context-aware queries
                    budget_total,
                    budget_spend,
                    context_mode,
                    grounding_score,
                    question_tier,
                    persona_proposal_count,
                    counterfactual_rollouts_used,
                    synthesis_enabled,
                    existential_mode_active,
                    imagination_unlock_event
                ))
            except sqlite3.OperationalError:
                # Column doesn't exist yet - add it and retry
                try:
                    conn.execute("ALTER TABLE action_traces ADD COLUMN frame_hash TEXT")
                    self._ensure_action_trace_columns(conn)
                    conn.execute("""
                        INSERT INTO action_traces (
                            session_id, game_id, action_number, coordinates,
                            timestamp, frame_before, frame_after, frame_changed,
                            score_before, score_after, score_change, response_data,
                            level_number, resulted_in_game_over, frame_hash,
                            budget_total, budget_spend, context_mode, grounding_score,
                            question_tier, persona_proposal_count, counterfactual_rollouts_used,
                            synthesis_enabled, existential_mode_active, imagination_unlock_event
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trace_data['session_id'],
                        trace_data['game_id'],
                        trace_data.get('action_number', 0),
                        json.dumps(trace_data.get('coordinates')) if trace_data.get('coordinates') else None,
                        trace_data['timestamp'],
                        json.dumps(trace_data.get('frame_before')) if trace_data.get('frame_before') else None,
                        json.dumps(trace_data.get('frame_after')) if trace_data.get('frame_after') else None,
                        trace_data.get('frame_changed', False),
                        trace_data.get('score_before', 0.0),
                        trace_data.get('score_after', 0.0),
                        trace_data.get('score_change', 0.0),
                        json.dumps(trace_data.get('response_data')) if trace_data.get('response_data') else None,
                        trace_data.get('level_number', 1),
                        trace_data.get('resulted_in_game_over', False),
                        frame_hash,
                        budget_total,
                        budget_spend,
                        context_mode,
                        grounding_score,
                        question_tier,
                        persona_proposal_count,
                        counterfactual_rollouts_used,
                        synthesis_enabled,
                        existential_mode_active,
                        imagination_unlock_event
                    ))
                except Exception:
                    # Fall back to old schema without frame_hash
                    conn.execute("""
                        INSERT INTO action_traces (
                            session_id, game_id, action_number, coordinates,
                            timestamp, frame_before, frame_after, frame_changed,
                            score_before, score_after, score_change, response_data,
                            level_number, resulted_in_game_over
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trace_data['session_id'],
                        trace_data['game_id'],
                        trace_data.get('action_number', 0),
                        json.dumps(trace_data.get('coordinates')) if trace_data.get('coordinates') else None,
                        trace_data['timestamp'],
                        json.dumps(trace_data.get('frame_before')) if trace_data.get('frame_before') else None,
                        json.dumps(trace_data.get('frame_after')) if trace_data.get('frame_after') else None,
                        trace_data.get('frame_changed', False),
                        trace_data.get('score_before', 0.0),
                        trace_data.get('score_after', 0.0),
                        trace_data.get('score_change', 0.0),
                        json.dumps(trace_data.get('response_data')) if trace_data.get('response_data') else None,
                        trace_data.get('level_number', 1),
                        trace_data.get('resulted_in_game_over', False)
                    ))
            conn.commit()

    def _ensure_action_trace_columns(self, conn: sqlite3.Connection) -> None:
        """Ensure action_traces has imagination telemetry columns."""
        try:
            cursor = conn.execute("PRAGMA table_info(action_traces)")
            existing = {row[1] for row in cursor.fetchall()}
            columns = [
                ("budget_total", "REAL"),
                ("budget_spend", "REAL"),
                ("context_mode", "TEXT"),
                ("grounding_score", "REAL"),
                ("question_tier", "TEXT"),
                ("persona_proposal_count", "INTEGER"),
                ("counterfactual_rollouts_used", "INTEGER"),
                ("synthesis_enabled", "BOOLEAN"),
                ("existential_mode_active", "BOOLEAN"),
                ("imagination_unlock_event", "TEXT"),
            ]
            for name, ddl_type in columns:
                if name not in existing:
                    try:
                        conn.execute(f"ALTER TABLE action_traces ADD COLUMN {name} {ddl_type}")
                    except Exception:
                        # Ignore if concurrent migration added it or if locked; best-effort
                        pass
        except Exception:
            # If pragma fails, do nothing to avoid raising during logging
            pass

    def get_action_traces(self, session_id: Optional[str] = None, game_id: Optional[str] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Get action traces.

        Args:
            session_id: Optional session ID filter
            game_id: Optional game ID filter
            limit: Maximum number of traces to return

        Returns:
            List of action trace dictionaries
        """
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if game_id:
            conditions.append("game_id = ?")
            params.append(game_id)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM action_traces
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """, params)

            results = []
            for row in cursor.fetchall():
                trace = dict(row)
                # Parse JSON fields
                for field in ['coordinates', 'frame_before', 'frame_after', 'response_data']:
                    if trace[field]:
                        try:
                            trace[field] = json.loads(trace[field])
                        except json.JSONDecodeError:
                            trace[field] = None
                results.append(trace)

            return results

    # ========================================================================
    # ACTION EFFECTIVENESS
    # ========================================================================

    def update_action_effectiveness(self, game_id: str, action_number: int,
                                  success: bool, score_impact: float = 0.0):
        """Update action effectiveness tracking.

        Args:
            game_id: Game ID
            action_number: Action number (1-7)
            success: Whether the action was successful
            score_impact: Score change from the action
        """
        with self._get_connection() as conn:
            # Get current effectiveness data
            cursor = conn.execute("""
                SELECT attempts, successes, avg_score_impact
                FROM action_effectiveness
                WHERE game_id = ? AND action_number = ?
            """, (game_id, action_number))

            row = cursor.fetchone()

            if row:
                # Update existing record
                attempts = row[0] + 1
                successes = row[1] + (1 if success else 0)
                success_rate = successes / attempts

                # Update average score impact
                current_avg = row[2] or 0.0
                new_avg = ((current_avg * (attempts - 1)) + score_impact) / attempts

                conn.execute("""
                    UPDATE action_effectiveness
                    SET attempts = ?, successes = ?, success_rate = ?,
                        avg_score_impact = ?, last_updated = ?
                    WHERE game_id = ? AND action_number = ?
                """, (attempts, successes, success_rate, new_avg,
                     datetime.now(), game_id, action_number))
            else:
                # Create new record
                success_rate = 1.0 if success else 0.0
                conn.execute("""
                    INSERT INTO action_effectiveness (
                        game_id, action_number, attempts, successes,
                        success_rate, avg_score_impact, last_updated
                    ) VALUES (?, ?, 1, ?, ?, ?, ?)
                """, (game_id, action_number, 1 if success else 0,
                     success_rate, score_impact, datetime.now()))

            conn.commit()

    def get_action_effectiveness(self, game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get action effectiveness data.

        Args:
            game_id: Optional game ID filter

        Returns:
            List of action effectiveness dictionaries
        """
        if game_id:
            query = "SELECT * FROM action_effectiveness WHERE game_id = ? ORDER BY action_number"
            params = (game_id,)
        else:
            query = "SELECT * FROM action_effectiveness ORDER BY game_id, action_number"
            params = ()

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # SCORE HISTORY
    # ========================================================================

    def save_score(self, session_id: str, game_id: str, action_number: int, score: float):
        """Save score to history.

        Args:
            session_id: Session ID
            game_id: Game ID
            action_number: Current action number
            score: Current score
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO score_history (session_id, game_id, action_number, score)
                VALUES (?, ?, ?, ?)
            """, (session_id, game_id, action_number, score))
            conn.commit()

    def get_score_history(self, session_id: Optional[str] = None, game_id: Optional[str] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """Get score history.

        Args:
            session_id: Optional session ID filter
            game_id: Optional game ID filter
            limit: Maximum number of records to return

        Returns:
            List of score history dictionaries
        """
        conditions = []
        params = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if game_id:
            conditions.append("game_id = ?")
            params.append(game_id)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM score_history
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """, params)

            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a custom query.
        
        FIX #16: Auto-commit after write operations so discoveries are
        immediately queryable in the same session.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # FIX #16: Auto-commit after write operations
            # This ensures discoveries made in action N are queryable in action N+1
            query_upper = query.strip().upper()
            if query_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'REPLACE')):
                conn.commit()
            
            return results

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary containing database statistics
        """
        with self._get_connection() as conn:
            stats = {}

            # Table counts
            tables = ['training_sessions', 'game_results', 'action_traces',
                     'action_effectiveness', 'score_history']

            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Recent activity
            cursor = conn.execute("""
                SELECT COUNT(*) FROM training_sessions
                WHERE start_time >= datetime('now', '-24 hours')
            """)
            stats['sessions_last_24h'] = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT COUNT(*) FROM game_results
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            stats['games_last_24h'] = cursor.fetchone()[0]

            return stats

    # ========================================================================
    # OUROBOROS EXTENSIONS
    # ========================================================================

    def execute_script(self, script: str):
        """Execute SQL script for schema extensions."""
        with self._get_connection() as conn:
            conn.executescript(script)
            conn.commit()

    def store_agent(self, agent_data: Dict[str, Any]):
        """Store agent in database.
        
        Fix #3 (CHECKLIST): Include Two-Streams columns so network wisdom isn't empty.
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO agents (
                    agent_id, agent_type, genome, epigenetics, generation, parent_ids,
                    specialization, created_at, is_active, total_games_played,
                    total_games_won, total_score_achieved,
                    self_network_bias, navigation_state, role_confidence, sensation_profile,
                    sensation_learning_rate, state_update_sensitivity, emotional_intelligence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_data['agent_id'],
                agent_data['agent_type'],
                agent_data['genome'],
                agent_data.get('epigenetics'),
                agent_data.get('generation', 0),
                agent_data.get('parent_ids', '[]'),
                agent_data['specialization'],
                agent_data.get('created_at', datetime.now().isoformat()),
                agent_data.get('is_active', True),
                agent_data.get('total_games_played', 0),
                agent_data.get('total_games_won', 0),
                agent_data.get('total_score_achieved', 0.0),
                # Fix #3: Include Two-Streams columns
                agent_data.get('self_network_bias', 0.5),
                agent_data.get('navigation_state', 0.0),
                agent_data.get('role_confidence', 0.5),
                agent_data.get('sensation_profile', '{}'),
                agent_data.get('sensation_learning_rate', 0.3),
                agent_data.get('state_update_sensitivity', 0.7),
                agent_data.get('emotional_intelligence_score', 0.0)
            ))
            conn.commit()

    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get all active agents."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents WHERE is_active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def get_active_agent_count(self) -> int:
        """Get count of active agents."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1")
            return cursor.fetchone()[0]

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def agent_exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        return self.get_agent(agent_id) is not None

    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]):
        """Update agent data."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET
                    agent_type = ?, genome = ?, generation = ?, parent_ids = ?,
                    specialization = ?, is_active = ?, total_games_played = ?,
                    total_games_won = ?, total_score_achieved = ?
                WHERE agent_id = ?
            """, (
                agent_data['agent_type'],
                agent_data['genome'],
                agent_data.get('generation', 0),
                agent_data.get('parent_ids', '[]'),
                agent_data['specialization'],
                agent_data.get('is_active', True),
                agent_data.get('total_games_played', 0),
                agent_data.get('total_games_won', 0),
                agent_data.get('total_score_achieved', 0.0),
                agent_id
            ))
            conn.commit()

    def store_arc_reward_data(self, agent_id: str, reward_data: Dict[str, Any]):
        """Store ARC reward data for agent."""
        with self._get_connection() as conn:
            # FIX (2025-01-11): session_id is NOT NULL in schema
            # Generate a fallback session_id if not provided
            session_id = reward_data.get('session_id') or str(uuid.uuid4())
            
            conn.execute("""
                INSERT INTO agent_arc_performance (
                    performance_id, agent_id, game_id, session_id, game_timestamp,
                    final_score, win_score_threshold, win_achieved, total_actions,
                    score_efficiency, win_proximity, level_progressions,
                    strategy_used, genome_config, base_reward, win_bonus,
                    efficiency_bonus, level_progression_bonus, total_evolutionary_reward
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                agent_id,
                reward_data.get('game_id', ''),
                session_id,
                datetime.now().isoformat(),
                reward_data.get('arc_native_rewards', {}).get('final_score', 0.0),
                reward_data.get('arc_native_rewards', {}).get('win_score_threshold', 0.0),
                reward_data.get('arc_native_rewards', {}).get('game_win', False),
                reward_data.get('arc_native_rewards', {}).get('total_actions', 0),
                reward_data.get('derived_metrics', {}).get('score_efficiency', 0.0),
                reward_data.get('derived_metrics', {}).get('win_proximity', 0.0),
                reward_data.get('arc_native_rewards', {}).get('level_progressions', 0),
                reward_data.get('strategy_used', 'agent_strategy'),
                json.dumps({}),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('base_reward', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('win_bonus', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('efficiency_bonus', 0.0),
                reward_data.get('evolutionary_feedback', {}).get('reward_breakdown', {}).get('level_bonus', 0.0),
                reward_data.get('total_evolutionary_reward', 0.0)
            ))
            conn.commit()

    def get_agent_arc_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent's ARC performance summary."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_games_played,
                    SUM(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END) as total_games_won,
                    AVG(final_score) as avg_score_per_game,
                    AVG(score_efficiency) as score_efficiency,
                    SUM(level_progressions) as level_progressions_detected,
                    AVG(total_evolutionary_reward) as avg_evolutionary_reward
                FROM agent_arc_performance
                WHERE agent_id = ?
            """, (agent_id,))

            row = cursor.fetchone()
            if not row or row[0] == 0:
                return None

            data = dict(row)
            data['win_rate'] = data['total_games_won'] / max(data['total_games_played'], 1)
            data['consistency_score'] = 0.5  # Placeholder
            data['level_progression_rate'] = data['level_progressions_detected'] / max(data['total_games_played'], 1)

            return data

    def sync_agent_performance_to_agents_table(self):
        """
        Sync agent_arc_performance data to agents table.
        Updates total_games_played, total_games_won, avg_score_per_game, score_efficiency.
        Call this after each evaluation cycle.
        """
        with self._get_connection() as conn:
            # Update all agents from their performance data
            conn.execute("""
                UPDATE agents
                SET 
                    total_games_played = (
                        SELECT COUNT(*) 
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    total_games_won = (
                        SELECT SUM(CASE WHEN win_achieved = 1 THEN 1 ELSE 0 END)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    avg_score_per_game = (
                        SELECT AVG(final_score)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    ),
                    score_efficiency = (
                        SELECT AVG(score_efficiency)
                        FROM agent_arc_performance 
                        WHERE agent_id = agents.agent_id
                    )
                WHERE EXISTS (
                    SELECT 1 FROM agent_arc_performance 
                    WHERE agent_id = agents.agent_id
                )
            """)
            conn.commit()
            
            # Return count of agents updated
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT agent_id) 
                FROM agent_arc_performance
            """)
            return cursor.fetchone()[0]

    def get_population_performance_data(self) -> List[Dict[str, Any]]:
        """Get performance data for all agents."""
        agents = self.get_active_agents()
        for agent in agents:
            performance = self.get_agent_arc_performance(agent['agent_id'])
            if performance:
                agent.update(performance)
            else:
                # Set defaults for agents with no performance data
                agent.update({
                    'total_games_played': 0,
                    'total_games_won': 0,
                    'win_rate': 0.0,
                    'avg_score_per_game': 0.0,
                    'score_efficiency': 0.0,
                    'level_progressions_detected': 0
                })
        return agents

    def store_evolution_decision(self, evolution_strategy: Dict[str, Any], performance_data: Dict[str, Any]):
        """Store Claude Code evolution decision."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO claude_evolution_decisions (
                    decision_id, generation, population_analysis, evolution_strategy,
                    reasoning, agents_created, agents_retired, mutations_applied,
                    crossovers_performed, expected_improvement_rate, target_win_rate,
                    strategy_focus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                evolution_strategy.get('generation', 0),
                json.dumps(performance_data),
                json.dumps(evolution_strategy),
                evolution_strategy.get('reasoning', ''),
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                0,  # Will be updated after evolution
                evolution_strategy.get('target_win_rate', 0.0),
                evolution_strategy.get('target_win_rate', 0.0),
                evolution_strategy.get('focus', 'balanced')
            ))
            conn.commit()

    def store_action_tracking(self, action_data: Dict[str, Any]):
        """Store action tracking data."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO arc_action_tracking (
                    action_id, agent_id, game_id, action_type, action_data,
                    coordinate_x, coordinate_y, api_request_sent, api_response_received,
                    coordinate_valid, action_accepted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                action_data['agent_id'],
                action_data.get('game_id', ''),
                action_data['action_type'],
                action_data['action_data'],
                action_data.get('coordinate_x'),
                action_data.get('coordinate_y'),
                action_data['api_request_sent'],
                action_data['api_response_received'],
                action_data.get('coordinate_valid', True),
                action_data.get('action_accepted', True)
            ))
            conn.commit()

    def record_intrinsic_milestone(
        self,
        *,
        hypothesis: str,
        attempt_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        game_type: Optional[str] = None,
        level_number: Optional[int] = None,
        expected_signal: Optional[str] = None,
        observed_signal: Optional[str] = None,
        outcome: Optional[str] = None,
        status: str = "pending",
        milestone_tag: Optional[str] = None,
        confidence: Optional[float] = None,
        evidence: Optional[Any] = None,
        source_mode: Optional[str] = None,
        generation: Optional[int] = None,
        decay_score: Optional[float] = None,
        reliability: Optional[float] = None,
        consensus: Optional[float] = None,
        source_attempt_id: Optional[str] = None,
    ) -> str:
        """Persist a thought experiment/intrinsic milestone telemetry row (DB-only)."""

        if not hypothesis:
            raise ValueError("hypothesis is required for intrinsic milestone")

        milestone_id = f"milestone_{uuid.uuid4().hex[:12]}"
        evidence_payload = json.dumps(evidence) if isinstance(evidence, (dict, list)) else evidence
        provenance_attempt = source_attempt_id or attempt_id
        default_generation = generation if generation is not None else 0

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO intrinsic_milestones (
                    milestone_id, attempt_id, agent_id, game_type, level_number,
                    hypothesis, expected_signal, observed_signal, outcome, status,
                    milestone_tag, confidence, evidence, source_attempt_id,
                    source_mode, generation, last_observed_generation, decay_score,
                    reliability, consensus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    milestone_id,
                    attempt_id,
                    agent_id,
                    game_type,
                    level_number,
                    hypothesis,
                    expected_signal,
                    observed_signal,
                    outcome,
                    status or "pending",
                    milestone_tag,
                    confidence if isinstance(confidence, (int, float)) else None,
                    evidence_payload,
                    provenance_attempt,
                    source_mode,
                    generation,
                    default_generation,
                    decay_score if isinstance(decay_score, (int, float)) else 0.0,
                    reliability if isinstance(reliability, (int, float)) else 0.5,
                    consensus if isinstance(consensus, (int, float)) else 0.0,
                ),
            )
            conn.commit()

        return milestone_id

    # General logging method
    def log_event(self, logger_name: str, level: str, message: str, **kwargs):
        """Log event to system_logs table."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO system_logs (
                    level, logger_name, message, extra_data
                ) VALUES (?, ?, ?, ?)
            """, (
                level,
                logger_name,
                message,
                json.dumps(kwargs) if kwargs else None
            ))
            conn.commit()

    # Placeholder methods for other Ouroboros operations
    def store_coordinator_log(self, log_data: Dict[str, Any]):
        """Store coordinator log entry."""
        self.log_event("coordinator", log_data['event_type'], log_data.get('event_data', '{}'))

    def store_evolution_log(self, log_data: Dict[str, Any]):
        """Store evolution log entry."""
        self.log_event("evolution", log_data['event_type'], log_data.get('event_data', '{}'))

    def store_rlvr_log(self, log_data: Dict[str, Any]):
        """Store RLVR log entry."""
        self.log_event("rlvr", log_data['event_type'], log_data.get('event_data', '{}'))

    def store_analysis_log(self, log_data: Dict[str, Any]):
        """Store analysis log entry."""
        self.log_event("analysis", log_data['event_type'], log_data.get('event_data', '{}'))

    def store_factory_log(self, log_data: Dict[str, Any]):
        """Store factory log entry."""
        self.log_event("factory", log_data['event_type'], log_data.get('event_data', '{}'))

    def store_agent_action(self, agent_id: str, action_record: Dict[str, Any]):
        """Store agent action record."""
        self.log_event("agent_action", f"agent_{agent_id}", json.dumps(action_record))

    def update_agent_performance(self, agent_id: str, performance_update: Dict[str, Any]):
        """Update agent performance data."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE agents SET
                    total_games_played = ?, total_games_won = ?,
                    total_score_achieved = ?, last_performance_update = ?
                WHERE agent_id = ?
            """, (
                performance_update['games_played'],
                performance_update['wins'],
                performance_update['total_score'],
                datetime.now().isoformat(),
                agent_id
            ))
            conn.commit()

    # Additional methods needed by performance analyzer
    def get_performance_data_since(self, since_date):
        """Get performance data since a specific date"""
        # Placeholder - return empty list for now
        return []

    def get_performance_data_before(self, before_date):
        """Get performance data before a specific date"""
        # Placeholder - return empty list for now
        return []

    def store_performance_analysis(self, analysis_data):
        """Store performance analysis results"""
        self.log_event("performance_analysis", "analysis_stored", json.dumps(analysis_data))

    def get_agents_by_generation(self, generation):
        """Get agents by generation"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agents WHERE generation = ?", (generation,))
            return [dict(row) for row in cursor.fetchall()]

    def get_agent_recent_performance(self, agent_id, limit=10):
        """Get agent's recent performance"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM agent_arc_performance
                WHERE agent_id = ?
                ORDER BY game_timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def store_population_fitness_summary(self, summary_data):
        """Store population fitness summary"""
        self.log_event("population_fitness", "summary_stored", json.dumps(summary_data))

    def store_reward_validation(self, validation_data):
        """Store reward validation results"""
        self.log_event("reward_validation", "validation_completed", json.dumps(validation_data))

    def get_agent_detailed_performance(self, agent_id):
        """Get detailed performance data for agent"""
        agent = self.get_agent(agent_id)
        if agent:
            performance = self.get_agent_arc_performance(agent_id)
            if performance:
                agent.update(performance)
        return agent

    def get_agent_performance_history(self, agent_id):
        """Get agent's performance history"""
        return self.get_agent_recent_performance(agent_id, limit=50)