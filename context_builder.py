"""
Context Builder - Build context for decision rungs
==================================================

This module builds the context dictionary that the decision rung system
needs to make action decisions. It extracts and packages:
- Game identification and state
- Agent info (ID, role, weights)
- Position tracking
- Safety weights from danger detection
- Recent action history
- Exploration stats
- CODS context

Usage:
    from context_builder import ContextBuilder

    builder = ContextBuilder(db)
    context = builder.build(loop_state, agent_config)

    # Pass to decision system
    action, reason = decision_system.decide(observation, context)
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from arcengine import GameAction, GameState

# Import our types
from arc_api_adapter import Observation
from outcome_processor import ActionOutcome, LoopState


@dataclass
class AgentConfig:
    """Configuration for an agent playing games."""
    agent_id: str
    role: str = "pioneer"  # pioneer, optimizer, generalist, exploiter

    # Stream weights (Two Streams theory)
    w_A: float = 0.5  # Private experience weight
    w_B: float = 0.5  # Collective wisdom weight

    # Exploration settings
    exploration_rate: float = 0.3

    # Budget
    action_budget: int = 2000

    # Metadata
    generation: int = 0
    fitness: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'w_A': self.w_A,
            'w_B': self.w_B,
            'exploration_rate': self.exploration_rate,
            'action_budget': self.action_budget,
            'generation': self.generation,
            'fitness': self.fitness,
        }


@dataclass
class DecisionContext:
    """
    Complete context for making a decision.

    This is what gets passed to the decision rung system.
    """
    # Game identification
    game_id: str
    game_type: str  # First 4 chars of game_id
    level: int

    # Game state
    score: float
    levels_completed: int
    win_levels: int
    game_state: GameState

    # Budget tracking
    action_count: int
    budget_remaining: int
    budget_used_percent: float
    phase: str  # "orientation", "hypothesis", "exploitation"

    # Agent info
    agent_id: Optional[str] = None
    agent_role: str = "pioneer"
    w_A: float = 0.5
    w_B: float = 0.5

    # Position tracking
    agent_position: Optional[Tuple[int, int]] = None
    last_position: Optional[Tuple[int, int]] = None
    position_history: List[Tuple[int, int]] = field(default_factory=lambda: [])

    # Safety weights (danger avoidance)
    action_safety_weights: Dict[str, float] = field(default_factory=lambda: {})

    # Recent history
    recent_actions: List[str] = field(default_factory=lambda: [])
    recent_outcomes: List[str] = field(default_factory=lambda: [])  # "positive", "negative", "neutral"

    # Exploration tracking
    is_frontier: bool = False  # Unbeaten level
    exploration_coverage: float = 0.0
    visited_positions: int = 0

    # CODS context (if available)
    cods_hypothesis: Optional[str] = None
    cods_confidence: float = 0.0

    # Sequence context
    has_winning_sequence: bool = False
    sequence_step: int = 0
    sequence_length: int = 0

    # Frontier checkpoint context (constructive pathfinding)
    checkpoint_sequence: Optional[List[int]] = None
    checkpoint_position: int = 0

    # Flags
    is_stuck: bool = False
    is_oscillating: bool = False
    death_count: int = 0

    # Frame info
    frame_width: int = 0
    frame_height: int = 0
    frame_hash: str = ""  # Hash of current frame for topology queries

    # Prior lessons (from lessons_learned table)
    prior_lessons: List[Dict[str, Any]] = field(default_factory=lambda: [])

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rung system compatibility."""
        return {
            # Game
            'game_id': self.game_id,
            'game_type': self.game_type,
            'level': self.level,
            'score': self.score,
            'levels_completed': self.levels_completed,
            'win_levels': self.win_levels,
            'game_state': self.game_state.name,

            # Budget
            'action_count': self.action_count,
            'budget_remaining': self.budget_remaining,
            'budget_used_percent': self.budget_used_percent,
            'phase': self.phase,

            # Agent
            'agent_id': self.agent_id,
            'agent_role': self.agent_role,
            'w_A': self.w_A,
            'w_B': self.w_B,

            # Position
            'agent_position': self.agent_position,
            'last_position': self.last_position,

            # Safety
            'action_safety_weights': self.action_safety_weights,

            # History
            'recent_actions': self.recent_actions,
            'recent_outcomes': self.recent_outcomes,

            # Exploration
            'is_frontier': self.is_frontier,
            'exploration_coverage': self.exploration_coverage,

            # CODS
            'cods_hypothesis': self.cods_hypothesis,
            'cods_confidence': self.cods_confidence,

            # Sequence
            'has_winning_sequence': self.has_winning_sequence,
            'sequence_step': self.sequence_step,
            'sequence_length': self.sequence_length,

            # Frontier checkpoint (constructive pathfinding)
            'checkpoint_sequence': self.checkpoint_sequence,
            'checkpoint_position': self.checkpoint_position,

            # Active sequence aliases (used by CONTEXT_ADAPTIVE strategy selection)
            # Maps checkpoint -> active_sequence for unified handling
            'active_sequence': self.checkpoint_sequence,
            'sequence_position': self.checkpoint_position,

            # Flags
            'is_stuck': self.is_stuck,
            'is_oscillating': self.is_oscillating,
            'death_count': self.death_count,

            # Frame
            'frame_width': self.frame_width,
            'frame_height': self.frame_height,
            'frame_hash': self.frame_hash,

            # Frontier mode (alias for is_frontier, used by topology rung)
            'frontier_mode': self.is_frontier,

            # Prior lessons for PriorLessonsRung
            'prior_lessons': self.prior_lessons,
        }


class ContextBuilder:
    """
    Build context for the decision rung system.

    Extracts and packages all the state that decision rungs need:
    - Game identification
    - Agent info (ID, role, w_A/w_B weights)
    - Position tracking
    - Safety weights from danger detection
    - Recent actions history
    - Exploration stats
    - CODS context
    - Frontier checkpoint replay state with divergence detection
    """

    def __init__(
        self,
        db: Any = None,
        exploration_tracker: Any = None,
        terminal_detector: Any = None,
    ):
        """
        Initialize the context builder.

        Args:
            db: Database interface for querying state
            exploration_tracker: Optional NetworkExplorationTracker
            terminal_detector: Optional TerminalPatternDetector
        """
        self._db: Any = db
        self._exploration_tracker: Any = exploration_tracker
        self._terminal_detector: Any = terminal_detector

        # Internal state
        self._recent_actions: List[str] = []
        self._recent_outcomes: List[str] = []
        self._position_history: List[Tuple[int, int]] = []
        self._visited_positions: Set[Tuple[int, int]] = set()
        self._death_count = 0
        self._current_game_id: Optional[str] = None

        # Frontier checkpoint replay state
        self._checkpoint_sequence: Optional[List[str]] = None
        self._checkpoint_position: int = 0
        self._checkpoint_level: Optional[int] = None  # Track which level checkpoint is for

        # Divergence detection state
        self._checkpoint_expected_frames: int = 0  # Expected unique frames from checkpoint
        self._checkpoint_frames_seen: Set[str] = set()  # Frame hashes seen during replay
        self._checkpoint_divergence_checked: bool = False  # Only check once at midpoint

    def build(
        self,
        loop_state: LoopState,
        agent_config: Optional[AgentConfig] = None,
        observation: Optional[Observation] = None,
    ) -> DecisionContext:
        """
        Build complete context for decision making.

        Args:
            loop_state: Current game loop state
            agent_config: Optional agent configuration
            observation: Optional current observation

        Returns:
            DecisionContext with all relevant information
        """
        agent_config = agent_config or AgentConfig(agent_id="default")

        # Calculate budget info
        budget = agent_config.action_budget
        budget_remaining = max(0, budget - loop_state.action_count)
        budget_used_percent = loop_state.action_count / budget if budget > 0 else 1.0

        # Determine phase based on budget used
        phase = self._determine_phase(budget_used_percent)

        # Get frame dimensions
        frame_width = 0
        frame_height = 0
        if loop_state.frame:
            frame_height = len(loop_state.frame)
            frame_width = len(loop_state.frame[0]) if frame_height > 0 else 0

        # Get agent position (simplified - would use self-model in full implementation)
        agent_position = self._detect_agent_position(loop_state.frame)

        # Check if this is a frontier (unbeaten) level
        is_frontier = self._check_is_frontier(loop_state.game_id, loop_state.current_level)

        # Get safety weights
        safety_weights = self._get_safety_weights(loop_state)

        # Check for winning sequence
        has_sequence, seq_step, seq_length = self._check_winning_sequence(
            loop_state.game_id, loop_state.current_level
        )

        # Get CODS context
        cods_hypothesis, cods_confidence = self._get_cods_context(loop_state.game_id)

        # Build context
        return DecisionContext(
            # Game
            game_id=loop_state.game_id,
            game_type=loop_state.game_id[:4] if len(loop_state.game_id) >= 4 else loop_state.game_id,
            level=loop_state.current_level,
            score=loop_state.score,
            levels_completed=loop_state.levels_completed,
            win_levels=loop_state.win_levels,
            game_state=loop_state.state,

            # Budget
            action_count=loop_state.action_count,
            budget_remaining=budget_remaining,
            budget_used_percent=budget_used_percent,
            phase=phase,

            # Agent
            agent_id=agent_config.agent_id,
            agent_role=agent_config.role,
            w_A=agent_config.w_A,
            w_B=agent_config.w_B,

            # Position
            agent_position=agent_position,
            last_position=self._position_history[-1] if self._position_history else None,
            position_history=self._position_history[-10:],

            # Safety
            action_safety_weights=safety_weights,

            # History
            recent_actions=self._recent_actions[-10:],
            recent_outcomes=self._recent_outcomes[-10:],

            # Exploration
            is_frontier=is_frontier,
            exploration_coverage=self._calculate_coverage(),
            visited_positions=len(self._visited_positions),

            # CODS
            cods_hypothesis=cods_hypothesis,
            cods_confidence=cods_confidence,

            # Sequence
            has_winning_sequence=has_sequence,
            sequence_step=seq_step,
            sequence_length=seq_length,

            # Frontier checkpoint (for CONTEXT_ADAPTIVE strategy transition)
            checkpoint_sequence=self._checkpoint_sequence,
            checkpoint_position=self._checkpoint_position,

            # Flags
            is_stuck=self._detect_stuck(),
            is_oscillating=self._detect_oscillation(),
            death_count=self._death_count,

            # Frame
            frame_width=frame_width,
            frame_height=frame_height,
        )

    def update(self, action: str, outcome: ActionOutcome, decision_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update internal state after an action.

        Args:
            action: The action name that was taken
            outcome: The outcome of the action
            decision_metadata: Optional metadata from the decision system (contains checkpoint info)
        """
        # Track action
        self._recent_actions.append(action)
        if len(self._recent_actions) > 50:
            self._recent_actions = self._recent_actions[-50:]

        # Track outcome type
        if outcome.is_positive:
            self._recent_outcomes.append("positive")
        elif outcome.is_negative:
            self._recent_outcomes.append("negative")
        else:
            self._recent_outcomes.append("neutral")

        if len(self._recent_outcomes) > 50:
            self._recent_outcomes = self._recent_outcomes[-50:]

        # Track position
        if outcome.position_delta and outcome.frame_after:
            # Update position based on delta
            if self._position_history:
                last_x, last_y = self._position_history[-1]
                dx, dy = outcome.position_delta
                new_pos = (last_x + dx, last_y + dy)
            else:
                new_pos = self._detect_agent_position(outcome.frame_after)

            if new_pos:
                self._position_history.append(new_pos)
                self._visited_positions.add(new_pos)

        if len(self._position_history) > 100:
            self._position_history = self._position_history[-100:]

        # Track deaths - also clears checkpoint on death
        if outcome.is_death:
            self._death_count += 1
            self._clear_checkpoint()

        # Handle checkpoint state from decision metadata
        if decision_metadata:
            self._handle_checkpoint_metadata(decision_metadata)

        # Advance checkpoint position if we're replaying
        if self._checkpoint_sequence is not None:
            # Track frame for divergence detection
            if outcome.frame_after:
                frame_hash = self._compute_frame_hash(outcome.frame_after)
                self._track_frame_for_divergence(frame_hash)

            # Check for divergence at midpoint
            if self._check_checkpoint_divergence():
                # Checkpoint has diverged - bail early and switch to WEIGHTED
                self._clear_checkpoint()
            else:
                self._checkpoint_position += 1
                # Check if we've exhausted the checkpoint
                if self._checkpoint_position >= len(self._checkpoint_sequence):
                    # Checkpoint exhausted - will fall through to WEIGHTED on next decision
                    # Keep the sequence for one more cycle so strategy can detect the transition
                    pass

    def _handle_checkpoint_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Handle checkpoint-related metadata from decision system.

        When FrontierCheckpointRung loads a checkpoint, it returns metadata with:
        - checkpoint_loaded: True
        - checkpoint_data: {'action_sequence': [...], 'unique_frames_seen': N, ...}

        This captures that data for subsequent context builds and divergence detection.
        """
        if metadata.get('checkpoint_loaded') and metadata.get('checkpoint_data'):
            checkpoint_data = metadata['checkpoint_data']
            sequence = checkpoint_data.get('action_sequence', [])
            if sequence:
                self._checkpoint_sequence = sequence
                self._checkpoint_position = 0  # Will be incremented after this action
                # Capture expected frames for divergence detection
                self._checkpoint_expected_frames = checkpoint_data.get('unique_frames_seen', 0)
                self._checkpoint_frames_seen = set()  # Reset frame tracking
                self._checkpoint_divergence_checked = False

    def _track_frame_for_divergence(self, frame_hash: str) -> None:
        """Track a frame hash during checkpoint replay for divergence detection."""
        if self._checkpoint_sequence is not None and frame_hash:
            self._checkpoint_frames_seen.add(frame_hash)

    def _check_checkpoint_divergence(self) -> bool:
        """
        Check if checkpoint replay has diverged from expected trajectory.

        Called at ~50% through the checkpoint. If unique_frames_seen is
        significantly below expected, the game state has diverged and we
        should bail early to avoid wasting actions.

        Returns:
            True if diverged (should clear checkpoint), False if on track
        """
        if self._checkpoint_sequence is None:
            return False

        if self._checkpoint_divergence_checked:
            return False  # Only check once

        seq_len = len(self._checkpoint_sequence)
        midpoint = seq_len // 2

        # Only check at or after midpoint
        if self._checkpoint_position < midpoint:
            return False

        self._checkpoint_divergence_checked = True

        # If no expected frames recorded, skip check
        if self._checkpoint_expected_frames <= 0:
            return False

        # Calculate expected frames at this point (proportional)
        progress_ratio = self._checkpoint_position / seq_len
        expected_at_this_point = int(self._checkpoint_expected_frames * progress_ratio)

        # Allow 30% tolerance - if we're seeing <70% of expected frames, bail
        threshold = expected_at_this_point * 0.7
        actual_frames = len(self._checkpoint_frames_seen)

        if actual_frames < threshold and expected_at_this_point >= 3:
            # Diverged - not seeing enough unique frames
            # Minimum 3 expected frames to trigger (avoid false positives on short checkpoints)
            return True

        return False

    def set_checkpoint(self, sequence: List[str], level: int) -> None:
        """
        Explicitly set a checkpoint sequence for replay.

        Args:
            sequence: List of action names to replay
            level: The level this checkpoint is for
        """
        self._checkpoint_sequence = sequence
        self._checkpoint_position = 0
        self._checkpoint_level = level
        self._checkpoint_expected_frames = 0
        self._checkpoint_frames_seen = set()
        self._checkpoint_divergence_checked = False

    def _clear_checkpoint(self) -> None:
        """Clear checkpoint state (on death, level change, divergence, or exhaustion)."""
        self._checkpoint_sequence = None
        self._checkpoint_position = 0
        self._checkpoint_level = None
        self._checkpoint_expected_frames = 0
        self._checkpoint_frames_seen = set()
        self._checkpoint_divergence_checked = False

    def _compute_frame_hash(self, frame: Optional[List[List[int]]]) -> str:
        """
        Compute a hash of a frame for divergence detection.

        Args:
            frame: 2D grid of integers

        Returns:
            Hash string, or empty string if frame is None
        """
        if not frame:
            return ""
        try:
            import hashlib

            # Flatten and convert to bytes
            flat = []
            for row in frame:
                for cell in row:
                    # Handle both scalar and array values
                    if hasattr(cell, '__iter__') and not isinstance(cell, (str, bytes)):
                        flat.extend(cell)
                    else:
                        flat.append(int(cell))
            data = bytes(flat)
            return hashlib.md5(data).hexdigest()[:12]
        except Exception:
            return ""

    def on_level_change(self, new_level: int) -> None:
        """
        Handle level transition.

        Clears checkpoint if it was for a different level.
        """
        if self._checkpoint_level is not None and self._checkpoint_level != new_level:
            self._clear_checkpoint()

    def reset(self, game_id: str) -> None:
        """
        Reset state for a new game.

        Args:
            game_id: The new game ID
        """
        self._current_game_id = game_id
        self._recent_actions.clear()
        self._recent_outcomes.clear()
        self._position_history.clear()
        self._visited_positions.clear()
        self._death_count = 0
        self._clear_checkpoint()  # Clear checkpoint on game reset

    def _determine_phase(self, budget_used_percent: float) -> str:
        """Determine the current game phase based on budget usage."""
        if budget_used_percent < 0.1:
            return "orientation"  # First 10% - learning game mechanics
        elif budget_used_percent < 0.5:
            return "hypothesis"  # 10-50% - testing theories
        else:
            return "exploitation"  # 50%+ - using what we've learned

    def _detect_agent_position(
        self,
        frame: Optional[List[List[int]]],
    ) -> Optional[Tuple[int, int]]:
        """
        Detect the agent's position in the frame.

        This is a simplified heuristic. Full implementation would use
        the agent self-model.
        """
        if not frame:
            return None

        # Simple heuristic: find first non-zero cell
        # (In reality, would track controlled object)
        try:
            for y, row in enumerate(frame):
                for x, val in enumerate(row):
                    # Handle both scalar and array values
                    try:
                        is_nonzero = bool(val != 0)
                    except ValueError:
                        # Numpy array - check if any element is nonzero
                        import numpy as np
                        is_nonzero = np.any(val != 0)

                    if is_nonzero:
                        return (x, y)
        except Exception:
            pass

        return None

    def _check_is_frontier(self, game_id: str, level: int) -> bool:
        """Check if this level has been beaten before."""
        if self._db is None:
            return True  # Assume frontier if no DB

        try:
            # Query database for winning sequences
            result = self._db.execute("""
                SELECT COUNT(*) FROM winning_sequences
                WHERE game_type = ? AND level = ? AND is_active = 1
            """, (game_id[:4], level)).fetchone()

            return result[0] == 0
        except Exception:
            return True

    def _get_safety_weights(
        self,
        loop_state: LoopState,
    ) -> Dict[str, float]:
        """
        Get safety weights for each action based on danger patterns.

        Higher weight = safer action.
        """
        weights: Dict[str, float] = {}

        # Default weights (all actions equally safe)
        for action in GameAction:
            weights[action.name] = 1.0

        if self._terminal_detector is None:
            return weights

        try:
            # Query terminal patterns for this game
            patterns: List[Dict[str, Any]] = self._terminal_detector.get_danger_patterns(
                loop_state.game_id[:4],
                loop_state.current_level,
            )

            # Reduce weight for actions that led to deaths
            for pattern in patterns:
                action_name: str = str(pattern.get('action', ''))
                if action_name in weights:
                    # Reduce weight based on death count
                    death_count: int = int(pattern.get('death_count', 0))
                    weights[action_name] = max(0.1, 1.0 - (death_count * 0.1))

        except Exception:
            pass

        return weights

    def _check_winning_sequence(
        self,
        game_id: str,
        level: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if there's a winning sequence for this level.

        Returns:
            Tuple of (has_sequence, current_step, total_length)
        """
        if self._db is None:
            return False, 0, 0

        try:
            # Query for winning sequence
            result = self._db.execute("""
                SELECT sequence_data, action_count
                FROM winning_sequences
                WHERE game_type = ? AND level = ? AND is_active = 1
                ORDER BY action_count ASC
                LIMIT 1
            """, (game_id[:4], level)).fetchone()

            if result:
                return True, 0, result[1]

            return False, 0, 0
        except Exception:
            return False, 0, 0

    def _get_cods_context(
        self,
        game_id: str,
    ) -> Tuple[Optional[str], float]:
        """
        Get CODS (Cognitive Operator Discovery System) context.

        Returns:
            Tuple of (hypothesis_description, confidence)
        """
        if self._db is None:
            return None, 0.0

        try:
            # Query for active hypothesis
            result = self._db.execute("""
                SELECT hypothesis_id, reliability_score
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1
                ORDER BY reliability_score DESC
                LIMIT 1
            """, (game_id[:4],)).fetchone()

            if result:
                return result[0], result[1]

            return None, 0.0
        except Exception:
            return None, 0.0

    def _calculate_coverage(self) -> float:
        """Calculate exploration coverage as fraction of visited positions."""
        if not self._visited_positions:
            return 0.0

        # Simple metric: visited positions / reasonable estimate
        # (Better would be: visited / total reachable positions)
        return min(1.0, len(self._visited_positions) / 100.0)

    def _detect_stuck(self) -> bool:
        """Detect if the agent appears stuck."""
        if len(self._recent_outcomes) < 10:
            return False

        # Stuck = many neutral outcomes in a row
        recent = self._recent_outcomes[-10:]
        neutral_count = sum(1 for o in recent if o == "neutral")
        return neutral_count >= 8

    def _detect_oscillation(self) -> bool:
        """Detect if recent actions show oscillation pattern."""
        if len(self._recent_actions) < 6:
            return False

        recent = self._recent_actions[-6:]

        # Check for A-B-A-B pattern
        if len(set(recent)) == 2:
            first = recent[0]
            second = recent[1]
            expected = [first, second, first, second, first, second]
            if recent == expected:
                return True

        return False


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Context Builder - Quick Test")
    print("=" * 50)

    # Create mock state
    loop_state = LoopState(
        game_id="ls20",
        current_level=0,
        action_count=50,
        score=0.0,
        state=GameState.NOT_FINISHED,
        frame=[[0, 1, 0], [0, 0, 0], [0, 0, 2]],
        levels_completed=0,
        win_levels=5,
    )

    agent_config = AgentConfig(
        agent_id="test-agent",
        role="pioneer",
        w_A=0.6,
        w_B=0.4,
        action_budget=2000,
    )

    # Create builder (no DB)
    builder = ContextBuilder()

    # Build context
    context = builder.build(loop_state, agent_config)

    print(f"\nGame: {context.game_id} (type: {context.game_type})")
    print(f"Level: {context.level}")
    print(f"Phase: {context.phase}")
    print(f"Budget: {context.action_count}/{agent_config.action_budget} ({context.budget_used_percent:.1%})")
    print(f"Agent: {context.agent_id} ({context.agent_role})")
    print(f"Weights: w_A={context.w_A}, w_B={context.w_B}")
    print(f"Frontier: {context.is_frontier}")
    print(f"Position: {context.agent_position}")

    # Test update
    print("\nTesting update...")
    from outcome_processor import ActionOutcome

    outcome = ActionOutcome(
        action=GameAction.ACTION1,
        action_name="ACTION1",
        frame_changed=True,
        position_changed=True,
        position_delta=(1, 0),
    )
    builder.update("ACTION1", outcome)

    context2 = builder.build(loop_state, agent_config)
    print(f"Recent actions: {context2.recent_actions}")
    print(f"Recent outcomes: {context2.recent_outcomes}")

    # Test to_dict
    print("\nContext as dict (sample keys):")
    d = context.to_dict()
    for key in ['game_id', 'phase', 'agent_role', 'is_frontier']:
        print(f"  {key}: {d[key]}")

    print("\n[OK] All tests passed!")
