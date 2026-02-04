"""
Question Manager for Epistemic State Machine.

This module manages the lifecycle of questions (KU quadrant):
1. Raising questions when rungs discover unknowns
2. Tracking attempts to answer questions
3. Demoting/abandoning questions after too many failed attempts
4. Providing question templates for common rung categories

Phase 1.6.2 of cognitive_routing_implementation_plan.md

Question Lifecycle:
    RAISED -> ACTIVE -> ANSWERED (success)
                    -> DEMOTED (3+ failed attempts, low priority)
                    -> ABANDONED (given up)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# QUESTION STATUS
# =============================================================================

class QuestionStatus(Enum):
    """Status of a question in its lifecycle."""
    RAISED = "raised"          # Just discovered
    ACTIVE = "active"          # Being actively pursued
    ANSWERED = "answered"      # Got satisfactory answer
    ABANDONED = "abandoned"    # Gave up after too many attempts
    DEMOTED = "demoted"        # Low priority after 3+ failed attempts


# =============================================================================
# MANAGED QUESTION
# =============================================================================

@dataclass
class ManagedQuestion:
    """
    A question tracked by the QuestionManager.

    Extends the basic Question concept with lifecycle tracking.
    """
    question_id: str
    text: str                           # Human-readable question
    answerable_by: List[str]            # Rungs that might answer this
    priority: float = 0.5               # 0.0 to 1.0
    status: QuestionStatus = QuestionStatus.RAISED
    raised_at: int = 0                  # Tick when first raised
    raised_by: Optional[str] = None     # Rung that raised this question
    attempts: int = 0                   # How many times we've tried to answer
    last_attempt_tick: int = 0          # When was last attempt
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    answer_value: Any = None            # The answer (if answered)
    answer_confidence: float = 0.0      # Confidence in answer
    answer_source: Optional[str] = None # Rung that answered

    def mark_answered(self, value: Any, confidence: float, source: str) -> None:
        """Mark this question as answered."""
        self.status = QuestionStatus.ANSWERED
        self.answer_value = value
        self.answer_confidence = confidence
        self.answer_source = source

    def record_attempt(self, tick: int, succeeded: bool) -> None:
        """Record an attempt to answer this question."""
        self.attempts += 1
        self.last_attempt_tick = tick

        if not succeeded and self.attempts >= 3:
            self.status = QuestionStatus.DEMOTED
            self.priority *= 0.5  # Halve priority

    @property
    def is_active(self) -> bool:
        """Is this question still active (not answered/abandoned)?"""
        return self.status in (QuestionStatus.RAISED, QuestionStatus.ACTIVE, QuestionStatus.DEMOTED)

    @property
    def age(self) -> int:
        """How many ticks since question was raised (requires current tick)."""
        return self.last_attempt_tick - self.raised_at if self.last_attempt_tick > 0 else 0


# =============================================================================
# QUESTION TEMPLATES
# =============================================================================

# Common question patterns by rung category
# These are templates - actual questions are instantiated with context
RUNG_QUESTION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "survey": [
        {
            "question_id": "what_objects",
            "text": "What are these objects?",
            "answerable_by": ["frame_interpretation", "pattern_detection"],
            "priority": 0.7,
        },
        {
            "question_id": "whats_interactive",
            "text": "What's interactive?",
            "answerable_by": ["control_tracker", "discovery_exploitation"],
            "priority": 0.8,
        },
    ],
    "frame_interpretation": [
        {
            "question_id": "physics_or_turn",
            "text": "Is this physics or turn-based?",
            "answerable_by": ["event_understanding", "physics_detection"],
            "priority": 0.6,
        },
        {
            "question_id": "what_changed",
            "text": "What caused that change?",
            "answerable_by": ["event_understanding", "causal_analysis"],
            "priority": 0.7,
        },
    ],
    "control_tracker": [
        {
            "question_id": "control_correct",
            "text": "Is my control hypothesis correct?",
            "answerable_by": ["hypothesis_testing", "discovery_exploitation"],
            "priority": 0.8,
        },
        {
            "question_id": "what_do_i_control",
            "text": "What object(s) do I control?",
            "answerable_by": ["control_tracker", "discovery_exploitation"],
            "priority": 0.9,
        },
    ],
    "hypothesis_testing": [
        {
            "question_id": "rule_generalizes",
            "text": "Does this rule generalize?",
            "answerable_by": ["abstraction_testing", "rule_transfer"],
            "priority": 0.6,
        },
    ],
    "pattern_detection": [
        {
            "question_id": "pattern_meaning",
            "text": "What does this pattern mean?",
            "answerable_by": ["frame_interpretation", "semantic_analysis"],
            "priority": 0.6,
        },
    ],
    "event_understanding": [
        {
            "question_id": "cause_effect",
            "text": "What caused this effect?",
            "answerable_by": ["causal_analysis", "physics_detection"],
            "priority": 0.7,
        },
    ],
}


# =============================================================================
# QUESTION MANAGER
# =============================================================================

class QuestionManager:
    """
    Manages question lifecycle for the KU (Known Unknowns) quadrant.

    Responsibilities:
    1. Track active questions with their status
    2. Record attempts to answer questions
    3. Demote/abandon questions after failures
    4. Provide prioritized list of questions to pursue
    5. Match questions to rungs that can answer them

    Usage:
        manager = QuestionManager()

        # When a rung raises a question
        manager.raise_question(
            question_id="what_control",
            text="What do I control?",
            answerable_by=["control_tracker"],
            raised_by="survey",
            current_tick=10
        )

        # Get questions for a rung to try answering
        questions = manager.get_questions_for_rung("control_tracker")

        # Record attempt result
        manager.record_attempt(
            question_id="what_control",
            succeeded=True,
            confidence=0.85,
            answer_value="blue_square",
            answer_source="control_tracker",
            current_tick=15
        )
    """

    # Thresholds
    ANSWER_CONFIDENCE_THRESHOLD = 0.6  # Min confidence to mark answered
    MAX_ATTEMPTS_BEFORE_DEMOTE = 3     # Attempts before demotion
    MAX_ATTEMPTS_BEFORE_ABANDON = 6    # Attempts before abandonment
    PRIORITY_BOOST_ON_RERAISE = 0.1    # Priority boost when re-raised

    def __init__(self):
        """Initialize the question manager."""
        self.questions: Dict[str, ManagedQuestion] = {}
        self.answered_history: List[str] = []  # History of answered question IDs
        self.abandoned_history: List[str] = []  # History of abandoned question IDs
        self._total_raised: int = 0
        self._total_answered: int = 0

    def reset(self) -> None:
        """Reset for a new game (keeps history for stats)."""
        self.questions.clear()

    def full_reset(self) -> None:
        """Full reset including history."""
        self.questions.clear()
        self.answered_history.clear()
        self.abandoned_history.clear()
        self._total_raised = 0
        self._total_answered = 0

    def raise_question(
        self,
        question_id: str,
        text: str,
        answerable_by: List[str],
        raised_by: Optional[str] = None,
        current_tick: int = 0,
        priority: float = 0.5,
        context: Optional[Dict[str, Any]] = None
    ) -> ManagedQuestion:
        """
        Raise a new question or boost priority if already exists.

        Args:
            question_id: Unique identifier for the question
            text: Human-readable question text
            answerable_by: List of rungs that might answer this
            raised_by: Rung that raised this question
            current_tick: Current tick number
            priority: Initial priority (0.0 to 1.0)
            context: Additional context about the question

        Returns:
            The created or updated ManagedQuestion
        """
        if question_id in self.questions:
            # Question already exists - boost priority
            q = self.questions[question_id]
            q.priority = min(1.0, q.priority + self.PRIORITY_BOOST_ON_RERAISE)
            logger.debug(f"Question '{question_id}' re-raised, priority now {q.priority:.2f}")
            return q

        # Create new question
        question = ManagedQuestion(
            question_id=question_id,
            text=text,
            answerable_by=answerable_by,
            priority=priority,
            status=QuestionStatus.ACTIVE,
            raised_at=current_tick,
            raised_by=raised_by,
            context=context or {}
        )

        self.questions[question_id] = question
        self._total_raised += 1

        logger.debug(f"Question raised: '{question_id}' by {raised_by}")
        return question

    def raise_from_template(
        self,
        rung_category: str,
        template_id: str,
        raised_by: str,
        current_tick: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ManagedQuestion]:
        """
        Raise a question from a predefined template.

        Args:
            rung_category: Category to look up template
            template_id: ID of template within category
            raised_by: Rung raising the question
            current_tick: Current tick
            context: Additional context

        Returns:
            Created question or None if template not found
        """
        templates = RUNG_QUESTION_TEMPLATES.get(rung_category, [])

        for template in templates:
            if template["question_id"] == template_id:
                return self.raise_question(
                    question_id=template["question_id"],
                    text=template["text"],
                    answerable_by=template["answerable_by"],
                    raised_by=raised_by,
                    current_tick=current_tick,
                    priority=template.get("priority", 0.5),
                    context=context
                )

        logger.warning(f"Template not found: {rung_category}/{template_id}")
        return None

    def record_attempt(
        self,
        question_id: str,
        succeeded: bool,
        confidence: float,
        current_tick: int,
        answer_value: Any = None,
        answer_source: Optional[str] = None
    ) -> bool:
        """
        Record an attempt to answer a question.

        Args:
            question_id: ID of question being answered
            succeeded: Whether the attempt succeeded
            confidence: Confidence in the answer
            current_tick: Current tick
            answer_value: The answer (if succeeded)
            answer_source: Rung that provided answer

        Returns:
            True if question was answered successfully
        """
        if question_id not in self.questions:
            logger.warning(f"Attempt recorded for unknown question: {question_id}")
            return False

        q = self.questions[question_id]
        q.record_attempt(current_tick, succeeded)

        # Check if successfully answered
        if succeeded and confidence >= self.ANSWER_CONFIDENCE_THRESHOLD:
            q.mark_answered(answer_value, confidence, answer_source)
            self.answered_history.append(question_id)
            self._total_answered += 1
            del self.questions[question_id]
            logger.debug(f"Question '{question_id}' ANSWERED with confidence {confidence:.2f}")
            return True

        # Check for abandonment
        if q.attempts >= self.MAX_ATTEMPTS_BEFORE_ABANDON:
            q.status = QuestionStatus.ABANDONED
            self.abandoned_history.append(question_id)
            del self.questions[question_id]
            logger.debug(f"Question '{question_id}' ABANDONED after {q.attempts} attempts")

        return False

    def get_active_questions(self) -> List[ManagedQuestion]:
        """
        Get all active questions sorted by priority.

        Returns:
            List of active questions, highest priority first
        """
        active = [q for q in self.questions.values() if q.is_active]
        return sorted(active, key=lambda q: q.priority, reverse=True)

    def get_questions_for_rung(self, rung_name: str) -> List[ManagedQuestion]:
        """
        Get questions that a specific rung might be able to answer.

        Args:
            rung_name: Name of the rung

        Returns:
            List of questions answerable by this rung, priority sorted
        """
        matching = [
            q for q in self.questions.values()
            if q.is_active and rung_name in q.answerable_by
        ]
        return sorted(matching, key=lambda q: q.priority, reverse=True)

    def get_highest_priority_question(self) -> Optional[ManagedQuestion]:
        """Get the single highest priority active question."""
        active = self.get_active_questions()
        return active[0] if active else None

    def get_question(self, question_id: str) -> Optional[ManagedQuestion]:
        """Get a specific question by ID."""
        return self.questions.get(question_id)

    def get_resolution_rate(self) -> float:
        """
        Calculate the question resolution rate.

        Returns:
            Ratio of answered to total raised (0.0 to 1.0)
        """
        if self._total_raised == 0:
            return 0.0
        return self._total_answered / self._total_raised

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics for monitoring."""
        active = [q for q in self.questions.values() if q.is_active]
        demoted = [q for q in self.questions.values() if q.status == QuestionStatus.DEMOTED]

        return {
            "total_raised": self._total_raised,
            "total_answered": self._total_answered,
            "total_abandoned": len(self.abandoned_history),
            "currently_active": len(active),
            "currently_demoted": len(demoted),
            "resolution_rate": self.get_resolution_rate(),
            "avg_priority": sum(q.priority for q in active) / len(active) if active else 0.0,
            "avg_attempts": sum(q.attempts for q in self.questions.values()) / len(self.questions) if self.questions else 0.0,
        }

    def __repr__(self) -> str:
        active = len([q for q in self.questions.values() if q.is_active])
        return f"QuestionManager(active={active}, answered={self._total_answered})"
