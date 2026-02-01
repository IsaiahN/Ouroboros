"""
Weaving Reporter - Self-reflection report generation.

Generates self-reflection "weaving reports" for every action decision.
Delegates to IThread when available for Two Streams consciousness.

DELEGATION: This class delegates to IThread for report generation.
IThread is the single source of truth for Two Streams consciousness.

This class is kept for backward compatibility and adds:
- Local database storage with sampling
- Outcome tracking

Local Database Storage: Uses sampling to prevent bloat:
- Sampling Rate: Store 1 in 10 decisions locally (10%)
- Exception: Always store if conflict_detected = True
- Exception: Always store level completion / game end decisions
"""

import logging
import random
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from database_interface import DatabaseInterface
    from engines.consciousness.i_thread import IThread as IThreadType

logger = logging.getLogger(__name__)

# Check IThread availability at module level
_ithread_available = False
IThread = None
try:
    from engines.consciousness.i_thread import IThread as IThreadImport
    IThread = IThreadImport
    _ithread_available = True
except ImportError:
    pass


class WeavingReporter:
    """
    Generates self-reflection "weaving reports" for every action.

    DELEGATION: This class now delegates to IThread for report generation.
    IThread is the single source of truth for Two Streams consciousness.

    This class is kept for backward compatibility and adds:
    - Local database storage with sampling
    - Outcome tracking

    Local Database Storage: Uses sampling to prevent bloat:
    - Sampling Rate: Store 1 in 10 decisions locally (10%)
    - Exception: Always store if conflict_detected = True
    - Exception: Always store level completion / game end decisions
    """

    # Sampling rate for local storage (10% of non-exceptional decisions)
    SAMPLING_RATE = 0.1

    def __init__(self, db: 'DatabaseInterface', i_thread: Optional['IThreadType'] = None):
        """Initialize weaving reporter.

        Args:
            db: Database interface
            i_thread: Optional IThread instance for delegation
        """
        self.db = db
        self._i_thread = i_thread

        # Create IThread if not provided and available
        if self._i_thread is None and _ithread_available and IThread is not None:
            try:
                self._i_thread = IThread(db)
            except Exception as e:
                logger.debug(f"Could not create IThread for WeavingReporter: {e}")

        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure decision_weaving_reports table exists."""
        # Table kept for backward compatibility and local storage
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS decision_weaving_reports (
                report_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                level_number INTEGER,
                action_number INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                emotional_input REAL,
                semantic_input REAL,
                identity_input REAL,
                private_memory_strength REAL,
                network_recommendation_strength REAL,
                self_network_bias REAL,
                final_decision_weight REAL,
                chosen_action TEXT,
                alternative_action TEXT,
                conflict_detected BOOLEAN DEFAULT FALSE,
                consciousness_intensity TEXT DEFAULT 'automatic',
                outcome_correct BOOLEAN,
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """)
        self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_weaving_agent_game
            ON decision_weaving_reports(agent_id, game_id)
        """)

    def generate_report(
        self,
        agent_id: str,
        game_id: str,
        level_number: int,
        action_number: int,
        chosen_action: str,
        private_memory_strength: float,
        network_recommendation_strength: float,
        self_network_bias: float,
        navigation_state: float,
        role_confidence: float,
        role_fit_score: float,
        sensation_profile: Dict[str, Any],
        alternative_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weaving report for an action decision.

        DELEGATION: Delegates to IThread.generate_weaving_report() when available.
        Falls back to local implementation for backward compatibility.

        Args:
            agent_id: Agent making the decision
            game_id: Current game
            level_number: Current level
            action_number: Action counter in this game
            chosen_action: The action being taken
            private_memory_strength: How strong agent's own memory signal is (0-1)
            network_recommendation_strength: How strong network's recommendation is (0-1)
            self_network_bias: Agent's bias toward self (0=network, 1=self)
            navigation_state: Agent's emotional state (-1 to 1)
            role_confidence: Agent's confidence in their role (0-1)
            role_fit_score: How well agent fits their role (0-1)
            sensation_profile: Agent's sensation mappings
            alternative_action: What network recommended (if different)

        Returns:
            Complete weaving report dictionary for API
        """
        # DELEGATE to IThread if available
        if self._i_thread is not None:
            try:
                return self._i_thread.generate_weaving_report(
                    agent_id=agent_id,
                    game_id=game_id,
                    level_number=level_number,
                    action_number=action_number,
                    chosen_action=chosen_action,
                    private_memory_strength=private_memory_strength,
                    network_recommendation_strength=network_recommendation_strength,
                    navigation_state=navigation_state,
                    role_confidence=role_confidence,
                    role_fit_score=role_fit_score,
                    sensation_profile=sensation_profile,
                    alternative_action=alternative_action
                )
            except Exception as e:
                logger.debug(f"IThread delegation failed, using fallback: {e}")

        # FALLBACK: Original local implementation
        # Calculate internal network inputs
        # Emotional: Map navigation_state from [-1,1] to [0,1]
        emotional_input = (navigation_state + 1.0) / 2.0

        # Semantic: Average of top sensation scores (if any)
        object_sensations = sensation_profile.get('object_sensations', {}) if sensation_profile else {}
        if object_sensations:
            top_sensations = sorted(object_sensations.values(), reverse=True)[:3]
            semantic_input = sum(top_sensations) / len(top_sensations) if top_sensations else 0.5
            # Normalize to 0-1 range (sensations are -1 to 1)
            semantic_input = (semantic_input + 1.0) / 2.0
        else:
            semantic_input = 0.5  # Neutral if no sensations

        # Identity: Average of role_confidence and role_fit_score
        identity_input = (role_confidence + role_fit_score) / 2.0

        # Calculate final decision weight using Two-Streams formula
        # final_weight = private * bias + network * (1 - bias)
        alpha = self_network_bias
        final_decision_weight = (
            private_memory_strength * alpha +
            network_recommendation_strength * (1.0 - alpha)
        )

        # Detect conflict (significant difference between private and network)
        conflict_detected = abs(private_memory_strength - network_recommendation_strength) > 0.3

        # Build human-readable summary
        emotion_label = self._get_emotion_label(navigation_state)

        report = {
            'report_id': f"weave_{uuid.uuid4().hex[:12]}",
            'agent_id': agent_id,
            'game_id': game_id,
            'level_number': level_number,
            'action_number': action_number,
            'timestamp': datetime.now().isoformat(),

            # Internal networks (Three Streams)
            'emotional_input': round(emotional_input, 3),
            'semantic_input': round(semantic_input, 3),
            'identity_input': round(identity_input, 3),

            # Two-Streams weighting
            'private_memory_strength': round(private_memory_strength, 3),
            'network_recommendation_strength': round(network_recommendation_strength, 3),
            'self_network_bias': round(self_network_bias, 3),
            'final_decision_weight': round(final_decision_weight, 3),

            # wA/wB state
            'w_a': round(self_network_bias, 3),  # wA = self_network_bias in fallback
            'w_b': round(1.0 - self_network_bias, 3),

            # Decision
            'chosen_action': chosen_action,
            'alternative_action': alternative_action,
            'conflict_detected': conflict_detected,
            'consciousness_intensity': 'deliberative' if conflict_detected else 'automatic',

            # Narrative summary
            'narrative': self._build_narrative(
                emotion_label, private_memory_strength, network_recommendation_strength,
                alpha, chosen_action, alternative_action, conflict_detected
            ),

            # Outcome (to be filled in later)
            'outcome_correct': None
        }

        return report

    def _get_emotion_label(self, navigation_state: float) -> str:
        """Get human-readable emotion label from navigation state."""
        if navigation_state < -0.5:
            return 'frustrated'
        elif navigation_state < -0.1:
            return 'cautious'
        elif navigation_state < 0.1:
            return 'neutral'
        elif navigation_state < 0.5:
            return 'curious'
        else:
            return 'confident'

    def _build_narrative(
        self,
        emotion: str,
        private_strength: float,
        network_strength: float,
        alpha: float,
        chosen_action: str,
        alternative: Optional[str],
        conflict: bool
    ) -> str:
        """Build human-readable narrative of decision."""
        parts = []

        # Emotional state
        parts.append(f"Feeling {emotion}")

        # Stream preference with strength context
        if alpha > 0.6:
            parts.append(f"trusting own experience (strength={private_strength:.2f})")
        elif alpha < 0.4:
            parts.append(f"following network wisdom (strength={network_strength:.2f})")
        else:
            parts.append(f"balancing self ({private_strength:.2f}) and network ({network_strength:.2f})")

        # Conflict
        if conflict:
            if alternative:
                parts.append(f"(conflicted: network suggested {alternative})")
            else:
                parts.append("(internal conflict detected)")

        # Decision
        parts.append(f"-> {chosen_action}")

        return " | ".join(parts)

    def format_for_api(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format weaving report for inclusion in API reasoning payload.

        DELEGATION: Uses IThread.format_weaving_for_api() when available.

        Returns a compact version suitable for the 16KB limit.
        """
        # Delegate to IThread if available
        if self._i_thread is not None:
            try:
                return self._i_thread.format_weaving_for_api(report)
            except Exception:
                pass  # Fall through to local implementation

        # Fallback: local implementation
        return {
            'emotional_network': report.get('emotional_input', 0.5),
            'semantic_network': report.get('semantic_input', 0.5),
            'identity_network': report.get('identity_input', 0.5),
            'private_memory': report.get('private_memory_strength', 0.5),
            'network_wisdom': report.get('network_recommendation_strength', 0.5),
            'self_trust_bias': report.get('self_network_bias', 0.5),
            'w_a': report.get('w_a', 0.5),
            'w_b': report.get('w_b', 0.5),
            'decision_weight': report.get('final_decision_weight', 0.5),
            'conflict': report.get('conflict_detected', False),
            'consciousness': report.get('consciousness_intensity', 'automatic'),
            'narrative': report.get('narrative', '')
        }

    def should_store_locally(self, report: Dict[str, Any], is_terminal: bool = False) -> bool:
        """
        Determine if this report should be stored in local database.

        Storage criteria (to prevent bloat):
        - Always store if conflict_detected = True
        - Always store if is_terminal (level/game end)
        - Otherwise, sample at 10% rate
        """
        # Always store conflicts
        if report.get('conflict_detected'):
            return True

        # Always store terminal decisions
        if is_terminal:
            return True

        # Otherwise, sample
        return random.random() < self.SAMPLING_RATE

    def store_report(self, report: Dict[str, Any]) -> None:
        """Store a weaving report in the database."""
        self.db.execute_query("""
            INSERT INTO decision_weaving_reports
            (report_id, agent_id, game_id, level_number, action_number, timestamp,
             emotional_input, semantic_input, identity_input,
             private_memory_strength, network_recommendation_strength,
             self_network_bias, final_decision_weight,
             chosen_action, alternative_action, conflict_detected, outcome_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report['report_id'], report['agent_id'], report['game_id'],
            report['level_number'], report['action_number'], report['timestamp'],
            report['emotional_input'], report['semantic_input'], report['identity_input'],
            report['private_memory_strength'], report['network_recommendation_strength'],
            report['self_network_bias'], report['final_decision_weight'],
            report['chosen_action'], report['alternative_action'],
            report['conflict_detected'], report.get('outcome_correct')
        ))

    def update_outcome(self, report_id: str, outcome_correct: bool) -> None:
        """Update the outcome for a stored report (for meta-learning)."""
        self.db.execute_query("""
            UPDATE decision_weaving_reports
            SET outcome_correct = ?
            WHERE report_id = ?
        """, (outcome_correct, report_id))
