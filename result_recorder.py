#!/usr/bin/env python3
"""
ResultRecorder — stores game results in the database.

Extracted from EvolutionRunner._store_game_result (Phase 4.1 decomposition).
Receives ALL dependencies via constructor injection.
Does NOT create its own DB connections or engine instances.
"""

import os
import sys

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import Any, Optional

from database_interface import DatabaseInterface
from evolution_types import GameResult
from pipeline_assertions import PipelineAssertions


class ResultRecorder:
    """Stores game results and winning sequences in the database.

    All engine references are injected via the constructor.
    Handles the 4 independent DB writes + post-win processing.
    """

    def __init__(
        self,
        db: DatabaseInterface,
        pipe: PipelineAssertions,
        viral_package_engine: Any = None,
        games_as_teachers_engine: Any = None,
        verbose: bool = False,
    ):
        self.db = db
        self.pipe = pipe
        self.viral_package_engine = viral_package_engine
        self.games_as_teachers_engine = games_as_teachers_engine
        self.verbose = verbose

    def store_game_result(
        self,
        result: GameResult,
        current_generation: int,
        session_id: Optional[str],
        use_cognitive_router: bool = False,
        world_model: Optional[dict] = None,
    ) -> None:
        """Store game result in database.

        Args:
            result: The GameResult to persist.
            current_generation: Current generation number.
            session_id: Session ID from the game player (may be None).
            use_cognitive_router: Whether cognitive strategy was used.
            world_model: Optional world_model dict from ContextBuilder (Task A2).
        """
        # Use existing session from play_game (avoids orphan sessions)
        if not session_id:
            # Fallback: create session if play_game didn't
            session_id = str(uuid.uuid4())
            try:
                self.db.execute_query("""
                    INSERT INTO training_sessions (
                        session_id, game_id, start_time, mode, status, total_actions
                    ) VALUES (?, ?, datetime('now'), 'evolution', 'completed', ?)
                """, (session_id, result.game_id, result.actions_taken))
            except Exception:
                pass
        else:
            # Update existing session to completed with final action count
            try:
                self.db.execute_query("""
                    UPDATE training_sessions
                    SET status = 'completed', total_actions = ?
                    WHERE session_id = ?
                """, (result.actions_taken, session_id))
            except Exception:
                pass

        # Junction 1 fix: Separate dual writes into independent try blocks.
        # Previously both INSERTs were in one try block -- if agent_arc_performance
        # failed (e.g. FK violation, column mismatch), game_results was also lost.

        # WRITE 1: game_results
        try:
            self.db.execute_query("""
                INSERT INTO game_results (
                    game_id, session_id, start_time, end_time, status,
                    final_score, total_actions, win_detected,
                    level_completions, frame_changes,
                    coordinate_attempts, coordinate_successes, generation
                ) VALUES (?, ?, datetime('now'), datetime('now'), 'completed',
                          ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.game_id,
                session_id,
                result.score,
                result.actions_taken,
                result.is_win,
                result.levels_completed,
                getattr(result, 'frame_changes', 0),
                getattr(result, 'coordinate_attempts', 0),
                getattr(result, 'coordinate_successes', 0),
                current_generation,
            ))
        except Exception as e:
            print(f"  [PIPE-BREAK] game_results INSERT failed: {e}")

        # WRITE 2: agent_arc_performance (independent -- one failure can't kill both)
        # CRITICAL: Without this, evolutionary_engine._calculate_standard_fitness()
        # returns 0.0 for ALL agents. Evolution becomes pure random drift.
        try:
            efficiency = result.score / max(1, result.actions_taken)
            level_bonus = result.levels_completed * 0.1
            win_bonus = 1.0 if result.is_win else 0.0
            total_reward = result.score + win_bonus + efficiency + level_bonus

            self.db.execute_query("""
                INSERT INTO agent_arc_performance (
                    performance_id, agent_id, game_id, session_id, game_timestamp,
                    final_score, win_score_threshold, win_achieved, total_actions,
                    score_efficiency, win_proximity, level_progressions,
                    strategy_used, genome_config,
                    base_reward, win_bonus, efficiency_bonus,
                    level_progression_bonus, total_evolutionary_reward
                ) VALUES (?, ?, ?, ?, datetime('now'),
                          ?, ?, ?, ?,
                          ?, ?, ?,
                          ?, ?,
                          ?, ?, ?,
                          ?, ?)
            """, (
                str(uuid.uuid4()),
                result.agent_id,
                result.game_id,
                session_id,
                result.score,
                1.0,  # win threshold = perfect score (all levels)
                result.is_win,
                result.actions_taken,
                efficiency,
                result.score,  # win_proximity = score / 1.0
                result.levels_completed,
                'cognitive' if use_cognitive_router else 'ladder',
                '{}',
                result.score,  # base_reward
                win_bonus,
                efficiency,
                level_bonus,
                total_reward,
            ))
        except Exception as e:
            print(f"  [PIPE-BREAK] agent_arc_performance INSERT failed: {e}")

        # WRITE 2b: agent_game_diversity UPSERT (feeds 40% diversity fitness)
        # Without this, _calculate_diversity_fitness_component() returns 0.0
        # for ALL agents. 40% of evolution signal is dead.
        try:
            self.db.execute_query("""
                INSERT INTO agent_game_diversity (
                    agent_id, game_id, attempts, first_attempt_score,
                    best_score, last_attempt_score, is_novel_game,
                    few_shot_improvement, last_played
                ) VALUES (?, ?, 1, ?, ?, ?, 1, 0.0, datetime('now'))
                ON CONFLICT(agent_id, game_id) DO UPDATE SET
                    attempts = agent_game_diversity.attempts + 1,
                    last_attempt_score = excluded.last_attempt_score,
                    best_score = MAX(agent_game_diversity.best_score, excluded.best_score),
                    is_novel_game = 0,
                    few_shot_improvement = CASE
                        WHEN agent_game_diversity.attempts = 1
                        THEN excluded.last_attempt_score - agent_game_diversity.first_attempt_score
                        ELSE agent_game_diversity.few_shot_improvement
                    END,
                    last_played = datetime('now')
            """, (
                result.agent_id,
                result.game_id,
                result.score,
                result.score,
                result.score,
            ))
        except Exception as e:
            print(f"  [PIPE-BREAK] agent_game_diversity UPSERT failed: {e}")

        # Pipeline assertion: verify BOTH writes landed
        self.pipe.assert_game_result_stored(session_id, result.game_id, result.agent_id)

        # Task A2: Persist world_model state to world_model_states table
        if world_model and isinstance(world_model, dict):
            self._persist_world_model(
                game_id=result.game_id,
                session_id=session_id or 'unknown',
                actions_taken=result.actions_taken,
                score=result.score,
                world_model=world_model,
            )

        # Phase 6A (Affinity): Update domain alignment history for this agent/game
        self._update_domain_alignment(
            result.agent_id, result.game_id,
            result.score, result.actions_taken, current_generation,
        )

        # Store winning sequence if won
        if result.is_win and result.action_sequence:
            self._store_winning_sequences(
                result, current_generation, session_id,
            )

    # ------------------------------------------------------------------
    # Phase 6A (Affinity): Domain Alignment Tracking
    # ------------------------------------------------------------------
    def _update_domain_alignment(
        self,
        agent_id: str,
        game_id: str,
        score: float,
        actions_taken: int,
        generation: int,
    ) -> None:
        """Track which game worlds this agent has encountered and how quickly it aligned.

        Updates the agent's domain_alignment_history JSON list:
          - On first encounter with a game_id: appends a new entry.
          - On first positive score: records actions_to_first_score
            (the alignment velocity numerator for this game).

        Non-critical: failures here never block game result storage.
        """
        try:
            history = self.db.get_agent_domain_alignment_history(agent_id)

            existing = next((d for d in history if d.get('game_id') == game_id), None)
            if existing is None:
                # First encounter with this game
                entry = {
                    'game_id': game_id,
                    'first_encounter_gen': generation,
                    'actions_to_first_score': actions_taken if score > 0 else None,
                    'first_positive_score': score if score > 0 else None,
                    'encounters': 1,
                }
                history.append(entry)
            else:
                existing['encounters'] = existing.get('encounters', 0) + 1
                if existing.get('actions_to_first_score') is None and score > 0:
                    # Just achieved first positive score on this game
                    existing['actions_to_first_score'] = actions_taken
                    existing['first_positive_score'] = score

            self.db.update_agent_domain_alignment_history(agent_id, history)

        except Exception as e:
            if self.verbose:
                print(f"    [AFFINITY-ERR] domain alignment update failed: {e}")

    # ------------------------------------------------------------------
    # Task A2: World Model Persistence
    # ------------------------------------------------------------------
    def _persist_world_model(
        self,
        game_id: str,
        session_id: str,
        actions_taken: int,
        score: float,
        world_model: dict,
    ) -> None:
        """Persist world_model causal_map and rules_learned to world_model_states.

        Serializes the causal_map and rules_learned as JSON and stores them
        in the world_model_states table. This allows future game sessions to
        seed their world model with previously learned causal knowledge.

        Non-critical: failures here never block game result storage.
        """
        try:
            import hashlib

            # Deterministic state_id per game_id: INSERT OR REPLACE
            # keeps exactly ONE row per game, preventing unbounded
            # growth (previously created ~20 MB/session with random UUIDs).
            state_id = f"wm_{game_id}"

            # Extract the key data to persist
            causal_map = world_model.get('causal_map', {})
            rules_learned = world_model.get('rules_learned', [])
            symbolic_state = world_model.get('symbolic_state')

            # Serialize objects_json: causal_map + rules_learned + H38 data
            no_effect_positions = world_model.get('no_effect_positions', {})
            objects_payload = {
                'causal_map': causal_map,
                'rules_learned': rules_learned,
                'no_effect_positions': no_effect_positions,
            }
            objects_json = json.dumps(objects_payload, default=str)

            # Compute grid_hash from causal_map keys for quick lookup
            map_keys = sorted(causal_map.keys()) if causal_map else []
            grid_hash = hashlib.md5(
                json.dumps(map_keys).encode()
            ).hexdigest()[:16] if map_keys else 'empty'

            # Metadata: symbolic engine state + action history summary
            metadata_payload = {}
            if symbolic_state:
                metadata_payload['symbolic_state'] = symbolic_state
            action_history = world_model.get('action_history', [])
            if action_history:
                metadata_payload['action_count'] = len(action_history)
                metadata_payload['last_actions'] = action_history[-5:]
            metadata_json = json.dumps(metadata_payload, default=str)

            self.db.execute_query("""
                INSERT OR REPLACE INTO world_model_states (
                    state_id, game_id, session_id, step_number,
                    objects_json, grid_hash, score, metadata,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                state_id,
                game_id,
                session_id,
                actions_taken,
                objects_json,
                grid_hash,
                score,
                metadata_json,
            ))
            if self.verbose:
                print(f"    [WM-SAVE] World model persisted: {state_id[:16]} "
                      f"({len(causal_map)} causal entries, {len(rules_learned)} rules)")
        except Exception as e:
            if self.verbose:
                print(f"    [WM-ERR] World model persistence failed: {e}")

    def _store_winning_sequences(
        self,
        result: GameResult,
        current_generation: int,
        session_id: str,
    ) -> None:
        """Store winning sequences and trigger post-win processing."""
        sequence_id = f"seq_{uuid.uuid4().hex[:12]}"
        game_type = result.game_id[:4] if len(result.game_id) >= 4 else result.game_id

        # WRITE 3: winning_sequences (partial)
        try:
            self.db.execute_query("""
                INSERT INTO winning_sequences (
                    sequence_id, game_id, game_type, level_number,
                    action_sequence, total_actions, total_score, efficiency_score,
                    agent_id, session_id, generation_discovered, is_active,
                    initial_frame, final_frame, discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', '[]', datetime('now'))
            """, (
                sequence_id,
                result.game_id,
                game_type,
                result.levels_completed,
                json.dumps(result.action_sequence),
                result.actions_taken,
                result.score,
                result.score / max(1, result.actions_taken),
                result.agent_id,
                session_id,
                current_generation,
            ))
            print(f"    [SAVED] Winning sequence {sequence_id[:12]} for {result.game_id}")
        except Exception as e:
            print(f"  [PIPE-BREAK] winning_sequences INSERT failed: {e}")

        # WRITE 4: winning_sequences_full_game (Junction 6 fix)
        if result.levels_completed >= result.total_levels:
            try:
                full_seq_id = f"fseq_{uuid.uuid4().hex[:12]}"
                self.db.execute_query("""
                    INSERT INTO winning_sequences_full_game (
                        sequence_id, game_id, total_levels,
                        agent_id, session_id, action_sequence,
                        total_actions, total_score, efficiency_score,
                        game_type, generation_discovered, is_active,
                        discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
                """, (
                    full_seq_id,
                    result.game_id,
                    result.total_levels,
                    result.agent_id,
                    session_id,
                    json.dumps(result.action_sequence),
                    result.actions_taken,
                    result.score,
                    result.score / max(1, result.actions_taken),
                    game_type,
                    current_generation,
                ))
                print(f"    [SAVED] Full-game sequence {full_seq_id[:12]} "
                      f"for {result.game_id} (replay path now active)")
            except Exception as fge:
                print(f"    [PIPE-BREAK] winning_sequences_full_game INSERT failed: {fge}")

        # Pipeline assertion: ALWAYS fires (outside all try blocks)
        self.pipe.assert_win_sequence_stored(
            result.game_id, session_id,
            is_full_game_win=(result.levels_completed >= result.total_levels),
        )

        # Non-critical post-win processing (viral packages, lessons)
        self._post_win_processing(result, sequence_id, game_type, current_generation)

        # Phase 2.2: Sequence generalization trigger
        self._try_sequence_generalization(result, game_type)

    def _post_win_processing(
        self,
        result: GameResult,
        sequence_id: str,
        game_type: str,
        current_generation: int,
    ) -> None:
        """Non-critical viral package creation and lesson extraction."""
        if self.viral_package_engine:
            try:
                package_id = self.viral_package_engine.create_viral_package_from_sequence(
                    sequence_id=sequence_id,
                    agent_id=result.agent_id,
                    generation=current_generation,
                    skip_if_exists=True
                )
                if package_id:
                    print(f"    [VIRAL] Created package {package_id[:12]} for network sharing")
            except Exception as vpe:
                if self.verbose:
                    print(f"    [VIRAL-ERR] Could not create package: {vpe}")

        if self.games_as_teachers_engine:
            try:
                action_ints = []
                for act in result.action_sequence:
                    if isinstance(act, str) and act.startswith('ACTION'):
                        action_ints.append(int(act.replace('ACTION', '')))
                    elif isinstance(act, int):
                        action_ints.append(act)

                lesson = self.games_as_teachers_engine.extract_lesson(
                    game_type=game_type,
                    level_number=result.levels_completed,
                    winning_sequence=action_ints,
                    frame_history=None,
                    working_theory=None
                )
                if lesson:
                    concept = lesson.get('concept_demonstrated', 'unknown')
                    print(f"    [LESSON] Concept demonstrated: {concept}")
            except Exception as le:
                if self.verbose:
                    print(f"    [LESSON-ERR] Could not extract lesson: {le}")

    def _try_sequence_generalization(
        self,
        result: GameResult,
        game_type: str,
    ) -> None:
        """Phase 2.2: Sequence generalization trigger.

        When 3+ winning sequences exist for this game_type/level,
        extract invariant/variant structure into sequence_concepts.
        Non-critical: failures here never block gameplay.
        """
        try:
            seq_count_row = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM winning_sequences
                WHERE game_type = ? AND level_number = ? AND is_active = 1
            """, (game_type, result.levels_completed))
            seq_count = seq_count_row[0]['cnt'] if seq_count_row else 0

            if seq_count >= 3:
                from engines.social.package_compressor import PackageCompressor
                compressor = PackageCompressor(self.db)
                gen_stats = compressor.compress_winning_sequences(
                    game_type=game_type,
                    similarity_threshold=0.85,
                    min_cluster_size=3,
                )
                if gen_stats.get('concepts_created', 0) > 0:
                    print(f"    [GENERALIZE] {gen_stats['concepts_created']} "
                          f"concept(s) from {seq_count} sequences for {game_type}")
        except Exception as ge:
            if self.verbose:
                print(f"    [GENERALIZE-ERR] Sequence generalization failed: {ge}")
