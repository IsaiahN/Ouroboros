#!/usr/bin/env python3
"""
Pariah Manager - Failure Pattern Management
============================================
Manages pariah patterns (failure patterns that agents learn to avoid).

Extracted from viral_package_engine.py for better organization.
Pariahs = Negative Selection (patterns to avoid, spread like warnings)

Theory (from agi_unified_theory.md):
- Pariahs mark failure patterns for the network to avoid
- toxicity(t) = initial_toxicity x (1 - decay_rate x generations_since_trigger)
- Without decay, ancient pariahs accumulate infinitely and agents become paralyzed
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

import json
import uuid
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface
from engines.engine_logger import get_engine_logger, log_silent_failure

logger = get_engine_logger("pariah_manager")


class PariahManager:
    """
    Manages failure patterns (pariahs) for the network.

    Pariahs are failure patterns that spread like warnings - teaching
    agents what NOT to do. They have toxicity that decays over time
    to prevent analysis paralysis.
    """

    def __init__(self, db: DatabaseInterface):
        """
        Initialize pariah manager.

        Args:
            db: Database interface for persistence
        """
        self.db = db
        self._ensure_pariah_level_column()

    # ========================================================================
    # SCHEMA MIGRATION / SETUP
    # ========================================================================

    def _ensure_pariah_level_column(self):
        """
        Ensure pariahs have source_level_number and backfill existing ones.

        Backfill logic: Use game's max completed level as the source level.
        Example: If as66 has been beaten to level 4, all as66 pariahs get source_level_number=4.
        This means on level 5 (frontier), those pariahs apply at only 5% strength.
        """
        # Allow quick-start/test mode to skip potentially heavy backfill
        if os.getenv("OUROBOROS_SKIP_PARIAH_BACKFILL") == "1":
            return
        try:
            # Check if column exists
            self.db.execute_query("SELECT source_level_number FROM pariahs LIMIT 1")
        except Exception:
            # Column doesn't exist - add it
            try:
                self.db.execute_query("""
                    ALTER TABLE pariahs ADD COLUMN source_level_number INTEGER DEFAULT 1
                """)
                logger.info("Added source_level_number column to pariahs table")
            except Exception as e:
                # Column already exists - this is expected
                logger.debug("source_level_number column already exists", detail=str(e))

        # Only backfill pariahs that still have source_level_number = 1 (default/unknown)
        # Use game's max beaten level as the assumed source level
        try:
            # First, count how many need updating
            need_update = self.db.execute_query("""
                SELECT COUNT(*) as cnt FROM pariahs
                WHERE source_level_number = 1
                AND source_game_id IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM game_results gr2
                    WHERE gr2.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                    AND gr2.level_completions > 1
                )
            """)

            if need_update and need_update[0].get('cnt', 0) > 0:
                # Only update and print if there are actually pariahs to backfill
                self.db.execute_query("""
                    UPDATE pariahs
                    SET source_level_number = (
                        SELECT COALESCE(MAX(gr.level_completions), 1)
                        FROM game_results gr
                        WHERE gr.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                        AND gr.level_completions > 0
                    )
                    WHERE source_level_number = 1
                    AND source_game_id IS NOT NULL
                    AND EXISTS (
                        SELECT 1 FROM game_results gr2
                        WHERE gr2.game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                        AND gr2.level_completions > 1
                    )
                """)
                logger.info(f"Backfilled {need_update[0]['cnt']} pariahs with source_level_number")
        except Exception as e:
            log_silent_failure(logger, "pariah_backfill", e, {"operation": "source_level_number backfill"})

    # ========================================================================
    # PARIAH CREATION
    # ========================================================================

    def create_pariah_from_failure(self,
                                   game_id: str,
                                   agent_id: str,
                                   failed_actions: List[int],
                                   failed_coordinates: List[Tuple[int, int]],
                                   final_score: float,
                                   generation: int,
                                   source_level_number: int = 1) -> Optional[str]:
        """
        Create a pariah (failure pattern) from a failed game.

        This extracts the failure pattern so the network can learn to avoid it.

        FIXED (2025-12-06): Now generates specific, actionable failure descriptions
        instead of generic "Failed with score X" messages. Pariahs are also marked
        as active and set to influence action selection.

        FIXED (2025-12-26): Added source_level_number for level-scoped pariah penalties.
        Pariahs from beaten levels apply weakly to frontier levels.

        Args:
            game_id: Game where failure occurred
            agent_id: Agent who failed
            failed_actions: Action sequence that failed
            failed_coordinates: Coordinate sequence that failed
            final_score: Final score (low = worse failure)
            generation: Current generation
            source_level_number: Level where failure occurred (for level-scoped penalties)

        Returns:
            pariah_id if created, None if failed
        """
        # Only create pariahs for severe failures (score < 1.0)
        if final_score >= 1.0:
            return None

        pariah_id = f"pariah_{uuid.uuid4().hex[:12]}"

        try:
            # Calculate toxicity based on how badly it failed
            toxicity = max(0.0, min(1.0, 1.0 - (final_score / 10.0)))  # 0 score = 1.0 toxicity

            # Generate specific failure description
            failure_description = self._analyze_failure_pattern(failed_actions, failed_coordinates, final_score)

            # Add source_level_number column if it doesn't exist (migration)
            try:
                self.db.execute_query("""
                    ALTER TABLE pariahs ADD COLUMN source_level_number INTEGER DEFAULT 1
                """)
                # Backfill existing pariahs using game's max completed level
                self.db.execute_query("""
                    UPDATE pariahs
                    SET source_level_number = COALESCE(
                        (SELECT MAX(level_completions)
                         FROM game_results
                         WHERE game_id LIKE substr(pariahs.source_game_id, 1, 4) || '%'
                         AND level_completions > 0),
                        1
                    )
                    WHERE source_level_number IS NULL OR source_level_number = 1
                """)
            except Exception as e:
                # Column may already exist - expected during normal operation
                logger.debug("pariah source_level_number update skipped", detail=str(e))

            self.db.execute_query("""
                INSERT INTO pariahs (
                    pariah_id, pariah_name, pariah_type,
                    action_sequence, coordinate_pattern, failure_description,
                    toxicity, detection_difficulty, context_specificity,
                    trigger_count, avg_score_loss,
                    discovery_generation, source_game_id, source_agent_id, source_level_number,
                    is_active, last_triggered_generation, avoidance_success_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pariah_id,
                f"Pariah_{game_id[:8]}_L{source_level_number}_{generation}",
                'action_sequence',
                json.dumps(failed_actions),
                json.dumps(failed_coordinates),
                failure_description,  # Now specific instead of generic
                toxicity,
                0.3,  # Initial detection difficulty
                0.5,  # Initial context specificity
                1,  # trigger_count (this failure)
                10.0 - final_score,  # avg_score_loss
                generation,
                game_id,
                agent_id,
                source_level_number,  # NEW: Level where failure occurred
                True,  # is_active
                generation,
                0.0  # No avoidance data yet
            ))

            # Make discoverer aware of this pariah
            self._make_agent_aware_of_pariah(agent_id, pariah_id, generation, 'self_discovery', None)

            return pariah_id

        except Exception as e:
            logger.error("Error creating pariah", exc=e)
            return None

    def _analyze_failure_pattern(
        self,
        failed_actions: List[int],
        failed_coordinates: List[Tuple[int, int]],
        final_score: float
    ) -> str:
        """
        Analyze a failure to generate a specific, actionable description.

        ADDED (2025-12-06): Pariahs need specific descriptions to be useful.
        This analyzes the action pattern to identify common failure modes:
        - Oscillation (repeated back-and-forth)
        - Edge trapping (stuck at boundaries)
        - Inefficiency (too many actions without progress)
        - Specific action overuse

        Returns:
            Specific failure description for network learning
        """
        if not failed_actions:
            return f"Empty action sequence, score {final_score:.2f}"

        descriptions = []

        # Detect oscillation (e.g., up-down-up-down or left-right-left-right)
        oscillation_count = 0
        for i in range(len(failed_actions) - 2):
            if failed_actions[i] == failed_actions[i + 2] and failed_actions[i] != failed_actions[i + 1]:
                oscillation_count += 1

        if oscillation_count >= 3:
            descriptions.append(f"oscillation detected ({oscillation_count} reversals)")

        # Detect action overuse (>40% same action)
        action_counts = Counter(failed_actions)
        most_common_action, most_common_count = action_counts.most_common(1)[0]
        if most_common_count / len(failed_actions) > 0.4:
            action_names = {1: 'up', 2: 'down', 3: 'left', 4: 'right', 5: 'wait', 6: 'click', 7: 'submit'}
            action_name = action_names.get(most_common_action, f'action{most_common_action}')
            descriptions.append(f"overused {action_name} ({most_common_count}/{len(failed_actions)} actions)")

        # Detect edge trapping from coordinates
        if failed_coordinates:
            x_coords = [c[0] for c in failed_coordinates if c]
            y_coords = [c[1] for c in failed_coordinates if c]

            if x_coords and y_coords:
                # Check if stuck at edges (0 or max values repeated)
                edge_x = sum(1 for x in x_coords if x <= 1 or x >= 28) / len(x_coords)
                edge_y = sum(1 for y in y_coords if y <= 1 or y >= 28) / len(y_coords)

                if edge_x > 0.5:
                    if sum(1 for x in x_coords if x <= 1) > sum(1 for x in x_coords if x >= 28):
                        descriptions.append("trapped at left edge")
                    else:
                        descriptions.append("trapped at right edge")
                if edge_y > 0.5:
                    if sum(1 for y in y_coords if y <= 1) > sum(1 for y in y_coords if y >= 28):
                        descriptions.append("trapped at top edge")
                    else:
                        descriptions.append("trapped at bottom edge")

        # Detect inefficiency (many actions, no progress)
        if len(failed_actions) > 50 and final_score < 0.5:
            descriptions.append(f"inefficient ({len(failed_actions)} actions for score {final_score:.1f})")

        # Combine descriptions or use default
        if descriptions:
            return f"FAILURE: {'; '.join(descriptions)}"
        else:
            return f"Unknown failure pattern, score {final_score:.2f}, {len(failed_actions)} actions"

    # ========================================================================
    # PARIAH AWARENESS / SPREADING
    # ========================================================================

    def _make_agent_aware_of_pariah(self,
                                    agent_id: str,
                                    pariah_id: str,
                                    generation: int,
                                    source: str,
                                    learned_from: Optional[str]):
        """
        Make an agent aware of a failure pattern.

        Args:
            agent_id: Agent to make aware
            pariah_id: Pariah they should know about
            generation: Current generation
            source: 'self_discovery', 'horizontal_transfer', 'inheritance'
            learned_from: Agent who taught them (if horizontal_transfer)
        """
        try:
            self.db.execute_query("""
                INSERT OR REPLACE INTO agent_pariah_awareness (
                    agent_id, pariah_id,
                    awareness_generation, awareness_source, learned_from_agent,
                    awareness_level, avoidance_priority,
                    is_active, last_encountered_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, pariah_id,
                generation, source, learned_from,
                0.8 if source == 'self_discovery' else 0.6,  # Discoverers are more aware
                0.7 if source == 'self_discovery' else 0.5,
                True,
                generation
            ))

            # Update pariah awareness count
            self.db.execute_query("""
                UPDATE pariahs
                SET total_awareness = total_awareness + 1,
                    active_awareness = active_awareness + 1
                WHERE pariah_id = ?
            """, (pariah_id,))

        except Exception as e:
            logger.error("Error making agent aware", agent_id=agent_id, pariah_id=pariah_id, exc=e)

    def spread_pariah_awareness(self,
                               pariah_id: str,
                               from_agent_id: str,
                               to_agent_id: str,
                               generation: int) -> bool:
        """
        Spread pariah awareness from one agent to another (horizontal transfer).

        Like warning others about danger - "Don't try this, it failed for me!"

        Args:
            pariah_id: Pariah to warn about
            from_agent_id: Agent spreading awareness
            to_agent_id: Agent learning about pariah
            generation: Current generation

        Returns:
            True if awareness spread, False if already aware or failed
        """
        # Check if already aware
        existing = self.db.execute_query("""
            SELECT * FROM agent_pariah_awareness
            WHERE agent_id = ? AND pariah_id = ? AND is_active = TRUE
        """, (to_agent_id, pariah_id))

        if existing:
            return False  # Already aware

        # Make agent aware
        self._make_agent_aware_of_pariah(to_agent_id, pariah_id, generation, 'horizontal_transfer', from_agent_id)

        return True

    # ========================================================================
    # PARIAH PENALTIES / ACTION WEIGHTS
    # ========================================================================

    def get_pariah_action_penalties(self, agent_id: str,
                                     game_id: str = None,
                                     current_level: int = None) -> Dict[int, float]:
        """
        Get action penalties from pariahs this agent is aware of.

        FIXED (2025-12-26): Now applies level-aware decay.
        Pariahs from beaten levels apply weakly to frontier levels.

        Level Decay Logic:
        - Same level as pariah source: 100% penalty
        - Adjacent level (+/- 1): 40% penalty
        - 2+ levels away: 15% penalty
        - On frontier AND pariah from beaten level: 5% penalty (just a hint)

        Args:
            agent_id: Agent to get penalties for
            game_id: Current game (for level context)
            current_level: Current level number (for decay calculation)

        Returns:
            Dict mapping action_id -> penalty (higher = avoid this action more)
        """
        # Get max beaten level for this game (to detect frontier)
        max_beaten_level = 0
        if game_id:
            try:
                result = self.db.execute_query("""
                    SELECT MAX(level_completions) as max_level
                    FROM game_results
                    WHERE game_id LIKE ? AND level_completions > 0
                """, (f"{game_id[:4]}%",))
                if result and result[0].get('max_level'):
                    max_beaten_level = result[0]['max_level']
            except Exception as e:
                log_silent_failure(logger, "max_beaten_level_query", e, {"game_id": game_id})

        is_frontier = current_level is not None and current_level > max_beaten_level

        # Get all pariahs this agent is aware of (with level info)
        awareness = self.db.execute_query("""
            SELECT
                pa.pariah_id,
                pa.awareness_level,
                pa.avoidance_priority,
                p.action_sequence,
                p.toxicity,
                p.source_game_id,
                COALESCE(p.source_level_number, 1) as source_level_number
            FROM agent_pariah_awareness pa
            JOIN pariahs p ON pa.pariah_id = p.pariah_id
            WHERE pa.agent_id = ? AND pa.is_active = TRUE AND p.is_active = TRUE
        """, (agent_id,))

        action_penalties = {}

        for aware in awareness:
            # Parse action sequence
            try:
                actions = json.loads(aware['action_sequence'])

                # Base penalty from awareness, priority, and toxicity
                base_penalty = (aware['awareness_level'] *
                               aware['avoidance_priority'] *
                               aware['toxicity'])

                # ============================================================
                # LEVEL-AWARE DECAY (2025-12-26)
                # Pariahs from beaten levels shouldn't block frontier exploration
                # ============================================================
                level_decay = 1.0  # Default: full penalty

                pariah_game_id = aware.get('source_game_id', '')
                pariah_level = aware.get('source_level_number', 1)

                # Only apply level decay if we have context AND same game
                if current_level is not None and game_id and pariah_game_id:
                    # Check if pariah is from same game type
                    same_game = (game_id[:4] == pariah_game_id[:4])

                    if same_game:
                        level_distance = abs(current_level - pariah_level)

                        if is_frontier and pariah_level <= max_beaten_level:
                            # On frontier, pariahs from beaten territory = very weak
                            level_decay = 0.05  # 5% - just a faint hint
                        elif level_distance == 0:
                            # Same level - full penalty
                            level_decay = 1.0
                        elif level_distance == 1:
                            # Adjacent level - moderate decay
                            level_decay = 0.4
                        else:
                            # 2+ levels away - heavy decay
                            level_decay = 0.15
                    else:
                        # Different game entirely - weak cross-game hint
                        level_decay = 0.1

                # Apply decayed penalty
                final_penalty = base_penalty * level_decay

                # FIX: Use SET of unique actions to avoid over-penalizing
                # sequences like [6,6,6...6] 100 times which was adding 100x penalty!
                unique_actions = set(actions)
                for action in unique_actions:
                    action_penalties[action] = action_penalties.get(action, 0.0) + final_penalty

            except (json.JSONDecodeError, TypeError):
                continue

        # ====================================================================
        # ESSENTIAL ACTION PROTECTION
        # If an action appears in winning sequences for this game, reduce penalty
        # This prevents blocking actions that are CORE to winning the game
        # Example: VC33 uses ACTION6 as the primary mechanic - can't penalize it
        # ====================================================================
        if game_id and action_penalties:
            try:
                # Get winning sequences for this game type
                winning_seqs = self.db.execute_query("""
                    SELECT action_sequence
                    FROM winning_sequences
                    WHERE game_id LIKE ? AND is_active = 1
                    LIMIT 20
                """, (f"{game_id[:4]}%",))

                if winning_seqs:
                    # Count action frequency in winning sequences
                    action_in_wins = {}
                    total_wins = len(winning_seqs)

                    for seq in winning_seqs:
                        try:
                            actions = json.loads(seq['action_sequence'])
                            unique = set(actions)
                            for a in unique:
                                action_in_wins[a] = action_in_wins.get(a, 0) + 1
                        except (json.JSONDecodeError, TypeError, KeyError):
                            continue

                    # If action appears in >50% of winning sequences, reduce penalty by 90%
                    for action, penalty in list(action_penalties.items()):
                        win_count = action_in_wins.get(action, 0)
                        if total_wins > 0 and win_count / total_wins > 0.5:
                            # This action is ESSENTIAL - almost always in wins
                            action_penalties[action] = penalty * 0.1  # 90% reduction
                        elif total_wins > 0 and win_count / total_wins > 0.25:
                            # Action appears often in wins - moderate reduction
                            action_penalties[action] = penalty * 0.3  # 70% reduction

            except Exception as e:
                log_silent_failure(logger, "win_sequence_check", e, {"game_id": game_id})

        return action_penalties

    def get_role_adjusted_pariah_penalties(
        self,
        agent_id: str,
        agent_role: str = 'generalist',
        game_id: str = None,
        level_number: int = None
    ) -> Dict[int, float]:
        """
        Get pariah penalties adjusted for agent role (pariah tolerance).

        Per Master Ruleset:
        - Exploiters and Optimizers should have immunity/tolerance to pariahs
        - This prevents analysis paralysis on well-explored games

        Role Tolerance Levels:
        - exploiter: 0.8 (80% pariah penalty ignored)
        - optimizer: 0.6 (60% penalty ignored)
        - pioneer: 0.3 (30% penalty ignored - still cautious on frontier)
        - generalist: 0.0 (full penalty applied)

        Args:
            agent_id: Agent to get penalties for
            agent_role: Agent's current role
            game_id: Optional - for network paralysis boost
            level_number: Optional - for level-specific paralysis detection

        Returns:
            Dict mapping action_id -> adjusted_penalty
        """
        # Role-based pariah tolerance
        ROLE_TOLERANCE = {
            'exploiter': 0.8,   # Nearly immune - meant to break through
            'optimizer': 0.6,   # Significant immunity - refining known paths
            'pioneer': 0.3,     # Some tolerance - exploring frontier
            'generalist': 0.0   # Full sensitivity - maintains network wisdom
        }

        base_tolerance = ROLE_TOLERANCE.get(agent_role.lower(), 0.0)

        # Check for network-level paralysis on this game/level
        paralysis_boost = 0.0
        if game_id and level_number:
            paralysis_boost = self._detect_network_paralysis(game_id, level_number)

        # Combined tolerance (capped at 0.95 - always some caution)
        final_tolerance = min(0.95, base_tolerance + paralysis_boost)

        # Get base penalties
        base_penalties = self.get_pariah_action_penalties(agent_id, game_id, level_number)

        # Apply role tolerance (reduce penalties by tolerance %)
        adjusted_penalties = {
            action: penalty * (1.0 - final_tolerance)
            for action, penalty in base_penalties.items()
        }

        return adjusted_penalties

    def _detect_network_paralysis(self, game_id: str, level_number: int,
                                   window_generations: int = 10) -> float:
        """
        Detect if the network is paralyzed on this game/level.

        Network paralysis = many agents attempting but none succeeding,
        potentially because pariah penalties are blocking valid strategies.

        Returns:
            Bonus tolerance to add (0.0 - 0.3) based on paralysis severity
        """
        try:
            # Count recent attempts vs successes on this level
            stats = self.db.execute_query("""
                SELECT
                    COUNT(DISTINCT agent_id) as unique_agents,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN level_completions >= ? THEN 1 ELSE 0 END) as successes
                FROM game_results
                WHERE game_id LIKE ?
                AND generation >= (SELECT MAX(generation) FROM game_results) - ?
            """, (level_number, f"{game_id[:4]}%", window_generations))

            if not stats or not stats[0]:
                return 0.0

            s = stats[0]
            unique_agents = s.get('unique_agents', 0) or 0
            total_attempts = s.get('total_attempts', 0) or 0
            successes = s.get('successes', 0) or 0

            # If many agents trying but zero successes, network may be paralyzed
            if unique_agents >= 5 and total_attempts >= 10 and successes == 0:
                # Scale boost by severity
                paralysis_severity = min(1.0, total_attempts / 50.0)
                return 0.3 * paralysis_severity  # Up to 0.3 extra tolerance

            return 0.0

        except Exception as e:
            logger.warning("Paralysis detection error", exc=e)
            return 0.0

    # ========================================================================
    # PARIAH LIFECYCLE (DECAY / OBSOLESCENCE)
    # ========================================================================

    def check_pariah_obsolescence(self, generation: int, threshold_generations: int = 30):
        """
        Check if any pariahs have become obsolete.

        CRITICAL FIX: Decay runs FIRST on ALL pariahs, then obsolescence check runs AFTER.
        Per agi_unified_theory.md: "Forgetting is not a bug - it's essential for intelligence."

        Pariahs are only marked obsolete if:
        1. Toxicity has decayed to minimum (0.1) AND
        2. Not triggered in threshold_generations (50+ gens)

        Low-toxicity pariahs remain ACTIVE to provide weak warnings.
        """
        # STEP 1: Apply toxicity decay FIRST to ALL pariahs (active or not)
        self.decay_pariah_toxicity(generation)

        # STEP 2: Reactivate decayed pariahs that were incorrectly marked inactive
        # Pariahs with toxicity > min should stay active for weak warnings
        reactivated = self.db.execute_query("""
            UPDATE pariahs
            SET is_active = TRUE, obsolescence_score = 0.0
            WHERE is_active = FALSE
            AND toxicity > 0.15
            RETURNING pariah_id
        """)
        if reactivated:
            logger.info(f"Reactivated {len(reactivated)} previously-obsolete pariahs")

        # STEP 3: Only mark truly obsolete pariahs (min toxicity AND very old)
        # Increased threshold to 50 generations - give more time
        self.db.execute_query("""
            UPDATE pariahs
            SET obsolescence_score = 1.0,
                is_active = FALSE
            WHERE last_triggered_generation < ? - 50
            AND toxicity <= 0.15
            AND is_active = TRUE
        """, (generation,))

    def decay_pariah_toxicity(self, generation: int, decay_rate: float = 0.03, min_toxicity: float = 0.1):
        """
        Apply relevance decay to pariah toxicity.

        Philosophy (from agi_unified_theory.md):
        "Forgetting is not a bug - it's essential for intelligence."
        Pariahs should fade naturally if not re-validated by newer generations.

        FIXED: Now operates on ALL pariahs, not just active ones.
        This ensures pariahs decay properly before obsolescence check.

        Decay Formula (exponential decay):
        new_toxicity = current_toxicity * decay_factor
        where decay_factor = max(0.3, 1.0 - decay_rate * generations_since_trigger)

        Args:
            generation: Current generation
            decay_rate: How fast toxicity decays per generation (default 3% - slower decay)
            min_toxicity: Minimum toxicity floor to maintain some warning (default 0.1)
        """
        try:
            # FIXED: Operate on ALL pariahs, not just active ones
            # This ensures decay happens before obsolescence marking
            pariahs = self.db.execute_query("""
                SELECT pariah_id, toxicity, discovery_generation,
                       COALESCE(last_triggered_generation, discovery_generation) as last_trigger
                FROM pariahs
                WHERE toxicity > ?
            """, (min_toxicity,))

            if not pariahs:
                return

            decayed_count = 0
            for p in pariahs:
                last_trigger = p['last_trigger'] or p['discovery_generation'] or 0
                generations_since_trigger = max(0, generation - last_trigger)

                # Apply decay based on age
                # FIXED: Cap at 30 generations to prevent over-decay
                decay_factor = 1.0 - (decay_rate * min(generations_since_trigger, 30))
                decay_factor = max(0.3, decay_factor)  # Floor at 30% of original

                new_toxicity = max(min_toxicity, p['toxicity'] * decay_factor)

                # Only update if toxicity actually changed significantly
                if abs(new_toxicity - p['toxicity']) > 0.005:
                    self.db.execute_query("""
                        UPDATE pariahs
                        SET toxicity = ?
                        WHERE pariah_id = ?
                    """, (new_toxicity, p['pariah_id']))
                    decayed_count += 1

            if decayed_count > 0:
                logger.debug(f"Decayed toxicity for {decayed_count} pariahs (gen {generation})")

        except Exception as e:
            logger.error("Error in toxicity decay", exc=e)

    def cleanup_obsolete_pariahs(self, current_generation: int) -> int:
        """
        Soft-retire pariahs that are no longer valid traps.

        A pariah should be retired when:
        1. High avoidance success rate (90%+) - agents easily avoid it, not a real trap
        2. Very old without recent triggers (50+ generations stale)
        3. Only triggered once (single failure, not a pattern)

        SOFT RETIREMENT: We don't delete, just deactivate (is_active = FALSE).
        This preserves history while removing from active queries.

        Returns:
            Number of pariahs soft-retired
        """
        try:
            retired = 0

            # 1. High avoidance success = not a real trap
            high_avoidance = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND avoidance_success_rate >= 0.9
                  AND total_awareness >= 5
            """)
            for p in (high_avoidance or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 1.0
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1

            # 2. Stale pariahs (50+ generations without trigger)
            stale_threshold = current_generation - 50
            stale = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND last_triggered_generation < ?
                  AND discovery_generation < ?
            """, (stale_threshold, stale_threshold))
            for p in (stale or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 0.8
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1

            # 3. Single-trigger pariahs older than 20 generations (not a pattern, just noise)
            noise_threshold = current_generation - 20
            noise = self.db.execute_query("""
                SELECT pariah_id FROM pariahs
                WHERE is_active = TRUE
                  AND trigger_count <= 1
                  AND discovery_generation < ?
            """, (noise_threshold,))
            for p in (noise or []):
                self.db.execute_query("""
                    UPDATE pariahs SET is_active = FALSE, obsolescence_score = 0.5
                    WHERE pariah_id = ?
                """, (p['pariah_id'],))
                retired += 1

            if retired > 0:
                logger.debug(f"Soft-retired {retired} obsolete pariahs")

            return retired

        except Exception as e:
            logger.error("Error retiring pariahs", exc=e)
            return 0

    # ========================================================================
    # DASHBOARD / QUERYING
    # ========================================================================

    def get_top_pariahs(self, limit: int = 10) -> List[Dict]:
        """Get most toxic pariahs by trigger count and toxicity."""
        return self.db.execute_query("""
            SELECT pariah_id, pariah_name, pariah_type,
                   toxicity, trigger_count, avg_score_loss,
                   total_awareness, active_awareness,
                   avoidance_success_rate, discovery_generation
            FROM pariahs
            WHERE is_active = TRUE
            ORDER BY toxicity DESC, trigger_count DESC
            LIMIT ?
        """, (limit,))
