import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Causal Map - Typed, persistent causal knowledge for a game.

This is where the 'leapfrog' happens:
- First few actions: slow, exploratory (filling the map)
- After mapping: fast, purposeful (executing from the map)

The causal map stores:
1. Per-position effects: "clicking HERE does THAT"
2. Cross-position rules: "clicking any cell toggles its neighbors"
3. Goal plans: "to match the goal, change THESE cells in THIS order"
4. Confidence: how sure we are about each mapping

The map feeds BACK into perception (Channel 5), creating the loop:
    ACT -> MAP.update() -> PERCEIVE reads MAP -> THINK -> MAP informs ACT
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TileEffect:
    """What happens when you click a specific tile position."""
    position: Tuple[int, int]              # (x, y) of the clicked tile
    affected: List[Tuple[int, int]]        # Positions that change when this is clicked
    color_transitions: Dict[Tuple[int, int], List[Tuple[int, int]]]
    # {(x,y): [(old_color, new_color), ...]} -- observed color changes
    observation_count: int = 0
    last_frame_changed: bool = True
    confidence: float = 0.0
    # Gap 4: Track goal-directedness of this effect
    productive_count: int = 0              # Times clicking here moved toward goal
    destructive_count: int = 0             # Times clicking here moved away from goal
    neutral_count: int = 0                 # Times clicking here changed nothing goal-relevant

    def __post_init__(self):
        """Update confidence from observation count."""
        self.confidence = min(0.95, 0.3 + (self.observation_count * 0.15))

    @property
    def productivity_rate(self) -> float:
        """How often clicking here is productive (0-1)."""
        total = self.productive_count + self.destructive_count + self.neutral_count
        if total == 0:
            return 0.5  # Unknown
        return self.productive_count / total


@dataclass
class CausalRule:
    """A generalized rule extracted from multiple TileEffects."""
    rule_type: str                         # "von_neumann", "moore", "toggle", "cycle", etc.
    description: str                       # "Clicking toggles self + 4 cardinal neighbors"
    evidence_count: int = 0                # How many observations support this
    confidence: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    # e.g. {"neighborhood": "von_neumann", "toggle_colors": [3, 9]}


@dataclass
class PlannedAction:
    """A single step in a goal-directed plan."""
    position: Tuple[int, int]              # Where to click
    expected_changes: List[Tuple[int, int, int, int]]  # (x, y, from_color, to_color)
    reason: str                            # Why this action
    step_number: int = 0
    confidence: float = 0.0


class CausalMap:
    """
    Persistent causal knowledge for a game session.

    Stores what we've learned about cause and effect:
    - What happens when we click each position
    - What rules govern the game
    - What plan would reach the goal state

    This is the system's compressed understanding of HOW THE GAME WORKS.
    It replaces the flat dict in context_builder._world_model['causal_map'].
    """

    def __init__(self, game_id: str = ""):
        self.game_id = game_id

        # Per-position effects
        self._effects: Dict[Tuple[int, int], TileEffect] = {}

        # Known interactive positions (tiles we can click)
        self._interactive_positions: Set[Tuple[int, int]] = set()

        # Explored vs unexplored
        self._explored: Set[Tuple[int, int]] = set()
        self._all_positions: Set[Tuple[int, int]] = set()  # Set of all known tile positions

        # Generalized rules
        self._rules: List[CausalRule] = []

        # Goal state
        self._goal_cells: Dict[Tuple[int, int], int] = {}  # {(x,y): target_color}
        self._current_cells: Dict[Tuple[int, int], int] = {}  # {(x,y): current_color}

        # Plan
        self._plan: List[PlannedAction] = []
        self._plan_valid: bool = False
        self._plan_step: int = 0

        # Color cycle knowledge
        self._color_cycles: Dict[Tuple[int, int], List[int]] = {}
        # {(x,y): [color_a, color_b, color_a, ...]}

        # Movement knowledge (Gap 3C / Gap 5 -- for movement games)
        self._walls: Set[Tuple[Tuple[int, int], int]] = set()
        # {((x, y), action_type)} -- blocked movement from position
        self._open_paths: Set[Tuple[Tuple[int, int], int]] = set()
        # {((x, y), action_type)} -- successful movement from position
        self._visited_positions: Set[Tuple[int, int]] = set()
        # All positions the agent has occupied

        # Delayed effect tracking (Gap 4 -- for VC33-style games)
        self._delayed_observations: List[Dict[str, Any]] = []
        # Frames observed after an action, for detecting delayed effects

    # ─── Public Properties ────────────────────────────────────────────

    @property
    def completeness(self) -> float:
        """How much of the game we understand (0-1)."""
        if not self._all_positions:
            return 0.0
        explored_frac = len(self._explored) / len(self._all_positions)
        # Also consider rule confidence
        rule_conf = max((r.confidence for r in self._rules), default=0.0)
        return min(1.0, explored_frac * 0.7 + rule_conf * 0.3)

    @property
    def has_plan(self) -> bool:
        """Whether we have a valid plan to reach the goal."""
        return self._plan_valid and len(self._plan) > 0

    @property
    def plan(self) -> List[PlannedAction]:
        """Current goal-directed plan."""
        return self._plan

    @property
    def plan_step(self) -> int:
        """Current step in the plan."""
        return self._plan_step

    # ─── Reading the Map (for PERCEIVE channel 5) ────────────────────

    def get_known_effects(self) -> Dict[Tuple[int, int], Any]:
        """Get all known position->effect mappings."""
        return {pos: eff for pos, eff in self._effects.items()}

    def get_unexplored(self) -> List[Tuple[int, int]]:
        """Get positions we haven't explored yet."""
        return sorted(self._all_positions - self._explored)

    def lookup(self, position: Tuple[int, int]) -> Optional[TileEffect]:
        """Look up what we know about clicking a specific position."""
        return self._effects.get(position)

    def get_next_plan_action(self) -> Optional[PlannedAction]:
        """Get the next action from the plan, if we have one."""
        if not self._plan_valid or self._plan_step >= len(self._plan):
            return None
        return self._plan[self._plan_step]

    def advance_plan(self):
        """Mark current plan step as executed, advance to next."""
        self._plan_step += 1
        if self._plan_step >= len(self._plan):
            self._plan_valid = False

    # ─── Goal Progress Feedback (Gap 4) ───────────────────────────────

    def record_goal_progress(
        self,
        click_pos: Tuple[int, int],
        goal_delta_before: int,
        goal_delta_after: int,
    ):
        """
        Record whether an action moved toward or away from the goal.

        This is the key feedback signal that makes the causal map
        GOAL-DIRECTED, not just effect-tracking.
        """
        effect = self._effects.get(click_pos)
        if effect is None:
            return

        progress = goal_delta_before - goal_delta_after
        if progress > 0:
            effect.productive_count += 1
        elif progress < 0:
            effect.destructive_count += 1
        else:
            effect.neutral_count += 1

    def get_productive_targets(self) -> List[Tuple[Tuple[int, int], float]]:
        """Get positions sorted by productivity rate (best first).

        Returns list of (position, productivity_rate) for positions
        that have been productive at least once.
        """
        productive = []
        for pos, eff in self._effects.items():
            if eff.productive_count > 0:
                productive.append((pos, eff.productivity_rate))
        return sorted(productive, key=lambda x: x[1], reverse=True)

    # ─── Writing to the Map (from ACT feedback) ──────────────────────

    def register_positions(self, positions: List[Tuple[int, int]]):
        """Register known interactive positions (from visual analysis)."""
        self._all_positions.update(positions)
        self._interactive_positions.update(positions)

    def set_goal(self, goal_cells: Dict[Tuple[int, int], int]):
        """Set the target state we're trying to reach."""
        self._goal_cells = goal_cells
        self._invalidate_plan()

    def set_current_state(self, current_cells: Dict[Tuple[int, int], int]):
        """Update current state of the grid."""
        self._current_cells = current_cells

    def update_from_action(
        self,
        click_pos: Tuple[int, int],
        pre_frame: Optional[np.ndarray],
        post_frame: Optional[np.ndarray],
        frame_changed: bool,
    ):
        """
        Learn from an action's consequence.

        This is the MAP phase of the PTMA loop:
        We clicked at click_pos, and the frame changed (or didn't).
        Record what happened so we know for next time.
        """
        self._explored.add(click_pos)

        if pre_frame is None or post_frame is None:
            return

        if not frame_changed:
            # Clicking here did nothing — record that
            if click_pos not in self._effects:
                self._effects[click_pos] = TileEffect(
                    position=click_pos,
                    affected=[],
                    color_transitions={},
                    observation_count=1,
                    last_frame_changed=False,
                )
            else:
                self._effects[click_pos].observation_count += 1
                self._effects[click_pos].last_frame_changed = False
            return

        # Frame changed — find what changed
        try:
            if pre_frame.shape != post_frame.shape:
                return
            diff_mask = pre_frame != post_frame
            if not diff_mask.any():
                return

            ys, xs = np.where(diff_mask)
            affected = []
            color_transitions: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)

            for i in range(len(ys)):
                y, x = int(ys[i]), int(xs[i])
                old_c = int(pre_frame[y, x])
                new_c = int(post_frame[y, x])
                pos = (x, y)
                affected.append(pos)
                color_transitions[pos].append((old_c, new_c))

            # Deduplicate affected positions
            affected_unique = sorted(set(affected))

            if click_pos in self._effects:
                # Update existing effect
                eff = self._effects[click_pos]
                eff.affected = affected_unique
                for pos, transitions in color_transitions.items():
                    if pos not in eff.color_transitions:
                        eff.color_transitions[pos] = []
                    eff.color_transitions[pos].extend(transitions)
                eff.observation_count += 1
                eff.last_frame_changed = True
                eff.confidence = min(0.95, 0.3 + (eff.observation_count * 0.15))
            else:
                self._effects[click_pos] = TileEffect(
                    position=click_pos,
                    affected=affected_unique,
                    color_transitions=dict(color_transitions),
                    observation_count=1,
                    last_frame_changed=True,
                )

            # Update color cycle knowledge
            self._update_color_cycles(color_transitions)

            # Try to extract rules from accumulated effects
            self._try_extract_rules()

            # Invalidate plan (state changed, plan may no longer be valid)
            self._invalidate_plan()

        except Exception as e:
            logger.debug(f"[CAUSAL-MAP] update_from_action failed: {e}")

    # ─── Planning ─────────────────────────────────────────────────────

    def plan_to_goal(self) -> List[PlannedAction]:
        """
        Use known rules to compute a plan from current to goal state.

        Returns an ordered list of actions that should transform
        current state into goal state, based on known causal effects.

        Gap 3: Enhanced with color cycle awareness -- if we know a
        position cycles through [A, B, C], and current=A, goal=C,
        we need 2 clicks, not 1.
        """
        if not self._goal_cells or not self._current_cells:
            return []

        # Find cells that need to change
        delta = {}
        for pos, goal_color in self._goal_cells.items():
            current_color = self._current_cells.get(pos)
            if current_color is not None and current_color != goal_color:
                delta[pos] = (current_color, goal_color)

        if not delta:
            # Already at goal!
            return []

        plan = []
        step = 0

        for target_pos, (current_c, goal_c) in delta.items():
            # Strategy 1: Use color cycle knowledge for direct computation
            cycle = self._color_cycles.get(target_pos, [])
            if len(cycle) >= 2:
                # Deduplicate to find the cycle pattern
                unique_cycle = []
                for c in cycle:
                    if not unique_cycle or c != unique_cycle[-1]:
                        unique_cycle.append(c)
                # Check if both colors are in the cycle
                if current_c in unique_cycle and goal_c in unique_cycle:
                    ci = unique_cycle.index(current_c)
                    gi = unique_cycle.index(goal_c)
                    # Compute forward clicks needed
                    clicks_needed = (gi - ci) % len(unique_cycle)
                    if clicks_needed == 0:
                        clicks_needed = len(unique_cycle)  # Full cycle
                    # Find click position that affects this target
                    click_at = self._find_click_for_target(target_pos)
                    if click_at is not None:
                        for _ in range(clicks_needed):
                            plan.append(PlannedAction(
                                position=click_at,
                                expected_changes=[(target_pos[0], target_pos[1], current_c, goal_c)],
                                reason=f"Cycle ({target_pos[0]},{target_pos[1]}) {current_c}->{goal_c} ({clicks_needed} clicks)",
                                step_number=step,
                                confidence=min(0.9, 0.4 + len(unique_cycle) * 0.1),
                            ))
                            step += 1
                        continue

            # Strategy 2: Find any effect that produces the desired transition
            best_click = None
            best_changes = []

            for click_pos, effect in self._effects.items():
                if target_pos in [p for p in effect.affected]:
                    transitions = effect.color_transitions.get(target_pos, [])
                    for old_c, new_c in transitions:
                        if old_c == current_c and new_c == goal_c:
                            expected = [
                                (p[0], p[1], current_c, goal_c)
                                for p in effect.affected[:5]
                            ]
                            best_click = click_pos
                            best_changes = expected
                            break
                    if best_click:
                        break

            if best_click:
                plan.append(PlannedAction(
                    position=best_click,
                    expected_changes=best_changes,
                    reason=f"Change ({target_pos[0]},{target_pos[1]}) from {current_c} to {goal_c}",
                    step_number=step,
                    confidence=self._effects[best_click].confidence,
                ))
                step += 1

        self._plan = plan
        self._plan_valid = len(plan) > 0
        self._plan_step = 0
        return plan

    def _find_click_for_target(self, target_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find which position to click to affect the target position."""
        # First check: does clicking the target itself affect it?
        if target_pos in self._effects and target_pos in self._effects[target_pos].affected:
            return target_pos
        # Otherwise search all effects for one that affects this target
        for click_pos, effect in self._effects.items():
            if target_pos in effect.affected:
                return click_pos
        return target_pos  # Default: try clicking the target directly

    # ─── Information Gain ─────────────────────────────────────────────

    def information_gain(self, position: Tuple[int, int]) -> float:
        """
        How much would clicking this position teach us?

        High for unexplored positions, low for well-understood ones.
        This drives the EXPLORE speed of action selection.
        """
        if position not in self._all_positions:
            return 0.5  # Unknown position, medium curiosity

        if position not in self._explored:
            return 1.0  # Never clicked, maximum curiosity

        effect = self._effects.get(position)
        if effect is None:
            return 0.8  # Clicked but no effect recorded?

        if effect.observation_count >= 3:
            return 0.1  # Well-understood, low curiosity

        if effect.observation_count == 1:
            return 0.6  # Only one observation, might learn more

        return 0.3  # Some observations, decreasing curiosity

    def best_exploration_target(self) -> Optional[Tuple[int, int]]:
        """Get the position with highest information gain."""
        if not self._all_positions:
            return None

        best_pos = None
        best_gain = -1.0

        for pos in self._all_positions:
            gain = self.information_gain(pos)
            if gain > best_gain:
                best_gain = gain
                best_pos = pos

        return best_pos

    # ─── Rule Extraction ──────────────────────────────────────────────

    def _detect_grid_spacing(self) -> List[int]:
        """Detect tile grid spacing from known interactive positions.

        Returns a list of candidate spacings (most common first), falling
        back to [8] if there aren't enough positions to detect a pattern.
        """
        if len(self._all_positions) < 2:
            return [8]  # Default fallback

        # Compute pairwise distances along X and Y axes
        positions = sorted(self._all_positions)
        x_gaps: Dict[int, int] = {}
        y_gaps: Dict[int, int] = {}

        for i, (x1, y1) in enumerate(positions):
            for x2, y2 in positions[i + 1:]:
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                if 2 <= dx <= 32 and dy == 0:  # Same row, reasonable gap
                    x_gaps[dx] = x_gaps.get(dx, 0) + 1
                if 2 <= dy <= 32 and dx == 0:  # Same column, reasonable gap
                    y_gaps[dy] = y_gaps.get(dy, 0) + 1

        # Find the most common gaps
        candidates = set()
        if x_gaps:
            best_x = max(x_gaps, key=x_gaps.get)
            candidates.add(best_x)
        if y_gaps:
            best_y = max(y_gaps, key=y_gaps.get)
            candidates.add(best_y)

        if not candidates:
            return [8]  # Default fallback

        return sorted(candidates)

    def _try_extract_rules(self):
        """Try to generalize from individual effects to rules."""
        if len(self._effects) < 3:
            return  # Not enough data

        # Detect grid spacing from known interactive positions
        spacing = self._detect_grid_spacing()

        # Check for von Neumann neighborhood pattern
        # (clicking toggles self + 4 cardinal neighbors)
        vn_evidence = 0
        total_effects = 0

        for click_pos, effect in self._effects.items():
            if not effect.last_frame_changed:
                continue
            total_effects += 1

            affected_set = set(effect.affected)
            if click_pos in affected_set:
                # Check if affected positions form a cross pattern
                cx, cy = click_pos
                # Try each detected spacing
                found_vn = False
                for sp in spacing:
                    expected_vn = {
                        (cx, cy),
                        (cx - sp, cy), (cx + sp, cy),
                        (cx, cy - sp), (cx, cy + sp),
                    }
                    overlap = len(affected_set & expected_vn)
                    if overlap >= 3:
                        vn_evidence += 1
                        found_vn = True
                        break
                if not found_vn:
                    # Fallback: check if ANY 4 affected positions form a cross
                    # by computing distances from click_pos
                    dists = sorted(
                        {abs(ax - cx) + abs(ay - cy) for (ax, ay) in affected_set if (ax, ay) != click_pos}
                    )
                    # If all same distance and >=4 points -> cross-like
                    if len(dists) >= 1 and len(affected_set) >= 3:
                        cardinal_dist = dists[0] if dists else 0
                        if cardinal_dist > 0:
                            expected_vn = {
                                (cx, cy),
                                (cx - cardinal_dist, cy), (cx + cardinal_dist, cy),
                                (cx, cy - cardinal_dist), (cx, cy + cardinal_dist),
                            }
                            overlap = len(affected_set & expected_vn)
                            if overlap >= 3:
                                vn_evidence += 1

        if total_effects > 0 and vn_evidence / total_effects > 0.5:
            # Von Neumann rule detected
            existing_vn = [r for r in self._rules if r.rule_type == 'von_neumann']
            if not existing_vn:
                self._rules.append(CausalRule(
                    rule_type='von_neumann',
                    description='Clicking toggles self + 4 cardinal neighbors',
                    evidence_count=vn_evidence,
                    confidence=min(0.9, vn_evidence / total_effects),
                ))
            else:
                existing_vn[0].evidence_count = vn_evidence
                existing_vn[0].confidence = min(0.9, vn_evidence / total_effects)

        # Check for simple toggle (clicking only affects self)
        self_only = sum(
            1 for eff in self._effects.values()
            if eff.last_frame_changed and len(set(eff.affected)) == 1
        )
        if total_effects > 0 and self_only / total_effects > 0.5:
            existing_toggle = [r for r in self._rules if r.rule_type == 'self_toggle']
            if not existing_toggle:
                self._rules.append(CausalRule(
                    rule_type='self_toggle',
                    description='Clicking toggles only the clicked cell',
                    evidence_count=self_only,
                    confidence=min(0.9, self_only / total_effects),
                ))

    def _update_color_cycles(
        self, transitions: Dict[Tuple[int, int], List[Tuple[int, int]]]
    ):
        """Track color cycling patterns at each position."""
        for pos, trans_list in transitions.items():
            if pos not in self._color_cycles:
                self._color_cycles[pos] = []
            for old_c, new_c in trans_list:
                cycle = self._color_cycles[pos]
                if not cycle:
                    cycle.append(old_c)
                cycle.append(new_c)

    def _invalidate_plan(self):
        """Mark the current plan as potentially invalid."""
        self._plan_valid = False

    # ─── Movement Knowledge (Gap 3C / Gap 5) ─────────────────────────

    def record_movement_result(
        self,
        action_type: int,
        agent_pos_before: Optional[Tuple[int, int]],
        agent_pos_after: Optional[Tuple[int, int]],
    ):
        """
        Record whether a directional action moved the agent.

        For movement games: tracks walls (action didn't move)
        and open paths (action did move). This builds a spatial
        map for pathfinding (Gap 3C).
        """
        if agent_pos_before is None or agent_pos_after is None:
            return
        moved = agent_pos_before != agent_pos_after
        if not moved:
            # Wall detected: from this position, this direction is blocked
            self._walls.add((agent_pos_before, action_type))
        else:
            # Open path: from this position, this direction works
            self._open_paths.add((agent_pos_before, action_type))
            self._visited_positions.add(agent_pos_after)

    def is_wall(self, position: Tuple[int, int], action: int) -> bool:
        """Check if moving in a direction from a position is blocked."""
        return (position, action) in self._walls

    def get_visited_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions the agent has visited."""
        return self._visited_positions

    # ─── Import from existing world_model dict ────────────────────────

    def import_from_world_model(self, world_model: Dict[str, Any]):
        """
        Import data from the existing context_builder._world_model dict.

        This bridges the old flat dict format to the typed CausalMap.
        """
        try:
            causal_dict = world_model.get('causal_map', {})
            for pos_key, effect_data in causal_dict.items():
                try:
                    # Parse position key
                    if isinstance(pos_key, str):
                        parts = pos_key.strip('()').split(',')
                        pos = (int(parts[0].strip()), int(parts[1].strip()))
                    elif isinstance(pos_key, tuple):
                        pos = pos_key
                    else:
                        continue

                    affected = effect_data.get('affected_cells', [])
                    self._effects[pos] = TileEffect(
                        position=pos,
                        affected=affected,
                        color_transitions=effect_data.get('color_transitions', {}),
                        observation_count=effect_data.get('observations', 1),
                        last_frame_changed=True,
                    )
                    self._explored.add(pos)
                    self._all_positions.add(pos)
                except Exception:
                    continue

            # Import goal state
            goal = world_model.get('goal_state', {})
            if goal:
                self._goal_cells = goal

            # Import current state
            cells = world_model.get('cell_states', {})
            if cells:
                self._current_cells = cells

        except Exception as e:
            logger.debug(f"[CAUSAL-MAP] Import from world_model failed: {e}")

    # ─── Serialization ────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Export to dict for storage/logging."""
        return {
            'game_id': self.game_id,
            'effects_count': len(self._effects),
            'explored_count': len(self._explored),
            'all_positions_count': len(self._all_positions),
            'rules': [
                {'type': r.rule_type, 'desc': r.description,
                 'evidence': r.evidence_count, 'confidence': r.confidence}
                for r in self._rules
            ],
            'completeness': self.completeness,
            'has_plan': self.has_plan,
            'plan_length': len(self._plan),
            'plan_step': self._plan_step,
        }

    def summary(self) -> str:
        """One-line summary for logging."""
        rules_str = ", ".join(r.rule_type for r in self._rules) if self._rules else "none"
        wall_str = ""
        if self._walls:
            wall_str = f" walls:{len(self._walls)}"
        productive = sum(1 for e in self._effects.values() if e.productive_count > 0)
        prod_str = f" productive:{productive}" if productive else ""
        return (
            f"[MAP] effects:{len(self._effects)} explored:{len(self._explored)}/{len(self._all_positions)} "
            f"rules:[{rules_str}] complete:{self.completeness:.0%} plan:{'yes' if self.has_plan else 'no'}"
            f"{wall_str}{prod_str}"
        )
