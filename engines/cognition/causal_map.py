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
    # Prediction-surprise: track which action context this was observed under
    context_tags: List[Tuple[int, ...]] = field(default_factory=list)
    # Each tag is the action_context tuple at time of observation
    surprise_count: int = 0                # Times prediction was wrong at this position
    prediction_count: int = 0              # Times we predicted before clicking here

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

    @property
    def reliability(self) -> float:
        """How reliably we can predict effects at this position (0-1).

        Low reliability means the position's effects are context-dependent.
        """
        if self.prediction_count == 0:
            return 0.5  # Unknown
        return 1.0 - (self.surprise_count / self.prediction_count)


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


@dataclass
class Prediction:
    """What we expect to happen when clicking a position."""
    position: Tuple[int, int]
    expected_affected: List[Tuple[int, int]]  # Positions we expect to change
    expected_transitions: Dict[Tuple[int, int], Tuple[int, int]]
    # {(x,y): (from_color, to_color)} -- predicted color changes
    confidence: float = 0.0
    source: str = "effects"  # 'effects', 'context_rule', 'cycle'


@dataclass
class SurpriseEvent:
    """A prediction failure -- the world did something unexpected."""
    position: Tuple[int, int]              # Where the action was
    action_context: Tuple[int, ...]        # Recent action history preceding this
    predicted_affected: int                # How many cells we expected to change
    actual_affected: int                   # How many actually changed
    predicted_change: bool                 # Did we expect a frame change?
    actual_change: bool                    # Did the frame actually change?
    mismatch_type: str                     # 'new_effects', 'missing_effects', 'different_effects'
    step_number: int = 0


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

        # HUD/environmental state tracking (Gap 5B)
        self._hud_change_positions: Dict[Tuple[int, int], int] = {}
        # {(x,y): count} -- positions whose actions caused HUD changes

        # ─── Tile Abstraction Layer ───────────────────────────────────
        # Maps raw pixel regions to logical tile coordinates.
        # When populated, update_from_action() aggregates pixel-level
        # diffs into tile-level effects -- fixing the pixel-vs-tile
        # granularity problem that produced "38 cells affected" artifacts.
        self._tile_map: Optional[Dict[str, Any]] = None
        # Structure: {
        #   'bounds': (y_min, x_min, y_max, x_max),  # panel bounds
        #   'rows': int, 'cols': int,
        #   'tile_w': int, 'tile_h': int,
        #   'sep_w': int,  # separator width between tiles
        # }

        # Object collision tracking (LS20 -- movement game interactions)
        self._collision_effects: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        # {object_color: [{hud_before, hud_after, position, ...}]}

        # ─── Prediction-Surprise-Context System ───────────────────────
        # Enables discovery of context-dependent mechanics (camera pans,
        # mode switches, state-dependent effects) through prediction
        # failure analysis rather than hardcoded assumptions.

        # Rolling window of recent action types (last N actions)
        self._action_context: List[int] = []
        self._context_window_size: int = 5

        # Surprise log -- prediction failures with their action context
        self._surprise_log: List[SurpriseEvent] = []
        self._max_surprise_log: int = 200

        # Context-dependent effects: when the SAME position produces
        # DIFFERENT effects depending on what actions preceded the click.
        # Key: context prefix tuple (e.g., (2,) means "after ACTION2")
        # Value: dict of position -> observed TileEffect under that context
        self._context_effects: Dict[
            Tuple[int, ...],
            Dict[Tuple[int, int], TileEffect]
        ] = {}

        # Total steps for surprise event numbering
        self._total_steps: int = 0

        # ─── H47: Score-Correlated Goal Discovery ─────────────────────
        # Learn goal states from score feedback instead of solver seeds.
        # Tracks which cell colors correlate with +score / -score.
        self._score_positive_states: Dict[
            Tuple[int, int], Dict[int, int]
        ] = defaultdict(dict)  # {(x,y): {color: count}}
        self._score_negative_states: Dict[
            Tuple[int, int], Dict[int, int]
        ] = defaultdict(dict)
        self._score_observations: int = 0
        self._goal_source: str = ''  # 'perceiver', 'score_correlation'

        # ─── H53: Win-State Goal Templates ────────────────────────────
        # When a level completes, capture the winning board state so future
        # sessions can use it as a goal without needing solver data or a
        # reference panel. Keyed by level number (1-based).
        self._win_templates: Dict[int, Dict[Tuple[int, int], int]] = {}
        # {level: {(x,y): color}} — the board state right before level-up

        # ─── Solver-Seeded Knowledge (H34) ────────────────────────────
        # Per-level ordered list of positions from solver sequences.
        # Used by H26 pixel targeting as high-priority click targets.
        self._solver_targets: Dict[int, List[Tuple[int, int]]] = {}
        # {level_number: [(x1,y1), (x2,y2), ...]} -- solver click order

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

    def get_solver_targets(self, level: int) -> List[Tuple[int, int]]:
        """Get solver-seeded target positions for a specific level."""
        return self._solver_targets.get(level, [])

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

    def reset_for_new_level(self):
        """Reset level-specific state while preserving game-level knowledge.

        PRESERVES (game-level mechanics that carry across levels):
        - _effects: position->effect mappings (mechanics don't change)
        - _rules: generalized causal rules
        - _color_cycles: tile color cycling patterns
        - _tile_map: tile grid structure (layout may change per level but
          the tile SIZE usually stays the same -- re-detected from perception)
        - _collision_effects: object collision knowledge (LS20)
        - _walls: known wall positions (LS20 maze layout may change, but
          the CONCEPT of walls persists)
        - _open_paths: known open paths
        - _context_effects: context-dependent effect knowledge
        - _surprise_log: prediction failures inform future predictions
        - _action_context: recent action history

        RESETS (level-specific layout that changes each level):
        - _goal_cells / _current_cells: new level = new goal layout
        - _plan / _plan_valid / _plan_step: old plan is invalid
        - _explored / _all_positions: new spatial layout to discover
        - _interactive_positions: new interactive region
        - _visited_positions: start fresh exploration
        - _delayed_observations: stale temporal data
        - _hud_change_positions: HUD layout may change
        - _tile_map: cleared so perception re-detects for new level
        """
        # Level-specific layout resets
        self._goal_cells = {}
        self._current_cells = {}
        self._plan = []
        self._plan_valid = False
        self._plan_step = 0
        self._explored = set()
        self._all_positions = set()
        self._interactive_positions = set()
        self._visited_positions = set()
        self._delayed_observations = []
        self._hud_change_positions = {}
        # Tile map is re-detected per level since layout may change
        self._tile_map = None

        # For movement games: walls from prior level may not apply to
        # new layout, but we keep them as weak priors. The agent will
        # re-confirm or override through interaction.
        # (We do NOT clear _walls or _open_paths.)

        logger.info(
            "[CAUSAL-MAP] Level reset: preserved %d effects, %d rules, "
            "%d color cycles, %d walls. Cleared goal/plan/explored/tile_map.",
            len(self._effects), len(self._rules),
            len(self._color_cycles), len(self._walls),
        )

    # ─── Prediction-Surprise-Context System ───────────────────────────
    #
    # This is how the CausalMap discovers context-dependent mechanics:
    #
    #   1. PREDICT: Before an action, predict what will happen based on
    #      known effects. "Clicking (5,3) should toggle red->blue."
    #
    #   2. OBSERVE: After the action, compare prediction to reality.
    #
    #   3. SURPRISE: If prediction was wrong, log a SurpriseEvent with
    #      the action_context (what actions preceded this one).
    #
    #   4. CORRELATE: After enough surprises, check if the same context
    #      prefix keeps appearing. "Every surprise at (5,3) happened
    #      after ACTION2" = context-dependent effect.
    #
    #   5. LEARN: Store context-dependent effects so future predictions
    #      use context: "after ACTION2, clicking (5,3) does Y instead."
    #
    # This handles camera panning, mode switches, state-dependent
    # mechanics, and any other quirk where the same position produces
    # different effects depending on recent actions.

    def record_action_context(self, action_type: int):
        """
        Record that an action was taken (any type: click, pan, move).

        This maintains the rolling context window that gets tagged
        onto observations. EVERY action must call this, not just
        clicks, because non-click actions (pans, mode switches)
        are exactly the context that explains why click effects
        change.
        """
        self._action_context.append(action_type)
        if len(self._action_context) > self._context_window_size:
            self._action_context = self._action_context[-self._context_window_size:]
        self._total_steps += 1

    def predict(self, position: Tuple[int, int]) -> Optional[Prediction]:
        """
        Predict what will happen if we click this position.

        First checks context-dependent effects (if we've learned that
        after certain actions, this position behaves differently).
        Falls back to the default position effects.

        Returns None if we have no knowledge about this position.
        """
        ctx = tuple(self._action_context)

        # Strategy 1: Check context-specific effects
        # Try progressively shorter context prefixes
        for prefix_len in range(len(ctx), 0, -1):
            prefix = ctx[-prefix_len:]
            ctx_effects = self._context_effects.get(prefix)
            if ctx_effects and position in ctx_effects:
                eff = ctx_effects[position]
                # Build prediction from context-specific knowledge
                transitions = {}
                for aff_pos, trans_list in eff.color_transitions.items():
                    if trans_list:
                        last = trans_list[-1]  # Most recent transition
                        transitions[aff_pos] = last
                return Prediction(
                    position=position,
                    expected_affected=list(eff.affected),
                    expected_transitions=transitions,
                    confidence=eff.confidence * 0.9,  # Slight discount
                    source='context_rule',
                )

        # Strategy 2: Default position effects
        eff = self._effects.get(position)
        if eff is None:
            return None

        transitions = {}
        for aff_pos, trans_list in eff.color_transitions.items():
            if trans_list:
                last = trans_list[-1]
                transitions[aff_pos] = last

        return Prediction(
            position=position,
            expected_affected=list(eff.affected),
            expected_transitions=transitions,
            confidence=eff.confidence,
            source='effects',
        )

    def check_surprise(
        self,
        click_pos: Tuple[int, int],
        prediction: Optional[Prediction],
        actual_affected: List[Tuple[int, int]],
        actual_changed: bool,
    ) -> Optional[SurpriseEvent]:
        """
        Compare prediction to actual outcome and log surprises.

        This is the key learning signal. When predictions fail, the
        action context at the time of failure tells us WHAT CAUSED
        the different outcome.

        Returns a SurpriseEvent if surprised, None if as expected.
        """
        if prediction is None:
            return None  # No prediction = nothing to be surprised about

        # Determine mismatch type
        predicted_change = len(prediction.expected_affected) > 0
        actual_set = set(actual_affected)
        predicted_set = set(prediction.expected_affected)

        # Check for surprise conditions
        surprised = False
        mismatch_type = ''

        if predicted_change != actual_changed:
            # Expected change but got none, or vice versa
            surprised = True
            mismatch_type = 'change_mismatch'
        elif actual_changed and predicted_change:
            # Both changed, but did different things change?
            overlap = predicted_set & actual_set
            union = predicted_set | actual_set

            # Check 1: spatial overlap -- are the same positions changing?
            if union and len(overlap) / len(union) < 0.6:
                surprised = True
                if actual_set - predicted_set:
                    mismatch_type = 'new_effects'
                elif predicted_set - actual_set:
                    mismatch_type = 'missing_effects'
                else:
                    mismatch_type = 'different_effects'

            # Check 2: magnitude change -- did the NUMBER of affected
            # cells change dramatically? (e.g., predicted 1 cell changed
            # but 50 changed = camera pan or mode switch)
            if not surprised and len(predicted_set) > 0:
                ratio = len(actual_set) / len(predicted_set)
                if ratio > 3.0 or ratio < 0.33:
                    surprised = True
                    mismatch_type = 'magnitude_change'

        if not surprised:
            # Update prediction success tracking
            eff = self._effects.get(click_pos)
            if eff:
                eff.prediction_count += 1
            return None

        # ─── SURPRISE DETECTED ───────────────────────────────────────
        ctx = tuple(self._action_context)
        event = SurpriseEvent(
            position=click_pos,
            action_context=ctx,
            predicted_affected=len(predicted_set),
            actual_affected=len(actual_set),
            predicted_change=predicted_change,
            actual_change=actual_changed,
            mismatch_type=mismatch_type,
            step_number=self._total_steps,
        )

        # Update surprise tracking on the effect
        eff = self._effects.get(click_pos)
        if eff:
            eff.surprise_count += 1
            eff.prediction_count += 1
            eff.context_tags.append(ctx)

        # Log the surprise
        self._surprise_log.append(event)
        if len(self._surprise_log) > self._max_surprise_log:
            self._surprise_log = self._surprise_log[-self._max_surprise_log:]

        logger.debug(
            f"[SURPRISE] at ({click_pos[0]},{click_pos[1]}) "
            f"type={mismatch_type} context={ctx} "
            f"predicted={len(predicted_set)} actual={len(actual_set)}"
        )

        # After accumulating surprises, try to learn context rules
        self._learn_context_rules()

        return event

    def _learn_context_rules(self):
        """
        Extract context-dependent rules from the surprise log.

        Pattern: if surprises at a position consistently happen after
        the same action prefix, then that prefix CHANGES what the
        position does. Store the actual effects observed under that
        context as context_effects.

        This is how the system discovers:
        - "After ACTION1 (pan up), tile positions show different content"
        - "After ACTION5 (mode switch), clicking does something else"
        - Any context-dependent mechanic, without hardcoding
        """
        if len(self._surprise_log) < 3:
            return  # Need enough data

        # Group surprises by position
        pos_surprises: Dict[Tuple[int, int], List[SurpriseEvent]] = defaultdict(list)
        for event in self._surprise_log:
            pos_surprises[event.position].append(event)

        for pos, events in pos_surprises.items():
            if len(events) < 2:
                continue

            # Find common context prefix across surprises at this position
            # Try each prefix length from 1 to context_window_size
            for prefix_len in range(1, self._context_window_size + 1):
                # Extract the prefix of each surprise's context
                prefix_counts: Dict[Tuple[int, ...], int] = defaultdict(int)
                for event in events:
                    if len(event.action_context) >= prefix_len:
                        # Use the LAST prefix_len actions as the context key
                        prefix = event.action_context[-prefix_len:]
                        prefix_counts[prefix] += 1

                # If a prefix appears in >60% of surprises at this position,
                # that prefix is the context that changes the effect
                for prefix, count in prefix_counts.items():
                    if count >= 2 and count / len(events) > 0.6:
                        # This context prefix correlates with surprises!
                        # Store the actual effects observed under this context
                        if prefix not in self._context_effects:
                            self._context_effects[prefix] = {}

                        # The actual effect under this context comes from
                        # the most recent observation at this position
                        # (the surprise showed the old prediction was wrong,
                        # so the current _effects entry IS the new-context effect)
                        eff = self._effects.get(pos)
                        if eff and pos not in self._context_effects[prefix]:
                            self._context_effects[prefix][pos] = TileEffect(
                                position=pos,
                                affected=list(eff.affected),
                                color_transitions=dict(eff.color_transitions),
                                observation_count=count,
                                last_frame_changed=eff.last_frame_changed,
                                confidence=min(0.8, count * 0.2),
                            )

                            logger.debug(
                                f"[CONTEXT-RULE] Learned: after {prefix}, "
                                f"pos ({pos[0]},{pos[1]}) has different effects "
                                f"(from {count} surprises)"
                            )

                            # Also create a CausalRule for this discovery
                            rule_type = f"context_dependent_{'_'.join(str(a) for a in prefix)}"
                            existing = [
                                r for r in self._rules if r.rule_type == rule_type
                            ]
                            if not existing:
                                self._rules.append(CausalRule(
                                    rule_type=rule_type,
                                    description=(
                                        f"After actions {prefix}, effects change "
                                        f"at {count} positions"
                                    ),
                                    evidence_count=count,
                                    confidence=min(0.8, count * 0.2),
                                    parameters={
                                        'context_prefix': list(prefix),
                                        'affected_positions': [list(pos)],
                                    },
                                ))

    @property
    def surprise_rate(self) -> float:
        """Fraction of predictions that were wrong (0-1).

        High surprise rate means the effects are context-dependent
        and the system hasn't fully learned the context rules yet.
        """
        total_pred = sum(e.prediction_count for e in self._effects.values())
        total_surp = sum(e.surprise_count for e in self._effects.values())
        if total_pred == 0:
            return 0.0
        return total_surp / total_pred

    @property
    def has_context_rules(self) -> bool:
        """Whether any context-dependent rules have been learned."""
        return len(self._context_effects) > 0

    @property
    def context_rule_count(self) -> int:
        """Number of distinct context prefixes with learned effects."""
        return len(self._context_effects)

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

    def set_tile_map(
        self,
        bounds: Tuple[int, int, int, int],
        rows: int,
        cols: int,
        tile_w: int,
        tile_h: int,
        sep_w: int = 0,
    ):
        """Set the tile abstraction map from visual perception.

        Once set, update_from_action() will aggregate pixel-level
        diffs into tile-level effects. This fixes the core granularity
        problem: a click that changes one tile (16-38 pixels) is
        recorded as affecting 1 tile, not 38 positions.

        Args:
            bounds: (y_min, x_min, y_max, x_max) of the tiled panel
            rows: Number of tile rows
            cols: Number of tile columns
            tile_w: Width of each tile in pixels
            tile_h: Height of each tile in pixels
            sep_w: Width of separator lines between tiles
        """
        if rows <= 0 or cols <= 0 or tile_w <= 0 or tile_h <= 0:
            return
        self._tile_map = {
            'bounds': bounds,
            'rows': rows,
            'cols': cols,
            'tile_w': tile_w,
            'tile_h': tile_h,
            'sep_w': sep_w,
        }
        logger.debug(
            f"[CAUSAL-MAP] Tile map set: {rows}x{cols} tiles, "
            f"{tile_w}x{tile_h}px each, sep={sep_w}"
        )

    def _pixel_to_tile(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """Convert pixel coordinates to tile coordinates.

        Returns the tile center (pixel coords) that this pixel belongs
        to, or None if the pixel is outside the tiled region or on a
        separator line.
        """
        if self._tile_map is None:
            return None

        tm = self._tile_map
        y_min, x_min, y_max, x_max = tm['bounds']

        # Check if pixel is within tiled panel
        if not (x_min <= px < x_max and y_min <= py < y_max):
            return None

        # Compute relative position within the panel
        rel_x = px - x_min
        rel_y = py - y_min

        # Compute tile column and row, accounting for separators
        tw = tm['tile_w']
        th = tm['tile_h']
        sep = tm['sep_w']
        cell_w = tw + sep
        cell_h = th + sep

        if cell_w <= 0 or cell_h <= 0:
            return None

        col = rel_x // cell_w
        row = rel_y // cell_h

        # Check bounds
        if col >= tm['cols'] or row >= tm['rows']:
            return None

        # Check if on a separator line
        x_in_cell = rel_x % cell_w
        y_in_cell = rel_y % cell_h
        if sep > 0 and (x_in_cell >= tw or y_in_cell >= th):
            return None  # On separator

        # Return tile center in pixel coordinates (for click targeting)
        tile_center_x = x_min + col * cell_w + tw // 2
        tile_center_y = y_min + row * cell_h + th // 2
        return (tile_center_x, tile_center_y)

    def _aggregate_pixel_diffs_to_tiles(
        self,
        pixel_positions: List[Tuple[int, int]],
        pre_frame: np.ndarray,
        post_frame: np.ndarray,
    ) -> Tuple[List[Tuple[int, int]], Dict[Tuple[int, int], List[Tuple[int, int]]]]:
        """Aggregate pixel-level diffs into tile-level diffs.

        Groups changed pixels by which tile they belong to. For each
        tile, picks the dominant color transition (the most common
        old_color -> new_color pair among its pixels).

        Returns:
            (affected_tiles, tile_color_transitions)
            - affected_tiles: list of tile center positions (deduplicated)
            - tile_color_transitions: {tile_center: [(old_color, new_color)]}
        """
        # Group changed pixels by their tile
        tile_pixels: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)

        for px, py in pixel_positions:
            tile_center = self._pixel_to_tile(px, py)
            if tile_center is not None:
                tile_pixels[tile_center].append((px, py))

        affected_tiles = sorted(tile_pixels.keys())
        tile_transitions: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        for tile_center, pixels in tile_pixels.items():
            # Find the dominant color transition for this tile
            transition_counts: Dict[Tuple[int, int], int] = {}
            for px, py in pixels:
                old_c = int(pre_frame[py, px])
                new_c = int(post_frame[py, px])
                key = (old_c, new_c)
                transition_counts[key] = transition_counts.get(key, 0) + 1

            # Take the most common transition
            if transition_counts:
                best = max(transition_counts.items(), key=lambda x: x[1])
                tile_transitions[tile_center] = [best[0]]

        return affected_tiles, tile_transitions

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

        Integrates with the prediction-surprise system:
        1. BEFORE updating, predict what should happen (from prior knowledge)
        2. Compute actual changes
        3. Compare prediction to reality -> detect surprises
        4. THEN update the effects as usual
        """
        self._explored.add(click_pos)
        self._all_positions.add(click_pos)

        if pre_frame is None or post_frame is None:
            return

        # ─── Step 1: Predict (before updating) ───────────────────────
        prediction = self.predict(click_pos)

        if not frame_changed:
            # Clicking here did nothing — check if that's surprising
            self.check_surprise(
                click_pos, prediction,
                actual_affected=[], actual_changed=False,
            )
            # Record the non-effect
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

            # ─── TILE ABSTRACTION: Aggregate pixels to tiles ──────────
            # When tile map is available, convert pixel-level diffs to
            # tile-level diffs. This is the key fix: a click that changes
            # one 7x7 tile is recorded as "1 tile affected" not "49 pixels."
            if self._tile_map is not None:
                raw_pixel_positions = sorted(set(affected))
                tile_affected, tile_transitions = self._aggregate_pixel_diffs_to_tiles(
                    raw_pixel_positions, pre_frame, post_frame,
                )
                if tile_affected:
                    # Use tile-level data instead of pixel-level
                    affected_unique = tile_affected
                    color_transitions = defaultdict(list)
                    for tile_pos, transitions in tile_transitions.items():
                        color_transitions[tile_pos] = transitions
                    # Also snap click_pos to tile center
                    snapped = self._pixel_to_tile(click_pos[0], click_pos[1])
                    if snapped is not None:
                        click_pos = snapped
                else:
                    # Tile aggregation found nothing (pixels on separators?)
                    # Fall through to pixel-level
                    affected_unique = sorted(set(affected))
            else:
                # No tile map -- use raw pixel positions (legacy behavior)
                affected_unique = sorted(set(affected))

            # ─── Step 2: Check surprise ───────────────────────────────
            self.check_surprise(
                click_pos, prediction,
                actual_affected=affected_unique,
                actual_changed=True,
            )

            # ─── Step 3: Update effects as usual ──────────────────────
            ctx = tuple(self._action_context)

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
                # Tag with current action context
                if ctx:
                    eff.context_tags.append(ctx)
            else:
                self._effects[click_pos] = TileEffect(
                    position=click_pos,
                    affected=affected_unique,
                    color_transitions=dict(color_transitions),
                    observation_count=1,
                    last_frame_changed=True,
                    context_tags=[ctx] if ctx else [],
                )

            # Update color cycle knowledge
            self._update_color_cycles(color_transitions)

            # Try to extract rules from accumulated effects
            self._try_extract_rules()

            # Invalidate plan (state changed, plan may no longer be valid)
            self._invalidate_plan()

        except Exception as e:
            logger.debug(f"[CAUSAL-MAP] update_from_action failed: {e}")

    # ─── H47: Score-Correlated Goal Discovery ────────────────────────

    def record_score_correlation(
        self,
        pre_frame: Optional[np.ndarray],
        post_frame: Optional[np.ndarray],
        score_delta: float,
    ):
        """Learn which state changes correlate with positive/negative score.

        When score_delta > 0: the post_frame colors at changed positions
        are likely "goal-approaching" states.  After N observations,
        infer_goal_from_scores() can derive goal cells from this data.
        """
        if pre_frame is None or post_frame is None or score_delta == 0:
            return
        try:
            if pre_frame.shape != post_frame.shape:
                return
            diff_mask = pre_frame != post_frame
            if not diff_mask.any():
                return

            ys, xs = np.where(diff_mask)
            # Cap to prevent huge diffs (level transitions) from polluting
            if len(ys) > 200:
                return

            for i in range(len(ys)):
                y, x = int(ys[i]), int(xs[i])
                pos = (x, y)
                new_color = int(post_frame[y, x])

                if score_delta > 0:
                    self._score_positive_states[pos][new_color] = (
                        self._score_positive_states[pos].get(new_color, 0) + 1
                    )
                else:
                    self._score_negative_states[pos][new_color] = (
                        self._score_negative_states[pos].get(new_color, 0) + 1
                    )

            self._score_observations += 1
        except Exception as e:
            logger.debug(f"[CAUSAL-MAP] H47 score correlation failed: {e}")

    # ─── H53: Win-State Goal Templates ───────────────────────────────

    def record_win_state(self, level: int, cells: Dict[Tuple[int, int], int]):
        """Capture the board state at level completion as a goal template.

        Called when level_changed=True, BEFORE the level reset, so we
        capture what the winning board actually looked like.  Stored by
        level number so future sessions can use it as the goal.
        """
        if not cells:
            return
        self._win_templates[level] = dict(cells)
        logger.info(
            f"[CAUSAL-MAP] H53: Captured win-state template for L{level} "
            f"({len(cells)} cells)"
        )

    def apply_win_template(self, level: int) -> bool:
        """Apply a captured win-state as goal_cells for the given level.

        Called on level start.  Only applies if we don't already have goals
        from a more authoritative source (perceiver panel or solver).
        Returns True if template was applied.
        """
        if self._goal_cells and len(self._goal_cells) > 3:
            return False  # Already have goals — don't override
        template = self._win_templates.get(level)
        if not template:
            return False
        self._goal_cells = dict(template)
        self._goal_source = 'win_template'
        logger.info(
            f"[CAUSAL-MAP] H53: Applied win-template as goal for L{level} "
            f"({len(self._goal_cells)} cells)"
        )
        return True

    def infer_goal_from_scores(self, min_observations: int = 3):
        """Derive goal cells from accumulated score correlations.

        For each position with enough positive-score data, the most
        frequent color seen during +score is probably the goal color.
        Only sets goals when we DON'T already have perceiver-detected goals.
        """
        if self._goal_cells and len(self._goal_cells) > 3:
            return  # Already have goals from perceiver — don't override

        inferred: Dict[Tuple[int, int], int] = {}
        for pos, color_counts in self._score_positive_states.items():
            total = sum(color_counts.values())
            if total < min_observations:
                continue
            best_color = max(color_counts, key=color_counts.get)  # type: ignore[arg-type]
            dominance = color_counts[best_color] / total
            if dominance >= 0.6:
                inferred[pos] = best_color

        if len(inferred) >= 3:
            self._goal_cells = inferred
            self._goal_source = 'score_correlation'
            logger.info(
                f"[CAUSAL-MAP] H47: Inferred {len(inferred)} goal cells "
                f"from {self._score_observations} score observations"
            )

    # ─── H49: Game-Agnostic Forward Simulation ────────────────────────

    def simulate_action(
        self,
        state: Dict[Tuple[int, int], int],
        click_pos: Tuple[int, int],
    ) -> Tuple[Dict[Tuple[int, int], int], float]:
        """Simulate a click on a state dict using learned effects.

        Uses color cycles and observed transitions to predict the
        resulting state.  Game-agnostic: works for ANY game where
        we've observed click effects.

        Returns:
            (new_state, confidence) where confidence 0-1.
        """
        effect = self._effects.get(click_pos)
        if effect is None or not effect.last_frame_changed:
            return dict(state), 0.0

        new_state = dict(state)
        transitions_applied = 0

        for affected_pos in effect.affected:
            current_color = state.get(affected_pos)
            if current_color is None:
                continue

            # Strategy 1: Color cycle knowledge
            cycle = self._color_cycles.get(affected_pos, [])
            if len(cycle) >= 2:
                unique: List[int] = []
                for c in cycle:
                    if not unique or c != unique[-1]:
                        unique.append(c)
                if current_color in unique:
                    idx = unique.index(current_color)
                    next_color = unique[(idx + 1) % len(unique)]
                    new_state[affected_pos] = next_color
                    transitions_applied += 1
                    continue

            # Strategy 2: Direct transition lookup (most recent first)
            trans = effect.color_transitions.get(affected_pos, [])
            for old_c, new_c in reversed(trans):
                if old_c == current_color:
                    new_state[affected_pos] = new_c
                    transitions_applied += 1
                    break

        confidence = effect.confidence * (
            transitions_applied / max(len(effect.affected), 1)
        )
        return new_state, confidence

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
                continue

            # ── H55: Self-toggle rule extrapolation ──────────────────
            # When no observed effect covers this target and the self_toggle
            # rule is known (clicking (x,y) affects only (x,y)), infer that
            # clicking target_pos will toggle it — even if never visited.
            # This lets the agent plan for the full board after seeing just
            # a few cells, without needing solver data.
            self_toggle_rule = next(
                (r for r in self._rules
                 if r.rule_type == 'self_toggle' and r.confidence >= 0.5),
                None
            )
            if self_toggle_rule:
                # Compute clicks needed based on color cycle (if known)
                cycle = self._color_cycles.get(target_pos, [])
                unique_cycle = []
                for c in cycle:
                    if c not in unique_cycle:
                        unique_cycle.append(c)
                if len(unique_cycle) >= 2 and current_c in unique_cycle and goal_c in unique_cycle:
                    ci = unique_cycle.index(current_c)
                    gi = unique_cycle.index(goal_c)
                    clicks_needed = (gi - ci) % len(unique_cycle) or len(unique_cycle)
                else:
                    clicks_needed = 1  # Default: one click to toggle
                conf = self_toggle_rule.confidence * 0.75  # Discounted — not yet observed
                for _ in range(clicks_needed):
                    plan.append(PlannedAction(
                        position=target_pos,
                        expected_changes=[(target_pos[0], target_pos[1], current_c, goal_c)],
                        reason=(
                            f"H55 self-toggle ({target_pos[0]},{target_pos[1]}) "
                            f"{current_c}->{goal_c} "
                            f"(rule conf={self_toggle_rule.confidence:.0%})"
                        ),
                        step_number=step,
                        confidence=conf,
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
        """Try to generalize from individual effects to rules.

        Data-driven rule extraction: discovers patterns from observations
        rather than looking for specific hardcoded patterns (e.g. von Neumann).

        Detects:
        - self_toggle: clicking affects only the clicked cell
        - multi_cell: clicking affects multiple cells (pattern learned from data)
        - color_cycle_N: tiles cycle through N colors
        - no_effect: some positions produce no change
        """
        if len(self._effects) < 3:
            return  # Not enough data

        total_effects = 0
        self_only_count = 0
        multi_cell_count = 0
        no_effect_count = 0
        affected_counts: list = []  # How many cells each click affects

        for _click_pos, effect in self._effects.items():
            if not effect.last_frame_changed:
                no_effect_count += 1
                continue
            total_effects += 1

            affected_set = set(effect.affected)
            n_affected = len(affected_set)
            affected_counts.append(n_affected)

            if n_affected <= 1:
                self_only_count += 1
            else:
                multi_cell_count += 1

        if total_effects == 0:
            return

        # ── Rule: self_toggle (clicking only affects the clicked cell) ──
        if self_only_count / total_effects > 0.5:
            existing = [r for r in self._rules if r.rule_type == 'self_toggle']
            if not existing:
                self._rules.append(CausalRule(
                    rule_type='self_toggle',
                    description='Clicking affects only the clicked cell',
                    evidence_count=self_only_count,
                    confidence=min(0.9, self_only_count / total_effects),
                ))
            else:
                existing[0].evidence_count = self_only_count
                existing[0].confidence = min(0.9, self_only_count / total_effects)

        # ── Rule: multi_cell (clicking affects multiple cells) ──
        # Discovered from data — describes what was observed, not assumed
        if multi_cell_count / total_effects > 0.3:
            # Compute average affected count for multi-cell effects
            multi_counts = [c for c in affected_counts if c > 1]
            avg_affected = (
                sum(multi_counts) / len(multi_counts) if multi_counts else 0
            )
            existing = [r for r in self._rules if r.rule_type == 'multi_cell']
            desc = (
                f'Clicking affects ~{avg_affected:.1f} cells on average '
                f'({multi_cell_count}/{total_effects} observations)'
            )
            if not existing:
                self._rules.append(CausalRule(
                    rule_type='multi_cell',
                    description=desc,
                    evidence_count=multi_cell_count,
                    confidence=min(0.9, multi_cell_count / total_effects),
                ))
            else:
                existing[0].evidence_count = multi_cell_count
                existing[0].confidence = min(0.9, multi_cell_count / total_effects)
                existing[0].description = desc

        # ── Rule: color_cycle_N (tiles cycle through N colors) ──
        cycle_lengths: list = []
        for pos, cycle in self._color_cycles.items():
            if len(cycle) >= 2:
                # Detect cycle length: find repeat in the sequence
                unique_colors = []
                for c in cycle:
                    if c in unique_colors:
                        break
                    unique_colors.append(c)
                if len(unique_colors) >= 2:
                    cycle_lengths.append(len(unique_colors))

        if cycle_lengths:
            from collections import Counter as _Counter
            most_common_len = _Counter(cycle_lengths).most_common(1)[0][0]
            existing = [
                r for r in self._rules
                if r.rule_type.startswith('color_cycle')
            ]
            desc = (
                f'Tiles cycle through {most_common_len} colors '
                f'(observed at {len(cycle_lengths)} positions)'
            )
            rule_type = f'color_cycle_{most_common_len}'
            if not existing:
                self._rules.append(CausalRule(
                    rule_type=rule_type,
                    description=desc,
                    evidence_count=len(cycle_lengths),
                    confidence=min(0.9, len(cycle_lengths) / max(total_effects, 1)),
                ))
            else:
                existing[0].rule_type = rule_type
                existing[0].description = desc
                existing[0].evidence_count = len(cycle_lengths)

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

    def find_path_bfs(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        grid_size: int = 64,
    ) -> List[int]:
        """
        Gap 3C: BFS pathfinding for movement games.

        Uses known walls and open paths to find the shortest sequence
        of directional actions (1=up, 2=down, 3=left, 4=right) from
        from_pos to to_pos.

        Returns a list of action_type ints representing the path,
        or an empty list if no path is found within the explored map.

        The BFS only considers positions we've visited or can infer
        are reachable. Unknown positions are treated as passable
        (optimistic exploration).
        """
        if from_pos == to_pos:
            return []

        # Direction offsets: action -> (dx, dy)
        direction_offsets = {
            1: (0, -1),   # up
            2: (0, 1),    # down
            3: (-1, 0),   # left
            4: (1, 0),    # right
        }

        # BFS
        from collections import deque as bfs_deque
        queue: 'bfs_deque[Tuple[Tuple[int, int], List[int]]]' = bfs_deque()
        queue.append((from_pos, []))
        visited: Set[Tuple[int, int]] = {from_pos}

        # Limit search to prevent runaway on large grids
        max_steps = min(grid_size * grid_size, 500)
        steps = 0

        while queue and steps < max_steps:
            steps += 1
            current, path = queue.popleft()

            for action, (dx, dy) in direction_offsets.items():
                next_pos = (current[0] + dx, current[1] + dy)

                # Bounds check
                if not (0 <= next_pos[0] < grid_size and 0 <= next_pos[1] < grid_size):
                    continue

                # Already visited in BFS
                if next_pos in visited:
                    continue

                # Known wall? Skip.
                if (current, action) in self._walls:
                    continue

                visited.add(next_pos)
                new_path = path + [action]

                if next_pos == to_pos:
                    return new_path

                queue.append((next_pos, new_path))

        return []  # No path found

    # ─── Environmental State Changes (Gap 5B) ─────────────────────────

    def record_hud_change(
        self,
        action_pos: Optional[Tuple[int, int]],
        action_type: int,
        _timer_urgency: str = "safe",
    ):
        """
        Record that an action caused the HUD/environment state to change.

        Gap 5B: The HUD (edge pixels) changed after this action. This
        might mean a timer advanced, a life was lost, a key was picked up,
        etc. We record the association so that the system can learn which
        actions cause environmental state transitions.

        This enriches per-position effects with 'environmental impact' --
        some positions do more than just change tiles; they change
        the game state itself.
        """
        if action_pos is None:
            return

        effect = self._effects.get(action_pos)
        if effect is not None:
            # Tag this effect as having environmental impact
            if not hasattr(effect, 'hud_change_count'):
                effect.hud_change_count = 0  # type: ignore[attr-defined]
            effect.hud_change_count += 1  # type: ignore[attr-defined]

        # Store separately for global awareness
        self._hud_change_positions[action_pos] = (
            self._hud_change_positions.get(action_pos, 0) + 1
        )

    # ─── Object Collision Tracking (LS20 movement games) ──────────────

    def record_collision(
        self,
        agent_pos: Tuple[int, int],
        object_color: int,
        hud_snapshot_before: Optional[Dict[str, Any]],
        hud_snapshot_after: Optional[Dict[str, Any]],
        _frame_before: Optional[np.ndarray] = None,
        _frame_after: Optional[np.ndarray] = None,
    ):
        """Record what happens when the agent collides with an object.

        For LS20-style movement games: the agent moves into a colored
        object and something changes (key symbol, lifespan, score).
        Track the association: object_color -> state change.

        This lets agents learn: "blue objects change my key symbol"
        or "orange objects extend my lifespan."
        """
        collision_record: Dict[str, Any] = {
            'position': agent_pos,
            'object_color': object_color,
        }

        # Compare HUD snapshots to detect what changed
        if hud_snapshot_before is not None and hud_snapshot_after is not None:
            changes: Dict[str, Any] = {}
            all_keys = set(hud_snapshot_before.keys()) | set(hud_snapshot_after.keys())
            for key in all_keys:
                before_val = hud_snapshot_before.get(key)
                after_val = hud_snapshot_after.get(key)
                if before_val != after_val:
                    changes[key] = {'before': before_val, 'after': after_val}
            if changes:
                collision_record['state_changes'] = changes
                collision_record['is_meaningful'] = True
            else:
                collision_record['is_meaningful'] = False
        else:
            collision_record['is_meaningful'] = None  # Unknown

        self._collision_effects[object_color].append(collision_record)

        # Log the discovery
        meaningful = collision_record.get('is_meaningful')
        if meaningful:
            logger.debug(
                f"[CAUSAL-MAP] Collision with color {object_color} at "
                f"{agent_pos}: state changed: "
                f"{collision_record.get('state_changes', {})}"
            )

    def get_collision_knowledge(self) -> Dict[int, Dict[str, Any]]:
        """Get summarized collision knowledge per object color.

        Returns {color: {count, meaningful_count, common_changes}}.
        """
        knowledge: Dict[int, Dict[str, Any]] = {}
        for color, records in self._collision_effects.items():
            meaningful = [r for r in records if r.get('is_meaningful')]
            knowledge[color] = {
                'collision_count': len(records),
                'meaningful_count': len(meaningful),
                'last_position': records[-1]['position'] if records else None,
            }
            # Aggregate common state changes
            if meaningful:
                change_keys: Dict[str, int] = {}
                for r in meaningful:
                    for key in r.get('state_changes', {}).keys():
                        change_keys[key] = change_keys.get(key, 0) + 1
                knowledge[color]['common_changes'] = change_keys
        return knowledge

    # ─── Temporal Causal Learning (VC33 delayed effects) ──────────────

    def start_delayed_observation(
        self,
        action_pos: Tuple[int, int],
        action_type: int,
        frame_at_action: Optional[np.ndarray],
        window_size: int = 5,
    ):
        """
        Begin tracking delayed effects from an action.

        For VC33-style games where clicking a switch doesn't
        produce immediate visible results -- the effect unfolds
        over subsequent frames (fluid flow, passenger movement).

        Args:
            action_pos: Where the action was taken
            action_type: What action was taken
            frame_at_action: Frame state when action was taken
            window_size: How many subsequent frames to observe
        """
        if frame_at_action is None:
            return

        obs = {
            'action_pos': action_pos,
            'action_type': action_type,
            'start_frame': frame_at_action.copy(),
            'window_size': window_size,
            'frames_remaining': window_size,
            'total_pixels_changed': 0,
            'delayed_changes': [],  # (step_offset, pixels_changed, regions)
        }
        self._delayed_observations.append(obs)

    def observe_delayed_frame(self, current_frame: np.ndarray):
        """
        Feed a new frame into all active delayed observation windows.

        Call this EVERY frame (even frames where no action was taken)
        so that delayed effects are attributed to the action that
        caused them.
        """
        completed = []

        for i, obs in enumerate(self._delayed_observations):
            if obs['frames_remaining'] <= 0:
                completed.append(i)
                continue

            obs['frames_remaining'] -= 1
            step_offset = obs['window_size'] - obs['frames_remaining']

            try:
                start = obs['start_frame']
                if start.shape != current_frame.shape:
                    continue

                diff = start != current_frame
                pixels_changed = int(diff.sum())

                if pixels_changed > 0:
                    obs['total_pixels_changed'] += pixels_changed

                    # Find the regions that changed
                    ys, xs = np.where(diff)
                    if len(xs) > 0:
                        cx = int(np.mean(xs))
                        cy = int(np.mean(ys))
                        obs['delayed_changes'].append({
                            'offset': step_offset,
                            'pixels': pixels_changed,
                            'centroid': (cx, cy),
                        })

            except Exception:
                continue

            if obs['frames_remaining'] <= 0:
                completed.append(i)

        # Process completed observations
        for i in sorted(completed, reverse=True):
            obs = self._delayed_observations.pop(i)
            self._process_completed_delayed_observation(obs)

    def _process_completed_delayed_observation(self, obs: Dict[str, Any]):
        """
        Process a completed delayed observation window.

        If significant delayed changes were detected, record them
        as effects of the original action. This lets the CausalMap
        understand that "clicking switch S caused passenger movement
        5 frames later."
        """
        action_pos = obs['action_pos']
        total_changed = obs['total_pixels_changed']
        delayed_changes = obs['delayed_changes']

        if total_changed == 0 or not delayed_changes:
            return  # No delayed effects observed

        # Record as extended effect
        effect = self._effects.get(action_pos)
        if effect is None:
            # Create a new effect for this position
            effect = TileEffect(
                position=action_pos,
                affected=[],
                color_transitions={},
                observation_count=0,
                last_frame_changed=True,
            )
            self._effects[action_pos] = effect

        # Add delayed-change regions as affected positions
        for change in delayed_changes:
            centroid = change['centroid']
            if centroid not in effect.affected:
                effect.affected.append(centroid)

        effect.observation_count += 1
        effect.last_frame_changed = True
        effect.confidence = min(0.95, 0.3 + (effect.observation_count * 0.15))

        self._explored.add(action_pos)
        self._all_positions.add(action_pos)

        logger.debug(
            f"[CAUSAL-MAP] Delayed effect: action at {action_pos} caused "
            f"{total_changed} pixel changes over {len(delayed_changes)} frames"
        )

    @property
    def has_active_delayed_observations(self) -> bool:
        """Whether any delayed observation windows are still active."""
        return len(self._delayed_observations) > 0

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

            # Import goal state (constraint_goal_state takes priority
            # over goal_state -- written by ConstraintDecoderRung)
            goal = world_model.get('constraint_goal_state') or world_model.get('goal_state', {})
            if isinstance(goal, dict) and goal:
                self._goal_cells = goal
                self._invalidate_plan()

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
            'surprise_rate': self.surprise_rate,
            'context_rules': self.context_rule_count,
            'surprise_count': len(self._surprise_log),
            'has_tile_map': self._tile_map is not None,
            'tile_map': self._tile_map,
            'collision_colors': list(self._collision_effects.keys()),
        }

    def summary(self) -> str:
        """One-line summary for logging."""
        rules_str = ", ".join(r.rule_type for r in self._rules) if self._rules else "none"
        wall_str = ""
        if self._walls:
            wall_str = f" walls:{len(self._walls)}"
        productive = sum(1 for e in self._effects.values() if e.productive_count > 0)
        prod_str = f" productive:{productive}" if productive else ""
        surprise_str = ""
        if self._surprise_log:
            surprise_str = f" surprises:{len(self._surprise_log)}({self.surprise_rate:.0%})"
        ctx_str = ""
        if self._context_effects:
            ctx_str = f" ctx_rules:{self.context_rule_count}"
        tile_str = ""
        if self._tile_map:
            tm = self._tile_map
            tile_str = f" tiles:{tm['rows']}x{tm['cols']}"
        collision_str = ""
        if self._collision_effects:
            total = sum(len(v) for v in self._collision_effects.values())
            collision_str = f" collisions:{total}"
        return (
            f"[MAP] effects:{len(self._effects)} explored:{len(self._explored)}/{len(self._all_positions)} "
            f"rules:[{rules_str}] complete:{self.completeness:.0%} plan:{'yes' if self.has_plan else 'no'}"
            f"{wall_str}{prod_str}{surprise_str}{ctx_str}{tile_str}{collision_str}"
        )
