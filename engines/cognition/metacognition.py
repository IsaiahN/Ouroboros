"""
Metacognitive Reasoning Engine

Provides metacognitive reasoning capabilities for agents:
1. Prediction BEFORE acting ("if theory is right, X should happen")
2. Assumption tracking (what might be wrong?)
3. Failure pattern analysis (what do failed attempts share?)
4. Elimination tracking (systematic possibility reduction)
5. Post-win reflection (extracting transferable insights)

This shifts agents from "random exploration" to "scientific hypothesis testing".
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


class MetacognitiveReasoningEngine:
    """
    Provides metacognitive reasoning capabilities for agents.

    Philosophy: Strong problem-solvers don't just try things - they:
    1. Make PREDICTIONS before acting ("if theory is right, X should happen")
    2. Track ASSUMPTIONS that might be wrong
    3. Analyze FAILURE PATTERNS (what do failed attempts have in common?)
    4. ELIMINATE possibilities systematically
    5. REFLECT after success to extract transferable insights

    This shifts agents from "random exploration" to "scientific hypothesis testing".
    """

    def __init__(self, db: "DatabaseInterface"):
        """Initialize metacognitive engine."""
        self.db = db
        self._ensure_tables()

        # Provenance for the current session (attempt/mode/generation/role)
        self._session_provenance: Dict[str, Any] = {}

        # Session state (cleared per game)
        self._current_assumptions: List[Dict[str, Any]] = []
        self._pending_prediction: Optional[Dict[str, Any]] = None
        self._failed_attempts: List[Dict[str, Any]] = []
        self._eliminated_actions: set = set()
        self._theory_revisions: List[Dict[str, Any]] = []
        self._current_theory: Optional[str] = None

        # Fix #4: Track contradicted action-object pairs for actionable theory revision
        # Key = action (e.g., 'ACTION1'), Value = list of contradictions
        self._contradicted_actions: Dict[str, List[Dict[str, Any]]] = {}

    def _ensure_tables(self) -> None:
        """Create metacognitive tracking tables."""
        # Track assumptions and their validity
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_assumptions (
                assumption_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The assumption
                assumption_text TEXT NOT NULL,
                assumption_type TEXT NOT NULL,  -- 'control', 'goal', 'obstacle', 'rule'

                -- Status
                is_valid BOOLEAN DEFAULT NULL,  -- NULL = untested, TRUE/FALSE = tested
                tested_at DATETIME,
                test_result TEXT,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Track predictions and outcomes
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_predictions (
                prediction_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The prediction
                theory_text TEXT NOT NULL,
                predicted_outcome TEXT NOT NULL,  -- "score will increase", "object will move right"
                action_taken TEXT NOT NULL,

                -- Outcome
                actual_outcome TEXT,
                prediction_correct BOOLEAN,
                theory_revised BOOLEAN DEFAULT FALSE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Track failure commonalities
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_failure_patterns (
                pattern_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The pattern
                common_factor TEXT NOT NULL,  -- "all failures involved color_3"
                failure_count INTEGER NOT NULL,
                example_actions TEXT,  -- JSON list of actions that failed

                -- Insight derived
                insight TEXT,
                insight_applied BOOLEAN DEFAULT FALSE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Track eliminated possibilities
        # NOTE: This table is for directional actions (ACTION1-5, ACTION7) only
        # ACTION6 (click) uses eliminated_click_coordinates table instead
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_eliminations (
                elimination_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- What was eliminated
                eliminated_action TEXT NOT NULL,  -- "ACTION1", "ACTION2", etc. (NOT ACTION6)
                reason TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,

                -- Evidence
                test_count INTEGER DEFAULT 1,
                consistent_failure BOOLEAN DEFAULT TRUE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Track eliminated CLICK COORDINATES for ACTION6 specifically
        # ACTION6 should never be eliminated as an action type - only specific coordinates
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS eliminated_click_coordinates (
                elimination_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The coordinate that failed
                click_x INTEGER NOT NULL,
                click_y INTEGER NOT NULL,

                -- Evidence
                reason TEXT NOT NULL,
                test_count INTEGER DEFAULT 1,
                consistent_failure BOOLEAN DEFAULT TRUE,

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(game_type, level_number, click_x, click_y)
            )
        """)

        # Track post-win reflections (the key insight)
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS metacognitive_insights (
                insight_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                level_number INTEGER NOT NULL,

                -- The insight
                key_insight TEXT NOT NULL,
                winning_strategy TEXT NOT NULL,

                -- What led to the breakthrough
                breakthrough_action TEXT,
                theory_at_breakthrough TEXT,
                actions_before_breakthrough INTEGER,

                -- Transferability
                is_transferable BOOLEAN DEFAULT FALSE,
                applicable_to TEXT,  -- JSON list of similar game types

                -- Provenance/decay
                source_attempt_id TEXT,
                source_mode TEXT,
                last_observed_generation INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 0.0,
                reliability REAL DEFAULT 0.5,
                consensus REAL DEFAULT 0.0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for fast lookup
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_metacog_assumptions_game
            ON metacognitive_assumptions(game_type, level_number, is_valid)
        """)

    # ========================================================================
    # 1. ASSUMPTION TRACKER
    # ========================================================================

    def register_assumption(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        assumption: str,
        assumption_type: str = 'rule'
    ) -> str:
        """
        Register an assumption the agent is making.

        Examples:
        - "I control the blue object"
        - "Rare colors are goals"
        - "ACTION1 moves me up"
        - "Walls cannot be passed"

        Args:
            agent_id: Agent making assumption
            game_type: Current game type
            level_number: Current level
            assumption: The assumption text
            assumption_type: 'control', 'goal', 'obstacle', 'rule'

        Returns:
            assumption_id
        """
        assumption_id = f"assume_{uuid.uuid4().hex[:12]}"

        self.db.execute_query("""
            INSERT INTO metacognitive_assumptions
            (assumption_id, agent_id, game_type, level_number, assumption_text, assumption_type,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assumption_id,
            agent_id,
            game_type,
            level_number,
            assumption,
            assumption_type,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))

        # Track in session
        self._current_assumptions.append({
            'id': assumption_id,
            'text': assumption,
            'type': assumption_type,
            'tested': False
        })

        logger.debug(f"[METACOG] Registered assumption: {assumption}")
        return assumption_id

    def challenge_assumption(
        self,
        assumption_id: str,
        is_valid: bool,
        test_result: str
    ) -> None:
        """
        Record the result of testing an assumption.

        Args:
            assumption_id: ID of assumption being tested
            is_valid: Whether assumption proved true
            test_result: Description of what happened
        """
        self.db.execute_query("""
            UPDATE metacognitive_assumptions
            SET is_valid = ?, tested_at = datetime('now'), test_result = ?
            WHERE assumption_id = ?
        """, (is_valid, test_result, assumption_id))

        # Update session state
        for a in self._current_assumptions:
            if a['id'] == assumption_id:
                a['tested'] = True
                a['valid'] = is_valid

        status = "CONFIRMED" if is_valid else "DISPROVEN"
        logger.info(f"[METACOG] Assumption {status}: {test_result}")

    def get_untested_assumptions(
        self,
        game_type: str,
        level_number: int
    ) -> List[Dict[str, Any]]:
        """Get assumptions that haven't been tested yet."""
        result = self.db.execute_query("""
            SELECT assumption_id, assumption_text, assumption_type
            FROM metacognitive_assumptions
            WHERE game_type = ? AND level_number = ? AND is_valid IS NULL
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number))

        return result or []

    def get_disproven_assumptions(
        self,
        game_type: str,
        level_number: int
    ) -> List[Dict[str, Any]]:
        """Get assumptions that were proven false - avoid repeating these errors."""
        result = self.db.execute_query("""
            SELECT assumption_text, test_result
            FROM metacognitive_assumptions
            WHERE game_type = ? AND level_number = ? AND is_valid = FALSE
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number))

        return result or []

    # ========================================================================
    # 2. PREDICTION BEFORE ACTION
    # ========================================================================

    def make_prediction(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        theory: str,
        predicted_outcome: str,
        action: str
    ) -> str:
        """
        Make a prediction before taking an action.

        This is the key shift from random exploration to hypothesis testing.

        Examples:
        - Theory: "I control the blue object"
          Prediction: "ACTION1 will move it up"
          Action: "ACTION1"

        - Theory: "Rare colors are goals"
          Prediction: "Touching color_7 will increase score"
          Action: "ACTION4" (move toward color_7)

        Args:
            agent_id: Agent making prediction
            game_type: Current game type
            level_number: Current level
            theory: The underlying theory being tested
            predicted_outcome: What should happen if theory is correct
            action: The action being taken to test

        Returns:
            prediction_id
        """
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"

        self.db.execute_query("""
            INSERT INTO metacognitive_predictions
            (prediction_id, agent_id, game_type, level_number, theory_text, predicted_outcome, action_taken,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id,
            agent_id,
            game_type,
            level_number,
            theory,
            predicted_outcome,
            action,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))

        # Store pending prediction for outcome evaluation
        self._pending_prediction = {
            'id': prediction_id,
            'theory': theory,
            'predicted': predicted_outcome,
            'action': action,
            'game_type': game_type,
            'level_number': level_number,
        }

        self._current_theory = theory

        logger.info(f"[METACOG] PREDICTION: If '{theory}' then {action} should cause '{predicted_outcome}'")
        return prediction_id

    def get_current_prediction(self) -> Optional[Dict[str, Any]]:
        """
        Get the current hypothesis being tested.

        This is the public interface for MetacognitivePredictionRung.

        Returns:
            Dict with 'test_action', 'confidence', 'hypothesis' or None
        """
        if not self._pending_prediction:
            return None

        return {
            'test_action': self._pending_prediction.get('action'),
            'confidence': 0.6,  # Default confidence for active prediction
            'hypothesis': self._pending_prediction.get('theory'),
            'predicted_outcome': self._pending_prediction.get('predicted'),
            'prediction_id': self._pending_prediction.get('id'),
            'game_type': self._pending_prediction.get('game_type'),
            'level': self._pending_prediction.get('level_number')
        }

    def _record_significance_observation(
        self,
        prediction_id: str,
        theory: str,
        game_type: str,
        level_number: int,
        prediction_correct: bool,
        generation: Optional[int],
    ) -> None:
        """Update reliability/consensus and promote strong hypotheses to beliefs."""
        try:
            total_rows = self.db.execute_query(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN prediction_correct = 1 THEN 1 ELSE 0 END) AS successes
                FROM metacognitive_predictions
                WHERE theory_text = ?
            """,
                (theory,),
            ) or []

            total = total_rows[0]['total'] if total_rows and 'total' in total_rows[0] else 0
            successes = total_rows[0]['successes'] if total_rows and 'successes' in total_rows[0] else 0
            reliability = round(successes / total, 3) if total else 0.5
            consensus = reliability  # proxy until cross-agent consensus is recorded
            decay_score = max(0.0, 1.0 - reliability)
            last_gen = generation or self._session_provenance.get('generation') or 0

            self.db.execute_query(
                """
                UPDATE metacognitive_predictions
                SET reliability = ?,
                    consensus = ?,
                    last_observed_generation = ?,
                    decay_score = ?
                WHERE prediction_id = ?
                """,
                (reliability, consensus, last_gen, decay_score, prediction_id),
            )

            # Keep assumptions in sync with observed reliability
            self.db.execute_query(
                """
                UPDATE metacognitive_assumptions
                SET reliability = COALESCE(?, reliability),
                    consensus = COALESCE(?, consensus),
                    last_observed_generation = COALESCE(?, last_observed_generation),
                    decay_score = COALESCE(?, decay_score)
                WHERE game_type = ? AND level_number = ?
                """,
                (reliability, consensus, last_gen, decay_score, game_type, level_number),
            )

            # Promotion: after >=3 observations and reliability >= 0.7, persist as belief/insight
            if total >= 3 and reliability >= 0.7:
                existing = self.db.execute_query(
                    """SELECT insight_id FROM metacognitive_insights
                        WHERE key_insight = ? LIMIT 1""",
                    (theory,),
                )
                if not existing:
                    insight_id = f"insight_{uuid.uuid4().hex[:12]}"
                    self.db.execute_query(
                        """
                        INSERT INTO metacognitive_insights(
                            insight_id, agent_id, game_type, level_number, key_insight, winning_strategy,
                            breakthrough_action, theory_at_breakthrough, actions_before_breakthrough,
                            is_transferable, source_attempt_id, source_mode, last_observed_generation,
                            decay_score, reliability, consensus
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            insight_id,
                            'metacog_auto',
                            game_type,
                            level_number,
                            theory,
                            f"Significance loop confirmed ({successes}/{total})",
                            None,
                            theory,
                            total,
                            True,
                            self._session_provenance.get('attempt_id'),
                            self._session_provenance.get('mode'),
                            last_gen,
                            decay_score,
                            reliability,
                            consensus,
                        ),
                    )
        except Exception:
            logger.debug("Significance observation recording failed (non-critical)")

    def evaluate_prediction(
        self,
        actual_outcome: str,
        score_before: float,
        score_after: float,
        frame_changed: bool,
        generation: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate the pending prediction against actual outcome.

        Returns evaluation with recommendation for theory revision.
        """
        if not self._pending_prediction:
            return {'status': 'no_pending_prediction'}

        pred = self._pending_prediction
        prediction_id = pred['id']

        # Determine if prediction was correct
        predicted = pred['predicted'].lower()
        prediction_correct = False

        # Parse actual_outcome to check for GAME_OVER
        is_game_over = 'game_over' in actual_outcome.lower() if actual_outcome else False

        if 'score' in predicted and 'increase' in predicted:
            # score_increase: Did score go up?
            prediction_correct = score_after > score_before
        elif 'avoid_failure' in predicted or 'avoid' in predicted:
            # avoid_failure: Did agent survive? (NOT game over)
            prediction_correct = not is_game_over
        elif 'frame_change' in predicted:
            # frame_change: Did the frame visibly change?
            prediction_correct = frame_changed
        elif 'object_control' in predicted or 'control' in predicted:
            # object_control: Did clicking/moving cause a change?
            prediction_correct = frame_changed
        elif 'discover_pattern' in predicted or 'discover' in predicted:
            # discover_pattern: Any observable effect counts as discovery
            prediction_correct = frame_changed or score_after != score_before
        elif 'move' in predicted:
            prediction_correct = frame_changed
        elif 'no change' in predicted:
            prediction_correct = not frame_changed
        else:
            # Generic fallback - frame change or score change counts as something happened
            prediction_correct = frame_changed or score_after > score_before

        # Record outcome
        self.db.execute_query("""
            UPDATE metacognitive_predictions
            SET actual_outcome = ?, prediction_correct = ?,
                last_observed_generation = COALESCE(?, last_observed_generation, 0),
                decay_score = COALESCE(decay_score, 0.0)
            WHERE prediction_id = ?
        """, (actual_outcome, prediction_correct, generation, prediction_id))

        result: Dict[str, Any] = {
            'prediction_id': prediction_id,
            'theory': pred['theory'],
            'predicted': pred['predicted'],
            'actual': actual_outcome,
            'correct': prediction_correct
        }

        if prediction_correct:
            logger.info(f"[METACOG] PREDICTION CORRECT: Theory '{pred['theory']}' confirmed!")
            result['recommendation'] = 'strengthen_theory'
        else:
            logger.info(f"[METACOG] PREDICTION WRONG: Expected '{pred['predicted']}', got '{actual_outcome}'")
            result['recommendation'] = 'revise_theory'

            # Queue theory revision
            self._theory_revisions.append({
                'old_theory': pred['theory'],
                'failed_prediction': pred['predicted'],
                'actual': actual_outcome
            })

        # Clear pending prediction
        self._pending_prediction = None

        # Update reliability/consensus and promotion ladder
        self._record_significance_observation(
            prediction_id=prediction_id,
            theory=pred['theory'],
            game_type=pred.get('game_type', 'unknown'),
            level_number=pred.get('level_number', 1),
            prediction_correct=prediction_correct,
            generation=generation,
        )

        return result

    # ========================================================================
    # 3. THEORY REVISION
    # ========================================================================

    def revise_theory(
        self,
        old_theory: str,
        failed_prediction: str,
        actual_outcome: str
    ) -> str:
        """
        Generate a revised theory based on failed prediction.

        Fix #4: Theory revision now AFFECTS behavior by populating
        _contradicted_actions for actionable filtering.

        Returns:
            New theory text
        """
        new_theory = old_theory

        # Fix #4: Extract action from theory/prediction and mark as contradicted
        action_match = re.search(r'ACTION(\d+)', old_theory.upper() + ' ' + failed_prediction.upper())
        if action_match:
            action_str = f"ACTION{action_match.group(1)}"
            if action_str not in self._contradicted_actions:
                self._contradicted_actions[action_str] = []
            self._contradicted_actions[action_str].append({
                'reason': failed_prediction,
                'outcome': actual_outcome,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"[METACOG-FIX4] Marked {action_str} as contradicted: {failed_prediction[:50]}")

        if 'control' in old_theory.lower() and 'no change' in actual_outcome.lower():
            # "I control X" but nothing moved -> probably don't control X
            new_theory = old_theory.replace('I control', 'I might NOT control')

        elif 'goal' in old_theory.lower() and 'no score' in actual_outcome.lower():
            # "X is goal" but score didn't increase -> probably not the goal
            new_theory = old_theory.replace('is a goal', 'is NOT a goal')

        elif 'move' in failed_prediction.lower() and 'blocked' in actual_outcome.lower():
            # Predicted movement but was blocked -> add obstacle awareness
            new_theory = f"{old_theory} (but obstacles block movement)"

        else:
            # Generic revision
            new_theory = f"REVISED: {old_theory} [failed: {failed_prediction}]"

        logger.info(f"[METACOG] THEORY REVISED: '{old_theory}' -> '{new_theory}'")

        self._current_theory = new_theory
        return new_theory

    def get_contradicted_actions(self) -> Dict[str, int]:
        """
        Fix #4: Get actions that have been contradicted by failed theories.

        Returns:
            Dict mapping action string to number of contradictions
        """
        return {action: len(contradictions)
                for action, contradictions in self._contradicted_actions.items()}

    def get_current_theory(self) -> Optional[str]:
        """Get the current working theory."""
        return self._current_theory

    # ========================================================================
    # 4. FAILURE INSIGHT GENERATION (for ContextualFailureRung)
    # ========================================================================

    def _generate_failure_insight(
        self,
        common_factor: str,
        _failures: List[Dict[str, Any]]  # Available for enhanced insight generation
    ) -> str:
        """Generate an insight from failure pattern."""
        if 'ACTION:' in common_factor:
            action = common_factor.replace('ACTION: ', '').replace('ACTION:', '').strip()
            # ACTION6 special case: don't suggest eliminating it entirely
            if action == '6' or action.upper() == 'ACTION6':
                return "Click locations causing death - try clicking different objects or coordinates"
            return f"Stop using ACTION{action} - it consistently causes death/penalty"
        elif 'is_game_over:True' in common_factor:
            return "This action pattern leads to death - find alternative approach"
        elif 'score_delta' in common_factor and '-' in common_factor:
            return "This action causes score penalty - avoid repeating"
        elif 'color' in common_factor.lower():
            return f"Avoid interaction with {common_factor.split(':')[1]} - it leads to death"
        elif 'position' in common_factor.lower():
            return f"This position/area is deadly - avoid or find another route"
        else:
            return f"Pattern detected: {common_factor} causes death/penalty"

    # ========================================================================
    # 5. ELIMINATION TRACKER
    # ========================================================================

    def eliminate_action(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action: str,
        reason: str,
        click_coords: Optional[Tuple[int, int]] = None
    ) -> None:
        """
        Mark an action as eliminated (proven not to work).

        NOTE: ACTION6 (click) should NOT be eliminated as an action type!
              Instead, use eliminate_click_coordinate() with specific coordinates.
        """
        # ACTION6 special handling: eliminate coordinates, not the action type
        action_upper = action.upper()
        if 'ACTION6' in action_upper or action == '6':
            if click_coords:
                self.eliminate_click_coordinate(
                    agent_id=agent_id,
                    game_type=game_type,
                    level_number=level_number,
                    click_x=click_coords[0],
                    click_y=click_coords[1],
                    reason=reason
                )
            else:
                logger.debug("[METACOG] REJECTED: Cannot eliminate ACTION6 as type - use eliminate_click_coordinate")
            return

        # Add to session set (only for non-ACTION6)
        self._eliminated_actions.add(action)

        # Check if already eliminated in DB
        existing = self.db.execute_query("""
            SELECT elimination_id, test_count FROM metacognitive_eliminations
            WHERE agent_id = ? AND game_type = ? AND level_number = ? AND eliminated_action = ?
        """, (agent_id, game_type, level_number, action))

        if existing:
            self.db.execute_query("""
                UPDATE metacognitive_eliminations
                SET test_count = test_count + 1,
                    last_observed_generation = COALESCE(?, last_observed_generation, 0),
                    decay_score = COALESCE(decay_score, 0.0)
                WHERE elimination_id = ?
            """, (
                self._session_provenance.get('generation'),
                existing[0]['elimination_id'],
            ))
        else:
            elimination_id = f"elim_{uuid.uuid4().hex[:12]}"
            self.db.execute_query("""
                INSERT INTO metacognitive_eliminations
                (elimination_id, agent_id, game_type, level_number, eliminated_action, reason,
                 source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elimination_id,
                agent_id,
                game_type,
                level_number,
                action,
                reason,
                self._session_provenance.get('attempt_id'),
                self._session_provenance.get('mode'),
                self._session_provenance.get('generation') or 0,
                0.0,
                0.5,
                0.0,
            ))

        logger.debug(f"[METACOG] ELIMINATED: {action} - {reason}")

    def eliminate_click_coordinate(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        click_x: int,
        click_y: int,
        reason: str
    ) -> None:
        """
        Mark a specific click coordinate as eliminated for ACTION6.

        Unlike eliminate_action() which eliminates an action type entirely,
        this method only eliminates a specific (x, y) coordinate for clicking.
        """
        existing = self.db.execute_query("""
            SELECT elimination_id, test_count FROM eliminated_click_coordinates
            WHERE game_type = ? AND level_number = ? AND click_x = ? AND click_y = ?
        """, (game_type, level_number, click_x, click_y))

        if existing:
            self.db.execute_query("""
                UPDATE eliminated_click_coordinates
                SET test_count = test_count + 1,
                    last_observed_generation = COALESCE(?, last_observed_generation, 0),
                    decay_score = COALESCE(decay_score, 0.0)
                WHERE elimination_id = ?
            """, (
                self._session_provenance.get('generation'),
                existing[0]['elimination_id'],
            ))
        else:
            elimination_id = f"click_elim_{uuid.uuid4().hex[:12]}"
            self.db.execute_query("""
                INSERT INTO eliminated_click_coordinates
                (elimination_id, agent_id, game_type, level_number, click_x, click_y, reason,
                 source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elimination_id,
                agent_id,
                game_type,
                level_number,
                click_x,
                click_y,
                reason,
                self._session_provenance.get('attempt_id'),
                self._session_provenance.get('mode'),
                self._session_provenance.get('generation') or 0,
                0.0,
                0.5,
                0.0,
            ))

        logger.debug(f"[METACOG] ELIMINATED CLICK: ({click_x}, {click_y}) - {reason}")

    def get_eliminated_click_coordinates(
        self,
        game_type: str,
        level_number: int,
        min_test_count: int = 2
    ) -> List[Tuple[int, int]]:
        """
        Get list of click coordinates that have been eliminated for this level.

        Returns:
            List of (x, y) tuples that should be avoided for clicking
        """
        result = self.db.execute_query("""
            SELECT click_x, click_y FROM eliminated_click_coordinates
            WHERE game_type = ? AND level_number = ?
              AND test_count >= ? AND consistent_failure = TRUE
            ORDER BY test_count DESC
        """, (game_type, level_number, min_test_count))

        if not result:
            return []

        return [(r['click_x'], r['click_y']) for r in result]

    def get_eliminated_actions(
        self,
        game_type: str,
        level_number: int,
        min_confidence: float = 0.6
    ) -> List[str]:
        """Get list of actions that have been eliminated for this level."""
        result = self.db.execute_query("""
            SELECT eliminated_action FROM metacognitive_eliminations
            WHERE game_type = ? AND level_number = ?
              AND confidence >= ? AND consistent_failure = TRUE
            ORDER BY test_count DESC
        """, (game_type, level_number, min_confidence))

        db_eliminated = [r['eliminated_action'] for r in (result or [])]

        # Combine with session eliminations
        all_eliminated = set(db_eliminated) | self._eliminated_actions
        return list(all_eliminated)

    def get_remaining_actions(
        self,
        game_type: str,
        level_number: int,
        all_actions: Optional[List[str]] = None
    ) -> List[str]:
        """Get actions that haven't been eliminated yet."""
        if all_actions is None:
            all_actions = [f"ACTION{i}" for i in range(1, 8)]

        eliminated = set(self.get_eliminated_actions(game_type, level_number))
        return [a for a in all_actions if a not in eliminated]

    # ========================================================================
    # 6. POST-WIN REFLECTION
    # ========================================================================

    def record_win_reflection(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        key_insight: str,
        winning_strategy: str,
        breakthrough_action: Optional[str] = None,
        theory_at_breakthrough: Optional[str] = None,
        actions_before_breakthrough: int = 0
    ) -> str:
        """
        Record reflection after winning - what was the key insight?

        Returns:
            insight_id
        """
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"

        # Determine if insight is transferable
        is_transferable = any([
            'all games' in key_insight.lower(),
            'always' in key_insight.lower(),
            'general rule' in key_insight.lower(),
            'pattern' in key_insight.lower()
        ])

        self.db.execute_query("""
            INSERT INTO metacognitive_insights
            (insight_id, agent_id, game_type, level_number, key_insight, winning_strategy,
             breakthrough_action, theory_at_breakthrough, actions_before_breakthrough, is_transferable,
             source_attempt_id, source_mode, last_observed_generation, decay_score, reliability, consensus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id, agent_id, game_type, level_number,
            key_insight, winning_strategy, breakthrough_action,
            theory_at_breakthrough, actions_before_breakthrough, is_transferable,
            self._session_provenance.get('attempt_id'),
            self._session_provenance.get('mode'),
            self._session_provenance.get('generation') or 0,
            0.0,
            0.5,
            0.0,
        ))

        logger.info(f"[METACOG] WIN REFLECTION: '{key_insight}' (strategy: {winning_strategy})")

        return insight_id

    def generate_win_reflection(
        self,
        agent_id: str,
        game_type: str,
        level_number: int,
        action_history: List[str],
        score_history: List[float]
    ) -> Dict[str, Any]:
        """
        Automatically generate win reflection from action history.

        Returns:
            Generated reflection
        """
        if not action_history or not score_history:
            return {'status': 'no_history'}

        # Find breakthrough moment (first significant score increase)
        breakthrough_idx: Optional[int] = None
        for i in range(1, len(score_history)):
            if score_history[i] > score_history[i-1]:
                breakthrough_idx = i
                break

        if breakthrough_idx is None:
            breakthrough_idx = len(action_history) - 1

        breakthrough_action = action_history[breakthrough_idx] if breakthrough_idx < len(action_history) else None

        # Analyze winning pattern
        action_counts: Dict[str, int] = {}
        for a in action_history:
            action_counts[a] = action_counts.get(a, 0) + 1

        most_used = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None

        # Generate key insight
        if breakthrough_action:
            key_insight = f"Breakthrough came from {breakthrough_action} at action {breakthrough_idx}"
        else:
            key_insight = f"Gradual progress using primarily {most_used}"

        # Generate winning strategy
        unique_actions = len(set(action_history))
        if unique_actions <= 2:
            winning_strategy = f"Focused approach using {unique_actions} action types"
        else:
            winning_strategy = f"Mixed approach with {unique_actions} different actions"

        # Record reflection
        insight_id = self.record_win_reflection(
            agent_id=agent_id,
            game_type=game_type,
            level_number=level_number,
            key_insight=key_insight,
            winning_strategy=winning_strategy,
            breakthrough_action=breakthrough_action,
            theory_at_breakthrough=self._current_theory,
            actions_before_breakthrough=breakthrough_idx or 0
        )

        return {
            'insight_id': insight_id,
            'key_insight': key_insight,
            'winning_strategy': winning_strategy,
            'breakthrough_action': breakthrough_action,
            'actions_before_breakthrough': breakthrough_idx
        }

    def get_relevant_insights(
        self,
        game_type: str,
        level_number: int,
        include_transferable: bool = True
    ) -> List[Dict[str, Any]]:
        """Get insights relevant to current game/level."""
        result = self.db.execute_query("""
            SELECT key_insight, winning_strategy, breakthrough_action, is_transferable
            FROM metacognitive_insights
            WHERE (game_type = ? AND level_number = ?)
               OR (is_transferable = TRUE AND ? = TRUE)
            ORDER BY created_at DESC
            LIMIT 5
        """, (game_type, level_number, include_transferable))

        return result or []

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get summary of current metacognitive state."""
        untested = [a for a in self._current_assumptions if not a.get('tested')]
        disproven = [a for a in self._current_assumptions if a.get('tested') and not a.get('valid')]

        return {
            'current_theory': self._current_theory,
            'assumptions_count': len(self._current_assumptions),
            'untested_assumptions': len(untested),
            'disproven_assumptions': len(disproven),
            'pending_prediction': self._pending_prediction is not None,
            'failures_recorded': len(self._failed_attempts),
            'actions_eliminated': len(self._eliminated_actions),
            'theory_revisions': len(self._theory_revisions)
        }
