"""
Deliberation Audit System - Record alternative interpretations for analysis.

Based on ARC-AGI-2 insights:
"Recording multiple alternative interpretations per decision enables
post-hoc analysis to understand why wrong predictions were made."

This module:
1. Records the top 5 interpretations considered for each decision
2. Tracks which interpretation was chosen and why
3. Links outcomes to enable retrospective analysis
4. Identifies patterns in wrong predictions
5. Enables learning from "almost right" interpretations

Usage:
    auditor = DeliberationAuditor(db)

    # During decision making
    auditor.start_deliberation(context)
    auditor.add_alternative(action, confidence, reason, rung)
    auditor.record_choice(chosen_action, confidence, reason, rung)

    # After action executed
    auditor.record_outcome(outcome_type, score_change)

    # Analysis
    wrong_predictions = auditor.analyze_wrong_predictions(game_type)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of action outcomes."""
    POSITIVE = "positive"      # Score increase, level complete, progress
    NEGATIVE = "negative"      # Death, score decrease, regression
    NEUTRAL = "neutral"        # No change, status quo


@dataclass
class AlternativeInterpretation:
    """A single alternative interpretation that was considered."""
    action: str
    confidence: float
    reason: str
    rung: str                          # Which decision rung suggested this
    why_rejected: Optional[str] = None  # Why it wasn't chosen

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'reason': self.reason,
            'rung': self.rung,
            'why_rejected': self.why_rejected,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlternativeInterpretation":
        return cls(
            action=data.get('action', ''),
            confidence=data.get('confidence', 0.0),
            reason=data.get('reason', ''),
            rung=data.get('rung', ''),
            why_rejected=data.get('why_rejected'),
        )


@dataclass
class DeliberationRecord:
    """Complete record of a deliberation session."""
    # Context
    game_id: str
    game_type: str
    level_number: int
    action_number: int
    agent_id: Optional[str] = None

    # Frame context
    frame_hash: Optional[str] = None
    frame_sparse_hash: Optional[str] = None

    # Choice
    chosen_action: Optional[str] = None
    chosen_confidence: float = 0.0
    chosen_reason: str = ""
    chosen_rung: str = ""

    # Alternatives (max 5)
    alternatives: List[AlternativeInterpretation] = field(default_factory=list)

    # Two-stage context
    detected_palette: Optional[Dict[str, Any]] = None
    object_count: int = 0
    transformation_count: int = 0

    # Sparse grid context
    sparse_cell_count: int = 0
    sparse_colors: List[int] = field(default_factory=list)

    # Outcome (filled after action)
    outcome_type: Optional[OutcomeType] = None
    score_change: float = 0.0
    was_correct: Optional[bool] = None

    # Retrospective
    better_alternative_index: Optional[int] = None
    retrospective_notes: str = ""

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def add_alternative(
        self,
        action: str,
        confidence: float,
        reason: str,
        rung: str,
        why_rejected: Optional[str] = None
    ) -> None:
        """Add an alternative interpretation (max 5)."""
        if len(self.alternatives) >= 5:
            # Replace lowest confidence if this is better
            min_conf_idx = min(range(len(self.alternatives)),
                              key=lambda i: self.alternatives[i].confidence)
            if confidence > self.alternatives[min_conf_idx].confidence:
                self.alternatives[min_conf_idx] = AlternativeInterpretation(
                    action=action,
                    confidence=confidence,
                    reason=reason,
                    rung=rung,
                    why_rejected=why_rejected,
                )
        else:
            self.alternatives.append(AlternativeInterpretation(
                action=action,
                confidence=confidence,
                reason=reason,
                rung=rung,
                why_rejected=why_rejected,
            ))

    def to_db_row(self) -> Dict[str, Any]:
        """Convert to database row format."""
        return {
            'game_id': self.game_id,
            'game_type': self.game_type,
            'level_number': self.level_number,
            'action_number': self.action_number,
            'agent_id': self.agent_id,
            'frame_hash': self.frame_hash,
            'frame_sparse_hash': self.frame_sparse_hash,
            'chosen_action': self.chosen_action,
            'chosen_confidence': self.chosen_confidence,
            'chosen_reason': self.chosen_reason,
            'chosen_rung': self.chosen_rung,
            'alternatives': json.dumps([a.to_dict() for a in self.alternatives]),
            'detected_palette': json.dumps(self.detected_palette) if self.detected_palette else None,
            'object_count': self.object_count,
            'transformation_count': self.transformation_count,
            'sparse_cell_count': self.sparse_cell_count,
            'sparse_colors': json.dumps(self.sparse_colors),
            'outcome_type': self.outcome_type.value if self.outcome_type else None,
            'score_change': self.score_change,
            'was_correct': 1 if self.was_correct else (0 if self.was_correct is False else None),
            'better_alternative_index': self.better_alternative_index,
            'retrospective_notes': self.retrospective_notes,
            'timestamp': self.timestamp.isoformat(),
        }


class DeliberationAuditor:
    """
    Audit system for recording and analyzing decision deliberations.

    Records top 5 alternative interpretations per decision to enable
    post-hoc analysis of wrong predictions.
    """

    def __init__(self, db: Any = None, enabled: bool = True):
        """
        Initialize the auditor.

        Args:
            db: DatabaseInterface instance
            enabled: Whether to record deliberations (can disable for performance)
        """
        self._db = db
        self.enabled = enabled
        self._current_record: Optional[DeliberationRecord] = None
        self._table_verified = False

        # Stats
        self.total_recorded = 0
        self.total_wrong = 0

    def _ensure_table(self) -> bool:
        """Ensure the deliberation_audit_log table exists."""
        if self._table_verified or self._db is None:
            return self._table_verified

        try:
            self._db.execute_query("""
                CREATE TABLE IF NOT EXISTS deliberation_audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    level_number INTEGER NOT NULL,
                    action_number INTEGER NOT NULL,
                    agent_id TEXT,
                    frame_hash TEXT,
                    frame_sparse_hash TEXT,
                    chosen_action TEXT NOT NULL,
                    chosen_confidence REAL,
                    chosen_reason TEXT,
                    chosen_rung TEXT,
                    alternatives TEXT,
                    detected_palette TEXT,
                    object_count INTEGER,
                    transformation_count INTEGER,
                    sparse_cell_count INTEGER,
                    sparse_colors TEXT,
                    outcome_type TEXT,
                    score_change REAL,
                    was_correct INTEGER,
                    better_alternative_index INTEGER,
                    retrospective_notes TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._table_verified = True
        except Exception as e:
            logger.debug(f"[DELIBERATION-AUDIT] Table creation failed: {e}")
            return False

        return True

    # =========================================================================
    # Recording Interface
    # =========================================================================

    def start_deliberation(
        self,
        game_id: str,
        game_type: str,
        level_number: int,
        action_number: int,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Start recording a new deliberation session.

        Args:
            game_id: Current game ID
            game_type: First 4 chars of game_id
            level_number: Current level
            action_number: Action count in this game
            agent_id: Optional agent ID
            context: Optional context dict with frame/palette info
        """
        if not self.enabled:
            return

        self._current_record = DeliberationRecord(
            game_id=game_id,
            game_type=game_type,
            level_number=level_number,
            action_number=action_number,
            agent_id=agent_id,
        )

        # Extract context if provided
        if context:
            self._current_record.frame_hash = context.get('frame_hash')

            # Two-stage analysis context
            palette = context.get('detected_palette')
            if palette:
                self._current_record.detected_palette = palette

            extracted = context.get('extracted_objects')
            if extracted:
                self._current_record.object_count = extracted.get('object_count', 0)

            transforms = context.get('detected_transformations')
            if transforms:
                self._current_record.transformation_count = len(transforms)

    def add_alternative(
        self,
        action: str,
        confidence: float,
        reason: str,
        rung: str,
        why_rejected: Optional[str] = None,
    ) -> None:
        """
        Add an alternative interpretation that was considered.

        Args:
            action: The action string (e.g., 'ACTION1')
            confidence: Confidence score (0.0-1.0)
            reason: Why this action was suggested
            rung: Which decision rung suggested this
            why_rejected: Why it wasn't chosen (optional)
        """
        if not self.enabled or self._current_record is None:
            return

        self._current_record.add_alternative(
            action=action,
            confidence=confidence,
            reason=reason,
            rung=rung,
            why_rejected=why_rejected,
        )

    def record_choice(
        self,
        action: str,
        confidence: float,
        reason: str,
        rung: str,
    ) -> None:
        """
        Record the final chosen action.

        Args:
            action: The chosen action
            confidence: Final confidence
            reason: Why this was chosen
            rung: Which rung's suggestion was used
        """
        if not self.enabled or self._current_record is None:
            return

        self._current_record.chosen_action = action
        self._current_record.chosen_confidence = confidence
        self._current_record.chosen_reason = reason
        self._current_record.chosen_rung = rung

        # Mark why alternatives were rejected
        for alt in self._current_record.alternatives:
            if alt.why_rejected is None:
                if alt.confidence < confidence:
                    alt.why_rejected = f"Lower confidence ({alt.confidence:.2f} < {confidence:.2f})"
                elif alt.action == action:
                    alt.why_rejected = "Same as chosen"
                else:
                    alt.why_rejected = f"Rung {rung} had priority"

    def set_sparse_context(
        self,
        cell_count: int,
        colors: List[int],
        sparse_hash: Optional[str] = None,
    ) -> None:
        """
        Add sparse grid context to the current record.

        Args:
            cell_count: Number of non-background cells
            colors: List of unique colors
            sparse_hash: Position-invariant structural hash
        """
        if not self.enabled or self._current_record is None:
            return

        self._current_record.sparse_cell_count = cell_count
        self._current_record.sparse_colors = colors
        if sparse_hash:
            self._current_record.frame_sparse_hash = sparse_hash

    def record_outcome(
        self,
        outcome_type: str,
        score_change: float = 0.0,
    ) -> None:
        """
        Record the outcome after the action was executed.

        Args:
            outcome_type: 'positive', 'negative', or 'neutral'
            score_change: Change in score
        """
        if not self.enabled or self._current_record is None:
            return

        try:
            self._current_record.outcome_type = OutcomeType(outcome_type)
        except ValueError:
            self._current_record.outcome_type = OutcomeType.NEUTRAL

        self._current_record.score_change = score_change
        self._current_record.was_correct = outcome_type == 'positive'

        if not self._current_record.was_correct:
            self.total_wrong += 1

    def finalize(self) -> Optional[int]:
        """
        Save the current record to database and return audit_id.

        Returns:
            audit_id if saved, None otherwise
        """
        if not self.enabled or self._current_record is None:
            return None

        if self._current_record.chosen_action is None:
            return None

        if not self._ensure_table():
            return None

        try:
            row = self._current_record.to_db_row()

            if self._db is None:
                return None

            self._db.execute_query("""
                INSERT INTO deliberation_audit_log (
                    game_id, game_type, level_number, action_number, agent_id,
                    frame_hash, frame_sparse_hash,
                    chosen_action, chosen_confidence, chosen_reason, chosen_rung,
                    alternatives,
                    detected_palette, object_count, transformation_count,
                    sparse_cell_count, sparse_colors,
                    outcome_type, score_change, was_correct,
                    better_alternative_index, retrospective_notes,
                    timestamp
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?
                )
            """, (
                row['game_id'], row['game_type'], row['level_number'],
                row['action_number'], row['agent_id'],
                row['frame_hash'], row['frame_sparse_hash'],
                row['chosen_action'], row['chosen_confidence'],
                row['chosen_reason'], row['chosen_rung'],
                row['alternatives'],
                row['detected_palette'], row['object_count'],
                row['transformation_count'],
                row['sparse_cell_count'], row['sparse_colors'],
                row['outcome_type'], row['score_change'], row['was_correct'],
                row['better_alternative_index'], row['retrospective_notes'],
                row['timestamp'],
            ))

            self.total_recorded += 1
            self._current_record = None

            # Return the last insert id (implementation depends on db interface)
            return self.total_recorded

        except Exception as e:
            logger.debug(f"[DELIBERATION-AUDIT] Failed to save record: {e}")
            return None

    # =========================================================================
    # Analysis Interface
    # =========================================================================

    def analyze_wrong_predictions(
        self,
        game_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Analyze predictions that were wrong.

        Returns records where was_correct = 0, ordered by most recent.

        Args:
            game_type: Optional filter by game type
            limit: Maximum records to return

        Returns:
            List of deliberation records that were wrong
        """
        if self._db is None:
            return []

        try:
            if game_type:
                results = self._db.execute_query("""
                    SELECT * FROM deliberation_audit_log
                    WHERE was_correct = 0 AND game_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (game_type, limit))
            else:
                results = self._db.execute_query("""
                    SELECT * FROM deliberation_audit_log
                    WHERE was_correct = 0
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            return [dict(r) for r in results] if results else []

        except Exception as e:
            logger.debug(f"[DELIBERATION-AUDIT] Analysis query failed: {e}")
            return []

    def get_alternative_success_rate(
        self,
        game_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze which alternatives would have been better.

        Returns statistics on how often a non-chosen alternative
        might have been the better choice.
        """
        if self._db is None:
            return {}

        try:
            if game_type:
                results = self._db.execute_query("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                        SUM(CASE WHEN was_correct = 0 THEN 1 ELSE 0 END) as wrong,
                        SUM(CASE WHEN better_alternative_index IS NOT NULL THEN 1 ELSE 0 END) as had_better_alt
                    FROM deliberation_audit_log
                    WHERE game_type = ?
                """, (game_type,))
            else:
                results = self._db.execute_query("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                        SUM(CASE WHEN was_correct = 0 THEN 1 ELSE 0 END) as wrong,
                        SUM(CASE WHEN better_alternative_index IS NOT NULL THEN 1 ELSE 0 END) as had_better_alt
                    FROM deliberation_audit_log
                """)

            if results:
                row = results[0]
                total = row['total'] or 0
                correct = row['correct'] or 0
                wrong = row['wrong'] or 0
                had_better = row['had_better_alt'] or 0

                return {
                    'total_decisions': total,
                    'correct': correct,
                    'wrong': wrong,
                    'accuracy': correct / total if total > 0 else 0.0,
                    'had_better_alternative': had_better,
                    'better_alt_rate': had_better / wrong if wrong > 0 else 0.0,
                }

            return {}

        except Exception as e:
            logger.debug(f"[DELIBERATION-AUDIT] Stats query failed: {e}")
            return {}

    def get_rung_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze which rungs make the best decisions.

        Returns per-rung statistics on accuracy.
        """
        if self._db is None:
            return {}

        try:
            results = self._db.execute_query("""
                SELECT
                    chosen_rung,
                    COUNT(*) as total,
                    SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(chosen_confidence) as avg_confidence
                FROM deliberation_audit_log
                WHERE chosen_rung IS NOT NULL
                GROUP BY chosen_rung
                ORDER BY total DESC
            """)

            stats: Dict[str, Dict[str, Any]] = {}
            if results:
                for row in results:
                    rung = row['chosen_rung']
                    total = row['total'] or 0
                    correct = row['correct'] or 0
                    stats[rung] = {
                        'total': total,
                        'correct': correct,
                        'accuracy': correct / total if total > 0 else 0.0,
                        'avg_confidence': row['avg_confidence'] or 0.0,
                    }

            return stats

        except Exception as e:
            logger.debug(f"[DELIBERATION-AUDIT] Rung stats query failed: {e}")
            return {}

    def mark_better_alternative(
        self,
        audit_id: int,
        better_index: int,
        notes: str = "",
    ) -> bool:
        """
        Mark which alternative would have been better (for retrospective analysis).

        Args:
            audit_id: The audit record ID
            better_index: Index (0-4) of the alternative that was better
            notes: Optional notes about why

        Returns:
            True if updated successfully
        """
        if self._db is None:
            return False

        try:
            self._db.execute_query("""
                UPDATE deliberation_audit_log
                SET better_alternative_index = ?,
                    retrospective_notes = ?
                WHERE audit_id = ?
            """, (better_index, notes, audit_id))
            return True
        except Exception:
            return False


# =============================================================================
# Singleton Access
# =============================================================================

_global_auditor: Optional[DeliberationAuditor] = None


def get_deliberation_auditor(db: Any = None) -> DeliberationAuditor:
    """Get or create the global deliberation auditor."""
    global _global_auditor

    if _global_auditor is None:
        _global_auditor = DeliberationAuditor(db=db)
    elif db is not None and _global_auditor._db is None:
        _global_auditor._db = db

    return _global_auditor


def record_deliberation(
    game_id: str,
    game_type: str,
    level: int,
    action_number: int,
    chosen_action: str,
    chosen_confidence: float,
    chosen_reason: str,
    chosen_rung: str,
    alternatives: List[Tuple[str, float, str, str]],  # (action, conf, reason, rung)
    context: Optional[Dict[str, Any]] = None,
    db: Any = None,
) -> None:
    """
    Convenience function to record a complete deliberation in one call.

    Args:
        game_id: Current game ID
        game_type: First 4 chars of game_id
        level: Current level
        action_number: Action count
        chosen_action: The chosen action
        chosen_confidence: Confidence of choice
        chosen_reason: Why chosen
        chosen_rung: Which rung provided it
        alternatives: List of (action, confidence, reason, rung) tuples
        context: Optional context dict
        db: Optional database interface
    """
    auditor = get_deliberation_auditor(db)

    auditor.start_deliberation(
        game_id=game_id,
        game_type=game_type,
        level_number=level,
        action_number=action_number,
        context=context,
    )

    for action, conf, reason, rung in alternatives:
        auditor.add_alternative(action, conf, reason, rung)

    auditor.record_choice(chosen_action, chosen_confidence, chosen_reason, chosen_rung)
    auditor.finalize()
