#!/usr/bin/env python3
"""
GamePlayer — plays a single game for a single agent.

Extracted from EvolutionRunner.play_game (Phase 4.1 decomposition).
Receives ALL dependencies via constructor injection.
Does NOT create its own DB connections or engine instances.
"""

import os
import sys

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import hashlib
import json
import random
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from arcengine import GameAction, GameState

from database_interface import DatabaseInterface

# Perception imports (always available)
from engines.perception.property_extractor import properties_to_json
from event_bus import EventBus, EventType, make_event
from evolution_types import AgentState, GameResult
from pipeline_assertions import PipelineAssertions


class GamePlayer:
    """Plays a single game for a single agent.

    All engine references are injected via the constructor.
    Game-scoped mutable state (_prev_frame, _prev_properties,
    _current_session_id) lives here and is reset per play_game call.
    """

    def __init__(
        self,
        db: DatabaseInterface,
        arcade: Any,          # arc_agi.Arcade
        context_builder: Any, # ContextBuilder
        decision_system: Any, # DecisionRungSystem
        event_bus: EventBus,
        pipe: PipelineAssertions,
        player_localizer: Any,     # PlayerLocalizer
        property_extractor: Any,   # PropertyExtractor
        mastery_system: Any = None,
        concept_discovery_engine: Any = None,
        op_mode: Any = None,       # OperationMode enum
        max_actions: int = 500,
        verbose: bool = False,
        use_cognitive_router: bool = False,
    ):
        self.db = db
        self.arcade = arcade
        self.context_builder = context_builder
        self.decision_system = decision_system
        self.event_bus = event_bus
        self.pipe = pipe
        self.player_localizer = player_localizer
        self.property_extractor = property_extractor
        self.mastery_system = mastery_system
        self.concept_discovery_engine = concept_discovery_engine
        self.op_mode = op_mode
        self.max_actions = max_actions
        self.verbose = verbose
        self._use_cognitive_router = use_cognitive_router

        # Game-scoped state (reset at the start of each play_game call)
        self._current_session_id: Optional[str] = None
        self._prev_frame: Optional[np.ndarray] = None
        self._prev_properties: Optional[dict] = None

    @property
    def last_session_id(self) -> Optional[str]:
        """Session ID from the most recent play_game call."""
        return self._current_session_id

    # ------------------------------------------------------------------
    # Standalone entry point (for core_gameplay.py convenience wrapper)
    # ------------------------------------------------------------------

    def play_game_standalone(
        self,
        game_id: str,
        agent_id: str = "standalone-agent",
        generation: int = 0,
    ) -> "GameResult":
        """Play a game without evolution infrastructure.

        Convenience method that wraps ``play_game()`` with a minimal
        ``AgentState`` and a no-op ``is_running_fn``.  This lets
        ``core_gameplay.GameplayEngine`` use the same game-playing
        code path as the production evolution runner.

        Args:
            game_id: ARC game identifier (e.g., "ls20").
            agent_id: Agent identifier string.
            generation: Generation number (default 0 for standalone).

        Returns:
            GameResult with score, levels, actions, and sequence.
        """
        agent = AgentState(
            agent_id=agent_id,
            generation=generation,
        )
        return self.play_game(
            agent=agent,
            game_id=game_id,
            current_generation=generation,
            is_running_fn=lambda: True,
        )

    # ------------------------------------------------------------------
    # Scorecard helpers (only used by play_game)
    # ------------------------------------------------------------------

    def _create_scorecard_tags(self, agent: AgentState, game_id: str) -> List[str]:
        """Generate scorecard tags."""
        from arc_agi import OperationMode

        if self.op_mode == OperationMode.ONLINE:
            mode_tag = "online"
        elif self.op_mode == OperationMode.OFFLINE:
            mode_tag = "offline"
        else:
            mode_tag = "normal"

        game_type = game_id[:4] if len(game_id) >= 4 else game_id

        role = "generalist"
        try:
            result = self.db.execute_query(
                "SELECT specialization FROM agents WHERE agent_id = ?",
                (agent.agent_id,)
            )
            if result:
                role = result[0].get('specialization', 'generalist') or 'generalist'
        except Exception:
            pass

        return [
            "branch_Ouroboros-v3",
            mode_tag,
            f"game_{game_type}",
            "agent",
            f"agent_{agent.agent_id.replace('agent_', '')}",
            f"mode_{role}",
            f"gen_{agent.generation}",
        ]

    def _get_or_create_scorecard(
        self, agent: AgentState, game_id: str
    ) -> Optional[str]:
        """Get or create a scorecard with proper tags."""
        try:
            tags = self._create_scorecard_tags(agent, game_id)
            scorecard_id = self.arcade.create_scorecard(
                source_url="https://github.com/BitterTruth-AI/Ouroboros",
                tags=tags
            )
            if self.verbose:
                print(f"    [SCORECARD] Created: {scorecard_id}")
                print(f"    [TAGS] {', '.join(tags)}")
            return scorecard_id
        except Exception as e:
            if self.verbose:
                print(f"    [WARN] Failed to create scorecard: {e}")
            return None

    # ------------------------------------------------------------------
    # Reasoning payload for API recordings
    # ------------------------------------------------------------------

    def _build_reasoning_payload(
        self,
        action: Any,
        reason: str,
        agent: Any,
        game_id: str,
        actions_taken: int,
        context: dict,
    ) -> Dict[str, Any]:
        """Build reasoning payload to send with each API step.

        This data is included in ARC API recordings so our decision
        logic is visible when reviewing replays.

        Args:
            action: The chosen GameAction.
            reason: Decision reason string from the rung system.
            agent: The agent playing (has agent_id).
            game_id: Current game identifier.
            actions_taken: Number of actions taken so far.
            context: The full decision context dict.

        Returns:
            Dict with reasoning metadata for the API.
        """
        action_name = action.name if hasattr(action, 'name') else str(action)
        payload: Dict[str, Any] = {
            "action": action_name,
            "reason": (reason[:200] if reason else "unknown"),
            "agent_id": getattr(agent, 'agent_id', 'unknown'),
            "game_id": game_id,
            "step": actions_taken,
            "level": context.get('current_level', 0),
            "score": context.get('score', 0.0),
        }

        # Add rung / decision metadata if available
        if hasattr(self.decision_system, 'last_decision_metadata'):
            metadata = self.decision_system.last_decision_metadata or {}
            rung = metadata.get("rung_name") or metadata.get("rung")
            if rung:
                payload["rung"] = str(rung)[:100]
            confidence = metadata.get("confidence")
            if confidence is not None:
                payload["confidence"] = float(confidence)

        # Replay mode flag
        if context.get('is_replay_mode'):
            payload["replay_mode"] = True
            payload["sequence_position"] = context.get('sequence_position', 0)

        return payload

    # ------------------------------------------------------------------
    # Frame / observation utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_frame_hash(obs: Any) -> str:
        """Compute hash of frame state for topology matching."""
        if obs is None:
            return "null_frame"
        try:
            frame_data = None
            for attr in ['frame', 'state', 'grid', 'observation']:
                if hasattr(obs, attr):
                    frame_data = getattr(obs, attr)
                    break
            if frame_data is None:
                frame_data = str(obs)
            if hasattr(frame_data, 'tolist'):
                frame_str = str(frame_data.tolist())
            else:
                frame_str = str(frame_data)
            return hashlib.md5(frame_str.encode()).hexdigest()[:16]
        except Exception:
            return "hash_error"

    @staticmethod
    def _get_frame_array(obs: Any) -> Optional[np.ndarray]:
        """Extract frame as numpy array from observation."""
        if obs is None:
            return None
        try:
            for attr in ['frame', 'grid', 'observation']:
                if hasattr(obs, attr):
                    data = getattr(obs, attr)
                    if isinstance(data, np.ndarray):
                        return data
                    if isinstance(data, list):
                        return np.array(data, dtype=np.uint8)
                    if hasattr(data, 'tolist'):
                        return np.array(data)
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Trace / symbolic recording (per-action data capture)
    # ------------------------------------------------------------------

    def _record_action_trace(
        self,
        game_id: str,
        action_num: int,
        obs_before: Any,
        obs_after: Any,
        score_before: float,
        score_after: float,
        level_before: int,
        level_after: int,
        is_game_over: bool,
        coordinates: Optional[Dict] = None,
    ) -> None:
        """Record action trace with frame hash and score change."""
        try:
            frame_hash_before = self._compute_frame_hash(obs_before)
            frame_hash_after = self._compute_frame_hash(obs_after)
            frame_changed = frame_hash_before != frame_hash_after

            frame_before_str = None
            frame_after_str = None
            try:
                if obs_before and hasattr(obs_before, 'frame'):
                    frame_before_str = str(obs_before.frame.tolist() if hasattr(obs_before.frame, 'tolist') else obs_before.frame)
                if obs_after and hasattr(obs_after, 'frame'):
                    frame_after_str = str(obs_after.frame.tolist() if hasattr(obs_after.frame, 'tolist') else obs_after.frame)
            except Exception:
                pass

            coords_json = None
            if coordinates:
                coords_json = json.dumps(coordinates)

            self.db.execute_query("""
                INSERT INTO action_traces (
                    session_id, game_id, action_number, coordinates, timestamp,
                    frame_before, frame_after, frame_changed,
                    score_before, score_after, score_change,
                    level_number, resulted_in_game_over,
                    frame_hash, created_at
                ) VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                self._current_session_id,
                game_id,
                action_num,
                coords_json,
                frame_before_str,
                frame_after_str,
                1 if frame_changed else 0,
                score_before,
                score_after,
                score_after - score_before,
                level_after,
                1 if is_game_over else 0,
                frame_hash_before,
            ))
        except Exception as e:
            if self.verbose:
                print(f"    [TRACE-ERR] {e}")

    def _record_player_state(
        self,
        game_id: str,
        action_num: int,
        action_taken: str,
        obs_before: Any,
        obs_after: Any,
        action_result: str,
        level_number: int,
    ) -> Optional[dict]:
        """Record player state for symbolic reasoning (Phase 0-1)."""
        try:
            frame_before = self._get_frame_array(obs_before)
            frame_after = self._get_frame_array(obs_after)

            if frame_before is None or frame_after is None:
                return None

            localization = self.player_localizer.localize(
                frame_before, frame_after, action_taken
            )

            player_region = None
            player_bbox = localization.get('region')
            confidence = localization.get('confidence', 0.0)

            current_properties = None
            if confidence >= 0.5 and player_bbox is not None:
                player_region = self.player_localizer.get_player_region(frame_after)
                if player_region is not None:
                    current_properties = self.property_extractor.extract_properties(player_region)

            property_changes = {}
            if self._prev_properties and current_properties:
                property_changes = self.property_extractor.properties_changed(
                    self._prev_properties, current_properties
                )
                if property_changes:
                    self._record_property_transformations(
                        game_id=game_id,
                        level_number=level_number,
                        player_bbox=player_bbox,
                        property_changes=property_changes
                    )
                    if self.verbose:
                        for prop, change in property_changes.items():
                            print(f"    [PROP] {prop}: {change['from']} -> {change['to']}")

            if action_result in ('success', 'win'):
                self._record_goal_outcome(
                    game_id=game_id,
                    level_number=level_number,
                    player_bbox=player_bbox,
                    properties=current_properties,
                    succeeded=True
                )

            props_json = properties_to_json(current_properties)

            self.db.execute_query("""
                INSERT INTO player_state_history (
                    session_id, game_id, level_number, action_number,
                    player_region_x, player_region_y, player_region_w, player_region_h,
                    localization_confidence, properties_json,
                    dominant_color, shape_phash, orientation,
                    action_taken, action_resulted_in, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                self._current_session_id,
                game_id,
                level_number,
                action_num,
                player_bbox[0] if player_bbox else None,
                player_bbox[1] if player_bbox else None,
                player_bbox[2] if player_bbox else None,
                player_bbox[3] if player_bbox else None,
                confidence,
                props_json,
                current_properties.get('dominant_color') if current_properties else None,
                current_properties.get('shape_signature') if current_properties else None,
                current_properties.get('orientation') if current_properties else None,
                action_taken,
                action_result,
            ))

            self._prev_frame = frame_after
            self._prev_properties = current_properties

            return current_properties

        except Exception as e:
            if self.verbose:
                print(f"    [STATE-ERR] {e}")
            return None

    def _record_property_transformations(
        self,
        game_id: str,
        level_number: int,
        player_bbox: Optional[tuple],
        property_changes: dict
    ) -> None:
        """Record property transformations to database (Phase 2)."""
        try:
            for prop_name, change in property_changes.items():
                existing = self.db.execute_query("""
                    SELECT id, times_observed FROM property_transformations
                    WHERE game_id = ? AND level_number = ?
                      AND object_position_x = ? AND object_position_y = ?
                      AND property_changed = ?
                      AND value_before = ? AND value_after = ?
                """, (
                    game_id, level_number,
                    player_bbox[0] if player_bbox else None,
                    player_bbox[1] if player_bbox else None,
                    prop_name,
                    str(change.get('from')),
                    str(change.get('to')),
                ))

                row = existing[0] if existing else None

                if row:
                    new_times = row['times_observed'] + 1
                    new_confidence = min(0.99, 0.5 + (new_times * 0.1))
                    self.db.execute_query("""
                        UPDATE property_transformations SET
                            times_observed = ?,
                            confidence = ?,
                            last_observed = datetime('now')
                        WHERE id = ?
                    """, (new_times, new_confidence, row['id']))
                else:
                    self.db.execute_query("""
                        INSERT INTO property_transformations (
                            game_id, level_number,
                            object_position_x, object_position_y,
                            property_changed, value_before, value_after,
                            times_observed, confidence, created_at, last_observed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.5, datetime('now'), datetime('now'))
                    """, (
                        game_id,
                        level_number,
                        player_bbox[0] if player_bbox else None,
                        player_bbox[1] if player_bbox else None,
                        prop_name,
                        str(change.get('from')),
                        str(change.get('to')),
                    ))
        except Exception as e:
            if self.verbose:
                print(f"    [TRANSFORM-ERR] {e}")

    def _record_goal_outcome(
        self,
        game_id: str,
        level_number: int,
        player_bbox: Optional[tuple],
        properties: Optional[dict],
        succeeded: bool
    ) -> None:
        """Record goal outcome to build requirement knowledge (Phase 3)."""
        if properties is None:
            return

        try:
            goal_index = 0

            existing = self.db.execute_query("""
                SELECT id, times_succeeded, times_failed
                FROM goal_requirements
                WHERE game_id = ? AND level_number = ? AND goal_index = ?
            """, (game_id, level_number, goal_index))

            row = existing[0] if existing else None

            if row:
                if succeeded:
                    new_succeeded = row['times_succeeded'] + 1
                    new_failed = row['times_failed']
                else:
                    new_succeeded = row['times_succeeded']
                    new_failed = row['times_failed'] + 1

                total = new_succeeded + new_failed
                new_confidence = new_succeeded / total if total > 0 else 0.0

                self.db.execute_query("""
                    UPDATE goal_requirements SET
                        times_succeeded = ?,
                        times_failed = ?,
                        confidence = ?,
                        required_dominant_color = ?,
                        required_shape_phash = ?,
                        required_orientation = ?,
                        last_observed = datetime('now')
                    WHERE id = ?
                """, (
                    new_succeeded,
                    new_failed,
                    new_confidence,
                    str(properties.get('dominant_color')) if succeeded else None,
                    properties.get('shape_signature') if succeeded else None,
                    properties.get('orientation') if succeeded else None,
                    row['id'],
                ))
            else:
                times_succeeded = 1 if succeeded else 0
                times_failed = 0 if succeeded else 1
                confidence = 1.0 if succeeded else 0.0

                self.db.execute_query("""
                    INSERT INTO goal_requirements (
                        game_id, level_number, goal_index,
                        goal_position_x, goal_position_y,
                        required_dominant_color, required_shape_phash, required_orientation,
                        times_succeeded, times_failed, confidence,
                        created_at, last_observed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    game_id,
                    level_number,
                    goal_index,
                    player_bbox[0] if player_bbox else None,
                    player_bbox[1] if player_bbox else None,
                    str(properties.get('dominant_color')) if succeeded else None,
                    properties.get('shape_signature') if succeeded else None,
                    properties.get('orientation') if succeeded else None,
                    times_succeeded,
                    times_failed,
                    confidence,
                ))
        except Exception as e:
            if self.verbose:
                print(f"    [GOAL-ERR] {e}")

    # ------------------------------------------------------------------
    # MAIN: play_game
    # ------------------------------------------------------------------

    def play_game(
        self,
        agent: AgentState,
        game_id: str,
        current_generation: int,
        is_running_fn: Callable[[], bool],
    ) -> GameResult:
        """Play a single game with an agent.

        Uses the decision system to select actions.
        Creates a scorecard with proper tags for tracking.

        Args:
            agent: The agent playing this game.
            game_id: ARC game identifier.
            current_generation: Current generation number.
            is_running_fn: Callable returning False when shutdown requested.

        Returns:
            GameResult with score, levels, actions, and sequence.
        """
        scorecard_id = self._get_or_create_scorecard(agent, game_id)

        env = None
        try:
            env = self.arcade.make(game_id, scorecard_id=scorecard_id)
        except Exception as e:
            print(f"  [ERROR] Failed to create env for {game_id}: {e}")
            return GameResult(
                game_id=game_id, agent_id=agent.agent_id, score=0.0,
                levels_completed=0, total_levels=1, is_win=False, actions_taken=0,
            )

        if env is None:
            print(f"  [ERROR] env is None for {game_id}")
            return GameResult(
                game_id=game_id, agent_id=agent.agent_id, score=0.0,
                levels_completed=0, total_levels=1, is_win=False, actions_taken=0,
            )

        actions_taken = 0
        action_sequence: List[str] = []
        last_obs = None
        prev_levels = 0
        prev_score = 0.0

        # State tracking for decision context
        last_action_str = ''
        last_frame_changed = True
        failed_actions: set = set()
        recent_actions: list = []
        last_score_delta = 0.0
        last_outcome_type = 'neutral'

        # Reset context builder for new game
        self.context_builder.reset(game_id)
        has_full_win = False
        active_sequence: list = []
        sequence_position = 0
        is_replay_mode = False
        stuck_count = 0
        tried_colors: set = set()
        level_start_action_index = 0
        current_frame_hash = ''
        has_level_sequence = False

        # Check for existing winning sequence (replay path)
        try:
            result = self.db.execute_query("""
                SELECT action_sequence FROM winning_sequences_full_game
                WHERE game_id = ? AND is_active = 1
                ORDER BY efficiency_score DESC LIMIT 1
            """, (game_id,))
            if result:
                has_full_win = True
                seq_data = result[0][0]
                if seq_data:
                    if isinstance(seq_data, str):
                        active_sequence = json.loads(seq_data)
                    else:
                        active_sequence = list(seq_data)
                    is_replay_mode = True
                    try:
                        self.db.execute_query("""
                            UPDATE winning_sequences_full_game
                            SET times_referenced = COALESCE(times_referenced, 0) + 1,
                                last_referenced = datetime('now')
                            WHERE game_id = ? AND is_active = 1
                        """, (game_id,))
                    except Exception:
                        pass
        except Exception:
            has_full_win = False

        # Load per-level winning sequence for level 1
        game_type = game_id[:4] if len(game_id) >= 4 else game_id
        if not active_sequence:
            try:
                level_seq = self.db.execute_query("""
                    SELECT action_sequence, sequence_id FROM winning_sequences
                    WHERE game_type = ? AND level_number = 1 AND is_active = 1
                    ORDER BY efficiency_score DESC LIMIT 1
                """, (game_type,))
                if level_seq and level_seq[0].get('action_sequence'):
                    seq_data = level_seq[0]['action_sequence']
                    active_sequence = json.loads(seq_data) if isinstance(seq_data, str) else list(seq_data)
                    is_replay_mode = True
                    has_level_sequence = True
                    try:
                        self.db.execute_query("""
                            UPDATE winning_sequences
                            SET times_referenced = COALESCE(times_referenced, 0) + 1,
                                last_referenced = datetime('now')
                            WHERE game_type = ? AND level_number = 1 AND is_active = 1
                        """, (game_type,))
                    except Exception:
                        pass
                    if self.verbose:
                        print(f"    [SEQ-LOAD] Level 1 sequence loaded: {level_seq[0].get('sequence_id', '?')[:16]} ({len(active_sequence)} actions)")
            except Exception:
                pass

        # Phase 1.1: Mastery-gated replay
        mastery_tier = 'novice'
        ablation_active = False
        ablation_skip_indices: set = set()
        ablation_skip_rate = 0.0
        current_sequence_id = ''
        if self.mastery_system and active_sequence and is_replay_mode:
            level_for_mastery = 1
            try:
                allowed, reason, mastery_status = self.mastery_system.should_allow_replay(
                    game_type, level_for_mastery
                )
                mastery_tier = mastery_status.tier
                if not allowed:
                    active_sequence = []
                    sequence_position = 0
                    is_replay_mode = False
                    has_level_sequence = False
                    if self.verbose:
                        print(f"    [MASTERY] Replay DENIED: {reason}")
                else:
                    skip_min, skip_max = self.mastery_system.get_ablation_skip_rate(mastery_tier)
                    if skip_max > 0 and len(active_sequence) > 3:
                        ablation_skip_rate = random.uniform(skip_min, skip_max)
                        n_skip = max(1, int(len(active_sequence) * ablation_skip_rate))
                        skippable = list(range(len(active_sequence) - 1))
                        if skippable:
                            ablation_skip_indices = set(random.sample(
                                skippable, min(n_skip, len(skippable))
                            ))
                            ablation_active = True
                    if self.verbose:
                        abl_str = f" (ablation: skip {len(ablation_skip_indices)}/{len(active_sequence)})" if ablation_active else ""
                        print(f"    [MASTERY] Replay ALLOWED: {reason}{abl_str}")
            except Exception as e:
                if self.verbose:
                    print(f"    [MASTERY-ERR] Check failed, allowing replay: {e}")

        # Reset symbolic reasoning state
        self.player_localizer.reset()
        self._prev_frame = None
        self._prev_properties = None

        # Reset visual analyzer
        try:
            va = None
            if hasattr(self.decision_system, '_engine_registry'):
                registry = self.decision_system._engine_registry
                if registry:
                    va = getattr(registry, 'visual_analyzer', None)
            if va:
                va.reset_clicked_coordinates()
                if hasattr(va, 'clear_priority_on_new_game'):
                    va.clear_priority_on_new_game()
                try:
                    agent_row = self.db.execute_query(
                        "SELECT specialization FROM agents WHERE agent_id = ?",
                        (agent.agent_id,)
                    )
                    agent_mode = agent_row[0]['specialization'] if agent_row and agent_row[0].get('specialization') else 'generalist'
                except Exception:
                    agent_mode = 'generalist'
                if hasattr(va, 'set_agent_mode'):
                    va.set_agent_mode(agent_mode)
        except Exception:
            pass

        # Create session for action traces (FK parent row)
        self._current_session_id = f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        try:
            self.db.execute_query("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status, total_actions
                ) VALUES (?, ?, datetime('now'), 'evolution', 'in_progress', 0)
            """, (self._current_session_id, game_id))
        except Exception as e:
            print(f"    [WARN] Failed to create training session: {e}")

        if not self.pipe.assert_session_exists(self._current_session_id):
            fallback_id = f"session_fallback_{uuid.uuid4().hex[:8]}"
            try:
                self.db.execute_query("""
                    INSERT INTO training_sessions (
                        session_id, game_id, start_time, mode, status, total_actions
                    ) VALUES (?, ?, datetime('now'), 'evolution', 'in_progress', 0)
                """, (fallback_id, game_id))
                self._current_session_id = fallback_id
                print(f"    [PIPE-RECOVER] Created fallback session {fallback_id[:16]}..")
            except Exception:
                pass

        # Initial observation
        initial_obs = env.observation_space
        available_actions = getattr(initial_obs, 'available_actions', [1, 2, 3, 4])
        win_levels = getattr(initial_obs, 'win_levels', 7)

        if self.verbose:
            print(f"    Game: {game_id} | Available actions: {available_actions} | Win at: {win_levels} levels")

        # ========== GAME LOOP ==========
        while actions_taken < self.max_actions:
            if not is_running_fn():
                break

            obs = last_obs if last_obs else initial_obs
            current_available = getattr(obs, 'available_actions', None) or available_actions

            # Build context via unified ContextBuilder
            context = self.context_builder.build_from_runner_state(
                game_id=game_id, obs=obs, agent_id=agent.agent_id,
                actions_taken=actions_taken, max_actions=self.max_actions,
                available_actions=current_available, win_levels=win_levels,
                last_action=last_action_str, recent_actions=recent_actions,
                last_frame_changed=last_frame_changed, failed_actions=failed_actions,
                score=getattr(obs, 'score', 0.0), score_delta=last_score_delta,
                last_outcome=last_outcome_type, has_full_win=has_full_win,
                active_sequence=active_sequence, sequence_position=sequence_position,
                is_replay_mode=is_replay_mode, has_level_sequence=has_level_sequence,
                stuck_count=stuck_count, tried_colors=tried_colors,
                frame_hash=current_frame_hash,
                level_start_action_index=level_start_action_index,
                session_id=self._current_session_id, scorecard_id=scorecard_id,
            ).to_dict()
            context['frame_changed'] = last_frame_changed
            context['actions_taken'] = actions_taken

            # Get action from decision system
            action_data = None
            try:
                result = self.decision_system.decide(obs, context)
                if isinstance(result, tuple):
                    action_str, reason = result
                    if isinstance(action_str, str) and action_str.startswith('ACTION'):
                        action_num = int(action_str.replace('ACTION', ''))
                    else:
                        action_num = random.choice(current_available)

                    if action_num == 6 and hasattr(self.decision_system, 'last_decision_metadata'):
                        metadata = self.decision_system.last_decision_metadata or {}
                        if 'pixel_position' in metadata:
                            px, py = metadata['pixel_position']
                            action_data = {'x': int(px), 'y': int(py)}
                        elif 'target' in metadata:
                            target = metadata['target']
                            action_data = {'x': int(target.get('x', 32)), 'y': int(target.get('y', 32))}
                        elif 'grid_target' in metadata:
                            grid_target = metadata['grid_target']
                            action_data = {'x': int(grid_target.get('x', 32)), 'y': int(grid_target.get('y', 32))}
                        elif 'x' in metadata and 'y' in metadata:
                            action_data = {'x': int(metadata['x']), 'y': int(metadata['y'])}
                        else:
                            action_data = {'x': 32, 'y': 32}
                            if self.verbose:
                                print(f"    [WARN] ACTION6 without coordinates, using default (32, 32)")
                elif hasattr(result, 'action'):
                    action_num = result.action
                else:
                    action_num = random.choice(current_available)

                if hasattr(action_num, 'value'):
                    action_num = action_num.value

                if action_num not in current_available:
                    if self.verbose:
                        rung_info = reason if 'reason' in dir() and reason else 'unknown'
                        print(f"    [WARN] Action {action_num} not in {current_available}, picking random | from: {rung_info[:50]}")
                    action_num = random.choice(current_available)

                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)
            except Exception as e:
                if self.verbose:
                    print(f"    [WARN] Decision failed: {e}, picking random")
                action_num = random.choice(available_actions)
                action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)

            # Take action with retry logic
            obs = None
            max_step_retries = 3
            step_retry_delay = 2.0

            # Build reasoning payload for API recording
            reasoning_payload = self._build_reasoning_payload(
                action=action,
                reason=reason if 'reason' in dir() and reason else 'unknown',
                agent=agent,
                game_id=game_id,
                actions_taken=actions_taken,
                context=context,
            )

            for step_attempt in range(max_step_retries):
                try:
                    obs_before = last_obs if last_obs else initial_obs
                    obs = env.step(action, data=action_data, reasoning=reasoning_payload)
                    if obs is None:
                        if step_attempt < max_step_retries - 1:
                            wait_time = step_retry_delay * (2 ** step_attempt)
                            print(f"    [API] Step returned None for {action.name}, retry {step_attempt + 1}/{max_step_retries} in {wait_time:.1f}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    [API] Step keeps failing after {max_step_retries} retries, ending game")
                            break
                    break
                except Exception as e:
                    err_str = str(e)
                    err_lower = err_str.lower()
                    is_server_error = any(code in err_lower for code in ['500', '502', '503', '504', 'server error', 'internal server'])
                    is_rate_limit = '429' in err_lower or 'rate limit' in err_lower
                    if is_server_error or is_rate_limit:
                        if step_attempt < max_step_retries - 1:
                            wait_time = step_retry_delay * (2 ** step_attempt)
                            print(f"    [API] Server error on {action.name}, retry {step_attempt + 1}/{max_step_retries} in {wait_time:.1f}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"    [API] Server error persists after {max_step_retries} retries, ending game")
                            obs = None
                            break
                    else:
                        print(f"    [ERROR] Step failed: {type(e).__name__}: {e}")
                        obs = None
                        break

            if obs is None:
                print(f"    [ABORT] Ending game {game_id} due to API failure")
                break

            actions_taken += 1
            action_sequence.append(action.name)

            # Update state tracking
            last_action_str = action.name
            recent_actions.append(action.name)
            if len(recent_actions) > 10:
                recent_actions.pop(0)

            frame_hash_before = self._compute_frame_hash(obs_before)
            frame_hash_after = self._compute_frame_hash(obs)
            last_frame_changed = frame_hash_before != frame_hash_after
            current_frame_hash = frame_hash_after

            # ACTION6 click feedback to visual_analyzer
            if action.name == 'ACTION6' and action_data:
                try:
                    va = None
                    if hasattr(self.decision_system, '_engine_registry'):
                        registry = self.decision_system._engine_registry
                        if registry:
                            va = getattr(registry, 'visual_analyzer', None)
                    if va and hasattr(va, 'mark_coordinate_clicked'):
                        va.mark_coordinate_clicked(
                            action_data.get('x', 32), action_data.get('y', 32),
                            frame_changed=last_frame_changed
                        )
                except Exception:
                    pass

            # Track failed actions and stuck state
            is_action6_only = current_available == [6]
            if not last_frame_changed and action.name.startswith('ACTION'):
                failed_actions.add(action.name)
                if not is_action6_only:
                    stuck_count += 1
            else:
                stuck_count = 0

            if 'reason' in dir() and reason and 'EMERGENCY' in reason:
                stuck_count = 0

            # Update sequence position
            if is_replay_mode and active_sequence and sequence_position < len(active_sequence):
                if ablation_active and sequence_position in ablation_skip_indices:
                    sequence_position += 1
                else:
                    expected_action = active_sequence[sequence_position]
                    if action.name == expected_action or action.name == f'ACTION{expected_action}':
                        sequence_position += 1

            last_obs = obs

            # Track level progress
            current_levels = getattr(obs, 'levels_completed', 0) or 0
            level_up = current_levels > prev_levels
            current_score = current_levels / win_levels if win_levels > 0 else 0.0
            last_score_delta = current_score - prev_score
            is_game_over = obs and obs.state in (GameState.WIN, GameState.GAME_OVER)
            is_death = obs and obs.state == GameState.GAME_OVER and not level_up

            # Outcome type
            if is_death:
                last_outcome_type = 'death'
                self.event_bus.publish(make_event(
                    EventType.AGENT_DEATH,
                    game_id=game_id, agent_id=agent.agent_id,
                    action_count=actions_taken, last_action=action.name,
                    level=current_levels, generation=current_generation,
                ))
                if self.concept_discovery_engine:
                    try:
                        death_patterns = [action.name, 'death']
                        if len(recent_actions) >= 2:
                            death_patterns.append('_'.join(recent_actions[-3:]))
                        op_id = f"{self._current_session_id}_{actions_taken}"
                        self.concept_discovery_engine.track_failed_operator_pattern(
                            operator_id=op_id, game_id=game_id, sub_patterns=death_patterns,
                        )
                    except Exception:
                        pass
            elif last_score_delta > 0 or level_up:
                last_outcome_type = 'positive'
            elif last_score_delta < 0:
                last_outcome_type = 'negative'
            else:
                last_outcome_type = 'neutral'

            # Phase 1.4: Feed successful actions to concept discovery
            if self.concept_discovery_engine and last_outcome_type == 'positive' and last_frame_changed:
                try:
                    sub_patterns = [action.name]
                    if action_data:
                        sub_patterns.append(f"click_{action_data.get('x', 0)}_{action_data.get('y', 0)}")
                    if level_up:
                        sub_patterns.append('level_transition')
                    if last_score_delta > 0:
                        sub_patterns.append(f"score_gain_{last_score_delta:.2f}")
                    if len(recent_actions) >= 2:
                        sub_patterns.append('_'.join(recent_actions[-3:]))
                    operator_id = f"{self._current_session_id}_{actions_taken}"
                    self.concept_discovery_engine.track_successful_operator_pattern(
                        operator_id=operator_id, game_id=game_id, sub_patterns=sub_patterns,
                    )
                except Exception:
                    pass

            self.context_builder.update_runner_outcome(action.name, last_outcome_type, last_frame_changed)

            # Record action trace
            self._record_action_trace(
                game_id=game_id, action_num=action_num,
                obs_before=obs_before, obs_after=obs,
                score_before=prev_score, score_after=current_score,
                level_before=prev_levels, level_after=current_levels,
                is_game_over=is_game_over, coordinates=action_data,
            )

            # Notify rungs about action outcome
            if hasattr(self.decision_system, 'notify_action_complete'):
                try:
                    frame_before = getattr(obs_before, 'frame', None)
                    frame_after = getattr(obs, 'frame', None)
                    if frame_before is not None and hasattr(frame_before, 'tolist'):
                        frame_before = frame_before.tolist()
                    if frame_after is not None and hasattr(frame_after, 'tolist'):
                        frame_after = frame_after.tolist()
                    self.decision_system.notify_action_complete(
                        action=action.name, action_data=action_data or {},
                        frame_before=frame_before, frame_after=frame_after,
                        context=context,
                    )
                except Exception:
                    pass

            # Record player state for symbolic reasoning
            action_result = 'continue'
            if is_game_over:
                action_result = 'win' if obs.state == GameState.WIN else 'death'
            elif level_up:
                action_result = 'success'

            self._record_player_state(
                game_id=game_id, action_num=actions_taken,
                action_taken=action.name, obs_before=obs_before,
                obs_after=obs, action_result=action_result,
                level_number=current_levels,
            )

            # Save per-level winning subsequences on level_up
            if level_up:
                try:
                    level_subsequence = action_sequence[level_start_action_index:]
                    if level_subsequence:
                        level_seq_id = f"seq_{uuid.uuid4().hex[:12]}"
                        level_just_beaten = prev_levels + 1

                        self.db.execute_query("""
                            INSERT INTO winning_sequences (
                                sequence_id, game_id, game_type, level_number,
                                action_sequence, total_actions, total_score,
                                efficiency_score, agent_id, session_id,
                                generation_discovered, is_active,
                                initial_frame, final_frame, discovered_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', '[]', datetime('now'))
                        """, (
                            level_seq_id, game_id, game_type, level_just_beaten,
                            json.dumps(level_subsequence), len(level_subsequence),
                            current_score, current_score / max(1, len(level_subsequence)),
                            agent.agent_id, self._current_session_id or 'unknown',
                            current_generation,
                        ))
                        if self.verbose:
                            print(f"    [SEQ-SAVE] Level {level_just_beaten} sequence saved: {level_seq_id[:16]} ({len(level_subsequence)} actions)")
                except Exception as e:
                    if self.verbose:
                        print(f"    [SEQ-ERR] Failed to save level sequence: {e}")

                level_start_action_index = len(action_sequence)

                # Publish LEVEL_UP event
                self.event_bus.publish(make_event(
                    EventType.LEVEL_UP,
                    game_id=game_id, agent_id=agent.agent_id,
                    level=current_levels, actions_taken=actions_taken,
                    score=current_score, generation=current_generation,
                ))

                # Phase 1.1: Mastery ablation recording
                if self.mastery_system:
                    game_type_m = game_id[:4] if len(game_id) >= 4 else game_id
                    level_just_beaten_m = prev_levels + 1
                    try:
                        if ablation_active:
                            self.mastery_system.record_ablation_result(
                                game_type=game_type_m, level_number=level_just_beaten_m,
                                sequence_id=current_sequence_id or 'unknown',
                                skipped_indices=sorted(ablation_skip_indices),
                                skip_rate=ablation_skip_rate, test_passed=True,
                                actions_taken=actions_taken - level_start_action_index,
                                final_score=current_score, agent_id=agent.agent_id,
                                generation=current_generation, tier_at_test=mastery_tier,
                            )
                        self.mastery_system.trigger_update(game_type_m, level_just_beaten_m, 'sequence_discovered')
                    except Exception:
                        pass
                    ablation_active = False
                    ablation_skip_indices = set()

                # Clear visual_analyzer clicked tracking for new level
                try:
                    va = None
                    if hasattr(self.decision_system, '_engine_registry'):
                        registry = self.decision_system._engine_registry
                        if registry:
                            va = getattr(registry, 'visual_analyzer', None)
                    if va:
                        va.reset_clicked_coordinates()
                except Exception:
                    pass

                # Load per-level winning sequence for next level
                next_level = current_levels + 1
                try:
                    next_seq = self.db.execute_query("""
                        SELECT action_sequence, sequence_id FROM winning_sequences
                        WHERE game_type = ? AND level_number = ? AND is_active = 1
                        ORDER BY efficiency_score DESC LIMIT 1
                    """, (game_type, next_level))
                    if next_seq and next_seq[0].get('action_sequence'):
                        seq_raw = next_seq[0]['action_sequence']
                        active_sequence = json.loads(seq_raw) if isinstance(seq_raw, str) else list(seq_raw)
                        sequence_position = 0
                        is_replay_mode = True
                        has_level_sequence = True
                        current_sequence_id = next_seq[0].get('sequence_id', '')
                        try:
                            self.db.execute_query("""
                                UPDATE winning_sequences
                                SET times_referenced = COALESCE(times_referenced, 0) + 1,
                                    last_referenced = datetime('now')
                                WHERE game_type = ? AND level_number = ? AND is_active = 1
                            """, (game_type, next_level))
                        except Exception:
                            pass

                        # Phase 1.1: Mastery gate for next level
                        if self.mastery_system:
                            try:
                                allowed, reason_m, ms = self.mastery_system.should_allow_replay(
                                    game_type, next_level
                                )
                                mastery_tier = ms.tier
                                if not allowed:
                                    active_sequence = []
                                    sequence_position = 0
                                    is_replay_mode = False
                                    has_level_sequence = False
                                    if self.verbose:
                                        print(f"    [MASTERY] Level {next_level} replay DENIED: {reason_m}")
                                else:
                                    skip_min, skip_max = self.mastery_system.get_ablation_skip_rate(mastery_tier)
                                    if skip_max > 0 and len(active_sequence) > 3:
                                        ablation_skip_rate = random.uniform(skip_min, skip_max)
                                        n_skip = max(1, int(len(active_sequence) * ablation_skip_rate))
                                        skippable = list(range(len(active_sequence) - 1))
                                        if skippable:
                                            ablation_skip_indices = set(random.sample(
                                                skippable, min(n_skip, len(skippable))
                                            ))
                                            ablation_active = True
                                    if self.verbose:
                                        abl_str = f" (ablation: skip {len(ablation_skip_indices)}/{len(active_sequence)})" if ablation_active else ""
                                        print(f"    [MASTERY] Level {next_level} replay ALLOWED: {reason_m}{abl_str}")
                            except Exception:
                                pass

                        if self.verbose and is_replay_mode:
                            print(f"    [SEQ-LOAD] Level {next_level} sequence loaded ({len(active_sequence)} actions)")
                    else:
                        active_sequence = []
                        sequence_position = 0
                        is_replay_mode = False
                        has_level_sequence = False
                except Exception:
                    active_sequence = []
                    sequence_position = 0
                    is_replay_mode = False
                    has_level_sequence = False

            prev_levels = current_levels
            prev_score = current_score

            # Verbose output
            if self.verbose:
                levels = current_levels
                state_str = str(obs.state).replace('GameState.', '') if obs else '?'
                level_indicator = ' [LEVEL UP!]' if level_up else ''
                coord_str = ''
                if action.name == 'ACTION6' and action_data:
                    coord_str = f" @ ({action_data.get('x', '?')}, {action_data.get('y', '?')})"

                trace_str = ''
                if self._use_cognitive_router and 'reason' in dir() and reason:
                    short_reason = reason[:60] + '...' if len(reason) > 60 else reason
                    trace_str = f" | {short_reason}"

                print(f"    [{actions_taken:3d}] {action.name:8s}{coord_str} -> levels={levels}/{win_levels} state={state_str}{level_indicator}{trace_str}")

            # Check for game end
            if obs and obs.state == GameState.WIN:
                if self.verbose:
                    print(f"    [WIN!] Game won after {actions_taken} actions!")
                self.event_bus.publish(make_event(
                    EventType.GAME_WON,
                    game_id=game_id, agent_id=agent.agent_id,
                    actions_taken=actions_taken, total_score=current_score,
                    levels_completed=current_levels, generation=current_generation,
                ))
                break
            if obs and obs.state == GameState.GAME_OVER:
                if self.verbose:
                    print(f"    [GAME OVER] after {actions_taken} actions")
                self.event_bus.publish(make_event(
                    EventType.GAME_OVER,
                    game_id=game_id, agent_id=agent.agent_id,
                    actions_taken=actions_taken, levels_completed=current_levels,
                    generation=current_generation,
                ))
                break

        # ========== EXTRACT RESULTS ==========
        levels_completed = 0
        total_levels = win_levels
        is_win = False

        if last_obs:
            levels_completed = getattr(last_obs, 'levels_completed', 0) or 0
            is_win = last_obs.state == GameState.WIN

        score = levels_completed / total_levels if total_levels > 0 else 0.0

        return GameResult(
            game_id=game_id, agent_id=agent.agent_id, score=score,
            levels_completed=levels_completed, total_levels=total_levels,
            is_win=is_win, actions_taken=actions_taken,
            action_sequence=action_sequence,
        )
