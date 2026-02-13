import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Cognitive Game Player — GamePlayer adapter that uses CognitiveLoop.

This module wraps the existing GamePlayer with the Perceive-Think-Map-Act
cognitive loop. It can be used as a DROP-IN REPLACEMENT for GamePlayer
or alongside it (controlled by a flag).

The key insight: we DON'T rewrite the 1,400-line game_player.py.
Instead, we wrap its decision path with the cognitive loop while
preserving all existing functionality (replay, mastery, events, etc.).

Usage in evolution_runner.py:
    from cognitive_game_player import CognitiveGamePlayer
    player = CognitiveGamePlayer(game_player)
    result = player.play_game(agent, game_id, generation, is_running_fn)
"""

import logging
import time
from typing import Any, Callable, List, Optional

import numpy as np
from arcengine import GameAction, GameState

from cognitive_loop import CognitiveLoop
from engines.cognition.cognitive_frame import CognitiveFrame
from evolution_types import AgentState, GameResult

logger = logging.getLogger(__name__)


class CognitiveGamePlayer:
    """
    Wraps GamePlayer with CognitiveLoop for the P-T-M-A cycle.

    Delegates all infrastructure (API calls, session management, event bus,
    mastery system, replay sequences, etc.) to the original GamePlayer.
    Intercepts the decision path to run through CognitiveLoop instead.
    """

    def __init__(self, game_player: Any, verbose: bool = True):
        """
        Args:
            game_player: Existing GamePlayer instance (fully initialized).
            verbose: Print cognitive frames to console.
        """
        self._gp = game_player
        self._verbose = verbose
        self._last_replay: List[CognitiveFrame] = []

    def play_game(
        self,
        agent: AgentState,
        game_id: str,
        current_generation: int,
        is_running_fn: Callable[[], bool],
    ) -> GameResult:
        """
        Play a game using the cognitive loop.

        Mirrors GamePlayer.play_game() signature exactly.
        Preserves all side effects (DB writes, events, etc.).
        """
        # Create cognitive loop
        loop = CognitiveLoop(
            decision_system=self._gp.decision_system,
            context_builder=self._gp.context_builder,
            verbose=self._verbose,
        )

        # Set up environment (reuse GamePlayer's setup)
        scorecard_id = self._gp._get_or_create_scorecard(agent, game_id)
        env = None
        try:
            env = self._gp.arcade.make(game_id, scorecard_id=scorecard_id)
        except Exception as e:
            print(f"  [ERROR] Failed to create env for {game_id}: {e}")
            return GameResult(
                game_id=game_id, agent_id=agent.agent_id, score=0.0,
                levels_completed=0, total_levels=1, is_win=False, actions_taken=0,
            )

        if env is None:
            return GameResult(
                game_id=game_id, agent_id=agent.agent_id, score=0.0,
                levels_completed=0, total_levels=1, is_win=False, actions_taken=0,
            )

        # Get initial observation
        initial_obs = env.observation_space
        available_actions = getattr(initial_obs, 'available_actions', [1, 2, 3, 4])
        win_levels = getattr(initial_obs, 'win_levels', 7)

        if self._verbose:
            print(f"    [COGNITIVE] Game: {game_id} | Actions: {available_actions} | Win at: {win_levels}")

        # Reset context builder
        self._gp.context_builder.reset(game_id)

        # Initialize cognitive loop
        loop.start_game(game_id, available_actions, self._gp.max_actions)

        # Game state
        actions_taken = 0
        action_sequence: List[str] = []
        level_start_action_index = 0
        last_obs = None
        prev_levels = 0
        prev_score = 0.0
        total_frame_changes = 0
        total_coord_attempts = 0
        total_coord_successes = 0

        # ========== COGNITIVE GAME LOOP ==========
        while actions_taken < self._gp.max_actions:
            if not is_running_fn():
                break

            obs = last_obs if last_obs else initial_obs
            current_available = getattr(obs, 'available_actions', None) or available_actions

            # Get frame
            frame = getattr(obs, 'frame', None)

            # ═══ COGNITIVE LOOP CYCLE ═══
            action_num, action_data, cf = loop.cycle(
                frame=frame,
                obs=obs,
                agent_id=agent.agent_id,
                agent_role=getattr(agent, 'role', 'pioneer'),
                w_A=getattr(agent, 'w_A', 0.5),
                w_B=getattr(agent, 'w_B', 0.5),
            )

            # Validate action
            if action_num not in current_available:
                import random
                action_num = random.choice(current_available)

            action = getattr(GameAction, f'ACTION{action_num}', GameAction.ACTION1)

            # Take action with retry
            new_obs = None
            for attempt in range(3):
                try:
                    new_obs = env.step(action, data=action_data)
                    if new_obs is not None:
                        break
                    time.sleep(2.0 * (2 ** attempt))
                except Exception as e:
                    err_str = str(e).lower()
                    if any(code in err_str for code in ['500', '502', '503', '504', '429']):
                        time.sleep(2.0 * (2 ** attempt))
                        continue
                    print(f"    [ERROR] Step failed: {e}")
                    break

            if new_obs is None:
                print(f"    [ABORT] Ending game {game_id} due to API failure")
                break

            actions_taken += 1
            action_sequence.append(action.name)

            # Compute frame change
            obs_before = obs
            frame_hash_before = self._compute_frame_hash(obs_before)
            frame_hash_after = self._compute_frame_hash(new_obs)
            frame_changed = frame_hash_before != frame_hash_after
            if frame_changed:
                total_frame_changes += 1
            if action.name == 'ACTION6':
                total_coord_attempts += 1
                if frame_changed:
                    total_coord_successes += 1

            # Track level progress
            current_levels = getattr(new_obs, 'levels_completed', 0) or 0
            level_up = current_levels > prev_levels
            current_score = current_levels / win_levels if win_levels > 0 else 0.0
            score_delta = current_score - prev_score

            # ═══ RECORD RESULT (closes the loop) ═══
            post_frame = getattr(new_obs, 'frame', None)
            loop.record_result(
                post_frame=post_frame,
                frame_changed=frame_changed,
                score_delta=score_delta,
                level_changed=level_up,
                new_level=current_levels + 1 if level_up else 0,
                new_score=current_score,
            )

            # ═══ NOTIFY RUNGS (close the feedback loop for all 80+ rungs) ═══
            if hasattr(self._gp.decision_system, 'notify_action_complete'):
                try:
                    frame_before = self._get_frame_array(obs)
                    frame_after = self._get_frame_array(new_obs)
                    if frame_before is not None and hasattr(frame_before, 'tolist'):
                        frame_before = frame_before.tolist()
                    if frame_after is not None and hasattr(frame_after, 'tolist'):
                        frame_after = frame_after.tolist()
                    self._gp.decision_system.notify_action_complete(
                        action=action.name, action_data=action_data or {},
                        frame_before=frame_before, frame_after=frame_after,
                        context={},
                    )
                except Exception:
                    pass

            # ═══ RECORD ACTION TRACE (persist to DB) ═══
            try:
                self._gp._record_action_trace(
                    game_id=game_id, action_num=action_num,
                    obs_before=obs, obs_after=new_obs,
                    score_before=prev_score, score_after=current_score,
                    level_before=prev_levels, level_after=current_levels,
                    is_game_over=(new_obs.state == GameState.GAME_OVER if new_obs else False),
                    coordinates=action_data,
                )
            except Exception:
                pass

            # Update context builder outcome
            outcome_type = 'neutral'
            if level_up or score_delta > 0:
                outcome_type = 'positive'
            elif new_obs and new_obs.state == GameState.GAME_OVER:
                outcome_type = 'death'
            self._gp.context_builder.update_runner_outcome(action.name, outcome_type, frame_changed)

            # Publish events (preserve existing behavior)
            if level_up:
                from event_bus import EventType, make_event
                self._gp.event_bus.publish(make_event(
                    EventType.LEVEL_UP,
                    game_id=game_id, agent_id=agent.agent_id,
                    level=current_levels, actions_taken=actions_taken,
                    score=current_score, generation=current_generation,
                ))

                # Record winning subsequence for this level
                try:
                    import json
                    import uuid
                    level_subsequence = action_sequence[level_start_action_index:]
                    if level_subsequence:
                        level_seq_id = f"seq_{uuid.uuid4().hex[:12]}"
                        level_just_beaten = prev_levels + 1
                        game_type = game_id[:4] if len(game_id) >= 4 else game_id
                        self._gp.db.execute_query("""
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
                            agent.agent_id, 'cognitive_session',
                            current_generation,
                        ))
                        if self._verbose:
                            print(f"    [SEQ-SAVE] Level {level_just_beaten} sequence saved ({len(level_subsequence)} actions)")
                except Exception:
                    pass

                level_start_action_index = len(action_sequence)

            # Verbose output (cognitive-enriched)
            if self._verbose:
                state_str = str(new_obs.state).replace('GameState.', '') if new_obs else '?'
                level_indicator = ' [LEVEL-UP]' if level_up else ''
                coord_str = ''
                if action.name == 'ACTION6' and action_data:
                    coord_str = f" @({action_data.get('x', '?')},{action_data.get('y', '?')})"
                speed = cf.action_speed
                print(
                    f"    [{actions_taken:3d}] {action.name}{coord_str} "
                    f"[{speed}] -> levels={current_levels}/{win_levels} "
                    f"state={state_str}{level_indicator}"
                )

            last_obs = new_obs
            prev_levels = current_levels
            prev_score = current_score

            # Check game end
            if new_obs and new_obs.state == GameState.WIN:
                if self._verbose:
                    print(f"    [WIN!] Game won after {actions_taken} actions!")
                from event_bus import EventType, make_event
                self._gp.event_bus.publish(make_event(
                    EventType.GAME_WON,
                    game_id=game_id, agent_id=agent.agent_id,
                    actions_taken=actions_taken, total_score=current_score,
                    levels_completed=current_levels, generation=current_generation,
                ))
                break
            if new_obs and new_obs.state == GameState.GAME_OVER:
                if self._verbose:
                    print(f"    [GAME OVER] after {actions_taken} actions")
                from event_bus import EventType, make_event
                self._gp.event_bus.publish(make_event(
                    EventType.GAME_OVER,
                    game_id=game_id, agent_id=agent.agent_id,
                    actions_taken=actions_taken, levels_completed=current_levels,
                    generation=current_generation,
                ))
                break

        # End game and get replay
        replay = loop.end_game()
        self._last_replay = replay

        # Extract results
        levels_completed = 0
        is_win = False
        if last_obs:
            levels_completed = getattr(last_obs, 'levels_completed', 0) or 0
            is_win = last_obs.state == GameState.WIN
        score = levels_completed / win_levels if win_levels > 0 else 0.0

        return GameResult(
            game_id=game_id, agent_id=agent.agent_id, score=score,
            levels_completed=levels_completed, total_levels=win_levels,
            is_win=is_win, actions_taken=actions_taken,
            action_sequence=action_sequence,
            frame_changes=total_frame_changes,
            coordinate_attempts=total_coord_attempts,
            coordinate_successes=total_coord_successes,
        )

    def get_last_replay(self) -> List[CognitiveFrame]:
        """Get the cognitive frame replay from the last game."""
        return self._last_replay

    def print_last_replay(self, mode: str = "log"):
        """Print the last game replay."""
        for cf in self._last_replay:
            if mode == "dashboard":
                print(cf.to_dashboard())
                print()
            else:
                print(cf.to_log_line())

    @staticmethod
    def _compute_frame_hash(obs: Any) -> str:
        """Compute a hash of the observation frame for change detection."""
        import hashlib
        frame = getattr(obs, 'frame', None)
        if frame is None:
            return ''
        if isinstance(frame, np.ndarray):
            return hashlib.md5(frame.tobytes()).hexdigest()

    @staticmethod
    def _get_frame_array(obs: Any) -> 'Optional[np.ndarray]':
        """Extract frame as numpy array from observation."""
        if obs is None:
            return None
        try:
            for attr in ('frame', 'grid', 'observation'):
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
        try:
            flat = str(frame)
            return hashlib.md5(flat.encode()).hexdigest()
        except Exception:
            return ''
