"""
Learning Systems - Coordinate all learning and memory systems
=============================================================

This module coordinates all the learning capabilities:
- CODS (Cognitive Operator Discovery System)
- Replay Learning (learn from game recordings)
- Self-Model (track controlled objects)
- Terminal Pattern Detection (death patterns)
- Network Knowledge Synthesis
- Sequence Mining

Instead of 50+ imports scattered in one file, this provides a clean
interface to all learning capabilities with lazy loading.

Usage:
    from learning_systems import LearningSystems

    learning = LearningSystems(db)

    # On game start
    learning.on_game_start(game_id, agent_id)

    # After each action
    learning.update(loop_state, action, outcome)

    # On game end
    learning.on_game_end(result)
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from arcengine import GameAction, GameState

# Import our types
from outcome_processor import ActionOutcome, LoopState


@dataclass
class GameResult:
    """Result of a complete game."""
    game_id: str
    final_score: float
    levels_completed: int
    win_levels: int
    total_actions: int
    is_win: bool
    is_full_win: bool
    action_sequence: List[str]
    agent_id: Optional[str] = None
    duration_seconds: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def win_rate(self) -> float:
        """Get win rate as levels_completed / win_levels."""
        if self.win_levels == 0:
            return 0.0
        return self.levels_completed / self.win_levels

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'game_id': self.game_id,
            'game_type': self.game_id[:4] if len(self.game_id) >= 4 else self.game_id,
            'final_score': self.final_score,
            'levels_completed': self.levels_completed,
            'win_levels': self.win_levels,
            'total_actions': self.total_actions,
            'is_win': self.is_win,
            'is_full_win': self.is_full_win,
            'agent_id': self.agent_id,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class LearningSystems:
    """
    Coordinator for all learning and memory systems.

    This provides a clean interface to all learning capabilities:
    - CODS (Cognitive Operator Discovery System)
    - Replay Learning
    - Self-Model updates
    - Terminal Pattern recording
    - Network knowledge synthesis

    All systems are lazy-loaded to avoid import overhead.
    """

    def __init__(
        self,
        db: Any = None,
        cods_engine: Any = None,
        replay_engine: Any = None,
        self_model: Any = None,
        terminal_detector: Any = None,
    ):
        """
        Initialize learning systems coordinator.

        Args:
            db: Database interface
            cods_engine: Optional pre-created CODSEngine
            replay_engine: Optional pre-created ReplayLearningEngine
            self_model: Optional pre-created AgentSelfModel
            terminal_detector: Optional pre-created TerminalPatternDetector
        """
        self._db: Any = db

        # Pre-created engines (optional)
        self._cods: Any = cods_engine
        self._replay: Any = replay_engine
        self._self_model: Any = self_model
        self._terminal: Any = terminal_detector

        # Lazy loading flags
        self._cods_loaded = cods_engine is not None
        self._replay_loaded = replay_engine is not None
        self._self_model_loaded = self_model is not None
        self._terminal_loaded = terminal_detector is not None

        # Session tracking
        self._current_game_id: Optional[str] = None
        self._current_agent_id: Optional[str] = None
        self._game_start_time: Optional[datetime] = None
        self._action_sequence: List[str] = []
        self._frame_history: List[List[List[int]]] = []

        # Frontier checkpoint tracking (per-level)
        self._level_action_sequence: List[str] = []
        self._unique_frame_hashes: Set[str] = set()
        self._current_level: int = 1

        # Movement observations for self-model
        self._movement_observations: List[Dict[str, Any]] = []

    # =========================================================================
    # Lazy Loading Properties
    # =========================================================================

    @property
    def cods(self) -> Any:
        """
        Get CODS engine (lazy loaded).

        DEPRECATED: Returns PrimitiveSuggester instead of CODSEngine.
        CODS has been deprecated - use primitive_suggester property instead.
        """
        if not self._cods_loaded:
            self._load_cods()
        return self._cods

    @property
    def primitive_suggester(self) -> Any:
        """Get primitive suggester (replaces CODS engine)."""
        if not self._cods_loaded:
            self._load_cods()
        return self._cods

    @property
    def replay(self) -> Any:
        """Get replay learning engine (lazy loaded)."""
        if not self._replay_loaded:
            self._load_replay()
        return self._replay

    @property
    def self_model(self) -> Any:
        """Get agent self-model (lazy loaded)."""
        if not self._self_model_loaded:
            self._load_self_model()
        return self._self_model

    @property
    def terminal_detector(self) -> Any:
        """Get terminal pattern detector (lazy loaded)."""
        if not self._terminal_loaded:
            self._load_terminal_detector()
        return self._terminal

    def _load_cods(self) -> None:
        """
        Lazy load primitive suggester (replaces deprecated CODS engine).

        Note: The 'cods' property name is kept for backward compatibility
        but now loads PrimitiveSuggester instead of CODSEngine.
        """
        try:
            from engines.social.primitive_suggester import PrimitiveSuggester
            self._cods = PrimitiveSuggester(self._db)
        except ImportError:
            self._cods = None
        except Exception as e:
            print(f"[WARN] Failed to load primitive suggester: {e}")
            self._cods = None
        self._cods_loaded = True

    def _load_replay(self) -> None:
        """Lazy load replay learning engine."""
        try:
            from engines.planning.replay_learning_engine import ReplayLearningEngine
            self._replay = ReplayLearningEngine(self._db)
        except ImportError:
            self._replay = None
        except Exception as e:
            print(f"[WARN] Failed to load replay engine: {e}")
            self._replay = None
        self._replay_loaded = True

    def _load_self_model(self) -> None:
        """Lazy load cognitive core."""
        try:
            from engines.self_model.cognitive_core import CognitiveCore
            self._self_model = CognitiveCore(self._db)
        except ImportError:
            self._self_model = None
        except Exception as e:
            print(f"[WARN] Failed to load self-model: {e}")
            self._self_model = None
        self._self_model_loaded = True

    def _load_terminal_detector(self) -> None:
        """Lazy load terminal pattern detector."""
        try:
            from engines.perception.terminal_pattern_detector import (
                TerminalPatternDetector,
            )
            self._terminal = TerminalPatternDetector(self._db)
        except ImportError:
            self._terminal = None
        except Exception as e:
            print(f"[WARN] Failed to load terminal detector: {e}")
            self._terminal = None
        self._terminal_loaded = True

    # =========================================================================
    # Game Lifecycle
    # =========================================================================

    def on_game_start(self, game_id: str, agent_id: Optional[str] = None) -> None:
        """
        Initialize learning systems for a new game.

        Args:
            game_id: The game identifier
            agent_id: Optional agent identifier
        """
        self._current_game_id = game_id
        self._current_agent_id = agent_id
        self._game_start_time = datetime.now()
        self._action_sequence.clear()
        self._frame_history.clear()
        self._movement_observations.clear()

        # Initialize self-model for this game
        if self.self_model:
            try:
                self.self_model.reset(game_id)
            except Exception as e:
                print(f"[WARN] Self-model reset failed: {e}")

    def on_game_end(self, result: GameResult) -> None:
        """
        Finalize learning from a completed game.

        Args:
            result: The game result
        """
        # Calculate duration
        if self._game_start_time:
            result.duration_seconds = (datetime.now() - self._game_start_time).total_seconds()

        # Store the action sequence
        result.action_sequence = self._action_sequence.copy()

        # Record game result to database
        self._record_game_result(result)

        # If this was a win, trigger learning
        if result.is_win or result.is_full_win:
            self._learn_from_win(result)

        # Synthesize movement observations into hypotheses
        if self._movement_observations:
            self._synthesize_control_hypotheses()

        # Reset session state
        self._current_game_id = None
        self._current_agent_id = None
        self._game_start_time = None

    # =========================================================================
    # Per-Action Updates
    # =========================================================================

    def update(
        self,
        state: LoopState,
        action: GameAction,
        outcome: ActionOutcome,
    ) -> None:
        """
        Update all learning systems with new experience.

        Called after each action is taken.

        Args:
            state: Game state before action
            action: The action that was taken
            outcome: The outcome of the action
        """
        # Track action sequence
        self._action_sequence.append(action.name)

        # Track frame for replay
        if outcome.frame_after:
            self._frame_history.append(outcome.frame_after)
            # Keep last 100 frames
            if len(self._frame_history) > 100:
                self._frame_history = self._frame_history[-100:]

        # Update self-model with movement observation
        if outcome.position_changed and outcome.position_delta:
            self._record_movement_observation(
                action=action,
                delta=outcome.position_delta,
                frame_before=outcome.frame_before,
                frame_after=outcome.frame_after,
            )

        # Track unique frames for frontier checkpoint (oscillation detection)
        if outcome.frame_after:
            frame_hash = self._compute_frame_hash(outcome.frame_after)
            self._unique_frame_hashes.add(frame_hash)

        # Track level transitions
        if state.current_level != self._current_level:
            # Reset per-level tracking on level change
            self._level_action_sequence.clear()
            self._unique_frame_hashes.clear()
            self._current_level = state.current_level

        # Track per-level action sequence
        self._level_action_sequence.append(action.name)

        # Record terminal pattern if death
        if outcome.is_death:
            self._record_terminal_pattern(
                action=action,
                frame=outcome.frame_before,
                state=state,
            )
            # Save frontier checkpoint for constructive pathfinding
            self._save_frontier_checkpoint(
                state=state,
                frame=outcome.frame_before,
            )

        # Update CODS with frame transition
        if outcome.frame_changed and self.cods:
            try:
                self.cods.observe_transition(
                    frame_before=outcome.frame_before,
                    frame_after=outcome.frame_after,
                    action=action.name,
                )
            except Exception:
                pass  # CODS update failed silently

    def _record_movement_observation(
        self,
        action: GameAction,
        delta: Tuple[int, int],
        frame_before: Optional[List[List[int]]],
        frame_after: Optional[List[List[int]]],
    ) -> None:
        """Record a movement observation for the self-model."""
        observation: Dict[str, Any] = {
            'action': action.name,
            'delta_x': delta[0],
            'delta_y': delta[1],
            'timestamp': datetime.now().isoformat(),
        }
        self._movement_observations.append(observation)

        # Also update self-model directly if available
        if self.self_model:
            try:
                self.self_model.record_movement_observation(
                    action=action.name,
                    delta=delta,
                    frame=frame_after,
                )
            except Exception:
                pass

    def _record_terminal_pattern(
        self,
        action: GameAction,
        frame: Optional[List[List[int]]],
        state: LoopState,
    ) -> None:
        """Record a terminal (death) pattern."""
        if self.terminal_detector:
            try:
                self.terminal_detector.record_death(
                    game_type=state.game_id[:4],
                    level=state.current_level,
                    action=action.name,
                    frame=frame,
                )
            except Exception:
                pass

        # Also record to database directly
        if self._db:
            try:
                self._db.execute("""
                    INSERT INTO terminal_patterns
                    (game_type, level, action, action_count, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    state.game_id[:4],
                    state.current_level,
                    action.name,
                    state.action_count,
                    datetime.now().isoformat(),
                ))
                self._db.commit()
            except Exception:
                pass

    # =========================================================================
    # Win Learning
    # =========================================================================

    def _learn_from_win(self, result: GameResult) -> None:
        """Learn from a winning game."""
        # Store winning sequence
        self._store_winning_sequence(result)

        # Trigger replay learning if available
        if self.replay:
            try:
                self.replay.learn_from_win(
                    game_id=result.game_id,
                    sequence=result.action_sequence,
                    frames=self._frame_history,
                )
            except Exception as e:
                print(f"[WARN] Replay learning failed: {e}")

    def _store_winning_sequence(self, result: GameResult) -> None:
        """Store a winning action sequence."""
        if not self._db:
            return

        try:
            import json

            # Check if it's a full win or partial
            if result.is_full_win:
                # Store in full game sequences table
                import uuid as _uuid
                seq_id = f"seq_{_uuid.uuid4().hex[:12]}"
                self._db.execute("""
                    INSERT INTO winning_sequences_full_game
                    (sequence_id, game_id, game_type, total_levels,
                     action_sequence, total_actions, total_score,
                     efficiency_score, agent_id, discovered_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    seq_id,
                    result.game_id,
                    result.game_id[:4],
                    result.levels_completed,
                    json.dumps(result.action_sequence),
                    result.total_actions,
                    getattr(result, 'score', 0.0),
                    getattr(result, 'score', 0.0) / max(1, result.total_actions),
                    result.agent_id,
                    datetime.now().isoformat(),
                ))
            else:
                # Store as partial sequence
                import uuid as _uuid
                seq_id = f"seq_{_uuid.uuid4().hex[:12]}"
                self._db.execute("""
                    INSERT INTO winning_sequences
                    (sequence_id, game_id, game_type, level_number,
                     action_sequence, total_actions, total_score,
                     efficiency_score, agent_id, session_id,
                     discovered_at, is_active, initial_frame, final_frame)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unknown', ?, 1, '[]', '[]')
                """, (
                    seq_id,
                    result.game_id,
                    result.game_id[:4],
                    result.levels_completed - 1,  # Last completed level
                    json.dumps(result.action_sequence),
                    result.total_actions,
                    getattr(result, 'score', 0.0),
                    getattr(result, 'score', 0.0) / max(1, result.total_actions),
                    result.agent_id,
                    datetime.now().isoformat(),
                ))

            self._db.commit()
        except Exception as e:
            print(f"[WARN] Failed to store winning sequence: {e}")

    # =========================================================================
    # Knowledge Synthesis
    # =========================================================================

    def _synthesize_control_hypotheses(self) -> None:
        """Synthesize movement observations into control hypotheses."""
        if not self._db or not self._movement_observations:
            return

        # Count action-movement correlations
        correlations: Dict[str, Dict[str, int]] = {}

        for obs in self._movement_observations:
            action = obs['action']
            dx, dy = obs['delta_x'], obs['delta_y']

            # Create direction key
            if dx > 0:
                direction = "RIGHT"
            elif dx < 0:
                direction = "LEFT"
            elif dy > 0:
                direction = "DOWN"
            elif dy < 0:
                direction = "UP"
            else:
                direction = "NONE"

            if action not in correlations:
                correlations[action] = {}

            correlations[action][direction] = correlations[action].get(direction, 0) + 1

        # Store hypotheses for actions with consistent correlations
        for action, directions in correlations.items():
            if not directions:
                continue

            # Find dominant direction
            total = sum(directions.values())
            dominant = max(directions.items(), key=lambda x: x[1])
            direction, count = dominant

            consistency = count / total if total > 0 else 0

            if consistency >= 0.7 and count >= 3:
                # Strong correlation - store as hypothesis
                try:
                    hypothesis_id = f"control_{action}_{direction}_{self._current_game_id}"

                    self._db.execute("""
                        INSERT OR REPLACE INTO network_object_control_hypotheses
                        (hypothesis_id, game_type, action_mapping, direction,
                         validation_attempts, reliability_score, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    """, (
                        hypothesis_id,
                        self._current_game_id[:4] if self._current_game_id else "unknown",
                        action,
                        direction,
                        count,
                        consistency,
                        datetime.now().isoformat(),
                    ))
                    self._db.commit()
                except Exception:
                    pass

    # =========================================================================
    # Database Recording
    # =========================================================================

    def _record_game_result(self, result: GameResult) -> None:
        """Record game result to database."""
        if not self._db:
            return

        try:
            self._db.execute("""
                INSERT INTO game_results
                (game_type, final_score, levels_completed, actions_taken,
                 agent_id, is_win, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.game_id[:4],
                result.final_score,
                result.levels_completed,
                result.total_actions,
                result.agent_id,
                1 if result.is_win else 0,
                datetime.now().isoformat(),
            ))
            self._db.commit()
        except Exception as e:
            print(f"[WARN] Failed to record game result: {e}")

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_control_hypotheses(
        self,
        game_type: str,
        min_reliability: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Get control hypotheses for a game type.

        Args:
            game_type: The game type (e.g., "ls20")
            min_reliability: Minimum reliability score

        Returns:
            List of hypothesis dictionaries
        """
        if not self._db:
            return []

        try:
            cursor = self._db.execute("""
                SELECT hypothesis_id, action_mapping, direction, reliability_score
                FROM network_object_control_hypotheses
                WHERE game_type = ? AND is_active = 1 AND reliability_score >= ?
                ORDER BY reliability_score DESC
            """, (game_type, min_reliability))

            results: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                results.append({
                    'hypothesis_id': row[0],
                    'action': row[1],
                    'direction': row[2],
                    'reliability': row[3],
                })

            return results
        except Exception:
            return []

    def get_winning_sequence(
        self,
        game_type: str,
        level: Optional[int] = None,
    ) -> Optional[List[str]]:
        """
        Get a winning sequence for a game/level.

        Args:
            game_type: The game type
            level: Optional specific level (None = full game sequence)

        Returns:
            List of action names, or None if no sequence found
        """
        if not self._db:
            return None

        try:
            import json

            if level is None:
                # Full game sequence
                cursor = self._db.execute("""
                    SELECT action_sequence FROM winning_sequences_full_game
                    WHERE game_type = ? AND is_active = 1
                    ORDER BY total_actions ASC
                    LIMIT 1
                """, (game_type,))
            else:
                # Level sequence
                cursor = self._db.execute("""
                    SELECT action_sequence FROM winning_sequences
                    WHERE game_type = ? AND level_number = ? AND is_active = 1
                    ORDER BY total_actions ASC
                    LIMIT 1
                """, (game_type, level))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])

            return None
        except Exception:
            return None

    # =========================================================================
    # Frontier Checkpoint Methods (Constructive Pathfinding)
    # =========================================================================

    def _compute_frame_hash(self, frame: List[List[int]]) -> str:
        """Compute a hash of a frame for deduplication."""
        import hashlib
        frame_str = str(frame)
        return hashlib.md5(frame_str.encode()).hexdigest()[:16]

    def _compute_survival_score(
        self,
        unique_frames: int,
        action_count: int,
    ) -> float:
        """
        Compute game-agnostic progress metric.

        Higher = better progress. Penalizes oscillation implicitly
        (more actions with fewer unique frames = lower score).

        Formula: (unique_frames * 10) + action_count
        """
        return (unique_frames * 10) + action_count

    def _is_frontier_level(self, game_type: str, level: int) -> bool:
        """Check if this level has no winning sequence (is frontier)."""
        if not self._db:
            return True  # Assume frontier if no DB

        try:
            cursor = self._db.execute("""
                SELECT 1 FROM winning_sequences
                WHERE game_type = ? AND level = ? AND is_active = 1
                LIMIT 1
            """, (game_type, level))
            return cursor.fetchone() is None
        except Exception:
            return True  # Assume frontier on error

    def _save_frontier_checkpoint(
        self,
        state: LoopState,
        frame: Optional[List[List[int]]],
    ) -> None:
        """
        Save frontier checkpoint on death for constructive pathfinding.

        Only saves if:
        - Level is frontier (no winning sequence)
        - At least 3 actions taken (instant deaths not useful)
        - Not pure oscillation (unique_frames > actions/3)

        See: architecture/frontier_checkpoint_system.md
        """
        if not self._db:
            return

        game_type = state.game_id[:4]
        level = state.current_level
        action_count = len(self._level_action_sequence)
        unique_frames = len(self._unique_frame_hashes)

        # Guard: Minimum actions threshold
        if action_count < 3:
            return

        # Guard: Oscillation filter (pure loops not useful)
        if unique_frames < action_count // 3:
            return

        # Guard: Only save for frontier levels
        if not self._is_frontier_level(game_type, level):
            return

        # Compute frame hash for deduplication
        terminal_frame_hash = self._compute_frame_hash(frame) if frame else "unknown"

        # Compute survival score
        survival_score = self._compute_survival_score(unique_frames, action_count)

        try:
            import json
            action_sequence_json = json.dumps(self._level_action_sequence)

            # UPSERT: Keep best path to each unique terminal state
            self._db.execute("""
                INSERT INTO frontier_checkpoints
                (game_type, level_number, terminal_frame_hash, action_sequence,
                 actions_count, unique_frames_seen, survival_score, terminal_reason,
                 times_used, times_extended, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'death', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (game_type, level_number, terminal_frame_hash) DO UPDATE SET
                    action_sequence = CASE
                        WHEN excluded.survival_score > frontier_checkpoints.survival_score
                        THEN excluded.action_sequence
                        ELSE frontier_checkpoints.action_sequence
                    END,
                    actions_count = CASE
                        WHEN excluded.survival_score > frontier_checkpoints.survival_score
                        THEN excluded.actions_count
                        ELSE frontier_checkpoints.actions_count
                    END,
                    survival_score = MAX(frontier_checkpoints.survival_score, excluded.survival_score),
                    unique_frames_seen = MAX(frontier_checkpoints.unique_frames_seen, excluded.unique_frames_seen),
                    times_extended = frontier_checkpoints.times_extended + 1,
                    last_used_at = CURRENT_TIMESTAMP
            """, (
                game_type,
                level,
                terminal_frame_hash,
                action_sequence_json,
                action_count,
                unique_frames,
                survival_score,
            ))
        except Exception:  # noqa: checkpoint saving is optimization, not critical
            pass


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    print("Learning Systems - Quick Test")
    print("=" * 50)

    # Create learning systems (no DB)
    learning = LearningSystems()

    # Test game lifecycle
    print("\nTest 1: Game lifecycle")
    learning.on_game_start("ls20", "test-agent")
    print(f"  Current game: {learning._current_game_id}")  # pyright: ignore[reportPrivateUsage]
    print(f"  Current agent: {learning._current_agent_id}")  # pyright: ignore[reportPrivateUsage]

    # Test update
    print("\nTest 2: Action update")
    from outcome_processor import ActionOutcome, LoopState

    state = LoopState(
        game_id="ls20",
        current_level=0,
        action_count=5,
        score=0.0,
        state=GameState.NOT_FINISHED,
        frame=[[0, 1, 0]],
        levels_completed=0,
        win_levels=5,
    )

    outcome = ActionOutcome(
        action=GameAction.ACTION1,
        action_name="ACTION1",
        position_changed=True,
        position_delta=(1, 0),
        frame_before=[[0, 1, 0]],
        frame_after=[[0, 0, 1]],
    )

    learning.update(state, GameAction.ACTION1, outcome)
    print(f"  Actions tracked: {len(learning._action_sequence)}")  # pyright: ignore[reportPrivateUsage]
    print(f"  Movement observations: {len(learning._movement_observations)}")  # pyright: ignore[reportPrivateUsage]

    # Test game end
    print("\nTest 3: Game end")
    result = GameResult(
        game_id="ls20",
        final_score=0.6,
        levels_completed=3,
        win_levels=5,
        total_actions=100,
        is_win=False,
        is_full_win=False,
        action_sequence=learning._action_sequence,  # pyright: ignore[reportPrivateUsage]
        agent_id="test-agent",
    )

    learning.on_game_end(result)
    print(f"  Win rate: {result.win_rate:.1%}")
    print(f"  Duration: {result.duration_seconds:.2f}s")

    # Test lazy loading flags
    print("\nTest 4: Lazy loading")
    print(f"  CODS loaded: {learning._cods_loaded}")  # pyright: ignore[reportPrivateUsage]
    print(f"  Replay loaded: {learning._replay_loaded}")  # pyright: ignore[reportPrivateUsage]
    print(f"  Self-model loaded: {learning._self_model_loaded}")  # pyright: ignore[reportPrivateUsage]
    print(f"  Terminal loaded: {learning._terminal_loaded}")  # pyright: ignore[reportPrivateUsage]

    print("\n[OK] All tests passed!")
