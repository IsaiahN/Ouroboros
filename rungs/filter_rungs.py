"""
Filter Rungs - Modify action weights / safety gates
===================================================
Extracted from decision_rung_system.py Phase 4.2.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from rungs.base import (
    Action6CoordinateProvider,
    DecisionRung,
    KnowledgeProvenance,
    RungResult,
    filter_available_actions,
    get_available_action_weights,
    get_available_actions_list,
    get_random_available_action,
    is_action_available,
    validate_action,
)

logger = logging.getLogger(__name__)


def _get_frame(game_state: Any) -> Any:
    """Extract frame from game_state whether it's a dict or object."""
    if isinstance(game_state, dict):
        return game_state.get('frame')
    return getattr(game_state, 'frame', None)


class DeathAvoidanceRung(DecisionRung):
    """Position-bucket death pattern avoidance - FILTER (modifies weights)"""
    name = "death_avoidance"
    category = "filter"
    default_priority = 15
    confidence_threshold = 0.6

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        detector = self.engines.terminal_pattern_detector
        if detector is None:
            return RungResult()

        try:
            # Get graduated weights from terminal pattern detector
            if hasattr(detector, 'get_graduated_action_weights'):
                game_type = context.get('game_type', '')
                level = context.get('level', 1)
                position = context.get('position', (0, 0))
                frontier_mode = context.get('frontier_mode', False)

                weights = detector.get_graduated_action_weights(
                    game_type=game_type,
                    level=level,
                    position=position,
                    frontier_mode=frontier_mode
                )

                # Find most dangerous action
                min_weight = min(weights.values()) if weights else 1.0
                dangerous_actions = [a for a, w in weights.items() if w < 0.3]

                return RungResult(
                    confidence=0.7 if dangerous_actions else 0.1,
                    reason=f"Danger weights calculated, {len(dangerous_actions)} risky actions",
                    weights=weights,
                    metadata={'dangerous_actions': dangerous_actions, 'min_weight': min_weight}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Death avoidance failed: {e}")


class PriorLessonsRung(DecisionRung):
    """Apply prior game lessons as graduated action weights - FILTER

    Converts lessons from game_lessons_learned table into safety weights.
    Lessons with caused_death=True heavily penalize their key_action.
    Lessons from wins boost their key_action.

    This closes the "last mile" gap where lessons were collected but never
    used in action selection.
    """
    name = "prior_lessons"
    category = "filter"
    default_priority = 16  # Right after death_avoidance (15)
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            # Get prior lessons from context (loaded by evolution runner)
            prior_lessons = context.get('prior_lessons', [])
            if not prior_lessons:
                return RungResult()

            # Initialize weights at 1.0 for AVAILABLE actions only
            weights = get_available_action_weights(context, 1.0)
            lessons_applied = 0

            for idx, lesson in enumerate(prior_lessons[:10]):  # Max 10 lessons
                key_action = lesson.get('key_action', '')
                if not key_action or not key_action.startswith('ACTION'):
                    continue

                confidence = lesson.get('confidence', 0.5)
                caused_death = lesson.get('caused_death', False)
                from_win = lesson.get('from_win', False)
                severity = lesson.get('severity', 1)
                occurrence = lesson.get('occurrence_count', 1)

                # Recency factor: earlier lessons in list are more recent/salient
                recency_factor = 1.0 - (idx * 0.05)

                if caused_death:
                    # Death lessons reduce weight significantly
                    # Formula: severity (1-3) * confidence * recency
                    penalty = min(0.9, severity * 0.25 * confidence * recency_factor)
                    weights[key_action] *= max(0.05, 1.0 - penalty)
                    lessons_applied += 1
                elif from_win:
                    # Win lessons boost the action
                    boost = min(0.5, 0.15 * confidence * recency_factor * min(occurrence, 5))
                    weights[key_action] = min(1.5, weights[key_action] * (1.0 + boost))
                    lessons_applied += 1
                else:
                    # Neutral lessons: slight penalty for failures
                    penalty = min(0.3, 0.1 * confidence * recency_factor)
                    weights[key_action] *= max(0.7, 1.0 - penalty)
                    lessons_applied += 1

            if lessons_applied == 0:
                return RungResult()

            # Find penalized actions
            penalized = [a for a, w in weights.items() if w < 0.7]
            boosted = [a for a, w in weights.items() if w > 1.0]

            # Genuine epistemic resolution: we know if we've encountered this before
            resolved = ['have_we_seen_this_before']
            death_lessons = [l for l in prior_lessons[:10] if l.get('caused_death')]
            if death_lessons:
                resolved.append('known_death_patterns')
            win_lessons = [l for l in prior_lessons[:10] if l.get('from_win')]
            if win_lessons:
                resolved.append('known_win_patterns')

            return RungResult(
                confidence=min(0.8, 0.3 + lessons_applied * 0.05),
                reason=f"Prior lessons: {lessons_applied} applied, {len(penalized)} penalized, {len(boosted)} boosted",
                weights=weights,
                metadata={
                    'lessons_applied': lessons_applied,
                    'penalized_actions': penalized,
                    'boosted_actions': boosted
                },
                resolved_questions=resolved,
            )
        except Exception as e:
            return RungResult(reason=f"Prior lessons failed: {e}")


class ThreeLayerFilterRung(DecisionRung):
    """Meta-learning filter preventing wasted actions - FILTER

    Implements three filtering layers using context and prior lessons:
    Layer 1: Failed action cache - penalize recently failed actions
    Layer 2: Object prefilter - penalize click actions with no valid target
    Layer 3: Pattern prediction - penalize actions with low success history
    """
    name = "three_layer_filter"
    category = "filter"
    default_priority = 55
    confidence_threshold = 0.0  # Modifies weights, doesn't suggest

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            weights: Dict[str, float] = {}
            frame = _get_frame(game_state)
            if frame is not None and hasattr(frame, 'tolist'):
                frame = frame.tolist()
            position = context.get('position', (0, 0))
            # Ensure position is a tuple of ints
            if hasattr(position, '__iter__') and not isinstance(position, str):
                position = tuple(int(p) for p in position[:2]) if len(list(position)) >= 2 else (0, 0)
            else:
                position = (0, 0)
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

            # Layer 1: Cache check - penalize recently failed actions
            # Uses 'failed_actions' from context (set by evolution_runner)
            failed_actions = context.get('failed_actions', set())
            recent_actions = context.get('recent_actions', [])

            for i in available:
                action = f'ACTION{i}'
                if action in failed_actions:
                    weights[action] = 0.1  # Heavily penalize failed actions
                else:
                    weights[action] = 1.0

            # Layer 2: Object prefilter for click actions
            # Penalize ACTION5/6/7 if there's no non-background pixel at position
            if frame is not None and isinstance(frame, list):
                for action_num in [5, 6, 7]:
                    if action_num in available:
                        action = f'ACTION{action_num}'
                        # Check if there's something to click at current position
                        y, x = position if len(position) >= 2 else (0, 0)
                        has_object = False

                        # Check 3x3 region around position
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                check_y, check_x = y + dy, x + dx
                                if (0 <= check_y < len(frame) and
                                    0 <= check_x < len(frame[0]) and
                                    frame[check_y][check_x] > 0):
                                    has_object = True
                                    break
                            if has_object:
                                break

                        if not has_object:
                            weights[action] = weights.get(action, 1.0) * 0.3

            # Layer 3: Pattern prediction using prior lessons
            prior_lessons = context.get('prior_lessons', [])
            for lesson in prior_lessons[:5]:
                key_action = lesson.get('key_action', '')
                if key_action in weights and lesson.get('caused_death', False):
                    severity = lesson.get('severity', 1)
                    weights[key_action] = weights.get(key_action, 1.0) * max(0.2, 1.0 - severity * 0.2)

            penalized_count = sum(1 for w in weights.values() if w < 1.0)
            if penalized_count > 0:
                return RungResult(
                    confidence=0.3,
                    weights=weights,
                    reason=f"3-layer filter applied: {penalized_count} actions penalized",
                    metadata={'filter_weights': weights}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Three-layer filter failed: {e}")


class PariahAvoidanceRung(DecisionRung):
    """Avoid actions that historically led to failures - FILTER"""
    name = "pariah_avoidance"
    category = "filter"
    default_priority = 17
    confidence_threshold = 0.0  # Modifies weights

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        vpe = self.engines.viral_package_engine
        if vpe is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', '')
            game_id = context.get('game_id', '')
            level = context.get('level', 1)
            role = context.get('agent_role', 'generalist')

            if not agent_id:
                return RungResult()

            # Role-adjusted penalty multipliers
            role_multipliers = {
                'pioneer': 0.3,
                'optimizer': 1.0,
                'generalist': 0.7,
                'exploiter': 0.5
            }
            multiplier = role_multipliers.get(role, 0.7)

            # Use the correct API: get_role_adjusted_pariah_penalties or get_pariah_action_penalties
            if hasattr(vpe, 'get_role_adjusted_pariah_penalties'):
                penalties = vpe.get_role_adjusted_pariah_penalties(
                    agent_id=agent_id,
                    agent_role=role,
                    game_id=game_id,
                    current_level=level
                )
            elif hasattr(vpe, 'get_pariah_action_penalties'):
                penalties = vpe.get_pariah_action_penalties(
                    agent_id=agent_id,
                    game_id=game_id,
                    current_level=level
                )
            else:
                return RungResult()

            if not penalties:
                return RungResult()

            # Convert penalties to weights (penalty -> weight inversion)
            weights: Dict[str, float] = {}
            for action_num, penalty in penalties.items():
                action = f'ACTION{action_num}'
                # Apply role multiplier to penalty, then convert to weight
                adjusted_penalty = penalty * multiplier
                weights[action] = max(0.05, 1.0 - min(0.95, adjusted_penalty))

            if weights:
                return RungResult(
                    confidence=0.4,
                    weights=weights,
                    reason=f"Pariah avoidance: {len(penalties)} actions penalized, role={role}",
                    metadata={'penalties': len(penalties), 'role_multiplier': multiplier}
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Pariah avoidance failed: {e}")


class TerminalPatternRung(DecisionRung):
    """Recognize approaching terminal states and avoid fatal action - FILTER"""
    name = "terminal_pattern"
    category = "filter"
    default_priority = 14
    confidence_threshold = 0.7

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        tpd = self.engines.terminal_pattern_detector
        if tpd is None:
            return RungResult()

        try:
            frame = _get_frame(game_state)

            if hasattr(tpd, 'detect_terminal_approach'):
                terminal = tpd.detect_terminal_approach(frame, context.get('last_actions', []))
                if terminal.get('approaching_terminal', False):
                    fatal_action = terminal.get('fatal_action')
                    weights = get_available_action_weights(context, 1.0)
                    if fatal_action and fatal_action in weights:
                        weights[fatal_action] = 0.05  # Near-block the fatal action
                    return RungResult(
                        confidence=0.75,
                        weights=weights,
                        reason=f"Terminal approach detected: avoid {fatal_action}",
                        metadata={'terminal': terminal}
                    )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Terminal pattern failed: {e}")


class DestructiveActionDetectionRung(DecisionRung):
    """Detect and penalize irreversible/destructive actions - FILTER

    For games like VC33 where:
    - Platform shrinking is one-directional (irreversible)
    - Random clicking gradually destroys the level state
    - Some actions reduce the number of interactive objects

    This rung:
    1. Track "entropy" of the game state over time
    2. Detect when actions DECREASE the number of objects or increase uniformity
    3. Penalize actions that historically produce entropy increase
    4. Suggest the system be more conservative with clicks

    ROOT CAUSE ADDRESSED: VC33 random clicking gradually destroys level
    state without recovery. The agent doesn't know which clicks are
    destructive vs productive.
    """
    name = "destructive_action_detection"
    category = "filter"
    default_priority = 16
    confidence_threshold = 0.3

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Track state complexity over time: game_key -> [complexity_score, ...]
        self._complexity_history: Dict[str, List[float]] = {}
        # Track which click positions caused complexity decrease
        self._destructive_positions: Dict[str, Set[Tuple[int, int]]] = {}
        # Count of destructive actions detected
        self._destruction_count: Dict[str, int] = {}
        # Total clicks tracked
        self._total_clicks: Dict[str, int] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        available = context.get('available_actions', [])
        if 6 not in available and 'ACTION6' not in available:
            return RungResult()

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        total = self._total_clicks.get(game_key, 0)
        destructive = self._destruction_count.get(game_key, 0)

        if total < 5:
            return RungResult()  # Not enough data

        destruction_rate = destructive / max(total, 1)
        destructive_positions = self._destructive_positions.get(game_key, set())

        # If destruction rate is high, apply penalty weights
        if destruction_rate > 0.3:
            # Reduce confidence in all click actions
            weights: Dict[str, float] = {}
            for a in available:
                action_name = f'ACTION{a}' if isinstance(a, int) else a
                if action_name == 'ACTION6':
                    # Penalize clicks based on destruction rate
                    weights[action_name] = max(0.2, 1.0 - destruction_rate)
                else:
                    weights[action_name] = 1.0

            return RungResult(
                weights=weights,
                reason=f"Destructive action detection: {destruction_rate:.0%} of clicks are destructive ({destructive}/{total})",
                metadata={
                    'destruction_rate': destruction_rate,
                    'destructive_positions': len(destructive_positions),
                }
            )

        return RungResult()

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Track whether clicks increase or decrease state complexity."""
        if action != 'ACTION6':
            return
        if frame_before is None or frame_after is None:
            return

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        click_x = action_data.get('x', 0)
        click_y = action_data.get('y', 0)

        self._total_clicks[game_key] = self._total_clicks.get(game_key, 0) + 1

        # Measure complexity before and after
        complexity_before = self._measure_complexity(frame_before)
        complexity_after = self._measure_complexity(frame_after)

        if game_key not in self._complexity_history:
            self._complexity_history[game_key] = []
        self._complexity_history[game_key].append(complexity_after)

        # Detect destruction: complexity decreased significantly
        if complexity_before > 0 and complexity_after < complexity_before * 0.9:
            if game_key not in self._destructive_positions:
                self._destructive_positions[game_key] = set()
            self._destructive_positions[game_key].add((click_x // 4, click_y // 4))
            self._destruction_count[game_key] = self._destruction_count.get(game_key, 0) + 1

    @staticmethod
    def _measure_complexity(frame: Any) -> float:
        """Measure frame complexity as number of distinct non-zero colored regions."""
        try:
            colors: Set[int] = set()
            non_zero = 0
            if isinstance(frame, list):
                for row in frame:
                    for pixel in row:
                        val = int(pixel) if hasattr(pixel, '__int__') else pixel
                        if val != 0:
                            colors.add(val)
                            non_zero += 1
            else:
                import numpy as np
                arr = np.array(frame)
                non_zero_mask = arr != 0
                colors = set(int(v) for v in np.unique(arr[non_zero_mask]))
                non_zero = int(np.sum(non_zero_mask))

            return len(colors) * 10 + non_zero * 0.01
        except Exception:
            return 0.0


class BudgetAwarePlanningRung(DecisionRung):
    """Adjust behavior based on remaining action budget - FILTER

    Cross-cutting fix for all games but especially LS20 (42 moves/level):
    1. Early game (0-30% budget): Encourage exploration, tolerate failures
    2. Mid game (30-70% budget): Balance explore/exploit
    3. Late game (70-100% budget): Maximize exploitation, minimize waste
    4. Critical (>90% budget): Emergency mode - only proven actions

    Also tracks "progress per action" efficiency to detect when the agent
    is wasting its budget on unproductive actions.

    ROOT CAUSE ADDRESSED: LS20's timer pressure kills exploration.
    ~42 moves per level means every action must count. The system needs
    to shift from exploration to exploitation as budget depletes.
    """
    name = "budget_aware_planning"
    category = "filter"
    default_priority = 6
    confidence_threshold = 0.2  # Low threshold - mostly provides weights

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Track productive vs wasted actions
        self._productive_actions: Dict[str, int] = {}
        self._total_actions: Dict[str, int] = {}

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        budget_used = context.get('budget_used_percent', 0)
        action_count = context.get('action_count', 0)
        action_budget = context.get('action_budget', 400)

        if action_budget <= 0:
            return RungResult()

        remaining_pct = 1.0 - budget_used

        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        puzzle_type = context.get('puzzle_type', 'unknown')
        game_key = f"{game_type}_L{level}"

        # Part 7.2: Deliberate experimentation mode
        # Levels 1-2: LEARNING phase - maximize information gain
        # Level 3: TRANSITIONING - start applying learned rules
        # Levels 4+: APPLYING - exploit knowledge to complete levels
        level_phase = context.get('level_phase', 'learning')
        if not level_phase or level_phase == 'learning':
            # Re-derive from level in case context didn't populate it
            if level <= 2:
                level_phase = 'learning'
            elif level == 3:
                level_phase = 'transitioning'
            else:
                level_phase = 'applying'

        # Calculate efficiency
        productive = self._productive_actions.get(game_key, 0)
        total = self._total_actions.get(game_key, 0)
        efficiency = productive / max(total, 1)

        # Phase-based behavior modification
        if remaining_pct < 0.10:
            # CRITICAL: Less than 10% budget remaining
            # Only allow actions with known positive outcomes
            # In learning phase, still don't penalize exploration
            exploration_penalty = 0.0 if level_phase == 'learning' else 0.7
            return RungResult(
                confidence=0.3,
                reason=f"CRITICAL budget: {remaining_pct:.0%} remaining, {action_count}/{action_budget} used. Efficiency: {efficiency:.0%}",
                metadata={
                    'budget_phase': 'critical',
                    'budget_remaining_pct': remaining_pct,
                    'efficiency': efficiency,
                    'confidence_boost': 0.3,  # Boost confidence of exploitation rungs
                    'level_phase': level_phase,
                    'puzzle_type': puzzle_type,
                    'exploration_penalty': exploration_penalty,
                }
            )
        elif remaining_pct < 0.30:
            # LATE: Shift strongly toward exploitation
            # In learning phase, never penalize exploration
            exploration_penalty = 0.0 if level_phase == 'learning' else 0.5
            return RungResult(
                reason=f"Late budget: {remaining_pct:.0%} remaining. Efficiency: {efficiency:.0%}",
                metadata={
                    'budget_phase': 'late',
                    'budget_remaining_pct': remaining_pct,
                    'efficiency': efficiency,
                    'exploration_penalty': exploration_penalty,
                    'level_phase': level_phase,
                    'puzzle_type': puzzle_type,
                }
            )
        elif remaining_pct < 0.70:
            # MID: Balanced
            exploration_penalty = 0.0 if level_phase == 'learning' else 0.0
            return RungResult(
                reason=f"Mid budget: {remaining_pct:.0%} remaining. Efficiency: {efficiency:.0%}",
                metadata={
                    'budget_phase': 'mid',
                    'budget_remaining_pct': remaining_pct,
                    'efficiency': efficiency,
                    'level_phase': level_phase,
                    'puzzle_type': puzzle_type,
                    'exploration_penalty': exploration_penalty,
                }
            )

        # EARLY: Full exploration allowed
        return RungResult(
            metadata={
                'budget_phase': 'early',
                'budget_remaining_pct': remaining_pct,
                'level_phase': level_phase,
                'puzzle_type': puzzle_type,
                'exploration_penalty': 0.0,
            }
        )

    def on_action_complete(
        self,
        action: str,
        action_data: Dict[str, Any],
        frame_before: Any,
        frame_after: Any,
        context: Dict[str, Any]
    ) -> None:
        """Track action productivity."""
        game_type = context.get('game_type', '')
        level = context.get('level', 1)
        game_key = f"{game_type}_L{level}"

        self._total_actions[game_key] = self._total_actions.get(game_key, 0) + 1

        # Count as productive if frame changed
        frame_changed = False
        try:
            if frame_before is not None and frame_after is not None:
                if isinstance(frame_before, list) and isinstance(frame_after, list):
                    frame_changed = frame_before != frame_after
                else:
                    import numpy as np
                    frame_changed = not np.array_equal(frame_before, frame_after)
        except Exception:
            pass

        if frame_changed:
            self._productive_actions[game_key] = self._productive_actions.get(game_key, 0) + 1


class TheoryContradictionRung(DecisionRung):
    """Filter actions that contradict current working theory - FILTER

    Wires: engines/cognition/metacognition.py:get_contradicted_actions()

    When metacognition's theory revision marks actions as contradicted
    (failed prediction -> action disproven), this rung applies negative
    weights to those actions, preventing repeated mistakes.
    """
    name = "theory_contradiction"
    category = "filter"
    default_priority = 17  # After death_avoidance (15), before hypothesis
    confidence_threshold = 0.3

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            # Get actions contradicted by failed theories
            if not hasattr(me, 'get_contradicted_actions'):
                return RungResult()

            contradicted = me.get_contradicted_actions()

            if not contradicted:
                return RungResult()

            # Build penalty weights for contradicted actions (available only)
            weights = get_available_action_weights(context, 1.0)
            penalized = []

            for action_str, contradiction_count in contradicted.items():
                if action_str in weights:
                    # More contradictions = stronger penalty
                    # 1 contradiction = 0.7, 2 = 0.5, 3+ = 0.3
                    penalty = min(0.7, 0.2 * contradiction_count)
                    weights[action_str] = max(0.3, 1.0 - penalty)
                    penalized.append(f"{action_str}({contradiction_count})")

            if not penalized:
                return RungResult()

            return RungResult(
                confidence=0.5,
                reason=f"Theory contradictions: {', '.join(penalized)}",
                weights=weights,
                metadata={'contradicted_actions': contradicted}
            )
        except Exception as e:
            return RungResult(reason=f"Theory contradiction failed: {e}")


class ViralPackageWeightsRung(DecisionRung):
    """Apply action weights from viral information packages - FILTER

    Wires: engines/social/viral_package_engine.py:get_package_action_weights()

    Viral packages carry knowledge from winning strategies that spread
    across the agent population. Each package contains action sequences
    weighted by success rate, infection strength, and emotional compatibility.

    This rung reads those packages and converts them to action weights,
    closing the loop: winning sequences -> viral packages -> action decisions.

    Data flow:
        winning_sequences -> viral_information_packages (post-game)
        -> agent_viral_infections (horizontal transfer)
        -> get_package_action_weights() (this rung reads)
        -> action weights applied to decision
    """
    name = "viral_package_weights"
    category = "filter"
    default_priority = 20  # After pariah_avoidance (19), before hypothesis
    confidence_threshold = 0.0  # Modifies weights, not a direct action

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        vpe = self.engines.viral_package_engine
        if vpe is None:
            return RungResult()

        try:
            agent_id = context.get('agent_id', '')
            if not agent_id:
                return RungResult()

            if not hasattr(vpe, 'get_package_action_weights'):
                return RungResult()

            generation = context.get('generation', 0)
            raw_weights = vpe.get_package_action_weights(
                agent_id=agent_id,
                generation=generation,
                track_retrieval=True,
            )

            if not raw_weights:
                return RungResult()

            # Convert int action keys to ACTION strings and normalize
            # get_package_action_weights returns {action_int: weight_float}
            weights: Dict[str, float] = {}
            max_weight = max(raw_weights.values()) if raw_weights else 1.0
            boosted_actions = []

            for action_num, weight in raw_weights.items():
                action = f'ACTION{action_num}'
                # Validate action is available in this game
                if not is_action_available(action, context):
                    continue
                # Normalize to 0.5-1.5 range (boost, not replace)
                normalized = 0.5 + (weight / max(max_weight, 0.001))
                weights[action] = min(1.5, normalized)
                if normalized > 1.0:
                    boosted_actions.append(f"{action}({normalized:.2f})")

            if weights:
                return RungResult(
                    confidence=0.35,
                    weights=weights,
                    reason=f"Viral packages: {len(raw_weights)} actions weighted, {len(boosted_actions)} boosted",
                    metadata={
                        'package_count': len(raw_weights),
                        'boosted': boosted_actions[:5],
                    }
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Viral package weights failed: {e}")


class MetacognitiveEliminationRung(DecisionRung):
    """Penalize actions that metacognition has systematically eliminated - FILTER

    Wires: engines/cognition/metacognition.py:get_eliminated_actions()

    The metacognitive engine tracks actions that consistently fail for a
    given game/level (e.g., ACTION3 always leads to death on level 2 of ft09).
    These eliminations are stored in metacognitive_eliminations table with
    confidence scores.

    This rung reads those eliminations and applies heavy weight penalties,
    effectively steering the agent away from provably bad actions without
    hard-blocking them (in case context has changed).

    Unlike contextual_failure (position-aware), this is GLOBAL elimination
    per game_type + level.

    Data flow:
        gameplay failures -> metacognitive_eliminations (recorded by MetacognitiveReasoningEngine)
        -> get_eliminated_actions() (this rung reads)
        -> heavy weight penalties on eliminated actions
    """
    name = "metacognitive_elimination"
    category = "filter"
    default_priority = 16  # Right with death_avoidance
    confidence_threshold = 0.0  # Modifies weights

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        me = self.engines.metacognitive_engine
        if me is None:
            return RungResult()

        try:
            if not hasattr(me, 'get_eliminated_actions'):
                return RungResult()

            game_type = context.get('game_type', '')
            level = context.get('level', 1)

            if not game_type:
                return RungResult()

            eliminated = me.get_eliminated_actions(
                game_type=game_type,
                level_number=level,
                min_confidence=0.6,
            )

            if not eliminated:
                return RungResult()

            # Build penalty weights for eliminated actions (available only)
            weights = get_available_action_weights(context, 1.0)
            penalized = []

            for action_str in eliminated:
                # Normalize action format
                if not action_str.startswith('ACTION'):
                    action_str = f'ACTION{action_str}'
                if action_str in weights:
                    # Heavy penalty: 0.1 weight (nearly eliminated but not hard-blocked)
                    weights[action_str] = 0.1
                    penalized.append(action_str)

            if penalized:
                return RungResult(
                    confidence=0.6,
                    weights=weights,
                    reason=f"Metacognitive eliminations: {', '.join(penalized)}",
                    metadata={
                        'eliminated_count': len(penalized),
                        'eliminated_actions': penalized,
                    }
                )
            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Metacognitive elimination failed: {e}")


class ContextualFailureRung(DecisionRung):
    """Track contextual failures - position/direction/object-aware - FILTER

    Unlike global action elimination, tracks CONTEXTUAL failure signatures:
    - Position region where failure occurred
    - Direction of movement (toward/away from object)
    - Nearby object types at time of failure

    This allows "ACTION3 toward wall at (3,4)" to be avoided without
    eliminating ACTION3 globally (which could deadlock all movement).

    Failure signatures decay over time (things can change).
    """
    name = "contextual_failure"
    category = "filter"
    default_priority = 14  # Before death_avoidance
    confidence_threshold = 0.3

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # In-memory failure signatures (per game_type, per level)
        # Structure: {(game_type, level): [FailureSignature, ...]}
        self._failure_signatures: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
        self._max_signatures_per_level = 50
        self._signature_decay_rate = 0.1  # Per evaluation cycle

    def _compute_position_region(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Bucket position into regions for fuzzy matching."""
        # 3x3 region bucketing - positions (0,0), (0,1), (0,2) all -> region (0, 0)
        return (position[0] // 3, position[1] // 3)

    def _compute_movement_direction(self, action: str, nearby_objects: List[Dict]) -> str:
        """Determine if action moves toward/away/parallel to nearest object."""
        # Simplified: Map actions to directions
        action_directions = {
            'ACTION1': 'up', 'ACTION2': 'down',
            'ACTION3': 'left', 'ACTION4': 'right',
            'ACTION5': 'stay', 'ACTION7': 'special',
        }
        direction = action_directions.get(action, 'unknown')

        if not nearby_objects:
            return 'no_nearby_object'

        # For simplicity, just return the direction - full implementation would
        # compute vector from agent to nearest object and compare
        return f"{direction}_near_object"

    def record_failure(
        self,
        game_type: str,
        level: int,
        position: Tuple[int, int],
        action: str,
        nearby_objects: List[Dict[str, Any]],
        outcome: str = 'death'
    ) -> None:
        """Record a contextual failure signature."""
        key = (game_type, level)

        if key not in self._failure_signatures:
            self._failure_signatures[key] = []

        signature = {
            'game_type': game_type,
            'level': level,
            'position_region': self._compute_position_region(position),
            'action': action,
            'movement_context': self._compute_movement_direction(action, nearby_objects),
            'nearby_colors': [o.get('color') for o in nearby_objects[:3]],
            'outcome': outcome,
            'confidence': 0.8,  # Initial confidence
            'created_at': datetime.now().isoformat(),
        }

        self._failure_signatures[key].append(signature)

        # Prune old signatures
        if len(self._failure_signatures[key]) > self._max_signatures_per_level:
            # Remove lowest confidence signatures
            self._failure_signatures[key].sort(key=lambda s: s['confidence'], reverse=True)
            self._failure_signatures[key] = self._failure_signatures[key][:self._max_signatures_per_level]

    def _decay_signatures(self, key: Tuple[str, int]) -> None:
        """Apply decay to signatures, removing those below threshold."""
        if key not in self._failure_signatures:
            return

        decayed = []
        for sig in self._failure_signatures[key]:
            sig['confidence'] -= self._signature_decay_rate
            if sig['confidence'] > 0.2:  # Keep if still confident
                decayed.append(sig)

        self._failure_signatures[key] = decayed

    def _match_signature(
        self,
        action: str,
        position: Tuple[int, int],
        nearby_objects: List[Dict],
        signatures: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check if current context matches any failure signature."""
        current_region = self._compute_position_region(position)
        current_context = self._compute_movement_direction(action, nearby_objects)
        current_colors = set(o.get('color') for o in nearby_objects[:3])

        for sig in signatures:
            # Must match action
            if sig['action'] != action:
                continue

            # Must match position region
            if sig['position_region'] != current_region:
                continue

            # Check color overlap (at least one matching nearby color)
            sig_colors = set(sig.get('nearby_colors', []))
            if sig_colors and current_colors and not sig_colors.intersection(current_colors):
                continue

            # Match found
            return sig

        return None

    def evaluate(self, game_state: Any, context: Dict[str, Any]) -> RungResult:
        try:
            game_type = context.get('game_type', '')
            level = context.get('level', 1)
            position = context.get('agent_position', (0, 0))
            nearby_objects = context.get('nearby_objects', [])

            key = (game_type, level)

            # Apply decay each evaluation
            self._decay_signatures(key)

            signatures = self._failure_signatures.get(key, [])
            if not signatures:
                return RungResult()

            # Record failure if last action caused death/penalty
            if context.get('last_outcome') == 'death' or context.get('score_delta', 0) < 0:
                last_action = context.get('last_action')
                last_position = context.get('last_position', position)
                if last_action:
                    self.record_failure(
                        game_type=game_type,
                        level=level,
                        position=last_position,
                        action=last_action,
                        nearby_objects=nearby_objects,
                        outcome='death' if context.get('last_outcome') == 'death' else 'penalty'
                    )

            # Check each action for matching failure signatures (available only)
            weights = get_available_action_weights(context, 1.0)
            penalized_actions = []
            available = context.get('available_actions', [1, 2, 3, 4, 5, 6, 7])

            for action_num in available:
                action = f'ACTION{action_num}'
                match = self._match_signature(action, position, nearby_objects, signatures)

                if match:
                    # Penalty proportional to signature confidence
                    penalty = match['confidence'] * 0.5  # Max 50% weight reduction
                    weights[action] = max(0.3, 1.0 - penalty)
                    penalized_actions.append(
                        f"{action}@{match['position_region']}({match['confidence']:.1f})"
                    )

            if penalized_actions:
                return RungResult(
                    confidence=0.4,
                    reason=f"Contextual failures: {', '.join(penalized_actions[:3])}",
                    weights=weights,
                    metadata={
                        'matched_signatures': len(penalized_actions),
                        'total_signatures': len(signatures),
                    }
                )

            return RungResult()
        except Exception as e:
            return RungResult(reason=f"Contextual failure check failed: {e}")


# =============================================================================
# ORDERING PRESETS (DEPRECATED - Phase 6)
# =============================================================================
#
# DEPRECATION NOTICE: Static ordering presets are deprecated as of Phase 6.
# Use DecisionStrategy.COGNITIVE with CognitiveRouter for dynamic selection.
# These presets will be removed in v3.0.
#
# Migration path:
#   1. Switch strategy to COGNITIVE: DecisionRungSystem(strategy='cognitive')
#   2. CognitiveRouter handles graph-based rung selection automatically
#   3. Edge weights evolve based on observed outcomes
#
# For details see: architecture/cognitive_routing_implementation_plan.md
#



# Registry of rungs in this module
RUNGS = {
    'death_avoidance': DeathAvoidanceRung,
    'prior_lessons': PriorLessonsRung,
    'three_layer_filter': ThreeLayerFilterRung,
    'pariah_avoidance': PariahAvoidanceRung,
    'terminal_pattern': TerminalPatternRung,
    'destructive_action_detection': DestructiveActionDetectionRung,
    'budget_aware_planning': BudgetAwarePlanningRung,
    'theory_contradiction': TheoryContradictionRung,
    'viral_package_weights': ViralPackageWeightsRung,
    'metacognitive_elimination': MetacognitiveEliminationRung,
    'contextual_failure': ContextualFailureRung,
}
