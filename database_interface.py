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
        self._initialize_database_from_template()

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

    def _initialize_database_from_template(self):
        """Initialize database from schema if it doesn't exist."""
        if not os.path.exists(self.db_path):
            # Create database from schema file
            self._create_database_from_schema()
        else:
            logger.debug(f"Database already exists: {self.db_path}")

    def _create_database_from_schema(self):
        """Create database using the schema file."""
        schema_path = Path(__file__).parent / "core_database_schema.sql"

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

    # ========================================================================
    # ALGORITHMIC EVOLUTION SYSTEM METHODS
    # ========================================================================

    def save_algorithm(self, algorithm_id: str, algorithm_type: str,
                      algorithm_data: str, generation: int = 0,
                      parent_ids: List[str] = None, fitness_score: float = 0.0):
        """Save an algorithm to the population.

        Args:
            algorithm_id: Unique algorithm identifier
            algorithm_type: Type of algorithm ('GP', 'VAE_generated', 'hybrid')
            algorithm_data: JSON serialized algorithm representation
            generation: Generation number
            parent_ids: List of parent algorithm IDs
            fitness_score: Current fitness score
        """
        import json

        parent_ids_json = json.dumps(parent_ids) if parent_ids else None

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO algorithm_population (
                    algorithm_id, algorithm_type, algorithm_data, generation,
                    parent_ids, fitness_score, games_evaluated, last_evaluated
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (algorithm_id, algorithm_type, algorithm_data, generation,
                 parent_ids_json, fitness_score, datetime.now()))
            conn.commit()

    def get_algorithms(self, algorithm_type: str = None, generation: int = None,
                      limit: int = None, min_fitness: float = None) -> List[Dict[str, Any]]:
        """Retrieve algorithms from population.

        Args:
            algorithm_type: Filter by algorithm type
            generation: Filter by generation
            limit: Maximum number of algorithms to return
            min_fitness: Minimum fitness score filter

        Returns:
            List of algorithm dictionaries
        """
        import json

        query = "SELECT * FROM algorithm_population WHERE 1=1"
        params = []

        if algorithm_type:
            query += " AND algorithm_type = ?"
            params.append(algorithm_type)

        if generation is not None:
            query += " AND generation = ?"
            params.append(generation)

        if min_fitness is not None:
            query += " AND fitness_score >= ?"
            params.append(min_fitness)

        query += " ORDER BY fitness_score DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                algorithm = dict(row)
                if algorithm['parent_ids']:
                    algorithm['parent_ids'] = json.loads(algorithm['parent_ids'])
                results.append(algorithm)
            return results

    def update_algorithm_fitness(self, algorithm_id: str, fitness_score: float):
        """Update algorithm fitness score.

        Args:
            algorithm_id: Algorithm identifier
            fitness_score: New fitness score
        """
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE algorithm_population
                SET fitness_score = ?, last_evaluated = ?, games_evaluated = games_evaluated + 1
                WHERE algorithm_id = ?
            """, (fitness_score, datetime.now(), algorithm_id))
            conn.commit()

    def save_algorithm_performance(self, algorithm_id: str, game_id: str,
                                 session_id: str, final_score: float,
                                 actions_taken: int, win_detected: bool,
                                 evaluation_context: Dict[str, Any] = None):
        """Save algorithm performance for a specific game.

        Args:
            algorithm_id: Algorithm identifier
            game_id: Game identifier
            session_id: Session identifier
            final_score: Final game score
            actions_taken: Number of actions taken
            win_detected: Whether the game was won
            evaluation_context: Additional evaluation metadata
        """
        import json

        context_json = json.dumps(evaluation_context) if evaluation_context else None

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO algorithm_performance (
                    algorithm_id, game_id, session_id, final_score,
                    actions_taken, win_detected, evaluation_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (algorithm_id, game_id, session_id, final_score,
                 actions_taken, win_detected, context_json))
            conn.commit()

    def get_algorithm_performance(self, algorithm_id: str = None,
                                game_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get algorithm performance data.

        Args:
            algorithm_id: Filter by algorithm ID
            game_id: Filter by game ID
            limit: Maximum number of records

        Returns:
            List of performance records
        """
        import json

        query = "SELECT * FROM algorithm_performance WHERE 1=1"
        params = []

        if algorithm_id:
            query += " AND algorithm_id = ?"
            params.append(algorithm_id)

        if game_id:
            query += " AND game_id = ?"
            params.append(game_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                record = dict(row)
                if record['evaluation_context']:
                    record['evaluation_context'] = json.loads(record['evaluation_context'])
                results.append(record)
            return results

    def save_mab_arm(self, arm_id: str, algorithm_id: str):
        """Create a new MAB arm for an algorithm.

        Args:
            arm_id: Unique arm identifier
            algorithm_id: Associated algorithm identifier
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO mab_arms (
                    arm_id, algorithm_id, total_pulls, total_reward,
                    avg_reward, confidence_interval
                ) VALUES (?, ?, 0, 0.0, 0.0, 1.0)
            """, (arm_id, algorithm_id))
            conn.commit()

    def update_mab_arm(self, arm_id: str, reward: float):
        """Update MAB arm with new reward observation.

        Args:
            arm_id: Arm identifier
            reward: Reward value from this pull
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT total_pulls, total_reward FROM mab_arms WHERE arm_id = ?
            """, (arm_id,))

            row = cursor.fetchone()
            if row:
                total_pulls = row[0] + 1
                total_reward = row[1] + reward
                avg_reward = total_reward / total_pulls

                # Calculate UCB confidence interval (simplified)
                import math
                confidence_interval = math.sqrt(2 * math.log(total_pulls + 1) / total_pulls)

                conn.execute("""
                    UPDATE mab_arms
                    SET total_pulls = ?, total_reward = ?, avg_reward = ?,
                        confidence_interval = ?, last_pulled = ?
                    WHERE arm_id = ?
                """, (total_pulls, total_reward, avg_reward, confidence_interval,
                     datetime.now(), arm_id))
                conn.commit()

    def get_mab_arms(self, algorithm_id: str = None) -> List[Dict[str, Any]]:
        """Get MAB arms data.

        Args:
            algorithm_id: Filter by algorithm ID

        Returns:
            List of MAB arm records
        """
        query = "SELECT * FROM mab_arms"
        params = []

        if algorithm_id:
            query += " WHERE algorithm_id = ?"
            params.append(algorithm_id)

        query += " ORDER BY avg_reward DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def save_evolution_history(self, generation: int, population_size: int,
                             best_fitness: float, avg_fitness: float,
                             diversity_metric: float = None,
                             operations_performed: List[str] = None):
        """Save evolution history record.

        Args:
            generation: Generation number
            population_size: Size of population
            best_fitness: Best fitness in generation
            avg_fitness: Average fitness in generation
            diversity_metric: Population diversity measure
            operations_performed: List of GP operations performed
        """
        import json

        operations_json = json.dumps(operations_performed) if operations_performed else None

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO evolution_history (
                    generation, population_size, best_fitness, avg_fitness,
                    diversity_metric, operations_performed
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (generation, population_size, best_fitness, avg_fitness,
                 diversity_metric, operations_json))
            conn.commit()

    def get_evolution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get evolution history.

        Args:
            limit: Maximum number of records

        Returns:
            List of evolution history records
        """
        import json

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM evolution_history
                ORDER BY generation DESC LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                record = dict(row)
                if record['operations_performed']:
                    record['operations_performed'] = json.loads(record['operations_performed'])
                results.append(record)
            return results

    def get_top_algorithms(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing algorithms using the database view.

        Args:
            limit: Maximum number of algorithms

        Returns:
            List of top algorithm records
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM top_algorithms LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]