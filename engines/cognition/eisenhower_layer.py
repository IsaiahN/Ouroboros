"""
Eisenhower Layer - Urgency x Importance Prioritization.

Phase 8.1 Implementation - Cognitive Routing Addon

This module implements the Eisenhower Matrix as a convergent layer that takes
divergent candidate rungs from the Rumsfeld/algorithm layer and prioritizes
them by urgency x importance.

The Rumsfeld Matrix asks "What do we know?"
The Eisenhower Matrix asks "What should we do NOW?"

Key concepts:
- Urgency: Is this needed for the NEXT action? (time pressure)
- Importance: Does this impact winning? (outcome impact)

Quadrants:
- Q1 (DO NOW): Urgent + Important - Execute immediately
- Q2 (SCHEDULE): Not Urgent + Important - Queue for later
- Q3 (DELEGATE): Urgent + Not Important - Use cached/heuristic path
- Q4 (ELIMINATE): Not Urgent + Not Important - Discard

This creates the convergent half of the dual-matrix architecture:
    Rumsfeld (divergent) -> many candidates
    Eisenhower (convergent) -> single prioritized action
"""
# RULE 1: PYTHONDONTWRITEBYTECODE=1 (no .pyc files)
import sys

sys.dont_write_bytecode = True

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from config.cognitive_parameters import DEFAULT_COGNITIVE_PARAMS as _PARAMS

if TYPE_CHECKING:
    from engines.cognition.blackboard import Blackboard

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class EisenhowerQuadrant(Enum):
    """Eisenhower Matrix quadrants based on urgency x importance."""
    Q1_DO = "do_now"           # Urgent + Important
    Q2_SCHEDULE = "schedule"   # Not Urgent + Important
    Q3_DELEGATE = "delegate"   # Urgent + Not Important
    Q4_ELIMINATE = "eliminate" # Not Urgent + Not Important


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UrgencyScore:
    """
    Computed urgency based on game state and resources.

    Urgency answers: "Is this needed for the NEXT action, or can it wait?"

    High urgency signals:
    - Low action budget remaining
    - High game state volatility
    - Blocking other progress
    - Risk of cascade failure
    """
    budget_pressure: float      # 0-1: how depleted is action budget
    volatility: float           # 0-1: how fast is game state changing
    blocking_factor: float      # 0-1: is this blocking other progress
    cascade_risk: float         # 0-1: will delay cause cascade failure

    @property
    def total(self) -> float:
        """
        Weighted combination with max of critical factors.

        Cascade risk alone can make something urgent.
        Uses weights from CognitiveParameters.
        """
        weighted = (
            self.budget_pressure * _PARAMS.urgency_budget_weight +
            self.volatility * _PARAMS.urgency_volatility_weight +
            self.blocking_factor * _PARAMS.urgency_blocking_weight +
            self.cascade_risk * _PARAMS.urgency_cascade_weight
        )
        # Cascade risk is critical - can override weighted average
        return max(weighted, self.cascade_risk)

    @property
    def is_urgent(self) -> bool:
        """Threshold for urgency classification."""
        return self.total > _PARAMS.urgency_threshold


@dataclass
class ImportanceScore:
    """
    Computed importance based on expected impact.

    Importance answers: "Does this impact winning, or just builds understanding?"

    High importance signals:
    - Directly affects win probability
    - Validates/invalidates working theory
    - Unlocks new action possibilities
    - High historical success rate
    """
    win_probability_delta: float  # How much does this affect P(win)
    theory_validation: float      # Does this confirm/deny working theory
    action_unlock: float          # Does this enable new actions
    edge_trust: float             # Historical success of this path

    @property
    def total(self) -> float:
        """Weighted combination emphasizing win probability. Uses CognitiveParameters."""
        return (
            self.win_probability_delta * _PARAMS.importance_win_prob_weight +
            self.theory_validation * _PARAMS.importance_theory_weight +
            self.action_unlock * _PARAMS.importance_unlock_weight +
            self.edge_trust * _PARAMS.importance_trust_weight
        )

    @property
    def is_important(self) -> bool:
        """Threshold for importance classification."""
        return self.total > _PARAMS.importance_threshold


@dataclass
class PrioritizedTask:
    """
    A task (rung candidate) with Eisenhower classification.

    Combines the rung name with computed urgency/importance scores
    and the resulting quadrant classification.
    """
    rung_name: str
    urgency: UrgencyScore
    importance: ImportanceScore
    quadrant: EisenhowerQuadrant
    source: str  # Which Rumsfeld quadrant generated this (KK/KU/UK/UU)

    @classmethod
    def classify(cls, rung_name: str, urgency: UrgencyScore,
                 importance: ImportanceScore, source: str) -> 'PrioritizedTask':
        """
        Classify a task into an Eisenhower quadrant.

        Uses urgency and importance thresholds to determine quadrant.
        """
        if urgency.is_urgent and importance.is_important:
            quadrant = EisenhowerQuadrant.Q1_DO
        elif not urgency.is_urgent and importance.is_important:
            quadrant = EisenhowerQuadrant.Q2_SCHEDULE
        elif urgency.is_urgent and not importance.is_important:
            quadrant = EisenhowerQuadrant.Q3_DELEGATE
        else:
            quadrant = EisenhowerQuadrant.Q4_ELIMINATE

        return cls(rung_name, urgency, importance, quadrant, source)

    def __repr__(self) -> str:
        return (
            f"PrioritizedTask({self.rung_name}, {self.quadrant.value}, "
            f"U={self.urgency.total:.2f}, I={self.importance.total:.2f})"
        )


# =============================================================================
# CROSS-MATRIX MAPPING
# =============================================================================

# How Rumsfeld quadrant biases Eisenhower classification
RUMSFELD_TO_EISENHOWER_BIAS: Dict[str, Dict[str, float]] = {
    'KK': {'importance_boost': 0.1, 'urgency_boost': 0.2},  # Trust what we know
    'KU': {'importance_boost': 0.2, 'urgency_boost': 0.0},  # Questions are important
    'UK': {'importance_boost': 0.1, 'urgency_boost': -0.1}, # Retrieval can wait
    'UU': {'importance_boost': 0.0, 'urgency_boost': -0.2}, # Exploration not urgent
}


# =============================================================================
# RUNG IMPORTANCE MAPPINGS
# =============================================================================

# Which rungs unlock critical capabilities
RUNG_UNLOCK_SCORES: Dict[str, float] = {
    'survey': 0.9,               # Unlocks everything
    'control_tracker': 0.8,      # Unlocks control-based actions
    'palette_detection': 0.7,    # Unlocks color-based reasoning
    'goal_detector': 0.75,       # Unlocks goal-directed behavior
    'pattern_matcher': 0.65,     # Unlocks pattern recognition
    'spatial_reasoner': 0.6,     # Unlocks spatial reasoning
}

# Default unlock score for unmapped rungs
DEFAULT_UNLOCK_SCORE = _PARAMS.default_rung_unlock_score


# =============================================================================
# EISENHOWER LAYER
# =============================================================================

class EisenhowerLayer:
    """
    Convergent layer that prioritizes tasks from Rumsfeld analysis.

    Takes the divergent output (many candidate rungs) and converges to
    a single prioritized action based on urgency x importance.

    Key features:
    - Computes urgency/importance for each candidate
    - Classifies into Q1/Q2/Q3/Q4 quadrants
    - Maintains scheduled queue for Q2 tasks
    - Ages scheduled tasks (Q2 can promote to Q1)
    - Handles all-ELIMINATE edge case
    - Supports iterative gating (re-evaluate after each execution)
    """

    # --- Configuration from CognitiveParameters ---
    MAX_SCHEDULED_QUEUE: int = _PARAMS.scheduled_queue_max
    AGING_RATE: float = _PARAMS.queue_aging_rate

    def __init__(self, blackboard: 'Blackboard'):
        """
        Initialize Eisenhower layer with blackboard reference.

        Args:
            blackboard: The shared blackboard for reading state
        """
        self.blackboard = blackboard
        self.scheduled_queue: List[PrioritizedTask] = []

        # Statistics for debugging
        self.stats = {
            'tasks_classified': 0,
            'q1_executed': 0,
            'q2_scheduled': 0,
            'q3_delegated': 0,
            'q4_eliminated': 0,
            'all_eliminate_triggered': 0,
            'promotions_from_aging': 0,
        }

    # =========================================================================
    # URGENCY COMPUTATION
    # =========================================================================

    def compute_urgency(self, rung_name: str) -> UrgencyScore:
        """
        Compute urgency score for a candidate rung.

        Urgency is time-pressure: "Do we need this NOW?"

        Phase 10: Now uses valence-tagged slots for O(1) urgency access
        when critical slots have inherent urgency encoded.

        Args:
            rung_name: Name of the candidate rung

        Returns:
            UrgencyScore with component breakdown
        """
        # Budget pressure: How depleted is our action budget?
        budget_used = self.blackboard.get('actions_taken', 0)
        budget_total = self.blackboard.get('action_budget', 400)
        budget_pressure = budget_used / budget_total if budget_total > 0 else 0

        # Volatility: How fast is game state changing?
        frame_delta = self.blackboard.get('frame_delta_magnitude', 0)
        volatility = min(frame_delta / 100, 1.0)  # Normalize to 0-1

        # Blocking factor: Is this blocking other progress?
        pending_questions = len(self.blackboard.get('open_questions', []))
        blocking_questions = self.blackboard.get('blocking_questions', [])
        is_blocking = rung_name in blocking_questions
        blocking_factor = 0.8 if is_blocking else min(pending_questions / 5, 1.0)

        # Cascade risk: Will delay break current strategy?
        strategy_stability = self.blackboard.get('strategy_stability', 1.0)
        cascade_risk = 1.0 - strategy_stability

        # Phase 10: Check for inherent urgency from valence-tagged slots
        # If critical threat indicators have high inherent urgency, use them
        aggregate_urgency = self.blackboard.get_aggregate_urgency()
        if aggregate_urgency > 0.7:
            # Boost cascade_risk when threat slots are highly urgent
            cascade_risk = max(cascade_risk, aggregate_urgency * 0.8)

        # Phase 9: Incorporate phenomenology felt urgency bias
        # Phenomenology compresses high-D state to a felt urgency signal
        felt_urgency = self.blackboard.get('felt_urgency_bias', 0.0)
        if felt_urgency > 0:
            # Blend felt urgency into cascade_risk (capped at 1.0)
            cascade_risk = min(1.0, cascade_risk + felt_urgency * 0.3)

        return UrgencyScore(
            budget_pressure=budget_pressure,
            volatility=volatility,
            blocking_factor=blocking_factor,
            cascade_risk=cascade_risk
        )

    # =========================================================================
    # IMPORTANCE COMPUTATION
    # =========================================================================

    def compute_importance(self, rung_name: str,
                           edge_trust: float = 0.5) -> ImportanceScore:
        """
        Compute importance score for a candidate rung.

        Importance is impact: "Does this affect winning?"

        Phase 10: Now uses valence-tagged slots for O(1) importance access
        when critical slots have inherent importance encoded.

        Args:
            rung_name: Name of the candidate rung
            edge_trust: Historical success rate of this rung (from graph evolution)

        Returns:
            ImportanceScore with component breakdown
        """
        # Win probability delta: How much does this rung typically help?
        rung_win_contribution = self.blackboard.get(
            f'rung_win_contribution_{rung_name}', 0.1
        )

        # Theory validation: Does this test our working theory?
        has_theory = self.blackboard.get('working_theory') is not None
        theory_testing_rungs = [
            'theory_gate', 'hypothesis_testing', 'scientific_method',
            'contradiction_detector', 'validation_rung'
        ]
        rung_tests_theory = rung_name in theory_testing_rungs
        theory_validation = 0.8 if has_theory and rung_tests_theory else 0.2

        # Action unlock: Does this enable new capabilities?
        action_unlock = RUNG_UNLOCK_SCORES.get(rung_name, DEFAULT_UNLOCK_SCORE)

        # Phase 10: Boost importance based on valence-tagged slots
        # If important slots indicate high stakes, raise baseline importance
        aggregate_importance = self.blackboard.get_aggregate_importance()
        if aggregate_importance > 0.6:
            # Boost win_probability_delta when slots indicate high importance
            rung_win_contribution = max(
                rung_win_contribution,
                aggregate_importance * 0.5
            )

        # Phase 9: Incorporate phenomenology felt importance bias
        # Phenomenology compresses high-D state to a felt importance signal
        felt_importance = self.blackboard.get('felt_importance_bias', 0.0)
        if felt_importance > 0:
            # Blend felt importance into win_probability_delta (capped at 1.0)
            rung_win_contribution = min(
                1.0, rung_win_contribution + felt_importance * 0.3
            )

        return ImportanceScore(
            win_probability_delta=rung_win_contribution,
            theory_validation=theory_validation,
            action_unlock=action_unlock,
            edge_trust=edge_trust
        )

    # =========================================================================
    # PRIORITIZATION
    # =========================================================================

    def prioritize(self, candidate_rungs: List[Tuple[str, float]]) -> Optional[str]:
        """
        Prioritize candidate rungs and return best action.

        Takes candidates from Rumsfeld/algorithm layer, classifies each
        using Eisenhower matrix, and returns the highest priority action.

        Args:
            candidate_rungs: List of (rung_name, edge_trust) tuples

        Returns:
            Best rung to execute, or None if all should be eliminated
        """
        if not candidate_rungs:
            return None

        # Get current Rumsfeld quadrant for cross-matrix bias
        epistemic_quadrant = self.blackboard.get('epistemic_quadrant', 'UU')
        bias = RUMSFELD_TO_EISENHOWER_BIAS.get(epistemic_quadrant, {})

        # Classify all candidates
        tasks = []
        for rung_name, edge_trust in candidate_rungs:
            urgency = self.compute_urgency(rung_name)
            importance = self.compute_importance(rung_name, edge_trust)

            # Apply Rumsfeld cross-matrix bias to shift urgency/importance
            # e.g. KK boosts urgency (+0.2), KU boosts importance (+0.2)
            urgency_boost = bias.get('urgency_boost', 0.0)
            importance_boost = bias.get('importance_boost', 0.0)
            if urgency_boost != 0.0:
                urgency.cascade_risk = max(0.0, min(1.0, urgency.cascade_risk + urgency_boost))
            if importance_boost != 0.0:
                importance.win_probability_delta = max(
                    0.0, min(1.0, importance.win_probability_delta + importance_boost)
                )

            task = PrioritizedTask.classify(
                rung_name, urgency, importance, epistemic_quadrant
            )
            tasks.append(task)
            self.stats['tasks_classified'] += 1

        # Sort by quadrant priority: Q1 > Q2 > Q3 > Q4
        # Within quadrant, sort by combined score (descending)
        def priority_key(t: PrioritizedTask) -> Tuple[int, float]:
            quadrant_priority = {
                EisenhowerQuadrant.Q1_DO: 0,
                EisenhowerQuadrant.Q2_SCHEDULE: 1,
                EisenhowerQuadrant.Q3_DELEGATE: 2,
                EisenhowerQuadrant.Q4_ELIMINATE: 3,
            }
            return (
                quadrant_priority[t.quadrant],
                -(t.urgency.total + t.importance.total)  # Negative for descending
            )

        tasks.sort(key=priority_key)

        best = tasks[0]

        # Handle based on quadrant
        if best.quadrant == EisenhowerQuadrant.Q1_DO:
            self.stats['q1_executed'] += 1
            return best.rung_name

        elif best.quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
            # Add to queue for later, but still execute if nothing better
            self._add_to_scheduled_queue(best)
            self.stats['q2_scheduled'] += 1
            return best.rung_name

        elif best.quadrant == EisenhowerQuadrant.Q3_DELEGATE:
            # Try to use cached/heuristic path instead
            cached = self.blackboard.get(f'cached_sequence_{best.rung_name}')
            self.stats['q3_delegated'] += 1
            if cached:
                return cached[0]  # First action from cached sequence
            return best.rung_name

        else:  # Q4_ELIMINATE
            self.stats['q4_eliminated'] += 1
            # Check scheduled queue for something better
            if self.scheduled_queue:
                scheduled = self.scheduled_queue.pop(0)
                return scheduled.rung_name
            # Nothing to do - trigger exploration
            return 'exploration_phase'

    # =========================================================================
    # ITERATIVE GATE (Per-Rung Evaluation)
    # =========================================================================

    def gate_single_rung(self, rung_name: str,
                         edge_trust: float) -> Tuple[EisenhowerQuadrant, Optional[str]]:
        """
        Evaluate a single rung as a gate before execution.

        This is the ITERATIVE version - called before EACH rung execution,
        not just once per cycle. After executing a rung, the blackboard
        changes, so we re-evaluate remaining candidates.

        Args:
            rung_name: The candidate rung to evaluate
            edge_trust: Historical success rate

        Returns:
            (quadrant, action_to_take):
            - Q1_DO: (Q1_DO, rung_name) - execute this rung
            - Q2_SCHEDULE: (Q2_SCHEDULE, None) - skip, added to queue
            - Q3_DELEGATE: (Q3_DELEGATE, cached_action) - use cached path
            - Q4_ELIMINATE: (Q4_ELIMINATE, None) - discard entirely
        """
        urgency = self.compute_urgency(rung_name)
        importance = self.compute_importance(rung_name, edge_trust)
        source = self.blackboard.get('epistemic_quadrant', 'UU')

        task = PrioritizedTask.classify(rung_name, urgency, importance, source)
        self.stats['tasks_classified'] += 1

        if task.quadrant == EisenhowerQuadrant.Q1_DO:
            self.stats['q1_executed'] += 1
            return (EisenhowerQuadrant.Q1_DO, rung_name)

        elif task.quadrant == EisenhowerQuadrant.Q2_SCHEDULE:
            self._add_to_scheduled_queue(task)
            self.stats['q2_scheduled'] += 1
            return (EisenhowerQuadrant.Q2_SCHEDULE, None)

        elif task.quadrant == EisenhowerQuadrant.Q3_DELEGATE:
            cached = self.blackboard.get(f'cached_sequence_{rung_name}')
            self.stats['q3_delegated'] += 1
            if cached:
                return (EisenhowerQuadrant.Q3_DELEGATE, cached[0])
            # No cache, fall through to execute
            return (EisenhowerQuadrant.Q3_DELEGATE, rung_name)

        else:  # Q4_ELIMINATE
            self.stats['q4_eliminated'] += 1
            return (EisenhowerQuadrant.Q4_ELIMINATE, None)

    # =========================================================================
    # SCHEDULED QUEUE MANAGEMENT
    # =========================================================================

    def _add_to_scheduled_queue(self, task: PrioritizedTask) -> None:
        """Add a task to the scheduled queue if not already present."""
        # Avoid duplicates
        if any(t.rung_name == task.rung_name for t in self.scheduled_queue):
            return
        self.scheduled_queue.append(task)

    def age_scheduled_queue(self) -> None:
        """
        Age items in scheduled queue - older items become more urgent.

        Called at the start of each routing cycle. Items that have been
        waiting gain urgency, potentially promoting Q2 to Q1.
        """
        aged_tasks = []
        for task in self.scheduled_queue:
            # Increase urgency due to waiting
            new_urgency = UrgencyScore(
                budget_pressure=min(1.0, task.urgency.budget_pressure + self.AGING_RATE),
                volatility=task.urgency.volatility,  # Doesn't age
                blocking_factor=min(1.0, task.urgency.blocking_factor + self.AGING_RATE * 0.5),
                cascade_risk=min(1.0, task.urgency.cascade_risk + self.AGING_RATE * 0.5)
            )

            # Reclassify with new urgency
            aged_task = PrioritizedTask.classify(
                task.rung_name, new_urgency, task.importance, task.source
            )
            aged_tasks.append(aged_task)

        # Replace queue with aged versions
        self.scheduled_queue = aged_tasks

        # Handle overflow - keep highest priority
        if len(self.scheduled_queue) > self.MAX_SCHEDULED_QUEUE:
            self.scheduled_queue.sort(
                key=lambda t: -(t.urgency.total + t.importance.total)
            )
            dropped = self.scheduled_queue[self.MAX_SCHEDULED_QUEUE:]
            self.scheduled_queue = self.scheduled_queue[:self.MAX_SCHEDULED_QUEUE]

            # Log what was dropped for debugging
            for task in dropped:
                logger.debug(
                    "[EISENHOWER] Queue overflow, dropped: %s (U=%.2f, I=%.2f)",
                    task.rung_name, task.urgency.total, task.importance.total
                )

    def pop_promoted_task(self) -> Optional[str]:
        """
        Check if any scheduled task has been promoted to Q1 through aging.

        Returns:
            Rung name if a Q1 task is available, None otherwise.
        """
        for i, task in enumerate(self.scheduled_queue):
            if task.quadrant == EisenhowerQuadrant.Q1_DO:
                self.scheduled_queue.pop(i)
                self.stats['promotions_from_aging'] += 1
                logger.info(
                    "[EISENHOWER] Task promoted via aging: %s", task.rung_name
                )
                return task.rung_name
        return None

    # =========================================================================
    # EDGE CASE HANDLING
    # =========================================================================

    def handle_all_eliminate(self) -> str:
        """
        Handle edge case where all candidates are Q4_ELIMINATE.

        This is a system health issue - we shouldn't normally be
        generating only useless candidates.

        Returns:
            A fallback rung to execute.
        """
        self.stats['all_eliminate_triggered'] += 1

        # Log the health event
        logger.warning(
            "[EISENHOWER] ALL-ELIMINATE triggered - all candidates were Q4"
        )

        # Record in blackboard for analysis
        health_events = self.blackboard.get('system_health_events', [])
        health_events.append({
            'type': 'all_eliminate',
            'tick': self.blackboard.get('tick', 0),
            'message': 'All candidates classified as Q4_ELIMINATE'
        })
        self.blackboard.slot('system_health_events', health_events, source_rung='eisenhower')

        # Priority 1: Check scheduled queue
        if self.scheduled_queue:
            task = self.scheduled_queue.pop(0)
            logger.info(
                "[EISENHOWER] Falling back to scheduled task: %s", task.rung_name
            )
            return task.rung_name

        # Priority 2: Check for promoted tasks
        promoted = self.pop_promoted_task()
        if promoted:
            return promoted

        # Priority 3: Explicit exploration
        logger.info("[EISENHOWER] Falling back to exploration_phase")
        return 'exploration_phase'

    # =========================================================================
    # DEBUGGING / INTROSPECTION
    # =========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Get classification statistics."""
        return self.stats.copy()

    def get_scheduled_queue_summary(self) -> List[str]:
        """Get summary of scheduled queue for debugging."""
        return [
            f"{t.rung_name} (U={t.urgency.total:.2f}, I={t.importance.total:.2f})"
            for t in self.scheduled_queue
        ]

    def reset_stats(self) -> None:
        """Reset statistics for new game."""
        self.stats = {
            'tasks_classified': 0,
            'q1_executed': 0,
            'q2_scheduled': 0,
            'q3_delegated': 0,
            'q4_eliminated': 0,
            'all_eliminate_triggered': 0,
            'promotions_from_aging': 0,
        }
        self.scheduled_queue.clear()
