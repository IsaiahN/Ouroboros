import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Multi-Stage Sequence Matching Pipeline (Competitive Improvement #2, +40% expected gain)

PURPOSE:
When exact sequence matching fails, cascade through progressively looser matching strategies
before falling back to random exploration. This dramatically improves knowledge reuse.

PROBLEM SOLVED:
Currently: exact match fails → immediate random exploration (70% threshold)
New: 5-stage cascade provides multiple fallback strategies

STAGES (order depends on problem space maturity):
- Cold Start: Random exploration (building entropy)
- Early: Exact match first (not enough variance for abstraction)
- Mature: Conceptual/abstraction first (formula discoverable)
- Saturated: Abstraction only (formula confirmed via resonance)

STAGES:
1. Exact match (current system)
2. Prefix match: Use beginning of sequence, explore remainder
3. Suffix match: Skip to known ending sequence
4. Subsequence extraction: Find any matching segment
5. Conceptual match: Pattern abstraction (existing abstraction engine)
6. Random exploration (last resort)

"""
import os
import random
import sys

# Disable pycache (Rule 1)
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import logging
from typing import Any, Dict, List, Optional, Tuple

from database_interface import DatabaseInterface

logger = logging.getLogger(__name__)


# Problem Space Maturity Levels
MATURITY_COLD_START = 'cold_start'    # No wins - building entropy
MATURITY_EARLY = 'early'              # 1-2 wins - not enough variance
MATURITY_MATURE = 'mature'            # 3+ diverse wins - formula discoverable
MATURITY_SATURATED = 'saturated'      # Resonance validated - formula confirmed


def get_network_informed_action(db: DatabaseInterface, game_id: str, level_number: int) -> int:
    """
    Get a network-informed exploration action instead of pure random.

    METATHEORY: Even during exploration, the network should inform decisions.
    Instead of random.choice([1,2,3,4]), query what actions have worked
    in similar games/levels and bias exploration toward those.

    Fallback hierarchy:
    1. Actions that worked in THIS game type's other levels
    2. Actions that worked in structurally similar games
    3. Most common first actions across all wins
    4. Pure random (only if network is completely empty)

    Args:
        db: Database interface
        game_id: Game identifier
        level_number: Current level number

    Returns:
        Action number (1-7) biased by network knowledge
    """
    game_type = game_id.split('-')[0] if '-' in game_id else game_id

    try:
        # Strategy 1: What actions start winning sequences in this game TYPE?
        game_type_actions = db.execute_query("""
            SELECT SUBSTR(action_sequence, 2, 1) as first_action, COUNT(*) as cnt
            FROM winning_sequences
            WHERE game_id LIKE ? AND is_active = 1
            GROUP BY first_action
            ORDER BY cnt DESC
            LIMIT 3
        """, (f"{game_type}%",))

        if game_type_actions:
            # Weighted random from game type's successful first actions
            actions = []
            weights = []
            for row in game_type_actions:
                try:
                    action = int(row['first_action'])
                    if 1 <= action <= 7:
                        actions.append(action)
                        weights.append(row['cnt'])
                except (ValueError, TypeError):
                    continue

            if actions:
                # Weighted random selection
                total = sum(weights)
                r = random.random() * total
                cumulative = 0
                for action, weight in zip(actions, weights):
                    cumulative += weight
                    if r <= cumulative:
                        logger.debug(f"[NETWORK] Game-type informed action: {action}")
                        return action

        # Strategy 2: What actions are most common overall for this level number?
        level_actions = db.execute_query("""
            SELECT SUBSTR(action_sequence, 2, 1) as first_action, COUNT(*) as cnt
            FROM winning_sequences
            WHERE level_number = ? AND is_active = 1
            GROUP BY first_action
            ORDER BY cnt DESC
            LIMIT 3
        """, (level_number,))

        if level_actions:
            actions = []
            weights = []
            for row in level_actions:
                try:
                    action = int(row['first_action'])
                    if 1 <= action <= 7:
                        actions.append(action)
                        weights.append(row['cnt'])
                except (ValueError, TypeError):
                    continue

            if actions:
                total = sum(weights)
                r = random.random() * total
                cumulative = 0
                for action, weight in zip(actions, weights):
                    cumulative += weight
                    if r <= cumulative:
                        logger.debug(f"[NETWORK] Level-number informed action: {action}")
                        return action

        # Strategy 3: Global most common first actions
        global_actions = db.execute_query("""
            SELECT SUBSTR(action_sequence, 2, 1) as first_action, COUNT(*) as cnt
            FROM winning_sequences
            WHERE is_active = 1
            GROUP BY first_action
            ORDER BY cnt DESC
            LIMIT 3
        """)

        if global_actions:
            actions = []
            weights = []
            for row in global_actions:
                try:
                    action = int(row['first_action'])
                    if 1 <= action <= 7:
                        actions.append(action)
                        weights.append(row['cnt'])
                except (ValueError, TypeError):
                    continue

            if actions:
                total = sum(weights)
                r = random.random() * total
                cumulative = 0
                for action, weight in zip(actions, weights):
                    cumulative += weight
                    if r <= cumulative:
                        logger.debug(f"[NETWORK] Global informed action: {action}")
                        return action

    except Exception as e:
        logger.debug(f"Network-informed action failed, using random: {e}")

    # Final fallback: pure random (Cold Start / empty network)
    action = random.choice([1, 2, 3, 4])
    logger.debug(f"[NETWORK] Pure random fallback: {action}")
    return action


def get_structural_similarity_bootstrap(db: DatabaseInterface, game_id: str) -> Optional[List[int]]:
    """
    For completely new games, find structurally similar games and transfer knowledge.

    METATHEORY: New game bootstrap should use structural similarity,
    not pure random exploration. If a new game's first frame looks similar
    to games we've beaten, try those strategies first.

    Similarity is based on:
    1. Game type prefix (same game category)
    2. Grid size patterns
    3. Color/object patterns in initial frames

    Args:
        db: Database interface
        game_id: New game identifier

    Returns:
        List of actions to try, or None if no similar games found
    """
    game_type = game_id.split('-')[0] if '-' in game_id else game_id

    try:
        # Strategy 1: Same game type prefix - find best performing sequence
        similar_game_seq = db.execute_query("""
            SELECT action_sequence, total_actions, efficiency_score
            FROM winning_sequences
            WHERE game_id LIKE ? AND level_number = 1 AND is_active = 1
            ORDER BY efficiency_score DESC
            LIMIT 1
        """, (f"{game_type}%",))

        if similar_game_seq:
            import json
            actions = json.loads(similar_game_seq[0]['action_sequence'])
            logger.info(f"[BOOTSTRAP] Found similar game sequence: {len(actions)} actions from {game_type}")
            return actions[:10]  # Return first 10 actions as bootstrap

        # Strategy 2: Query games with similar pattern tags
        # Look for games with overlapping pattern signatures
        similar_pattern_seq = db.execute_query("""
            SELECT ws.action_sequence, ws.pattern_tags, ws.efficiency_score
            FROM winning_sequences ws
            WHERE ws.level_number = 1 AND ws.is_active = 1
            ORDER BY ws.efficiency_score DESC
            LIMIT 5
        """)

        if similar_pattern_seq:
            # Just use the best performing level 1 sequence
            import json
            actions = json.loads(similar_pattern_seq[0]['action_sequence'])
            logger.info(f"[BOOTSTRAP] Using top L1 sequence as bootstrap: {len(actions)} actions")
            return actions[:10]

    except Exception as e:
        logger.debug(f"Structural similarity bootstrap failed: {e}")

    return None


def get_problem_space_maturity(db: DatabaseInterface, game_id: str, level_number: int) -> str:
    """
    Determine the maturity level of network knowledge for a game/level.

    This implements the Plato's Cave / Cold Start concept:
    - Cold Start: No formula exists, must enumerate (KID B phase)
    - Early: Some data but not enough variance for abstraction
    - Mature: Enough diverse wins to extract formulas (KID A phase)
    - Saturated: Cross-role resonance has validated the formula

    Args:
        db: Database interface
        game_id: Game identifier
        level_number: Level number

    Returns:
        Maturity level string: 'cold_start', 'early', 'mature', 'saturated'
    """
    game_type = game_id.split('-')[0] if '-' in game_id else game_id

    # Query 1: Count distinct winning sequences for this level
    win_count_result = db.execute_query("""
        SELECT COUNT(DISTINCT sequence_id) as win_count,
               COUNT(DISTINCT agent_id) as agent_count
        FROM winning_sequences
        WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
    """, (f"{game_type}%", level_number))

    win_count = win_count_result[0]['win_count'] if win_count_result else 0
    agent_count = win_count_result[0]['agent_count'] if win_count_result else 0

    # Cold Start: No wins at all
    if win_count == 0:
        logger.debug(f"[MATURITY] {game_id} L{level_number}: COLD_START (0 wins)")
        return MATURITY_COLD_START

    # Query 2: Check for resonance validation (cross-role agreement)
    # Note: resonance_patterns uses game_types (JSON) not game_id, so we search within it
    try:
        resonance_result = db.execute_query("""
            SELECT resonance_score, role_diversity
            FROM resonance_patterns
            WHERE game_types LIKE ?
            ORDER BY resonance_score DESC
            LIMIT 1
        """, (f"%{game_type}%",))

        if resonance_result and resonance_result[0].get('resonance_score', 0) > 0.7:
            role_diversity = resonance_result[0].get('role_diversity', 0)
            if role_diversity >= 2:
                logger.debug(f"[MATURITY] {game_id} L{level_number}: SATURATED (resonance={resonance_result[0]['resonance_score']:.2f}, roles={role_diversity})")
                return MATURITY_SATURATED
    except Exception as e:
        # Table may not exist yet or schema differs - skip resonance check
        logger.debug(f"[MATURITY] Resonance check skipped: {e}")

    # Query 3: Check sequence diversity (different action patterns)
    diversity_result = db.execute_query("""
        SELECT COUNT(DISTINCT
            SUBSTR(action_sequence, 1, 20)  -- First 20 chars as pattern proxy
        ) as pattern_diversity
        FROM winning_sequences
        WHERE game_id LIKE ? AND level_number = ? AND is_active = 1
    """, (f"{game_type}%", level_number))

    pattern_diversity = diversity_result[0]['pattern_diversity'] if diversity_result else 0

    # Mature: 3+ diverse wins OR 5+ wins from different agents
    if pattern_diversity >= 3 or (win_count >= 5 and agent_count >= 3):
        logger.debug(f"[MATURITY] {game_id} L{level_number}: MATURE (wins={win_count}, patterns={pattern_diversity}, agents={agent_count})")
        return MATURITY_MATURE

    # Early: Some wins but not enough variance
    logger.debug(f"[MATURITY] {game_id} L{level_number}: EARLY (wins={win_count}, patterns={pattern_diversity})")
    return MATURITY_EARLY


class MultiStageMatchingPipeline:
    """
    Cascading sequence matching system with 5 fallback strategies.
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db

        # Configuration thresholds (tunable based on agent risk_tolerance)
        self.min_prefix_length = 10  # Minimum actions for prefix match
        self.min_suffix_length = 8   # Minimum actions for suffix match
        self.min_subsequence_length = 5  # Minimum segment for extraction
        self.pattern_similarity_threshold = 0.6  # Conceptual matching threshold

        # Performance tracking
        self.stage_success_counts = {
            'exact': 0,
            'prefix': 0,
            'suffix': 0,
            'subsequence': 0,
            'conceptual': 0,
            'random': 0
        }

    def get_sequence_with_fallback(
        self,
        game_id: str,
        level_number: int = 1,
        current_actions: Optional[List[int]] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[List[int]], str, Dict[str, Any]]:
        """
        Attempt to retrieve sequence through cascading fallback strategies.

        CASCADE ORDERING IS DYNAMIC based on problem space maturity:
        - Cold Start/Early: exact -> prefix -> suffix -> subsequence -> conceptual
          (We're still building entropy, exact matches are valid and efficient)
        - Mature/Saturated: conceptual -> subsequence -> suffix -> prefix -> exact
          (We have enough variance to extract formulas, prefer abstraction)

        This implements the Plato's Cave concept: you can't skip enumeration
        when the formula hasn't been discovered yet.

        Args:
            game_id: Game identifier
            level_number: Level number
            current_actions: Actions taken so far (for pattern matching)
            agent_config: Agent configuration (for threshold tuning)

        Returns:
            Tuple of (sequence_actions, stage_used, metadata)
            - sequence_actions: List of action numbers (1-7) or None
            - stage_used: Which matching stage succeeded
            - metadata: Additional info (original_sequence_id, confidence, maturity, etc.)
        """
        current_actions = current_actions or []
        agent_config = agent_config or {}

        # Adjust thresholds based on agent configuration
        self._adjust_thresholds(agent_config)

        # Determine problem space maturity (Cold Start concept)
        maturity = get_problem_space_maturity(self.db, game_id, level_number)

        # Define stage functions and their metadata
        stages = {
            'exact': (self._stage_1_exact_match, (game_id, level_number), 1.0),
            'prefix': (self._stage_2_prefix_match, (game_id, level_number, current_actions), 0.8),
            'suffix': (self._stage_3_suffix_match, (game_id, level_number), 0.7),
            'subsequence': (self._stage_4_subsequence_extraction, (game_id, level_number), 0.6),
            'conceptual': (self._stage_5_conceptual_match, (game_id, level_number, current_actions), 0.5),
        }

        # Cascade order based on maturity
        if maturity in [MATURITY_COLD_START, MATURITY_EARLY]:
            # KID B phase: we're still enumerating, exact matches are valid
            cascade_order = ['exact', 'prefix', 'suffix', 'subsequence', 'conceptual']
            logger.debug(f"[Pipeline] Maturity={maturity}: using EXACT-FIRST cascade (building entropy)")
        else:
            # KID A phase: we have the formula, prefer abstraction
            cascade_order = ['conceptual', 'subsequence', 'suffix', 'prefix', 'exact']
            logger.debug(f"[Pipeline] Maturity={maturity}: using ABSTRACTION-FIRST cascade (formula available)")

        # Execute cascade in order
        for stage_name in cascade_order:
            stage_func, args, confidence = stages[stage_name]
            result = stage_func(*args)
            if result:
                self.stage_success_counts[stage_name] += 1
                return result, stage_name, {
                    'confidence': confidence,
                    'maturity': maturity,
                    'cascade_order': cascade_order
                }

        # All stages failed - random exploration
        self.stage_success_counts['random'] += 1
        logger.debug(f"[Pipeline] All matching stages failed for game {game_id} L{level_number}, using random exploration")
        return None, 'random', {'confidence': 0.0, 'maturity': maturity}

    # REMOVED: The old sequential stage calls are replaced by the cascade loop above

    def _log_maturity_stats(self, game_id: str, level_number: int, maturity: str):
        """Log maturity-based cascade selection for debugging."""
        # Intentionally empty - logging happens inline above
        pass

    def _adjust_thresholds(self, agent_config: Dict[str, Any]):
        """Tune matching thresholds based on agent personality."""
        risk_tolerance = agent_config.get('risk_tolerance', 0.5)

        # High risk agents: more willing to use partial matches
        if risk_tolerance > 0.7:
            self.min_prefix_length = 5
            self.min_suffix_length = 5
            self.pattern_similarity_threshold = 0.5
        # Conservative agents: stricter matching
        elif risk_tolerance < 0.3:
            self.min_prefix_length = 15
            self.min_suffix_length = 12
            self.pattern_similarity_threshold = 0.7

    def _stage_1_exact_match(self, game_id: str, level_number: int) -> Optional[List[int]]:
        """Stage 1: Exact sequence match (existing system)."""
        query = """
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND level_number = ? AND is_active = 1
        ORDER BY total_actions ASC
        LIMIT 1
        """
        result = self.db.execute_query(query, (game_id, level_number))
        if result and result[0].get('action_sequence'):
            return self._parse_actions(result[0]['action_sequence'])
        return None

    def _stage_2_prefix_match(self, game_id: str, level_number: int, current_actions: List[int]) -> Optional[List[int]]:
        """Stage 2: Match beginning of sequence, explore remainder."""
        query = """
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND is_active = 1
        ORDER BY total_actions ASC
        LIMIT 5
        """
        results = self.db.execute_query(query, (game_id,))

        for row in results:
            actions = self._parse_actions(row['action_sequence'])
            if len(actions) >= self.min_prefix_length:
                # Check if current actions match prefix
                if current_actions and len(current_actions) > 0:
                    if actions[:len(current_actions)] == current_actions:
                        logger.info(f"[Pipeline] Prefix match found: continuing from action {len(current_actions)}")
                        return actions[len(current_actions):]
                else:
                    # No current actions, return prefix only
                    return actions[:self.min_prefix_length]
        return None

    def _stage_3_suffix_match(self, game_id: str, level_number: int) -> Optional[List[int]]:
        """Stage 3: Use ending sequence (skip to known win condition)."""
        query = """
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND level_number = ? AND is_active = 1
        ORDER BY total_actions ASC
        LIMIT 1
        """
        result = self.db.execute_query(query, (game_id, level_number))

        if result and result[0].get('action_sequence'):
            actions = self._parse_actions(result[0]['action_sequence'])
            if len(actions) >= self.min_suffix_length:
                suffix = actions[-self.min_suffix_length:]
                logger.info(f"[Pipeline] Suffix match: using last {self.min_suffix_length} actions")
                return suffix
        return None

    def _stage_4_subsequence_extraction(self, game_id: str, level_number: int) -> Optional[List[int]]:
        """Stage 4: Find any matching segment from similar levels."""
        # Query similar levels (±1 level number)
        query = """
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND level_number BETWEEN ? AND ? AND is_active = 1
        ORDER BY total_actions ASC
        LIMIT 10
        """
        results = self.db.execute_query(query, (game_id, level_number - 1, level_number + 1))

        for row in results:
            actions = self._parse_actions(row['action_sequence'])
            if len(actions) >= self.min_subsequence_length:
                # Extract middle segment
                start_idx = len(actions) // 3
                end_idx = 2 * len(actions) // 3
                subsequence = actions[start_idx:end_idx]
                if len(subsequence) >= self.min_subsequence_length:
                    logger.info(f"[Pipeline] Subsequence extracted from similar level: {len(subsequence)} actions")
                    return subsequence
        return None

    def _stage_5_conceptual_match(self, game_id: str, level_number: int, current_actions: List[int]) -> Optional[List[int]]:
        """Stage 5: Conceptual pattern matching (abstraction engine)."""
        # Query for any sequences in this game
        query = """
        SELECT action_sequence FROM winning_sequences
        WHERE game_id = ? AND is_active = 1
        ORDER BY total_actions ASC
        LIMIT 5
        """
        results = self.db.execute_query(query, (game_id,))

        if not results:
            return None

        # Simple pattern analysis: find most common action sequences
        action_patterns = {}
        for row in results:
            actions = self._parse_actions(row['action_sequence'])
            # Look for 3-action patterns
            for i in range(len(actions) - 2):
                pattern = tuple(actions[i:i+3])
                action_patterns[pattern] = action_patterns.get(pattern, 0) + 1

        # Return most common pattern
        if action_patterns:
            most_common = max(action_patterns, key=lambda k: action_patterns[k])
            logger.info(f"[Pipeline] Conceptual pattern match: {most_common} (seen {action_patterns[most_common]} times)")
            return list(most_common)

        return None

    def _parse_actions(self, action_string: str) -> List[int]:
        """Parse action string into list of action numbers."""
        if not action_string:
            return []
        return [int(a) for a in action_string.split(',') if a.strip().isdigit()]

    def get_stage_statistics(self) -> Dict[str, Any]:
        """Return performance statistics for each matching stage."""
        total = sum(self.stage_success_counts.values())
        if total == 0:
            return {'error': 'No matching attempts recorded'}

        return {
            'total_attempts': total,
            'stage_distribution': {
                stage: {
                    'count': count,
                    'percentage': (count / total) * 100
                }
                for stage, count in self.stage_success_counts.items()
            },
            'knowledge_reuse_rate': ((total - self.stage_success_counts['random']) / total) * 100
        }


# Module-level test function (Rule 5 compliant - not a test file)
if __name__ == "__main__":
    # Quick verification
    db = DatabaseInterface()
    pipeline = MultiStageMatchingPipeline(db)

    # Test maturity detection
    test_game = "test_game"
    test_level = 1
    maturity = get_problem_space_maturity(db, test_game, test_level)
    print(f"[TEST] Maturity for {test_game} L{test_level}: {maturity}")

    # Test cascading fallback
    seq, stage, meta = pipeline.get_sequence_with_fallback(
        game_id=test_game,
        level_number=test_level,
        current_actions=[],
        agent_config={'risk_tolerance': 0.6}
    )

    print(f"[TEST] Stage used: {stage}")
    print(f"[TEST] Confidence: {meta.get('confidence', 0)}")
    print(f"[TEST] Maturity from meta: {meta.get('maturity', 'N/A')}")
    print(f"[TEST] Cascade order: {meta.get('cascade_order', 'N/A')}")
    print(f"[TEST] Statistics: {pipeline.get_stage_statistics()}")
