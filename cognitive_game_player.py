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

import json as _json
import logging
import time
import uuid
from datetime import datetime
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

    def __init__(self, game_player: Any, verbose: bool = True, observe: bool = False):
        """
        Args:
            game_player: Existing GamePlayer instance (fully initialized).
            verbose: Print cognitive frames to console.
            observe: Enable Tier 2 observation (frame snapshots at key moments).
        """
        self._gp = game_player
        self._verbose = verbose
        self._observe = observe
        self._last_replay: List[CognitiveFrame] = []

        # ═══ Tier 1 Observation Logging ═══
        self._observation_log_path = "log/observation_log.jsonl"
        self._observation_max_lines = 40_000  # Ring buffer size
        self._obs_writes_since_check = 0  # Counter for truncation trigger

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
            db=self._gp.db,
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

        # Create session for action traces (mirrors GamePlayer.play_game)
        self._gp._current_session_id = (
            f"session_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
        )
        try:
            self._gp.db.execute_query("""
                INSERT INTO training_sessions (
                    session_id, game_id, start_time, mode, status, total_actions
                ) VALUES (?, ?, datetime('now'), 'evolution', 'in_progress', 0)
            """, (self._gp._current_session_id, game_id))
        except Exception as e:
            logger.warning(f"[COGNITIVE] Failed to create training session: {e}")

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

        # Per-level action budget: starts at max_actions (150), extends
        # by actions_per_level on each level-up. Unused actions carry
        # forward as a speed bonus for fast solvers.
        actions_per_level = self._gp.max_actions
        action_budget = actions_per_level

        # ═══ FALLBACK: Load winning sequences (used only if cognitive loop stalls) ═══
        fallback_sequence: List[str] = []
        fallback_position = 0
        fallback_active = False
        fallback_threshold = min(150, self._gp.max_actions // 5)
        # Only load sequences as a safety net -- cognitive loop is primary
        game_type = game_id[:4] if len(game_id) >= 4 else game_id
        try:
            result = self._gp.db.execute_query("""
                SELECT action_sequence FROM winning_sequences
                WHERE game_type = ? AND level_number = 1 AND is_active = 1
                ORDER BY efficiency_score DESC LIMIT 1
            """, (game_type,))
            if result:
                import json
                seq_data = result[0].get('action_sequence') if isinstance(result[0], dict) else result[0][0]
                if seq_data:
                    fallback_sequence = json.loads(seq_data) if isinstance(seq_data, str) else list(seq_data)
                    if self._verbose:
                        print(f"    [FALLBACK] Sequence loaded ({len(fallback_sequence)} actions) -- will use if stuck after {fallback_threshold} actions")
        except Exception:
            pass

        # ========== COGNITIVE GAME LOOP ==========
        while actions_taken < action_budget:
            if not is_running_fn():
                break

            obs = last_obs if last_obs else initial_obs
            current_available = getattr(obs, 'available_actions', None) or available_actions

            # ═══ FALLBACK CHECK: If stuck too long with no progress, switch to replay ═══
            if (
                not fallback_active
                and fallback_sequence
                and actions_taken >= fallback_threshold
                and prev_levels == 0
            ):
                fallback_active = True
                fallback_position = 0
                if self._verbose:
                    print(f"    [FALLBACK-ACTIVE] No progress after {actions_taken} actions, replaying winning sequence")

            # Get frame
            frame = getattr(obs, 'frame', None)

            # ═══ ACTION SELECTION: Fallback replay OR cognitive cycle ═══
            cf = None
            if fallback_active and fallback_sequence and fallback_position < len(fallback_sequence):
                # Replay from winning sequence
                seq_entry = fallback_sequence[fallback_position]
                fallback_position += 1
                # Parse sequence entry: can be int, dict with 'action', or ACTION name
                if isinstance(seq_entry, dict):
                    action_num = seq_entry.get('action', seq_entry.get('action_num', 1))
                    action_data = seq_entry.get('data', seq_entry.get('action_data', None))
                elif isinstance(seq_entry, int):
                    action_num = seq_entry
                    action_data = None
                elif isinstance(seq_entry, str) and seq_entry.startswith('ACTION'):
                    action_num = int(seq_entry.replace('ACTION', ''))
                    action_data = None
                else:
                    action_num = int(seq_entry) if seq_entry else 1
                    action_data = None
                if fallback_position >= len(fallback_sequence):
                    fallback_active = False
                    if self._verbose:
                        print(f"    [FALLBACK-DONE] Sequence exhausted after {fallback_position} actions, returning to cognitive loop")
            else:
                # Normal cognitive cycle
                if fallback_active:
                    # Sequence ran out, back to cognitive
                    fallback_active = False
                action_num, action_data, cf = loop.cycle(
                    frame=frame,
                    obs=obs,
                    agent_id=agent.agent_id,
                    agent_role=getattr(agent, 'role', 'pioneer'),
                    w_A=getattr(agent, 'w_A', 0.5),
                    w_B=getattr(agent, 'w_B', 0.5),
                    available_actions=current_available,
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

            # Print cognitive frame AFTER record_result (frame_changed is now known)
            if self._verbose and cf:
                print(cf.to_log_line())

            # ═══ NOTIFY RUNGS (close the feedback loop for all 80+ rungs) ═══
            # Gap 4D: Pass rich outcome context so rungs can adjust confidence
            # based on whether the action was productive/destructive/wasted
            if hasattr(self._gp.decision_system, 'notify_action_complete'):
                try:
                    frame_before = self._get_frame_array(obs)
                    frame_after = self._get_frame_array(new_obs)
                    if frame_before is not None and hasattr(frame_before, 'tolist'):
                        frame_before = frame_before.tolist()
                    if frame_after is not None and hasattr(frame_after, 'tolist'):
                        frame_after = frame_after.tolist()
                    # Build rich outcome context from cognitive frame
                    outcome_context = {}
                    if cf:
                        outcome_context = {
                            'frame_changed': frame_changed,
                            'was_productive': cf.was_productive,
                            'was_destructive': cf.was_destructive,
                            'was_wasted': cf.was_wasted,
                            'was_neutral': cf.was_neutral,
                            'goal_progress_delta': cf.goal_progress_delta,
                            'goal_cells_total': cf.goal_cells_total,
                            'goal_cells_correct': cf.goal_cells_correct,
                            'pixels_changed': cf.pixels_changed,
                        }
                    self._gp.decision_system.notify_action_complete(
                        action=action.name, action_data=action_data or {},
                        frame_before=frame_before, frame_after=frame_after,
                        context=outcome_context,
                    )
                except Exception:
                    pass

            # ═══ TIER 1 OBSERVATION LOGGING (structured JSONL) ═══
            self._write_observation_record(
                agent_id=agent.agent_id,
                game_id=game_id,
                generation=current_generation,
                step=actions_taken,
                level=current_levels,
                action_type=action_num,
                action_data=action_data,
                frame_changed=frame_changed,
                cf=cf,
            )

            # ═══ TIER 2: Periodic frame snapshot (every 20 actions) ═══
            if actions_taken % 20 == 0:
                self._write_frame_snapshot(
                    reason='periodic', agent_id=agent.agent_id,
                    game_id=game_id, generation=current_generation,
                    step=actions_taken, level=current_levels,
                    frame=self._get_frame_array(new_obs), cf=cf,
                )

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
                # ═══ PER-LEVEL BUDGET EXTENSION ═══
                # Grant another actions_per_level actions for the new level.
                # Any unspent actions from previous levels carry forward.
                old_budget = action_budget
                action_budget += actions_per_level
                remaining = action_budget - actions_taken
                if self._verbose:
                    print(f"    [BUDGET] Level {current_levels}: "
                          f"budget {old_budget} -> {action_budget} "
                          f"({remaining} actions remaining)")

                # Update cognitive loop's internal budget so strategy
                # planning knows the extended horizon
                loop._max_actions = action_budget

                # ═══ TIER 2: Snapshot on level-up ═══
                post_frame_arr = self._get_frame_array(new_obs)
                self._write_frame_snapshot(
                    reason='level_up', agent_id=agent.agent_id,
                    game_id=game_id, generation=current_generation,
                    step=actions_taken, level=current_levels,
                    frame=post_frame_arr, cf=cf,
                )

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
                speed = cf.action_speed if cf else 'FALLBACK'
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
                # ═══ TIER 2: Snapshot on game-over ═══
                self._write_frame_snapshot(
                    reason='game_over', agent_id=agent.agent_id,
                    game_id=game_id, generation=current_generation,
                    step=actions_taken, level=current_levels,
                    frame=self._get_frame_array(new_obs), cf=cf,
                )
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

        # ═══ PERSIST CAUSAL MAP KNOWLEDGE TO DATABASE ═══
        # Save what the agent learned (effects, rules, color cycles)
        # so the next generation inherits this understanding.
        self._persist_causal_knowledge(loop, game_id, agent.agent_id, current_generation)

        # ═══ RECORD ACTION PRODUCTIVITY (Gap 4C) ═══
        # Replace dead avg_score_impact with goal-directed productivity
        self._record_action_productivity(replay, game_id)

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

    # ═══════════════════════════════════════════════════════════════════
    # GAP 4C: ACTION PRODUCTIVITY METRIC
    # ═══════════════════════════════════════════════════════════════════

    def _record_action_productivity(
        self,
        replay: List[CognitiveFrame],
        game_id: str,
    ):
        """
        Record action productivity to the database.

        Replaces the dead avg_score_impact metric with goal-directed
        productivity: what fraction of actions moved toward the goal.
        Updates the action_effectiveness table with frame_change_rate
        and goal_productivity columns.
        """
        if not replay:
            return
        try:
            # Aggregate per action type
            action_stats: dict = {}
            for cf in replay:
                a = cf.action_type
                if a not in action_stats:
                    action_stats[a] = {
                        'attempts': 0, 'frame_changes': 0,
                        'productive': 0, 'destructive': 0, 'wasted': 0,
                    }
                action_stats[a]['attempts'] += 1
                if cf.frame_changed:
                    action_stats[a]['frame_changes'] += 1
                if cf.was_productive:
                    action_stats[a]['productive'] += 1
                if cf.was_destructive:
                    action_stats[a]['destructive'] += 1
                if cf.was_wasted:
                    action_stats[a]['wasted'] += 1

            for action_num, stats in action_stats.items():
                attempts = stats['attempts']
                if attempts == 0:
                    continue
                success_rate = stats['frame_changes'] / attempts
                productivity = stats['productive'] / attempts
                # Upsert into action_effectiveness
                self._gp.db.execute_query("""
                    INSERT INTO action_effectiveness
                        (game_id, action_number, attempts, successes,
                         success_rate, avg_score_impact)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(game_id, action_number) DO UPDATE SET
                        attempts = attempts + excluded.attempts,
                        successes = successes + excluded.successes,
                        success_rate = (
                            (successes + excluded.successes) * 1.0 /
                            NULLIF(attempts + excluded.attempts, 0)
                        ),
                        avg_score_impact = ?,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    game_id, action_num, attempts, stats['frame_changes'],
                    success_rate, productivity,
                    productivity,
                ))
        except Exception as e:
            logger.debug(f"[GAP4C] Action productivity recording failed: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # CAUSAL MAP PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════

    def _persist_causal_knowledge(
        self,
        loop: CognitiveLoop,
        game_id: str,
        agent_id: str,
        generation: int,
    ):
        """
        Persist learned causal knowledge to the database.

        Saves the CausalMap's effects, rules, and color cycles
        as a world_model_state so the next generation inherits
        this understanding. This is what makes learning compound
        across agent lifetimes.
        """
        causal_map = loop.causal_map
        if causal_map is None:
            return

        try:
            import uuid as _uuid

            # Build a serializable snapshot of causal knowledge
            causal_data = {}
            for pos, effect in causal_map._effects.items():
                pos_key = f"({pos[0]},{pos[1]})"
                observations = []
                for affected_pos in effect.affected:
                    transitions = effect.color_transitions.get(affected_pos, [])
                    if isinstance(transitions, list):
                        for old_c, new_c in transitions:
                            observations.append({
                                'changes': [{
                                    'x': affected_pos[0],
                                    'y': affected_pos[1],
                                    'from_color': old_c,
                                    'to_color': new_c,
                                }]
                            })
                    elif isinstance(transitions, dict):
                        observations.append({
                            'changes': [{
                                'x': affected_pos[0],
                                'y': affected_pos[1],
                                'from_color': transitions.get('from', 0),
                                'to_color': transitions.get('to', 0),
                            }]
                        })

                causal_data[pos_key] = {
                    'observations': observations,
                    'observation_count': effect.observation_count,
                    'productive_count': effect.productive_count,
                    'destructive_count': effect.destructive_count,
                    'confidence': effect.confidence,
                }

            # Include color cycle knowledge
            color_cycles = {}
            for pos, cycle in causal_map._color_cycles.items():
                color_cycles[f"({pos[0]},{pos[1]})"] = cycle

            # Include movement knowledge
            walls = [
                {'pos': list(pos), 'action': act}
                for pos, act in causal_map._walls
            ]

            objects_json = _json.dumps({
                'causal_map': causal_data,
                'color_cycles': color_cycles,
                'walls': walls,
                'rules': [
                    {'type': r.rule_type, 'desc': r.description,
                     'evidence': r.evidence_count, 'confidence': r.confidence}
                    for r in causal_map._rules
                ],
                'completeness': causal_map.completeness,
            })

            # Upsert per game_type: use deterministic state_id so we
            # replace the prior snapshot rather than creating unbounded rows.
            # The game_type's best knowledge always overwrites the old one.
            game_type = game_id[:4] if len(game_id) >= 4 else game_id
            state_id = f"wms_{game_type}_best"
            step_number = len(causal_map._effects)  # Proxy for knowledge depth

            # Only overwrite if this session learned MORE than what's stored
            existing = self._gp.db.execute_query("""
                SELECT step_number FROM world_model_states
                WHERE state_id = ?
            """, (state_id,))
            existing_depth = 0
            if existing:
                existing_depth = int(existing[0].get('step_number', 0)
                                     if isinstance(existing[0], dict)
                                     else existing[0][0] or 0)

            if step_number >= existing_depth:
                self._gp.db.execute_query("""
                    INSERT OR REPLACE INTO world_model_states
                        (state_id, game_id, session_id, step_number,
                         objects_json, grid_hash, score, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    state_id, game_id, f"gen_{generation}_{agent_id[:8]}",
                    step_number, objects_json, '', 0.0,
                    _json.dumps({'generation': generation, 'agent_id': agent_id}),
                ))

            # Also persist distilled mechanics to learned_game_mechanics
            # for cross-game transfer learning
            self._persist_mechanics(causal_map, game_type, generation)

            if self._verbose:
                print(
                    f"    [PERSIST] Saved {len(causal_map._effects)} effects, "
                    f"{len(causal_map._rules)} rules, "
                    f"{len(causal_map._color_cycles)} color cycles"
                )
        except Exception as e:
            logger.debug(f"[PERSIST] Causal knowledge save failed: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # MECHANIC PERSISTENCE (cross-game transfer learning)
    # ═══════════════════════════════════════════════════════════════════

    def _persist_mechanics(
        self,
        causal_map,
        game_type: str,
        generation: int,
    ):
        """Distill and persist game mechanics for cross-game transfer.

        Extracts high-level mechanic types from the causal map and
        upserts them into learned_game_mechanics. These are then
        available to ALL agents playing ANY game, enabling inference
        like 'this new game might use toggle_neighbors because the
        spatial effects pattern matches FT09'.
        """
        try:
            # Ensure table exists (safe for first run)
            self._gp.db.execute_query("""
                CREATE TABLE IF NOT EXISTS learned_game_mechanics (
                    mechanic_id TEXT PRIMARY KEY,
                    game_type TEXT NOT NULL,
                    mechanic_type TEXT NOT NULL,
                    mechanic_data TEXT NOT NULL,
                    observation_count INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.5,
                    first_discovered_gen INTEGER DEFAULT 0,
                    last_confirmed_gen INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            mechanics_saved = 0

            # --- Color cycles -> 'color_cycle' mechanic ---
            if causal_map._color_cycles:
                # Find the most common cycle length
                cycle_lengths = [len(c) for c in causal_map._color_cycles.values() if c]
                if cycle_lengths:
                    common_len = max(set(cycle_lengths), key=cycle_lengths.count)
                    # Get unique colors involved
                    all_colors = set()
                    for cycle in causal_map._color_cycles.values():
                        all_colors.update(cycle)
                    mechanic_data = _json.dumps({
                        'cycle_length': common_len,
                        'colors_involved': sorted(all_colors),
                        'positions_with_cycles': len(causal_map._color_cycles),
                    })
                    self._upsert_mechanic(
                        game_type, 'color_cycle', mechanic_data,
                        len(causal_map._color_cycles), generation,
                    )
                    mechanics_saved += 1

            # --- Neighbor effects -> 'toggle_neighbors' mechanic ---
            # If clicking a position affects OTHER positions too
            multi_effect_count = sum(
                1 for e in causal_map._effects.values()
                if len(e.affected) > 1
            )
            if multi_effect_count > 0:
                # Analyze the neighbor pattern
                neighbor_offsets = []
                for e in causal_map._effects.values():
                    for affected_pos in e.affected:
                        if affected_pos != e.position:
                            dx = affected_pos[0] - e.position[0]
                            dy = affected_pos[1] - e.position[1]
                            neighbor_offsets.append((dx, dy))
                # Find most common offset pattern
                from collections import Counter
                offset_counts = Counter(neighbor_offsets)
                top_offsets = offset_counts.most_common(8)
                mechanic_data = _json.dumps({
                    'multi_effect_positions': multi_effect_count,
                    'common_offsets': [
                        {'dx': o[0], 'dy': o[1], 'count': c}
                        for o, c in top_offsets
                    ],
                })
                self._upsert_mechanic(
                    game_type, 'toggle_neighbors', mechanic_data,
                    multi_effect_count, generation,
                )
                mechanics_saved += 1

            # --- Walls -> 'wall_blocked' mechanic ---
            if causal_map._walls:
                mechanic_data = _json.dumps({
                    'wall_count': len(causal_map._walls),
                    'open_path_count': len(causal_map._open_paths),
                })
                self._upsert_mechanic(
                    game_type, 'wall_blocked', mechanic_data,
                    len(causal_map._walls), generation,
                )
                mechanics_saved += 1

            # --- Context-dependent effects -> 'context_dependent' mechanic ---
            if causal_map._context_effects:
                mechanic_data = _json.dumps({
                    'context_rule_count': len(causal_map._context_effects),
                    'context_prefixes': [
                        str(prefix)
                        for prefix in list(causal_map._context_effects.keys())[:10]
                    ],
                })
                self._upsert_mechanic(
                    game_type, 'context_dependent', mechanic_data,
                    len(causal_map._context_effects), generation,
                )
                mechanics_saved += 1

            # --- Surprise rate -> 'unpredictable_effects' mechanic ---
            if causal_map._surprise_log and causal_map.surprise_rate > 0.3:
                mechanic_data = _json.dumps({
                    'surprise_rate': round(causal_map.surprise_rate, 3),
                    'surprise_count': len(causal_map._surprise_log),
                })
                self._upsert_mechanic(
                    game_type, 'unpredictable_effects', mechanic_data,
                    len(causal_map._surprise_log), generation,
                )
                mechanics_saved += 1

            # --- Delayed effects -> 'delayed_effect' mechanic ---
            if causal_map._delayed_observations:
                mechanic_data = _json.dumps({
                    'delayed_observation_count': len(causal_map._delayed_observations),
                })
                self._upsert_mechanic(
                    game_type, 'delayed_effect', mechanic_data,
                    len(causal_map._delayed_observations), generation,
                )
                mechanics_saved += 1

            # --- Rules -> individual mechanic entries ---
            for rule in causal_map._rules:
                if rule.confidence > 0.4 and rule.evidence_count > 0:
                    # Skip action_effectiveness rules (those are per-game, not mechanics)
                    if rule.rule_type.startswith('action') or rule.rule_type.startswith('lesson_'):
                        continue
                    mechanic_data = _json.dumps({
                        'description': rule.description,
                        'parameters': rule.parameters,
                    })
                    self._upsert_mechanic(
                        game_type, f'rule_{rule.rule_type}', mechanic_data,
                        rule.evidence_count, generation,
                    )
                    mechanics_saved += 1

            if self._verbose and mechanics_saved > 0:
                print(f"    [MECHANICS] Persisted {mechanics_saved} mechanics for {game_type}")

        except Exception as e:
            logger.debug(f"[MECHANICS] Mechanic persistence failed: {e}")

    def _upsert_mechanic(
        self,
        game_type: str,
        mechanic_type: str,
        mechanic_data: str,
        observation_count: int,
        generation: int,
    ):
        """Upsert a single mechanic into learned_game_mechanics."""
        mechanic_id = f"{game_type}_{mechanic_type}"
        self._gp.db.execute_query("""
            INSERT INTO learned_game_mechanics
                (mechanic_id, game_type, mechanic_type, mechanic_data,
                 observation_count, confidence, first_discovered_gen,
                 last_confirmed_gen, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(mechanic_id) DO UPDATE SET
                mechanic_data = excluded.mechanic_data,
                observation_count = observation_count + excluded.observation_count,
                confidence = MIN(0.95, confidence + 0.05),
                last_confirmed_gen = excluded.last_confirmed_gen,
                updated_at = datetime('now')
        """, (
            mechanic_id, game_type, mechanic_type, mechanic_data,
            observation_count,
            min(0.8, 0.3 + observation_count * 0.05),
            generation, generation,
        ))

    # ═══════════════════════════════════════════════════════════════════
    # TIER 1 OBSERVATION LOGGING
    # ═══════════════════════════════════════════════════════════════════

    def _write_observation_record(
        self,
        agent_id: str,
        game_id: str,
        generation: int,
        step: int,
        level: int,
        action_type: int,
        action_data: Optional[dict],
        frame_changed: bool,
        cf: Optional[CognitiveFrame],
    ):
        """
        Write a structured observation record to the JSONL log.

        Tier 1 of the observation system: zero-infrastructure,
        immediate value. Produces a ring-buffer JSONL file that
        both humans and LLM can analyze after runs.
        """
        try:
            record = {
                'ts': datetime.now().isoformat(timespec='milliseconds'),
                'agent': agent_id[:12],
                'game': game_id[:8] if game_id else '',
                'gen': generation,
                'step': step,
                'level': level,
                'action': action_type,
            }
            if action_data:
                record['x'] = action_data.get('x')
                record['y'] = action_data.get('y')
            record['frame_chg'] = frame_changed

            if cf:
                record['strategy'] = cf.strategy
                record['speed'] = cf.action_speed
                record['rung'] = cf.rung_name or None
                record['confidence'] = round(cf.action_confidence, 3)
                record['map_pct'] = round(cf.map_completeness, 3)
                record['productive'] = cf.was_productive
                record['destructive'] = cf.was_destructive
                record['wasted'] = cf.was_wasted
                record['goal_delta'] = cf.goal_progress_delta
                record['goal_total'] = cf.goal_cells_total
                record['goal_correct'] = cf.goal_cells_correct
                record['pixels_chg'] = cf.pixels_changed
                record['surprise'] = round(cf.surprise, 3)
                record['hud_chg'] = cf.hud_state_changed
                record['timer'] = cf.timer_urgency

            # Append to ring-buffer log file
            with open(self._observation_log_path, 'a', encoding='utf-8') as f:
                f.write(_json.dumps(record, separators=(',', ':')) + '\n')

            # Ring-buffer: truncate when file exceeds max lines.
            # Use class-level counter (persists across games) to avoid
            # the step%1000 bug where step resets each game and never
            # reaches 1000 when max_actions < 1000.
            self._obs_writes_since_check += 1
            if self._obs_writes_since_check >= 5000:
                self._obs_writes_since_check = 0
                try:
                    with open(self._observation_log_path, 'r', encoding='utf-8') as rf:
                        lines = rf.readlines()
                    if len(lines) > self._observation_max_lines:
                        keep = lines[-self._observation_max_lines:]
                        with open(self._observation_log_path, 'w', encoding='utf-8') as wf:
                            wf.writelines(keep)
                except Exception:
                    pass

        except Exception:
            pass  # Never let logging crash the game loop

    # ═══════════════════════════════════════════════════════════════════
    # TIER 2 OBSERVATION: FRAME SNAPSHOTS (--observe flag)
    # ═══════════════════════════════════════════════════════════════════

    def _write_frame_snapshot(
        self,
        reason: str,
        agent_id: str,
        game_id: str,
        generation: int,
        step: int,
        level: int,
        frame: 'Optional[np.ndarray]',
        cf: Optional[CognitiveFrame],
    ):
        """
        Tier 2: Save a frame snapshot to the observation log.

        Only active when --observe flag is set. Captures the full
        frame grid (as a list-of-lists) at key moments:
        - Level-up: what the game looked like when we leveled up
        - Game-over: final state for post-mortem analysis
        - Every 20th action: periodic checkpoints

        These snapshots enable visual replay and LLM analysis of
        what the agent actually saw.
        """
        if not self._observe or frame is None:
            return
        try:
            record = {
                'ts': datetime.now().isoformat(timespec='milliseconds'),
                'type': 'frame_snapshot',
                'reason': reason,
                'agent': agent_id[:12],
                'game': game_id[:8] if game_id else '',
                'gen': generation,
                'step': step,
                'level': level,
            }
            # Convert frame to compact list-of-lists (int)
            if isinstance(frame, np.ndarray):
                record['frame'] = frame.tolist()
            elif isinstance(frame, list):
                record['frame'] = frame
            else:
                return  # Can't serialize, skip

            if cf:
                record['strategy'] = cf.strategy
                record['map_pct'] = round(cf.map_completeness, 3)

            with open(self._observation_log_path, 'a', encoding='utf-8') as f:
                f.write(_json.dumps(record, separators=(',', ':')) + '\n')

        except Exception:
            pass  # Never let snapshots crash the game loop

    @staticmethod
    def _compute_frame_hash(obs: Any) -> str:
        """Compute a hash of the observation frame for change detection.

        obs.frame can be:
          - np.ndarray (64x64)        -> hash directly
          - list wrapping an ndarray  -> unwrap, then hash
          - list of lists (raw ints)  -> convert to ndarray, then hash
          - None                      -> return empty string
        """
        import hashlib
        frame = getattr(obs, 'frame', None)
        if frame is None:
            return ''
        # Unwrap list-wrapped ndarray: [ndarray(64,64)] -> ndarray(64,64)
        if isinstance(frame, list):
            if len(frame) == 1 and isinstance(frame[0], np.ndarray):
                frame = frame[0]
            else:
                try:
                    frame = np.array(frame, dtype=np.uint8)
                except (ValueError, TypeError):
                    return hashlib.md5(str(frame).encode()).hexdigest()
        if isinstance(frame, np.ndarray):
            return hashlib.md5(frame.tobytes()).hexdigest()
        # Fallback for any other type
        return hashlib.md5(str(frame).encode()).hexdigest()

    @staticmethod
    def _get_frame_array(obs: Any) -> 'Optional[np.ndarray]':
        """Extract frame as numpy array from observation.

        Handles the common case where obs.frame is a list wrapping
        a single ndarray: [ndarray(64,64)] -> ndarray(64,64).
        """
        if obs is None:
            return None
        try:
            for attr in ('frame', 'grid', 'observation'):
                if hasattr(obs, attr):
                    data = getattr(obs, attr)
                    if isinstance(data, np.ndarray):
                        return data
                    if isinstance(data, list):
                        # Unwrap [ndarray] -> ndarray
                        if len(data) == 1 and isinstance(data[0], np.ndarray):
                            return data[0]
                        return np.array(data, dtype=np.uint8)
                    if hasattr(data, 'tolist'):
                        return np.array(data)
            return None
        except Exception:
            return None
