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
            conn.execute("""
                INSERT OR REPLACE INTO game_results (
                    game_id, session_id, start_time, end_time, status,
                    final_score, total_actions, actions_taken, available_actions, win_detected,
                    level_completions, frame_changes, coordinate_attempts,
                    coordinate_successes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_data['game_id'],
                game_data['session_id'],
                game_data.get('start_time', datetime.now()),
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
                game_data.get('coordinate_successes', 0)
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
    # OUROBOROS EXTENSIONS
    # ========================================================================

    def execute_script(self, script: str):
        """Execute SQL script for schema extensions."""
        with self._get_connection() as conn:
            conn.executescript(script)
            conn.commit()

    def store_agent(self, agent_data: Dict[str, Any]):
        """Store agent in database."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO agents (
                    agent_id, agent_type, genome, generation, parent_ids,
                    specialization, created_at, is_active, total_games_played,
                    total_games_won, total_score_achieved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_data['agent_id'],
                agent_data['agent_type'],
                agent_data['genome'],
                agent_data.get('generation', 0),
                agent_data.get('parent_ids', '[]'),
                agent_data['specialization'],
                agent_data.get('created_at', datetime.now().isoformat()),
                agent_data.get('is_active', True),
                agent_data.get('total_games_played', 0),
                agent_data.get('total_games_won', 0),
                agent_data.get('total_score_achieved', 0.0)
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
                reward_data.get('session_id', ''),
                datetime.now().isoformat(),
                reward_data.get('arc_native_rewards', {}).get('final_score', 0.0),
                reward_data.get('arc_native_rewards', {}).get('win_score_threshold', 0.0),
                reward_data.get('arc_native_rewards', {}).get('game_win', False),
                reward_data.get('arc_native_rewards', {}).get('total_actions', 0),
                reward_data.get('derived_metrics', {}).get('score_efficiency', 0.0),
                reward_data.get('derived_metrics', {}).get('win_proximity', 0.0),
                reward_data.get('arc_native_rewards', {}).get('level_progressions', 0),
                'agent_strategy',
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