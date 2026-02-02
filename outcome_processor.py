"""
Outcome Processor - Process action results and detect state changes
===================================================================

This module processes the results of each action taken in the game,
detecting meaningful changes like:
- Frame changes (visual differences)
- Score/level changes
- Deaths (game over)
- Level completions
- Full game wins

Usage:
    from outcome_processor import OutcomeProcessor, ActionOutcome

    processor = OutcomeProcessor(db)
    outcome = processor.process(before_state, action, observation)

    if outcome.is_death:
        handle_death()
    elif outcome.is_level_complete:
        handle_level_completion()
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from arcengine import GameAction, GameState

# Import our types
from arc_api_adapter import Observation


@dataclass
class ActionOutcome:
    """
    Result of taking an action in the game.

    Contains all the information about what changed after the action.
    """
    # The action that was taken
    action: GameAction
    action_name: str

    # Frame analysis
    frame_changed: bool = False
    frame_delta_count: int = 0  # Number of pixels that changed

    # Score/level changes
    level_changed: bool = False
    levels_before: int = 0
    levels_after: int = 0
    level_delta: int = 0

    # Terminal states
    is_death: bool = False
    is_level_complete: bool = False
    is_game_win: bool = False
    is_full_win: bool = False  # All levels completed

    # Movement detection
    position_changed: bool = False
    position_delta: Optional[Tuple[int, int]] = None  # (dx, dy)

    # State tracking
    state_before: GameState = GameState.NOT_PLAYED
    state_after: GameState = GameState.NOT_PLAYED

    # Frame data (for learning)
    frame_before: Optional[List[List[int]]] = None
    frame_after: Optional[List[List[int]]] = None

    # Event understanding (from EventDetector)
    detected_events: List[Dict[str, Any]] = field(default_factory=list)
    process_classification: Optional[Dict[str, Any]] = None

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_terminal(self) -> bool:
        """Check if this outcome ends the game."""
        return self.is_death or self.is_game_win

    @property
    def is_positive(self) -> bool:
        """Check if this outcome is positive (level complete or win)."""
        return self.is_level_complete or self.is_game_win

    @property
    def is_negative(self) -> bool:
        """Check if this outcome is negative (death)."""
        return self.is_death

    @property
    def is_neutral(self) -> bool:
        """Check if this outcome is neutral (no terminal state)."""
        return not self.is_terminal

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'action': self.action_name,
            'frame_changed': self.frame_changed,
            'frame_delta_count': self.frame_delta_count,
            'level_changed': self.level_changed,
            'levels_before': self.levels_before,
            'levels_after': self.levels_after,
            'level_delta': self.level_delta,
            'is_death': self.is_death,
            'is_level_complete': self.is_level_complete,
            'is_game_win': self.is_game_win,
            'is_full_win': self.is_full_win,
            'position_changed': self.position_changed,
            'position_delta': self.position_delta,
            'state_before': self.state_before.name,
            'state_after': self.state_after.name,
            'detected_events': self.detected_events,
            'process_classification': self.process_classification,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class LoopState:
    """
    Current state of the game loop.

    This is a simplified view of the game state for outcome processing.
    """
    game_id: str
    current_level: int
    action_count: int
    score: float
    state: GameState
    frame: Optional[List[List[int]]]
    levels_completed: int
    win_levels: int

    @property
    def is_terminal(self) -> bool:
        """Check if game has ended."""
        return self.state in (GameState.WIN, GameState.GAME_OVER)


class OutcomeProcessor:
    """
    Process action outcomes and detect meaningful state changes.

    This class is responsible for:
    1. Detecting frame changes between states
    2. Detecting score/level changes
    3. Detecting deaths (game over)
    4. Detecting level completions
    5. Detecting full game wins
    6. Optionally recording outcomes for learning

    Usage:
        processor = OutcomeProcessor(db)
        outcome = processor.process(before_state, action, observation)
    """

    def __init__(self, db: Any = None, session_id: Optional[str] = None):
        """
        Initialize the outcome processor.

        Args:
            db: Optional database interface for recording outcomes
            session_id: Optional session identifier (auto-generated if not provided)
        """
        self._db: Any = db
        self._frame_change_threshold = 0  # Any change counts
        # Generate session_id for action trace grouping
        self._session_id = session_id or f"session_{hashlib.md5(str(random.random()).encode()).hexdigest()[:8]}_{int(datetime.now().timestamp())}"
        # Lazy-loaded event detection components
        self._event_detector: Any = None
        self._recent_events: List[Dict[str, Any]] = []  # Ring buffer of recent events
        self._max_recent_events = 50

    def process(
        self,
        before_state: LoopState,
        action: GameAction,
        observation: Observation,
    ) -> ActionOutcome:
        """
        Process the outcome of an action.

        Args:
            before_state: State before the action was taken
            action: The action that was taken
            observation: The observation after the action

        Returns:
            ActionOutcome with all detected changes
        """
        # Get frames for comparison
        frame_before = before_state.frame
        frame_after = observation.frame

        # Detect frame changes
        frame_changed, frame_delta_count = self._detect_frame_change(
            frame_before, frame_after
        )

        # Detect level changes
        levels_before = before_state.levels_completed
        levels_after = observation.levels_completed
        level_changed = levels_after != levels_before
        level_delta = levels_after - levels_before

        # Detect terminal states
        is_death = observation.state == GameState.GAME_OVER
        is_game_win = observation.state == GameState.WIN
        is_level_complete = level_delta > 0 and not is_death
        is_full_win = is_game_win and levels_after >= observation.win_levels

        # Detect position changes (simple heuristic)
        position_changed, position_delta = self._detect_position_change(
            frame_before, frame_after
        )

        outcome = ActionOutcome(
            action=action,
            action_name=action.name,
            frame_changed=frame_changed,
            frame_delta_count=frame_delta_count,
            level_changed=level_changed,
            levels_before=levels_before,
            levels_after=levels_after,
            level_delta=level_delta,
            is_death=is_death,
            is_level_complete=is_level_complete,
            is_game_win=is_game_win,
            is_full_win=is_full_win,
            position_changed=position_changed,
            position_delta=position_delta,
            state_before=before_state.state,
            state_after=observation.state,
            frame_before=frame_before,
            frame_after=frame_after,
        )

        # Detect events if frame changed significantly (enables event understanding)
        if frame_changed and frame_delta_count > 10:
            events, process_class = self._detect_events(
                frame_before, frame_after, action
            )
            outcome.detected_events = events
            outcome.process_classification = process_class
            # Add to recent events ring buffer
            self._recent_events.extend(events)
            if len(self._recent_events) > self._max_recent_events:
                self._recent_events = self._recent_events[-self._max_recent_events:]

        # Record action trace to database (enables FrontierTopologyRung)
        self._record_action_trace(before_state, action, outcome, observation)

        return outcome

    def get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent detected events for context building."""
        return list(self._recent_events)

    def _get_event_detector(self) -> Any:
        """Lazy-load the event detector."""
        if self._event_detector is None:
            try:
                from engines.perception.event_detector import EventDetector
                self._event_detector = EventDetector()
            except ImportError:
                pass
        return self._event_detector

    def _detect_events(
        self,
        frame_before: Any,
        frame_after: Any,
        action: GameAction,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Detect events between frames using EventDetector.

        Args:
            frame_before: Frame before action
            frame_after: Frame after action
            action: The action that was taken

        Returns:
            Tuple of (list of event dicts, process classification dict or None)
        """
        detector = self._get_event_detector()
        if detector is None:
            return [], None

        try:
            import numpy as np

            # Convert frames to numpy if needed
            if not isinstance(frame_before, np.ndarray):
                frame_before = np.array(frame_before, dtype=np.uint8)
            if not isinstance(frame_after, np.ndarray):
                frame_after = np.array(frame_after, dtype=np.uint8)

            # Extract action number for timestamp
            action_number = 0
            if action.name.startswith('ACTION'):
                try:
                    action_number = int(action.name[6:])
                except ValueError:
                    pass

            # Detect events
            _tracked, events = detector.detect_events_from_frames(
                frame_before, frame_after, action_number
            )

            # Classify process
            process_class = None
            if events:
                classification = detector.classify_process(events)
                process_class = {
                    'process_type': classification.process_type.value,
                    'confidence': classification.confidence,
                    'description': classification.description,
                    'event_count': classification.event_count,
                }

            # Convert events to dicts
            event_dicts = [e.to_dict() for e in events]

            return event_dicts, process_class

        except Exception:
            return [], None

    def _record_action_trace(
        self,
        before_state: LoopState,
        action: GameAction,
        outcome: ActionOutcome,
        observation: Observation,
    ) -> None:
        """
        Record action trace to database for network-level learning.

        This enables FrontierTopologyRung to aggregate knowledge across all agents
        about what actions work from each frame state.

        Args:
            before_state: State before action was taken
            action: The action that was executed
            outcome: The processed outcome
            observation: The observation after the action
        """
        if self._db is None:
            return

        try:
            # Extract action number from name (ACTION1 -> 1, ACTION2 -> 2, etc.)
            action_number = 0
            if action.name.startswith('ACTION'):
                try:
                    action_number = int(action.name[6:])
                except ValueError:
                    pass

            # Build trace data
            trace_data: Dict[str, Any] = {
                'session_id': self._session_id,
                'game_id': before_state.game_id,
                'action_number': action_number,
                'timestamp': outcome.timestamp.isoformat(),
                'frame_before': outcome.frame_before,  # List[List[int]], will compute frame_hash
                'frame_after': outcome.frame_after,
                'frame_changed': outcome.frame_changed,
                'score_before': before_state.score,
                'score_after': observation.score,
                'score_change': observation.score - before_state.score,
                'level_number': before_state.current_level + 1,  # 1-indexed
                'resulted_in_game_over': outcome.is_death,
                'response_data': {
                    'action': action.name,
                    'state': outcome.state_after.name,
                    'level_delta': outcome.level_delta,
                    'is_level_complete': outcome.is_level_complete,
                    'is_game_win': outcome.is_game_win,
                },
            }

            # Call save_action_trace which will compute frame_hash
            self._db.save_action_trace(trace_data)

        except Exception:  # noqa: Telemetry failure is acceptable
            # Log but don't fail the game loop
            # Per Rule 2: use database logging, but we don't want to import that here
            # Silent failure is acceptable for telemetry
            pass

    def _detect_frame_change(
        self,
        frame_before: Optional[List[List[int]]],
        frame_after: Optional[List[List[int]]],
    ) -> Tuple[bool, int]:
        """
        Detect if the frame changed between states.

        Returns:
            Tuple of (changed: bool, delta_count: int)
        """
        if frame_before is None or frame_after is None:
            return False, 0

        # Handle different frame sizes
        if len(frame_before) != len(frame_after):
            return True, -1  # Size changed, can't count

        delta_count = 0
        try:
            for row_before, row_after in zip(frame_before, frame_after):
                if len(row_before) != len(row_after):
                    return True, -1  # Row size changed

                for val_before, val_after in zip(row_before, row_after):
                    # Handle numpy arrays and scalars
                    try:
                        import numpy as np
                        if isinstance(val_before, np.ndarray) or isinstance(val_after, np.ndarray):
                            if not np.array_equal(val_before, val_after):
                                delta_count += 1
                        else:
                            if val_before != val_after:
                                delta_count += 1
                    except ImportError:
                        if val_before != val_after:
                            delta_count += 1
        except Exception:
            return True, -1

        changed = delta_count > self._frame_change_threshold
        return changed, delta_count

    def _detect_position_change(
        self,
        frame_before: Optional[List[List[int]]],
        frame_after: Optional[List[List[int]]],
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Detect if the agent's position changed.

        This is a simple heuristic - looks for a consistent movement pattern
        in the frame changes. More sophisticated detection would use the
        agent self-model.

        Returns:
            Tuple of (changed: bool, delta: Optional[Tuple[int, int]])
        """
        if frame_before is None or frame_after is None:
            return False, None

        # Find positions that changed
        # This is a simplified heuristic - real position detection
        # would use the self-model to track controlled objects

        appeared: List[Tuple[int, int, Any]] = []  # Positions that appeared
        disappeared: List[Tuple[int, int, Any]] = []  # Positions that disappeared

        try:
            import numpy as np
            has_numpy = True
        except ImportError:
            np = None  # type: ignore
            has_numpy = False

        try:
            height = min(len(frame_before), len(frame_after))
            for y in range(height):
                width = min(len(frame_before[y]), len(frame_after[y]))
                for x in range(width):
                    val_before: Any = frame_before[y][x]
                    val_after: Any = frame_after[y][x]

                    # Handle numpy arrays
                    if has_numpy and np is not None:
                        if isinstance(val_before, np.ndarray):
                            val_before = int(float(np.sum(val_before)))  # type: ignore
                        if isinstance(val_after, np.ndarray):
                            val_after = int(float(np.sum(val_after)))  # type: ignore

                    if val_before != val_after:
                        if val_before == 0 and val_after != 0:
                            appeared.append((x, y, val_after))
                        elif val_before != 0 and val_after == 0:
                            disappeared.append((x, y, val_before))
        except Exception:
            return False, None

        # Simple heuristic: if exactly one thing moved, calculate delta
        if len(appeared) == 1 and len(disappeared) == 1:
            ax, ay, av = appeared[0]
            dx_pos, dy_pos, dv = disappeared[0]

            # Same color/value = same object moved
            if av == dv:
                delta = (ax - dx_pos, ay - dy_pos)
                return True, delta

        # Multiple changes or no clear movement
        if appeared or disappeared:
            return True, None

        return False, None

    def record(
        self,
        outcome: ActionOutcome,
        context: Dict[str, Any],
    ) -> None:
        """
        Record an outcome to the database for learning.

        Args:
            outcome: The action outcome to record
            context: Additional context (game_id, agent_id, etc.)
        """
        if self._db is None:
            return

        # Build record
        record = outcome.to_dict()
        record.update({
            'game_id': context.get('game_id'),
            'agent_id': context.get('agent_id'),
            'action_count': context.get('action_count'),
            'level': context.get('level'),
        })

        # Store in database
        try:
            self._db.record_action_outcome(record)
        except AttributeError:
            # Database doesn't have this method yet
            pass
        except Exception as e:
            # Log but don't fail
            print(f"[WARN] Failed to record outcome: {e}")


class OutcomeTracker:
    """
    Track outcomes over a game session for pattern analysis.

    Maintains a history of outcomes to detect patterns like:
    - Repeated deaths at same location
    - Oscillation (repeated back-and-forth)
    - Progress stalls
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize the tracker.

        Args:
            max_history: Maximum number of outcomes to track
        """
        self._history: List[ActionOutcome] = []
        self._max_history = max_history

        # Aggregates
        self._death_count = 0
        self._level_complete_count = 0
        self._frame_change_count = 0
        self._no_change_streak = 0

    def add(self, outcome: ActionOutcome) -> None:
        """Add an outcome to the history."""
        self._history.append(outcome)

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Update aggregates
        if outcome.is_death:
            self._death_count += 1
        if outcome.is_level_complete:
            self._level_complete_count += 1
        if outcome.frame_changed:
            self._frame_change_count += 1
            self._no_change_streak = 0
        else:
            self._no_change_streak += 1

    @property
    def history(self) -> List[ActionOutcome]:
        """Get the outcome history."""
        return self._history.copy()

    @property
    def death_count(self) -> int:
        """Get total deaths tracked."""
        return self._death_count

    @property
    def level_complete_count(self) -> int:
        """Get total level completions tracked."""
        return self._level_complete_count

    @property
    def no_change_streak(self) -> int:
        """Get current streak of no-change outcomes."""
        return self._no_change_streak

    def get_recent_actions(self, n: int = 10) -> List[str]:
        """Get the last n action names."""
        return [o.action_name for o in self._history[-n:]]

    def detect_oscillation(self, window: int = 6) -> bool:
        """
        Detect if recent actions show oscillation pattern.

        Oscillation = repeated back-and-forth like: A1, A2, A1, A2, A1, A2
        """
        if len(self._history) < window:
            return False

        recent = self.get_recent_actions(window)

        # Check for A-B-A-B pattern
        if window >= 4:
            first = recent[0]
            second = recent[1]

            if first != second:
                expected = [first, second] * (window // 2)
                if recent[:len(expected)] == expected:
                    return True

        return False

    def detect_stuck(self, threshold: int = 10) -> bool:
        """
        Detect if the agent appears stuck (no progress).

        Stuck = many actions with no frame changes or level progress.
        """
        return self._no_change_streak >= threshold

    def get_action_distribution(self) -> Dict[str, int]:
        """Get distribution of actions taken."""
        dist: Dict[str, int] = {}
        for outcome in self._history:
            dist[outcome.action_name] = dist.get(outcome.action_name, 0) + 1
        return dist

    def reset(self) -> None:
        """Reset the tracker for a new game."""
        self._history.clear()
        self._death_count = 0
        self._level_complete_count = 0
        self._frame_change_count = 0
        self._no_change_streak = 0


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Outcome Processor - Quick Test")
    print("=" * 50)

    # Create a mock state
    before = LoopState(
        game_id="ls20",
        current_level=0,
        action_count=5,
        score=0.0,
        state=GameState.NOT_FINISHED,
        frame=[[0, 1, 0], [0, 0, 0], [0, 0, 2]],
        levels_completed=0,
        win_levels=5,
    )

    # Create processor
    processor = OutcomeProcessor()

    # Test frame change detection (using public interface via process())
    print("\nTest 1: Frame change detection")
    frame1 = [[0, 1, 0], [0, 0, 0], [0, 0, 2]]
    frame2 = [[0, 0, 0], [0, 1, 0], [0, 0, 2]]  # 1 moved down
    # Access private method for testing only
    changed, count = processor._detect_frame_change(frame1, frame2)  # pyright: ignore[reportPrivateUsage]
    print(f"  Frame changed: {changed}, pixels changed: {count}")

    # Test position detection
    print("\nTest 2: Position change detection")
    pos_changed, delta = processor._detect_position_change(frame1, frame2)  # pyright: ignore[reportPrivateUsage]
    print(f"  Position changed: {pos_changed}, delta: {delta}")

    # Test outcome tracker
    print("\nTest 3: Outcome tracker")
    tracker = OutcomeTracker()

    # Simulate some outcomes
    for i in range(6):
        action = GameAction.ACTION1 if i % 2 == 0 else GameAction.ACTION2
        outcome = ActionOutcome(
            action=action,
            action_name=action.name,
            frame_changed=True,
        )
        tracker.add(outcome)

    print(f"  Actions: {tracker.get_recent_actions()}")
    print(f"  Oscillation detected: {tracker.detect_oscillation()}")
    print(f"  Action distribution: {tracker.get_action_distribution()}")

    print("\n[OK] All tests passed!")
