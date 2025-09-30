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

logger = logging.getLogger(__name__)


class DatabaseInterface:
    """Core database interface for game mechanics."""

    def __init__(self, db_path: str = "core_game_mechanics.db"):
        """Initialize database interface.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_database_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            self._local.connection.execute("PRAGMA journal_mode=WAL")
        return self._local.connection

    def _ensure_database_exists(self):
        """Ensure database exists and is initialized with schema."""
        schema_path = Path(__file__).parent / "core_database_schema.sql"

        with self._get_connection() as conn:
            # Read and execute schema
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn.executescript(schema)
            conn.commit()

        logger.info(f"Database initialized at: {self.db_path}")

    def close(self):
        """Close database connections."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def create_session(self, session_id: str = None, mode: str = "gameplay",
                      game_id: str = None) -> str:
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
            conn.execute("""
                INSERT OR REPLACE INTO game_results (
                    game_id, session_id, start_time, end_time, status,
                    final_score, total_actions, actions_taken, win_detected,
                    level_completions, frame_changes, coordinate_attempts,
                    coordinate_successes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['game_id'],
                game_data['session_id'],
                game_data.get('start_time', datetime.now()),
                game_data.get('end_time', datetime.now()),
                game_data['status'],
                game_data.get('final_score', 0.0),
                game_data.get('total_actions', 0),
                json.dumps(game_data.get('actions_taken', [])),
                game_data.get('win_detected', False),
                game_data.get('level_completions', 0),
                game_data.get('frame_changes', 0),
                game_data.get('coordinate_attempts', 0),
                game_data.get('coordinate_successes', 0)
            ))
            conn.commit()

        logger.debug(f"Saved game result: {game_data['game_id']}")

    def get_game_results(self, session_id: str = None, game_id: str = None,
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

    def save_action_trace(self, trace_data: Dict[str, Any]):
        """Save action trace to database.

        Args:
            trace_data: Dictionary containing action trace data
        """
        required_fields = ['session_id', 'game_id', 'timestamp']
        if not all(field in trace_data for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO action_traces (
                    session_id, game_id, action_number, coordinates,
                    timestamp, frame_before, frame_after, frame_changed,
                    score_before, score_after, score_change, response_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(trace_data.get('response_data')) if trace_data.get('response_data') else None
            ))
            conn.commit()

    def get_action_traces(self, session_id: str = None, game_id: str = None,
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

    def get_action_effectiveness(self, game_id: str = None) -> List[Dict[str, Any]]:
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

    def get_score_history(self, session_id: str = None, game_id: str = None,
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

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

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