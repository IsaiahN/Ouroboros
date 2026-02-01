import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be FIRST before other imports

"""
Frustration Detection & Quorum Sensing System
==============================================

NOTE: The QUORUM SIGNAL EMISSION portion of this system has been DEPRECATED.
The old approach was to emit "mutation_rate" signals which:
1. Were never properly consumed
2. Targeted the wrong response (mutation doesn't help stuck gameplay)
3. Created duplicate spam in the database

This is now SUPERSEDED by network_knowledge_synthesis.py which provides:
- Intelligent knowledge synthesis from stuck agents
- Targeted interventions (extend discovery phase, queue experiments, etc.)
- Integration with Scientific Method Engine, CODS, Q1-Q5

The frustration TRACKING (update_agent_frustration) is still used by
network_knowledge_synthesis to detect quorum conditions.

===== LEGACY DOCSTRING =====

Detects when agents are stuck and triggers network-wide "desperation mode"
through the existing regulatory signal system. Extends regulatory_signal_engine.py.

Following Rule 2: All frustration data stored in database
Following Rule 3: Enhances existing signal system, doesn't replace it
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class FrustrationDetector:
    """
    Detects agent frustration (being stuck with 0 progress) and triggers
    network-wide desperation signals through quorum sensing.

    Frustration Indicators:
    - Zero score improvement over N games
    - Repeated failures on same game
    - Action diversity collapse (spamming same actions)
    - High action count with low results

    Dynamic Quorum System:
    - Quorum threshold scales with team size: 70-80% of agents on game
    - Minimum 3 agents must be frustrated
    - Later generations (with more viral wisdom) use lower threshold (70%)
    - Earlier generations use higher threshold (80%) to prevent premature alarms
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Frustration thresholds
        self.frustrated_threshold = 5  # Games with 0 progress
        self.min_frustrated_count = 3  # Minimum agents that must be frustrated
        self.base_quorum_threshold = 0.80  # Base threshold for early generations
        self.mature_quorum_threshold = 0.70  # Threshold for later generations with viral wisdom
        self.generation_maturity_threshold = 50  # Generation at which network considered "mature"
        self.desperation_signal_strength = 8.0  # Very high priority

        # Initialize schema
        self._initialize_schema()

    def _calculate_dynamic_quorum_threshold(self, generation: int, agents_on_game: int) -> float:
        """
        Calculate dynamic quorum threshold based on generation and team size.

        Philosophy:
        - Early generations (less viral wisdom) -> higher threshold (80%)
          to avoid premature alarms when network is still learning
        - Later generations (more accumulated wisdom) -> lower threshold (70%)
          to detect subtler gaps in understanding
        - Small teams require near-unanimity
        - Large teams require strong majority

        Args:
            generation: Current generation number
            agents_on_game: Number of agents working on this game

        Returns:
            Dynamic quorum threshold (0.70 to 0.80)
        """
        # Calculate maturity factor: 0.0 at gen 0, 1.0 at gen 50+
        maturity_factor = min(1.0, generation / self.generation_maturity_threshold)

        # Interpolate threshold: starts at 80%, moves toward 70% as network matures
        # Early gens: 80% (more conservative, avoid false alarms)
        # Mature gens: 70% (more sensitive, detect subtle gaps)
        threshold = self.base_quorum_threshold - (maturity_factor * (self.base_quorum_threshold - self.mature_quorum_threshold))

        # Adjust slightly for team size:
        # - Very small teams (3-4): require near-unanimity, stay at base threshold
        # - Larger teams (10+): can use the mature threshold more aggressively
        if agents_on_game <= 4:
            # Small teams: keep threshold high (near-unanimity needed)
            threshold = max(threshold, 0.75)
        elif agents_on_game >= 10:
            # Large teams: can be slightly more sensitive
            threshold = threshold - 0.02  # 2% more sensitive

        return threshold

    def _initialize_schema(self):
        """Create frustration tracking tables"""
        try:
            # Agent frustration states
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS agent_frustration_states (
                    agent_id TEXT PRIMARY KEY,
                    generation INTEGER NOT NULL,

                    -- Frustration metrics
                    is_frustrated BOOLEAN DEFAULT FALSE,
                    frustration_level REAL DEFAULT 0.0,  -- 0.0 to 1.0
                    games_without_progress INTEGER DEFAULT 0,
                    consecutive_failures INTEGER DEFAULT 0,
                    action_diversity_score REAL DEFAULT 1.0,  -- 1.0=diverse, 0.0=repetitive

                    -- Frustration triggers
                    stuck_on_game_id TEXT,
                    last_score_improvement REAL DEFAULT 0.0,
                    games_since_improvement INTEGER DEFAULT 0,

                    -- Timestamps
                    became_frustrated_at TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            # Network frustration quorum events
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS frustration_quorum_events (
                    event_id TEXT PRIMARY KEY,
                    generation INTEGER NOT NULL,
                    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Quorum metrics
                    total_agents INTEGER NOT NULL,
                    frustrated_agents INTEGER NOT NULL,
                    frustration_ratio REAL NOT NULL,
                    quorum_reached BOOLEAN NOT NULL,

                    -- Trigger details
                    desperation_signal_id TEXT,  -- Signal emitted if quorum reached
                    signal_strength REAL,

                    -- Network response
                    parameter_adjustments TEXT,  -- JSON: what changed
                    response_timestamp TIMESTAMP,

                    -- Outcome tracking
                    frustration_resolved BOOLEAN DEFAULT FALSE,
                    resolution_generation INTEGER,
                    improvement_observed REAL DEFAULT 0.0
                )
            """)

            # Frustration resolution strategies
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS frustration_resolutions (
                    resolution_id TEXT PRIMARY KEY,
                    quorum_event_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,

                    -- Strategy applied
                    strategy_type TEXT NOT NULL,  -- 'increase_mutation', 'boost_exploration', 'reset_population', etc.
                    strategy_parameters TEXT NOT NULL,  -- JSON

                    -- Effectiveness
                    agents_affected INTEGER DEFAULT 0,
                    frustration_before REAL NOT NULL,
                    frustration_after REAL,
                    resolution_successful BOOLEAN,

                    -- Timestamps
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    measured_at TIMESTAMP,

                    FOREIGN KEY (quorum_event_id) REFERENCES frustration_quorum_events(event_id)
                )
            """)

            # Create indexes
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_frustration_states_frustrated ON agent_frustration_states(is_frustrated)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_frustration_states_level ON agent_frustration_states(frustration_level DESC)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_quorum_events_generation ON frustration_quorum_events(generation)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_quorum_events_reached ON frustration_quorum_events(quorum_reached)")

            self.logger.info("Frustration detection schema initialized")

        except Exception as e:
            self.logger.error(f"Schema initialization error: {e}")

    def update_agent_frustration(self, agent_id: str, game_id: str,
                                 score_achieved: float, previous_best_score: float,
                                 actions_taken: int, generation: int):
        """
        Update agent's frustration state based on game performance.

        Args:
            agent_id: Agent to update
            game_id: Game just played
            score_achieved: Score achieved in this game
            previous_best_score: Agent's previous best on this game
            actions_taken: Actions used
            generation: Current generation
        """
        try:
            # Get current frustration state
            current_state = self.db.execute_query("""
                SELECT * FROM agent_frustration_states WHERE agent_id = ?
            """, (agent_id,))

            if not current_state:
                # Initialize new state
                self._initialize_agent_frustration_state(agent_id, generation)
                current_state = self.db.execute_query("""
                    SELECT * FROM agent_frustration_states WHERE agent_id = ?
                """, (agent_id,))

            state = current_state[0] if current_state else {}

            # Check for progress
            made_progress = score_achieved > previous_best_score
            score_improvement = score_achieved - previous_best_score

            if made_progress:
                # Progress made, reduce frustration
                new_games_without_progress = 0
                new_consecutive_failures = 0
                new_games_since_improvement = 0
                new_is_frustrated = False
                new_frustration_level = max(0.0, state.get('frustration_level', 0.0) - 0.2)

            else:
                # No progress, increase frustration
                new_games_without_progress = state.get('games_without_progress', 0) + 1
                new_consecutive_failures = state.get('consecutive_failures', 0) + (1 if score_achieved == 0 else 0)
                new_games_since_improvement = state.get('games_since_improvement', 0) + 1

                # Calculate frustration level
                frustration_factors = {
                    'no_progress': min(1.0, new_games_without_progress / 10.0),
                    'failures': min(1.0, new_consecutive_failures / 5.0),
                    'stagnation': min(1.0, new_games_since_improvement / 15.0),
                    'action_inefficiency': min(1.0, actions_taken / 100.0) if score_achieved == 0 else 0.0
                }

                new_frustration_level = sum(frustration_factors.values()) / len(frustration_factors)
                new_is_frustrated = new_games_without_progress >= self.frustrated_threshold

            # Calculate action diversity (check last N actions)
            action_diversity = self._calculate_action_diversity(agent_id, game_id)

            # Update state
            self.db.execute_query("""
                UPDATE agent_frustration_states
                SET generation = ?,
                    is_frustrated = ?,
                    frustration_level = ?,
                    games_without_progress = ?,
                    consecutive_failures = ?,
                    action_diversity_score = ?,
                    stuck_on_game_id = ?,
                    last_score_improvement = ?,
                    games_since_improvement = ?,
                    became_frustrated_at = CASE
                        WHEN ? = 1 AND is_frustrated = 0 THEN ?
                        WHEN ? = 0 THEN NULL
                        ELSE became_frustrated_at
                    END,
                    last_updated = ?
                WHERE agent_id = ?
            """, (
                generation, new_is_frustrated, new_frustration_level,
                new_games_without_progress, new_consecutive_failures,
                action_diversity, game_id if not made_progress else None,
                score_improvement, new_games_since_improvement,
                new_is_frustrated, datetime.now().isoformat(),
                new_is_frustrated, datetime.now().isoformat(),
                agent_id
            ))

            if new_is_frustrated and not state.get('is_frustrated', False):
                self.logger.info(f"Agent {agent_id[:8]} became frustrated (level: {new_frustration_level:.2f})")

        except Exception as e:
            self.logger.error(f"Error updating frustration for {agent_id}: {e}")

    def _initialize_agent_frustration_state(self, agent_id: str, generation: int):
        """Initialize frustration state for new agent"""
        try:
            self.db.execute_query("""
                INSERT OR IGNORE INTO agent_frustration_states (
                    agent_id, generation
                ) VALUES (?, ?)
            """, (agent_id, generation))
        except Exception as e:
            self.logger.error(f"Error initializing frustration state: {e}")

    def _calculate_action_diversity(self, agent_id: str, game_id: str) -> float:
        """
        Calculate action diversity score for agent.
        Returns 1.0 for high diversity, 0.0 for repetitive actions.
        """
        try:
            # Get recent actions from this agent
            recent_actions = self.db.execute_query("""
                SELECT action_type FROM arc_action_tracking
                WHERE agent_id = ? AND game_id = ?
                ORDER BY action_timestamp DESC
                LIMIT 20
            """, (agent_id, game_id))

            if not recent_actions or len(recent_actions) < 5:
                return 1.0  # Not enough data, assume diverse

            # Count unique actions
            action_types = [a['action_type'] for a in recent_actions]
            unique_actions = len(set(action_types))
            total_actions = len(action_types)

            # Calculate Shannon entropy (diversity measure)
            from collections import Counter
            counts = Counter(action_types)
            total = sum(counts.values())

            if total == 0:
                return 1.0

            entropy = -sum((count/total) * np.log2(count/total) for count in counts.values() if count > 0)
            max_entropy = np.log2(7)  # Max entropy with 7 possible actions

            diversity_score = entropy / max_entropy if max_entropy > 0 else 1.0

            return diversity_score

        except Exception as e:
            self.logger.error(f"Error calculating action diversity: {e}")
            return 1.0

    def check_frustration_quorum(self, generation: int) -> Optional[str]:
        """
        Check if frustration quorum has been reached for any SPECIFIC GAME.

        Quorum is PER-GAME, not network-wide. It only makes sense to trigger
        desperation mode when multiple agents are stuck on the SAME game,
        not when agents working on different games are frustrated.

        Dynamic Quorum System:
        - Threshold: 70-80% of agents working on a specific game are frustrated
        - Minimum: 3 agents must be frustrated (regardless of percentage)
        - Generation-aware: Later generations with more viral wisdom use lower threshold

        The insight: "agents with access to N generations of viral wisdom are still stuck"
        is valuable data about what the network doesn't know yet.

        Returns:
            quorum_event_id if quorum reached for any game, None otherwise
        """
        try:
            # Get per-game frustration statistics
            # Only consider games where at least 3 agents are working (meaningful quorum)
            per_game_stats = self.db.execute_query("""
                SELECT
                    stuck_on_game_id as game_id,
                    COUNT(*) as agents_on_game,
                    SUM(CASE WHEN is_frustrated = 1 THEN 1 ELSE 0 END) as frustrated_on_game,
                    AVG(frustration_level) as avg_frustration
                FROM agent_frustration_states
                WHERE generation = ?
                  AND stuck_on_game_id IS NOT NULL
                GROUP BY stuck_on_game_id
                HAVING agents_on_game >= 3
            """, (generation,))

            if not per_game_stats:
                return None

            # Check each game for quorum with dynamic threshold
            quorum_games = []
            for stat in per_game_stats:
                game_id = stat['game_id']
                total = stat['agents_on_game']
                frustrated = stat['frustrated_on_game']
                frustration_ratio = frustrated / total if total > 0 else 0.0

                # Calculate dynamic threshold for this specific game
                dynamic_threshold = self._calculate_dynamic_quorum_threshold(generation, total)

                # Quorum reached if:
                # 1. frustration_ratio >= dynamic_threshold (70-80% depending on conditions)
                # 2. AND minimum 3 agents are frustrated (regardless of percentage)
                if frustration_ratio >= dynamic_threshold and frustrated >= self.min_frustrated_count:
                    quorum_games.append({
                        'game_id': game_id,
                        'total': total,
                        'frustrated': frustrated,
                        'ratio': frustration_ratio,
                        'threshold_used': dynamic_threshold,
                        'avg_frustration': stat['avg_frustration']
                    })

            if not quorum_games:
                return None

            # Record quorum event for the most frustrated game
            most_frustrated_game = max(quorum_games, key=lambda g: g['ratio'])
            event_id = f"frust_quorum_{uuid.uuid4().hex[:12]}"

            # Emit desperation signal for the specific game
            desperation_signal_id, signal_strength = self._emit_desperation_signal(
                generation,
                most_frustrated_game['ratio'],
                game_id=most_frustrated_game['game_id']
            )

            self.logger.warning(
                f"[!] GAME-SPECIFIC FRUSTRATION QUORUM: {most_frustrated_game['frustrated']}/"
                f"{most_frustrated_game['total']} agents frustrated on game "
                f"{most_frustrated_game['game_id']} ({most_frustrated_game['ratio']*100:.1f}% >= "
                f"{most_frustrated_game['threshold_used']*100:.0f}% threshold at gen {generation})"
            )

            self.db.execute_query("""
                INSERT INTO frustration_quorum_events (
                    event_id, generation, total_agents, frustrated_agents,
                    frustration_ratio, quorum_reached, desperation_signal_id,
                    signal_strength
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, generation, most_frustrated_game['total'],
                most_frustrated_game['frustrated'],
                most_frustrated_game['ratio'], True, desperation_signal_id,
                signal_strength
            ))

            return event_id

        except Exception as e:
            self.logger.error(f"Error checking frustration quorum: {e}")
            return None

    def _emit_desperation_signal(self, generation: int, frustration_ratio: float,
                                  game_id: Optional[str] = None) -> Tuple[str, float]:
        """
        Emit high-priority desperation signal through regulatory system.

        Now game-specific: signals are targeted to specific games where
        multiple agents are stuck, not broadcast network-wide.

        Args:
            generation: Current generation
            frustration_ratio: Ratio of frustrated agents on this game
            game_id: The specific game causing frustration (optional)

        Returns:
            (signal_id, signal_strength)
        """
        try:
            signal_id = f"sig_desperation_{uuid.uuid4().hex[:12]}"

            # Scale signal strength by severity (lower than before since game-specific)
            signal_strength = self.desperation_signal_strength * (0.5 + frustration_ratio * 0.5)

            # Insert signal directly into regulatory signals table
            # Include game_id in signal_type for game-specific targeting
            signal_type = f'frustration_cascade:{game_id}' if game_id else 'frustration_cascade'

            self.db.execute_query("""
                INSERT INTO network_regulatory_signals (
                    signal_id, generation, signal_type, signal_source_agent,
                    initial_strength, current_strength, target_parameter,
                    adjustment_direction, adjustment_magnitude, expires_generation,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id, generation, signal_type, None,
                signal_strength, signal_strength, 'mutation_rate',
                'increase', 0.10, generation + 5, True  # Shorter duration, smaller magnitude
            ))

            # Also emit exploration boost signal for this game
            exploration_signal_id = f"sig_explore_boost_{uuid.uuid4().hex[:12]}"
            explore_signal_type = f'exploration_need:{game_id}' if game_id else 'exploration_need'

            self.db.execute_query("""
                INSERT INTO network_regulatory_signals (
                    signal_id, generation, signal_type, signal_source_agent,
                    initial_strength, current_strength, target_parameter,
                    adjustment_direction, adjustment_magnitude, expires_generation,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                exploration_signal_id, generation, explore_signal_type, None,
                signal_strength * 0.8, signal_strength * 0.8, 'exploration_ratio',
                'increase', 0.15, generation + 5, True  # Shorter duration, smaller magnitude
            ))

            game_info = f" for game {game_id}" if game_id else ""
            self.logger.info(f"Emitted game-specific desperation signals{game_info}: {signal_id[:16]}")

            return signal_id, signal_strength

        except Exception as e:
            self.logger.error(f"Error emitting desperation signal: {e}")
            return ("error", 0.0)

    def apply_frustration_resolution(self, quorum_event_id: str, generation: int) -> Dict[str, Any]:
        """
        Apply resolution strategies for frustrated population.

        Strategies:
        1. Increase mutation rate (more exploration)
        2. Boost action budgets (more attempts)
        3. Inject diversity (create new random agents)
        4. Reset stuck agents (clear bad habits)
        """
        try:
            # Get quorum event
            event = self.db.execute_query("""
                SELECT * FROM frustration_quorum_events WHERE event_id = ?
            """, (quorum_event_id,))

            if not event:
                return {}

            event = event[0]
            frustration_ratio = event['frustration_ratio']

            # Determine resolution strategies based on frustration severity
            strategies = []

            if frustration_ratio > 0.5:
                # Severe frustration: aggressive intervention
                strategies.extend([
                    {'type': 'increase_mutation', 'magnitude': 0.20},
                    {'type': 'boost_exploration', 'magnitude': 0.30},
                    {'type': 'inject_diversity', 'count': 10}
                ])
            elif frustration_ratio > 0.3:
                # Moderate frustration: standard intervention
                strategies.extend([
                    {'type': 'increase_mutation', 'magnitude': 0.15},
                    {'type': 'boost_exploration', 'magnitude': 0.20}
                ])

            # Apply strategies
            results = []
            for strategy in strategies:
                resolution_id = f"res_{uuid.uuid4().hex[:12]}"

                # Record strategy
                self.db.execute_query("""
                    INSERT INTO frustration_resolutions (
                        resolution_id, quorum_event_id, generation,
                        strategy_type, strategy_parameters, frustration_before
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    resolution_id, quorum_event_id, generation,
                    strategy['type'], json.dumps(strategy), frustration_ratio
                ))

                results.append({
                    'resolution_id': resolution_id,
                    'strategy': strategy
                })

            self.logger.info(f"Applied {len(results)} frustration resolution strategies")

            return {
                'quorum_event_id': quorum_event_id,
                'strategies_applied': len(results),
                'strategies': results
            }

        except Exception as e:
            self.logger.error(f"Error applying frustration resolution: {e}")
            return {}

    def is_frustrated(self, agent_id: Optional[str] = None, generation: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if agent(s) are frustrated.

        This is the public interface for FrustrationDetectionRung.

        Args:
            agent_id: Optional specific agent to check. If None, checks overall network.
            generation: Optional generation. If None, uses current generation.

        Returns:
            Dict with 'is_frustrated', 'reason', 'severity', 'frustration_level'
        """
        try:
            # If no generation provided, get most recent
            if generation is None:
                gen_result = self.db.execute_query("""
                    SELECT MAX(generation) as gen FROM agent_frustration_states
                """)
                generation = gen_result[0]['gen'] if gen_result and gen_result[0]['gen'] else 0

            if agent_id:
                # Check specific agent
                result = self.db.execute_query("""
                    SELECT is_frustrated, frustration_level, games_without_progress,
                           stuck_on_game_id, action_diversity_score
                    FROM agent_frustration_states
                    WHERE agent_id = ? AND generation = ?
                """, (agent_id, generation))

                if result and result[0]:
                    state = result[0]
                    return {
                        'is_frustrated': bool(state.get('is_frustrated', False)),
                        'frustration_level': state.get('frustration_level', 0.0),
                        'reason': f"Agent stuck on {state.get('stuck_on_game_id', 'unknown')} for {state.get('games_without_progress', 0)} games",
                        'severity': min(1.0, state.get('frustration_level', 0) / 5.0),
                        'action_diversity': state.get('action_diversity_score', 0)
                    }
            else:
                # Check network-level frustration
                result = self.db.execute_query("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN is_frustrated = 1 THEN 1 ELSE 0 END) as frustrated,
                        AVG(frustration_level) as avg_level,
                        MAX(frustration_level) as max_level
                    FROM agent_frustration_states
                    WHERE generation = ?
                """, (generation,))

                if result and result[0]:
                    stats = result[0]
                    total = stats.get('total', 0) or 0
                    frustrated = stats.get('frustrated', 0) or 0
                    avg_level = stats.get('avg_level', 0) or 0
                    frustrated_ratio = frustrated / total if total > 0 else 0

                    # Network is frustrated if >30% of agents are frustrated
                    is_frustrated = frustrated_ratio > 0.3 or avg_level > 3.0

                    return {
                        'is_frustrated': is_frustrated,
                        'frustration_level': avg_level,
                        'reason': f"{frustrated}/{total} agents frustrated ({frustrated_ratio*100:.1f}%)",
                        'severity': min(1.0, avg_level / 5.0),
                        'frustrated_count': frustrated,
                        'total_agents': total
                    }

            return {'is_frustrated': False, 'reason': 'No frustration data', 'severity': 0}

        except Exception as e:
            self.logger.error(f"Error checking frustration: {e}")
            return {'is_frustrated': False, 'reason': f'Error: {e}', 'severity': 0}

    def get_frustration_report(self, generation: int) -> Dict[str, Any]:
        """Get current frustration status report"""
        try:
            # Overall statistics
            stats = self.db.execute_query("""
                SELECT
                    COUNT(*) as total_agents,
                    SUM(CASE WHEN is_frustrated = 1 THEN 1 ELSE 0 END) as frustrated_count,
                    AVG(frustration_level) as avg_frustration,
                    MAX(frustration_level) as max_frustration,
                    AVG(games_without_progress) as avg_games_no_progress,
                    AVG(action_diversity_score) as avg_diversity
                FROM agent_frustration_states
                WHERE generation = ?
            """, (generation,))

            # Recent quorum events
            quorum_events = self.db.execute_query("""
                SELECT * FROM frustration_quorum_events
                WHERE generation >= ?
                ORDER BY generation DESC
                LIMIT 5
            """, (generation - 10,))

            # Most frustrated agents
            top_frustrated = self.db.execute_query("""
                SELECT agent_id, frustration_level, games_without_progress,
                       stuck_on_game_id, action_diversity_score
                FROM agent_frustration_states
                WHERE generation = ? AND is_frustrated = 1
                ORDER BY frustration_level DESC
                LIMIT 10
            """, (generation,))

            return {
                'generation': generation,
                'statistics': stats[0] if stats else {},
                'quorum_threshold': self.quorum_threshold,
                'recent_quorum_events': quorum_events,
                'most_frustrated_agents': top_frustrated
            }

        except Exception as e:
            self.logger.error(f"Error generating frustration report: {e}")
            return {}


# Import numpy for entropy calculation
import numpy as np
