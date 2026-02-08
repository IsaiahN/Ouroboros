#!/usr/bin/env python3
"""
I-Thread: The Consciousness Weaver
===================================

Implements the I-Thread from Unified Agent Consciousness Theory.

The I-Thread is the persistent identity that weaves Stream A (private experience)
and Stream B (collective network wisdom) together moment-by-moment. It learns
which stream to trust in which contexts, developing personality over time.

Key Responsibilities:
1. Maintain w_A/w_B weights (Stream A vs Stream B trust)
2. Learn from stream conflicts and outcomes
3. Track personality development over time
4. Compute surprise when streams conflict
5. Synthesize weighted actions from competing stream proposals

Theory Reference:
- When streams agree: Action is automatic, low consciousness intensity
- When streams conflict: Consciousness becomes vivid, deliberation required
- Outcomes update weights: Learning which stream to trust in context

Database Storage:
- agents.self_network_bias: Stores w_B (0=full self-trust, 1=full network-trust)
- i_thread_history: Logs weight updates for personality tracking

Author: Ouroboros System
Version: 1.0
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: No pycache

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

# Extracted DeliberationEngine (Jan 31 2026 refactor)
from engines.consciousness.deliberation_engine import (
    DELIBERATION_CONFIG,
    DeliberationEngine,
)

# Extracted types (Jan 2026 refactor) - import will shadow local definitions
from engines.consciousness.i_thread_types import (
    CONFLICT_THRESHOLD,
    HIGH_CONFLICT_THRESHOLD,
    ROLE_DEFAULT_WEIGHTS,
    ConflictResult,
    DeliberationResult,
    GutInstinctResult,
    IThreadState,
    MortalityState,
    ReasoningLog,
    StreamProposal,
    SynthesisResult,
)

# TYPE_CHECKING import to avoid circular dependency
if TYPE_CHECKING:
    from engines.planning.sequence_abstraction import SequenceAbstraction
    from engines.social.resonance_detector import ResonanceDetector

logger = logging.getLogger(__name__)


# =============================================================================
# COGNITIVE FACULTY IMPORTS (Runtime, not TYPE_CHECKING)
# =============================================================================
# These are the agent's cognitive faculties - how it imagines, recognizes, and understands.
# They are facets of the agent's unified experience, not external services.
# =============================================================================

def _get_resonance_detector():
    """Lazy import to avoid circular dependency."""
    try:
        from database_interface import DatabaseInterface
        from engines.social.resonance_detector import ResonanceDetector
        return ResonanceDetector(DatabaseInterface())
    except ImportError:
        return None

def _get_sequence_abstraction():
    """Lazy import to avoid circular dependency."""
    try:
        from engines.planning.sequence_abstraction import SequenceAbstraction
        return SequenceAbstraction()
    except ImportError:
        return None


# =============================================================================
# NOTE: DeliberationEngine and related types extracted Jan 31 2026
# =============================================================================
# The following were moved to separate modules:
#
# From engines.consciousness.deliberation_engine:
#   - DeliberationEngine class
#   - DELIBERATION_CONFIG constant
#
# From engines.consciousness.i_thread_types:
#   - GutInstinctResult dataclass
#   - DeliberationResult dataclass
#   - ReasoningLog dataclass
#   - IThreadState dataclass
#   - MultiConflictResult dataclass
#
# These are imported at the top of this file for backwards compatibility.
# =============================================================================


# =============================================================================
# NOTE: ORPHANED DUPLICATE IThread CLASS REMOVED (Jan 31 2026)
# =============================================================================
# ~1,200 lines of corrupted orphaned code were removed here.
# The proper IThread class implementation follows below.
# =============================================================================


# NOTE: IThreadState and MultiConflictResult dataclasses are imported from
# engines.consciousness.i_thread_types (see imports at top of file).
# Duplicate local definitions were removed Jan 31 2026.


class IThread:
    """
    The I-Thread: Persistent identity weaver for Two Streams consciousness.

    Maintains the w_A/w_B weights that determine how much an agent trusts
    its private experience (Stream A) vs collective network wisdom (Stream B).

    Usage:
        i_thread = IThread(db)
        state = i_thread.get_state(agent_id)

        # When streams conflict:
        conflict = i_thread.detect_conflict(stream_a_proposal, stream_b_proposal)

        # Synthesize action:
        synthesis = i_thread.synthesize(state, stream_a_proposal, stream_b_proposal)

        # After outcome, update weights:
        i_thread.learn_from_outcome(agent_id, chosen_source='stream_a', outcome='positive')
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self._ensure_tables_exist()
        self._state_cache: Dict[str, IThreadState] = {}

    def _ensure_tables_exist(self):
        """Create I-Thread tracking tables if they don't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS i_thread_history (
                    history_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,

                    -- Weight state
                    w_a_before REAL,
                    w_b_before REAL,
                    w_a_after REAL,
                    w_b_after REAL,

                    -- Learning event
                    event_type TEXT,  -- 'conflict_resolution', 'outcome_learning', 'role_reset'
                    chosen_source TEXT,  -- 'stream_a', 'stream_b', 'synthesis'
                    outcome TEXT,  -- 'positive', 'negative', 'neutral'
                    conflict_score REAL,
                    surprise_score REAL,

                    -- Context
                    game_id TEXT,
                    level_number INTEGER,
                    action_taken TEXT,

                    -- Tracking
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_i_thread_agent
                ON i_thread_history(agent_id, created_at DESC)
            """)

            # ================================================================
            # EPISODIC MEMORY TABLE: Compressed autobiographical memories
            # ================================================================
            # Stores significant episodes that shape agent identity.
            # Not every action - just meaningful moments that matter.
            # ================================================================
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS i_thread_episodic_memories (
                    memory_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    game_id TEXT,
                    level_number INTEGER DEFAULT 1,

                    -- Episode classification
                    episode_type TEXT NOT NULL,  -- 'breakthrough', 'frustration', 'surprise', 'validation', 'failure', 'mastery'
                    summary TEXT NOT NULL,  -- Natural language description

                    -- Emotional/significance markers
                    emotional_valence REAL DEFAULT 0.0,  -- -1.0 to +1.0
                    significance REAL DEFAULT 0.5,  -- 0.0 to 1.0

                    -- Learning content
                    belief_formed TEXT,  -- "Corners matter in maze games"
                    rule_discovered TEXT,  -- "click_corner -> reveal_path"

                    -- Stream context at time of episode
                    stream_source TEXT DEFAULT 'stream_a',
                    w_a_at_time REAL DEFAULT 0.5,
                    w_b_at_time REAL DEFAULT 0.5,

                    -- Retrieval tracking
                    times_recalled INTEGER DEFAULT 0,
                    last_recalled DATETIME,

                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_episodic_agent_type
                ON i_thread_episodic_memories(agent_id, episode_type, significance DESC)
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_episodic_game_type
                ON i_thread_episodic_memories(game_type, episode_type)
            """)

            # ================================================================
            # MORTALITY COLUMNS: Add to agents table if not exist
            # ================================================================
            # These columns track agent mortality awareness state.
            # ================================================================
            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN vitality REAL DEFAULT 1.0
                """)
            except Exception:
                pass  # Column likely exists

            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN legacy_score REAL DEFAULT 0.0
                """)
            except Exception:
                pass  # Column likely exists

            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN last_reflection TEXT DEFAULT NULL
                """)
            except Exception:
                pass  # Column likely exists

            try:
                self.db.execute_query("""
                    ALTER TABLE agents ADD COLUMN reflection_count INTEGER DEFAULT 0
                """)
            except Exception:
                pass  # Column likely exists

            logger.debug("[I-THREAD] Tables initialized (including episodic memory and mortality columns)")

        except Exception as e:
            logger.debug(f"I-Thread table creation (may already exist): {e}")

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def get_state(self, agent_id: str) -> IThreadState:
        """
        Get current I-Thread state for an agent.

        Loads from database and caches for session performance.

        Args:
            agent_id: Agent identifier

        Returns:
            IThreadState with current w_A/w_B weights
        """
        if agent_id in self._state_cache:
            return self._state_cache[agent_id]

        # Load from database
        try:
            result = self.db.execute_query(
                "SELECT self_network_bias FROM agents WHERE agent_id = ?",
                (agent_id,)
            )

            if result:
                w_b = result[0].get('self_network_bias', 0.5) or 0.5
                w_a = 1.0 - w_b  # w_A + w_B = 1.0
            else:
                w_a, w_b = 0.5, 0.5

        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to load state for {agent_id[:8]}: {e}")
            w_a, w_b = 0.5, 0.5

        # Load historical stats
        stats = self._load_historical_stats(agent_id)

        state = IThreadState(
            agent_id=agent_id,
            w_a=w_a,
            w_b=w_b,
            conflicts_resolved=stats.get('total_conflicts', 0),
            stream_a_wins=stats.get('stream_a_wins', 0),
            stream_b_wins=stats.get('stream_b_wins', 0),
            personality_label=self._compute_personality_label(w_a, w_b)
        )

        self._state_cache[agent_id] = state
        return state

    def _load_historical_stats(self, agent_id: str) -> Dict[str, int]:
        """Load cumulative stats from history table."""
        try:
            result = self.db.execute_query("""
                SELECT
                    COUNT(*) as total_conflicts,
                    SUM(CASE WHEN chosen_source = 'stream_a' THEN 1 ELSE 0 END) as stream_a_wins,
                    SUM(CASE WHEN chosen_source = 'stream_b' THEN 1 ELSE 0 END) as stream_b_wins
                FROM i_thread_history
                WHERE agent_id = ? AND event_type = 'conflict_resolution'
            """, (agent_id,))

            if result:
                return {
                    'total_conflicts': result[0].get('total_conflicts', 0) or 0,
                    'stream_a_wins': result[0].get('stream_a_wins', 0) or 0,
                    'stream_b_wins': result[0].get('stream_b_wins', 0) or 0,
                }
        except Exception:
            pass

        return {'total_conflicts': 0, 'stream_a_wins': 0, 'stream_b_wins': 0}

    def _compute_personality_label(self, w_a: float, w_b: float) -> str:
        """Compute personality label from weights."""
        if w_a > w_b + 0.2:
            return 'self-trusting'
        elif w_b > w_a + 0.2:
            return 'network-trusting'
        else:
            return 'balanced'

    # =========================================================================
    # CONFLICT DETECTION
    # =========================================================================

    def detect_conflict(
        self,
        stream_a_proposal: StreamProposal,
        stream_b_proposal: StreamProposal
    ) -> ConflictResult:
        """
        Detect if Stream A and Stream B are in conflict.

        Conflict = streams propose different actions with confidence.

        Args:
            stream_a_proposal: What private experience suggests
            stream_b_proposal: What network wisdom suggests

        Returns:
            ConflictResult with conflict score and consciousness intensity
        """
        # Different actions = potential conflict
        if stream_a_proposal.action != stream_b_proposal.action:
            # Conflict score based on confidence difference
            avg_confidence = (stream_a_proposal.confidence + stream_b_proposal.confidence) / 2
            conflict_score = avg_confidence  # Higher confidence = stronger conflict
        else:
            # Same action = no conflict
            conflict_score = 0.0

        # Determine consciousness intensity
        if conflict_score < CONFLICT_THRESHOLD:
            intensity = 'automatic'
        elif conflict_score < HIGH_CONFLICT_THRESHOLD:
            intensity = 'deliberative'
        else:
            intensity = 'vivid'

        return ConflictResult(
            has_conflict=conflict_score >= CONFLICT_THRESHOLD,
            conflict_score=conflict_score,
            stream_a_proposal=stream_a_proposal,
            stream_b_proposal=stream_b_proposal,
            consciousness_intensity=intensity
        )

    # =========================================================================
    # SYNTHESIS: WEIGHTED ACTION SELECTION
    # =========================================================================

    def synthesize(
        self,
        state: IThreadState,
        stream_a_proposal: StreamProposal,
        stream_b_proposal: StreamProposal,
        _context: Optional[Dict[str, Any]] = None
    ) -> SynthesisResult:
        """
        Synthesize an action from competing stream proposals.

        Uses w_A/w_B weights to determine which stream to trust.

        Args:
            state: Current I-Thread state with weights
            stream_a_proposal: Private experience proposal
            stream_b_proposal: Network wisdom proposal
            _context: Optional context (game state, history) - reserved for future use

        Returns:
            SynthesisResult with chosen action and metadata
        """
        conflict = self.detect_conflict(stream_a_proposal, stream_b_proposal)

        # Calculate weighted scores
        score_a = stream_a_proposal.confidence * state.w_a
        score_b = stream_b_proposal.confidence * state.w_b

        # Choose based on weighted scores
        if score_a > score_b:
            chosen_action = stream_a_proposal.action
            chosen_source = 'stream_a'
            confidence = stream_a_proposal.confidence
        elif score_b > score_a:
            chosen_action = stream_b_proposal.action
            chosen_source = 'stream_b'
            confidence = stream_b_proposal.confidence
        else:
            # Tie - could synthesize novel action, for now pick stream_a
            chosen_action = stream_a_proposal.action
            chosen_source = 'synthesis'
            confidence = (stream_a_proposal.confidence + stream_b_proposal.confidence) / 2

        # Calculate surprise: How unexpected is this choice?
        # High surprise when low-weight stream wins due to high confidence
        if chosen_source == 'stream_a' and state.w_a < state.w_b:
            surprise = state.w_b - state.w_a  # Underdog won
        elif chosen_source == 'stream_b' and state.w_b < state.w_a:
            surprise = state.w_a - state.w_b  # Underdog won
        else:
            surprise = 0.0  # Expected outcome

        return SynthesisResult(
            chosen_action=chosen_action,
            confidence=confidence,
            chosen_source=chosen_source,
            surprise_score=surprise,
            w_a_used=state.w_a,
            w_b_used=state.w_b,
            deliberation_required=conflict.has_conflict
        )

    # =========================================================================
    # LEARNING: UPDATE WEIGHTS FROM OUTCOMES
    # =========================================================================

    def learn_from_outcome(
        self,
        agent_id: str,
        chosen_source: str,
        outcome: str,  # 'positive', 'negative', 'neutral'
        game_id: Optional[str] = None,
        level_number: Optional[int] = None,
        action_taken: Optional[str] = None,
        conflict_score: float = 0.0,
        surprise_score: float = 0.0
    ) -> Tuple[float, float]:
        """
        Learn from action outcome by adjusting w_A/w_B weights.

        If the chosen stream led to positive outcome, increase its weight.
        If negative, decrease its weight (increase the other).

        Args:
            agent_id: Agent identifier
            chosen_source: Which stream was followed ('stream_a', 'stream_b')
            outcome: Result of the action
            game_id: Optional game context
            level_number: Optional level context
            action_taken: Optional action taken
            conflict_score: How much conflict there was
            surprise_score: How surprising the synthesis was

        Returns:
            Tuple of (new_w_a, new_w_b)
        """
        state = self.get_state(agent_id)

        w_a_before = state.w_a
        w_b_before = state.w_b

        # Calculate weight adjustment
        learning_rate = state.learning_rate

        if outcome == 'positive':
            # Reward the chosen stream
            if chosen_source == 'stream_a':
                adjustment = learning_rate
            elif chosen_source == 'stream_b':
                adjustment = -learning_rate  # Decrease w_a, increase w_b
            else:
                adjustment = 0.0  # Synthesis - no clear winner
        elif outcome == 'negative':
            # Punish the chosen stream
            if chosen_source == 'stream_a':
                adjustment = -learning_rate
            elif chosen_source == 'stream_b':
                adjustment = learning_rate  # Increase w_a, decrease w_b
            else:
                adjustment = 0.0
        else:
            adjustment = 0.0  # Neutral - no update

        # Apply adjustment with bounds
        new_w_a = max(0.1, min(0.9, state.w_a + adjustment))
        new_w_b = 1.0 - new_w_a  # Maintain sum = 1.0

        # Update state
        state.w_a = new_w_a
        state.w_b = new_w_b
        state.last_update = datetime.now()
        state.personality_label = self._compute_personality_label(new_w_a, new_w_b)

        if conflict_score > 0:
            state.total_conflicts += 1
            if chosen_source == 'stream_a':
                state.stream_a_wins += 1
            elif chosen_source == 'stream_b':
                state.stream_b_wins += 1

        # Persist to database
        self._save_state(agent_id, new_w_b)  # DB stores w_b as self_network_bias

        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=w_b_before,
            w_a_after=new_w_a,
            w_b_after=new_w_b,
            event_type='outcome_learning',
            chosen_source=chosen_source,
            outcome=outcome,
            game_id=game_id,
            level_number=level_number,
            action_taken=action_taken,
            conflict_score=conflict_score,
            surprise_score=surprise_score
        )

        return (new_w_a, new_w_b)

    def _save_state(self, agent_id: str, w_b: float):
        """Save w_B to database (self_network_bias field)."""
        try:
            self.db.execute_query(
                "UPDATE agents SET self_network_bias = ? WHERE agent_id = ?",
                (w_b, agent_id)
            )
        except Exception as e:
            logger.warning(f"[I-THREAD] Failed to save state: {e}")

    def _log_history(
        self,
        agent_id: str,
        w_a_before: float,
        w_b_before: float,
        w_a_after: float,
        w_b_after: float,
        event_type: str,
        chosen_source: Optional[str] = None,
        outcome: Optional[str] = None,
        conflict_score: float = 0.0,
        surprise_score: float = 0.0,
        game_id: Optional[str] = None,
        level_number: Optional[int] = None,
        action_taken: Optional[str] = None
    ):
        """Log weight change to history table."""
        try:
            history_id = str(uuid.uuid4())[:12]
            self.db.execute_query("""
                INSERT INTO i_thread_history (
                    history_id, agent_id,
                    w_a_before, w_b_before, w_a_after, w_b_after,
                    event_type, chosen_source, outcome,
                    conflict_score, surprise_score,
                    game_id, level_number, action_taken
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, agent_id,
                w_a_before, w_b_before, w_a_after, w_b_after,
                event_type, chosen_source, outcome,
                conflict_score, surprise_score,
                game_id, level_number, action_taken
            ))
        except Exception as e:
            logger.debug(f"[I-THREAD] History log failed: {e}")

    # =========================================================================
    # ROLE TRANSITIONS
    # =========================================================================

    def reset_for_role_change(
        self,
        agent_id: str,
        new_role: str
    ) -> Tuple[float, float]:
        """
        Reset w_A/w_B when agent changes roles.

        Per theory: Role changes reset stream weighting to role defaults.

        Args:
            agent_id: Agent identifier
            new_role: New role being assigned

        Returns:
            Tuple of (new_w_a, new_w_b)
        """
        state = self.get_state(agent_id)
        w_a_before = state.w_a
        w_b_before = state.w_b

        # Get role defaults
        new_w_a, new_w_b = ROLE_DEFAULT_WEIGHTS.get(new_role.lower(), (0.5, 0.5))

        # Update state
        state.w_a = new_w_a
        state.w_b = new_w_b
        state.personality_label = self._compute_personality_label(new_w_a, new_w_b)

        # Persist
        self._save_state(agent_id, new_w_b)

        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=w_b_before,
            w_a_after=new_w_a,
            w_b_after=new_w_b,
            event_type='role_reset',
            outcome=f'role_change_to_{new_role}'
        )

        logger.info(
            f"[I-THREAD] {agent_id[:8]} role -> {new_role}: "
            f"w_A: {w_a_before:.2f} -> {new_w_a:.2f}"
        )

        return new_w_a, new_w_b

    # =========================================================================
    # PERSONALITY ANALYSIS
    # =========================================================================

    def get_personality_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get personality summary for an agent.

        Returns:
            Dict with personality metrics and history
        """
        state = self.get_state(agent_id)

        return {
            'agent_id': agent_id,
            'w_a': state.w_a,
            'w_b': state.w_b,
            'personality_label': state.personality_label,
            'total_conflicts_resolved': state.conflicts_resolved,
            'stream_a_win_rate': (
                state.stream_a_wins / state.conflicts_resolved
                if state.conflicts_resolved > 0 else 0.5
            ),
            'stream_b_win_rate': (
                state.stream_b_wins / state.conflicts_resolved
                if state.conflicts_resolved > 0 else 0.5
            ),
            'learning_rate': state.learning_rate
        }

    def clear_cache(self, agent_id: Optional[str] = None):
        """Clear state cache for agent or all agents."""
        if agent_id:
            self._state_cache.pop(agent_id, None)
        else:
            self._state_cache.clear()

    # =========================================================================
    # TEMPORARY SELF-TRUST BOOST (Escape/Frontier Exploration)
    # =========================================================================
    # When agents break out of stuck states or reach frontiers, temporarily
    # boost their self-trust (wA) to encourage exploration over network following.
    # =========================================================================

    def boost_self_trust(
        self,
        agent_id: str,
        boost_amount: float = 0.25,
        max_wA: float = 1.0,
        reason: str = 'exploration'
    ) -> Tuple[float, float, float]:
        """
        Temporarily boost wA (self-trust) for exploration.

        Called when:
        - Agent escapes stuck state independently
        - Agent reaches frontier level with no sequences
        - Agent needs to explore without network guidance

        Args:
            agent_id: Agent identifier
            boost_amount: How much to add to wA (default 0.25)
            max_wA: Maximum wA after boost (default 1.0)
            reason: Why boosting (for logging)

        Returns:
            Tuple of (original_wA, boosted_wA, boosted_wB)
        """
        state = self.get_state(agent_id)
        original_wA = state.w_a

        # Calculate boosted wA (capped at max)
        boosted_wA = min(max_wA, state.w_a + boost_amount)
        boosted_wB = 1.0 - boosted_wA

        if boosted_wA > state.w_a:
            # Store original for restoration
            state.original_w_a = original_wA
            state.novelty_boost_active = True

            # Apply boost
            state.w_a = boosted_wA
            state.w_b = boosted_wB
            state.personality_label = self._compute_personality_label(boosted_wA, boosted_wB)

            # Persist
            self._save_state(agent_id, boosted_wB)

            # Log history
            self._log_history(
                agent_id=agent_id,
                w_a_before=original_wA,
                w_b_before=1.0 - original_wA,
                w_a_after=boosted_wA,
                w_b_after=boosted_wB,
                event_type='self_trust_boost',
                outcome=reason
            )

            logger.info(
                f"[I-THREAD] {agent_id[:8]} {reason} boost: "
                f"w_A: {original_wA:.2f} -> {boosted_wA:.2f}"
            )

        return original_wA, boosted_wA, boosted_wB

    def restore_self_trust(
        self,
        agent_id: str,
        original_wA: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Restore wA to original value after temporary boost.

        Called when:
        - Agent exits self-directed mode
        - Agent finds network sequences for new level
        - Exploration phase ends

        Args:
            agent_id: Agent identifier
            original_wA: Original wA to restore (or use stored value)

        Returns:
            Tuple of (restored_wA, restored_wB)
        """
        state = self.get_state(agent_id)

        # Determine what to restore to
        if original_wA is not None:
            restore_wA = original_wA
        elif hasattr(state, 'original_w_a') and state.original_w_a is not None:
            restore_wA = state.original_w_a
        else:
            # No original stored, nothing to restore
            return state.w_a, state.w_b

        w_a_before = state.w_a
        restore_wB = 1.0 - restore_wA

        # Restore state
        state.w_a = restore_wA
        state.w_b = restore_wB
        state.original_w_a = None
        state.novelty_boost_active = False
        state.personality_label = self._compute_personality_label(restore_wA, restore_wB)

        # Persist
        self._save_state(agent_id, restore_wB)

        # Log history
        self._log_history(
            agent_id=agent_id,
            w_a_before=w_a_before,
            w_b_before=1.0 - w_a_before,
            w_a_after=restore_wA,
            w_b_after=restore_wB,
            event_type='self_trust_restore',
            outcome='exploration_complete'
        )

        logger.debug(
            f"[I-THREAD] {agent_id[:8]} restored: "
            f"w_A: {w_a_before:.2f} -> {restore_wA:.2f}"
        )

        return restore_wA, restore_wB

    # =========================================================================
    # QUERY HELPERS (Private Methods)
    # =========================================================================

    def _query_episodic_memories(
        self,
        agent_id: str,
        game_type: str
    ) -> List[Dict[str, Any]]:
        """
        Query episodic memories (thoughts from previous games).

        This implements "reexamine their thoughts of previous games" requirement.
        Returns breakthroughs, frustrations, and lessons learned.
        """
        try:
            results = self.db.execute_query("""
                SELECT memory_id, episode_type, summary, belief_formed,
                       rule_discovered, emotional_valence, significance
                FROM i_thread_episodic_memories
                WHERE agent_id = ? AND game_type = ?
                ORDER BY significance DESC, created_at DESC
                LIMIT 10
            """, (agent_id, game_type))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []

    def _query_past_attempts(
        self,
        agent_id: str,
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """Query past action outcomes for this game/level from action_traces.

        Uses collective data (all agents) since action_traces has no agent_id
        column. Columns: action_number (int), score_change (real).
        """
        try:
            results = self.db.execute_query("""
                SELECT action_number as action,
                       CASE WHEN score_change > 0 THEN 'positive'
                            WHEN score_change < 0 THEN 'negative'
                            ELSE 'neutral' END as outcome,
                       score_change as score_delta
                FROM action_traces
                WHERE game_id LIKE ? AND level_number = ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (f"{game_type}%", level))
            return results if results else []
        except Exception:
            return []

    def _query_network_hypotheses(
        self,
        game_type: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """Query network hypotheses for this game/level."""
        try:
            results = self.db.execute_query("""
                SELECT hypothesis_id,
                       controlled_object as recommended_action,
                       reliability_score as reliability,
                       validation_attempts
                FROM network_object_control_hypotheses
                WHERE game_type = ?
                  AND level_number = ?
                  AND is_active = 1
                  AND (validation_attempts >= 3 OR validated_by_win = 1)
                ORDER BY reliability_score DESC
                LIMIT 10
            """, (game_type, level))
            return [dict(r) for r in results] if results else []
        except Exception:
            return []

    def _get_available_primitives(self, agent_id: str) -> List[str]:
        """Get list of primitives available to this agent."""
        # For now, return a basic list - could be enhanced to query CODS
        return [
            'detect_novelty', 'detect_motion', 'object_permanence',
            'pattern_matching', 'spatial_reasoning', 'temporal_tracking'
        ]

    # =========================================================================
    # DELIBERATION DELEGATION (Uses DeliberationEngine)
    # =========================================================================

    def compute_deliberation_budget(
        self,
        is_frontier: bool,
        network_traction: float,
        agent_performance: float,
        tension_state: str,
        actions_remaining_pct: float,
        following_sequence: bool
    ) -> Tuple[float, str]:
        """
        Compute how much time to allocate for deliberation.
        Delegates to DeliberationEngine.
        """
        engine = DeliberationEngine(self.db)
        return engine.compute_deliberation_budget(
            is_frontier=is_frontier,
            network_traction=network_traction,
            agent_performance=agent_performance,
            tension_state=tension_state,
            actions_remaining_pct=actions_remaining_pct,
            following_sequence=following_sequence
        )

    def capture_gut_instinct(
        self,
        available_actions: List[str],
        recent_actions: List[str],
        recent_outcomes: List[str],
        w_a: float,
        w_b: float,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None
    ) -> GutInstinctResult:
        """
        Capture immediate gut instinct before deliberation.
        Delegates to DeliberationEngine.
        """
        engine = DeliberationEngine(self.db)
        return engine.capture_gut_instinct(
            available_actions=available_actions,
            recent_actions=recent_actions,
            recent_outcomes=recent_outcomes,
            w_a=w_a,
            w_b=w_b,
            network_recommendation=network_recommendation,
            private_preference=private_preference
        )

    def conduct_deliberation(
        self,
        gut_result: GutInstinctResult,
        available_actions: List[str],
        budget_seconds: float,
        game_context: Dict[str, Any],
        agent_id: str,
        w_a: float,
        w_b: float
    ) -> DeliberationResult:
        """
        Conduct full deliberation process.
        Delegates to DeliberationEngine.
        """
        engine = DeliberationEngine(self.db)
        return engine.conduct_deliberation(
            gut_result=gut_result,
            available_actions=available_actions,
            budget_seconds=budget_seconds,
            game_context=game_context,
            agent_id=agent_id,
            w_a=w_a,
            w_b=w_b
        )

    def decide_action(
        self,
        agent_id: str,
        game_context: Dict[str, Any],
        available_actions: List[str],
        i_thread_state: Optional['IThreadState'] = None,
        mortality_state: Optional['MortalityState'] = None,
        recent_actions: Optional[List[str]] = None,
        recent_outcomes: Optional[List[str]] = None,
        network_recommendation: Optional[str] = None,
        private_preference: Optional[str] = None,
        following_sequence: bool = False
    ) -> ReasoningLog:
        """
        Main entry point: Decide which action to take.

        Captures gut instinct, optionally performs deliberation,
        and returns complete reasoning log.

        Args:
            agent_id: Agent making decision
            game_context: Dict with game_id, game_type, level, frame, etc.
            available_actions: Valid actions
            i_thread_state: Current IThread state (for stream weights)
            mortality_state: Current mortality state (for tension)
            recent_actions: Last N actions taken
            recent_outcomes: Outcomes of those actions
            network_recommendation: Stream B suggestion
            private_preference: Stream A suggestion
            following_sequence: Are we executing a known sequence?

        Returns:
            ReasoningLog with complete decision record
        """
        import time

        decision_start = datetime.now()
        start_time = time.time()

        # Extract context
        game_id = game_context.get('game_id', 'unknown')
        game_type = game_context.get('game_type', 'unknown')
        level = game_context.get('level', 1)
        action_number = game_context.get('action_number', 0)
        actions_remaining = game_context.get('actions_remaining', 400)
        actions_budget = game_context.get('actions_budget', 400)
        is_frontier = game_context.get('is_frontier', True)
        network_traction = game_context.get('network_traction', 0.0)

        # Get stream weights
        w_a = i_thread_state.w_a if i_thread_state else 0.5
        w_b = i_thread_state.w_b if i_thread_state else 0.5

        # Get tension state
        tension_state = 'optimal'
        if mortality_state:
            pressure = mortality_state.compute_existential_pressure()
            tension_result = mortality_state.compute_tension_state(pressure)
            tension_state = tension_result.get('state', 'optimal')

        # Compute agent performance (placeholder - would come from agent stats)
        agent_performance = 0.5  # Default to median
        try:
            perf_result = self.db.execute_query("""
                SELECT AVG(CASE WHEN final_score > 0 THEN 1.0 ELSE 0.0 END) as win_rate
                FROM game_results
                WHERE agent_id = ? AND created_at > datetime('now', '-7 days')
            """, (agent_id,))
            if perf_result and perf_result[0]['win_rate']:
                agent_performance = float(perf_result[0]['win_rate'])
        except Exception:
            pass

        # Compute deliberation budget
        actions_remaining_pct = actions_remaining / actions_budget if actions_budget > 0 else 1.0
        budget_seconds, budget_reason = self.compute_deliberation_budget(
            is_frontier=is_frontier,
            network_traction=network_traction,
            agent_performance=agent_performance,
            tension_state=tension_state,
            actions_remaining_pct=actions_remaining_pct,
            following_sequence=following_sequence
        )

        # Step 1: Always capture gut instinct
        gut_result = self.capture_gut_instinct(
            available_actions=available_actions,
            recent_actions=recent_actions or [],
            recent_outcomes=recent_outcomes or [],
            w_a=w_a,
            w_b=w_b,
            network_recommendation=network_recommendation,
            private_preference=private_preference
        )

        # Step 2: Decide whether to deliberate
        deliberation_result = None
        skip_reason = None

        should_skip = (
            following_sequence or
            tension_state == 'panic' or
            actions_remaining_pct < 0.1 or
            budget_seconds <= DELIBERATION_CONFIG['min_deliberation']
        )

        if should_skip:
            if following_sequence:
                skip_reason = "Following validated sequence"
            elif tension_state == 'panic':
                skip_reason = "Panic state - relying on instinct"
            elif actions_remaining_pct < 0.1:
                skip_reason = "Critical action budget - no time to think"
            else:
                skip_reason = "Minimal budget allocated"
        else:
            # Conduct deliberation
            deliberation_result = self.conduct_deliberation(
                gut_result=gut_result,
                available_actions=available_actions,
                budget_seconds=budget_seconds,
                game_context=game_context,
                agent_id=agent_id,
                w_a=w_a,
                w_b=w_b
            )

        # Determine final action
        if deliberation_result:
            final_action = deliberation_result.action
            final_confidence = deliberation_result.confidence
            decision_source = 'deliberation' if deliberation_result.changed_from_gut else 'gut_confirmed'
        else:
            final_action = gut_result.action
            final_confidence = gut_result.confidence
            decision_source = 'gut'

        # Calculate total time
        total_time_ms = (time.time() - start_time) * 1000

        # Create reasoning log
        log_id = f"rl_{agent_id}_{game_id}_{level}_{action_number}_{int(time.time()*1000)}"

        reasoning_log = ReasoningLog(
            log_id=log_id,
            agent_id=agent_id,
            game_id=game_id,
            game_type=game_type,
            level=level,
            action_number=action_number,
            is_frontier=is_frontier,
            network_traction=network_traction,
            actions_remaining=actions_remaining,
            actions_budget=actions_budget,
            tension_state=tension_state,
            deliberation_budget_seconds=budget_seconds,
            budget_reason=budget_reason,
            gut=gut_result,
            deliberation=deliberation_result,
            deliberation_skipped_reason=skip_reason,
            final_action=final_action,
            final_confidence=final_confidence,
            decision_source=decision_source,
            decision_started_at=decision_start,
            decision_completed_at=datetime.now(),
            total_decision_time_ms=total_time_ms
        )

        # Store in database
        self._store_reasoning_log(reasoning_log)

        return reasoning_log

    def _store_reasoning_log(self, log: ReasoningLog) -> None:
        """Store reasoning log in database."""
        import json

        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO action_reasoning_logs (
                    log_id, agent_id, game_id, game_type, level, action_number,
                    is_frontier, network_traction, actions_remaining, actions_budget,
                    tension_state, deliberation_budget_seconds, budget_reason,
                    gut_action, gut_confidence, gut_basis, gut_response_time_ms,
                    gut_stream_a_influence, gut_stream_b_influence, gut_pattern_matched,
                    deliberation_performed, deliberation_action, deliberation_confidence,
                    deliberation_time_seconds, deliberation_reasoning_steps,
                    deliberation_changed_from_gut, deliberation_change_reason,
                    deliberation_skipped_reason,
                    examined_past_attempts, examined_network_hypotheses,
                    examined_episodic_memories, examined_primitives,
                    stream_conflict_detected, stream_conflict_resolution,
                    missing_primitive_signal,
                    final_action, final_confidence, decision_source, total_decision_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.log_id, log.agent_id, log.game_id, log.game_type, log.level,
                log.action_number, 1 if log.is_frontier else 0, log.network_traction,
                log.actions_remaining, log.actions_budget, log.tension_state,
                log.deliberation_budget_seconds, log.budget_reason,
                log.gut.action, log.gut.confidence, log.gut.basis,
                log.gut.response_time_ms, log.gut.stream_a_influence,
                log.gut.stream_b_influence, log.gut.pattern_matched,
                1 if log.deliberation else 0,
                log.deliberation.action if log.deliberation else None,
                log.deliberation.confidence if log.deliberation else None,
                log.deliberation.time_spent_seconds if log.deliberation else None,
                json.dumps(log.deliberation.reasoning_steps) if log.deliberation else None,
                1 if log.deliberation and log.deliberation.changed_from_gut else 0,
                log.deliberation.change_reason if log.deliberation else None,
                log.deliberation_skipped_reason,
                log.deliberation.examined_past_attempts if log.deliberation else 0,
                log.deliberation.examined_network_hypotheses if log.deliberation else 0,
                log.deliberation.examined_episodic_memories if log.deliberation else 0,
                log.deliberation.examined_primitives if log.deliberation else 0,
                1 if log.deliberation and log.deliberation.stream_conflict_detected else 0,
                log.deliberation.stream_conflict_resolution if log.deliberation else None,
                log.deliberation.missing_primitive_signal if log.deliberation else None,
                log.final_action, log.final_confidence, log.decision_source,
                log.total_decision_time_ms
            ))
        except Exception as e:
            logger.warning(f"Failed to store reasoning log: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def compute_surprise(
    stream_a_confidence: float,
    stream_b_confidence: float,
    chosen_source: str,
    w_a: float,
    w_b: float
) -> float:
    """
    Compute surprise score for a synthesis decision.

    Surprise is high when:
    - Low-weight stream wins due to high confidence
    - Streams strongly disagree but synthesis creates novel action

    Args:
        stream_a_confidence: Stream A's confidence in its proposal
        stream_b_confidence: Stream B's confidence in its proposal
        chosen_source: Which stream was ultimately chosen
        w_a: Stream A weight
        w_b: Stream B weight

    Returns:
        Surprise score 0.0 to 1.0
    """
    # Expected winner based on weights
    expected_winner = 'stream_a' if w_a > w_b else 'stream_b'

    # Base surprise from weight underdog winning
    if chosen_source != expected_winner and chosen_source != 'synthesis':
        weight_surprise = abs(w_a - w_b)
    else:
        weight_surprise = 0.0

    # Confidence surprise - high when both streams are confident but differ
    confidence_agreement = 1.0 - abs(stream_a_confidence - stream_b_confidence)
    avg_confidence = (stream_a_confidence + stream_b_confidence) / 2
    confidence_surprise = confidence_agreement * avg_confidence * 0.5

    return min(1.0, weight_surprise + confidence_surprise)
