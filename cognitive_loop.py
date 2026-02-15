import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Cognitive Loop - Perceive -> Think -> Map -> Act

This is the central nervous system that makes the agent an ORGANISM
rather than a bag of organs. It orchestrates:

1. PERCEIVE: Multimodal scene understanding (parallel channels)
2. THINK: Phenomenological compression (felt-state + strategy)
3. MAP: Causal knowledge update/query (the leapfrog enabler)
4. ACT: Three-speed decision making (mapped/reasoned/explore)

And crucially: the output of ACT feeds back into PERCEIVE on the next
cycle, closing the loop. The causal map informs perception, perception
informs thinking, thinking consults the map, the map drives action.

This module does NOT replace the existing DecisionRungSystem.
It WRAPS it, adding structured perception and causal reasoning around
the existing rung evaluation. Rungs become the "REASONED" speed of
action selection — the middle path between fast mapped execution and
slow exploratory discovery.

Usage:
    loop = CognitiveLoop(decision_system, db)
    loop.start_game(game_id, available_actions)

    # Per action:
    action, data, frame_record = loop.cycle(frame, obs)
    # ... execute action ...
    loop.record_result(frame_changed, score_delta, level_changed)

    # After game:
    replay = loop.get_replay()
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from engines.cognition.causal_map import CausalMap, PlannedAction
from engines.cognition.cognitive_frame import CognitiveFrame
from engines.cognition.phenomenology_layer import FeltState, PhenomenologyLayer, Valence
from engines.perception.perceiver import Perceiver
from engines.perception.perceptual_field import PerceptualField

logger = logging.getLogger(__name__)


# =============================================================================
# PERCEPTUAL BLACKBOARD ADAPTER
# =============================================================================


class PerceptualBlackboardAdapter:
    """
    Adapter that makes PerceptualField + CognitiveLoop state look like a
    Blackboard for PhenomenologyLayer.

    PhenomenologyLayer reads from ``blackboard.get(key, default)`` and writes
    via ``blackboard.slot(key, value, source_rung=...)``.  This adapter
    translates those reads into live PerceptualField fields and CognitiveLoop
    game state so PhenomenologyLayer can compress perception without
    depending on the full Blackboard infrastructure.

    Written values (from ``inject()``) are stored in a local overlay dict
    and returned on subsequent ``get()`` calls, closing the feedback loop.
    """

    def __init__(self) -> None:
        self._percept: Optional[PerceptualField] = None
        self._loop_state: Dict[str, Any] = {}
        self._injected: Dict[str, Any] = {}
        self._prev_confidence: float = 0.0
        self._recent_strategies: List[str] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def update(
        self, percept: PerceptualField, loop_state: Dict[str, Any]
    ) -> None:
        """Refresh with fresh perception + loop state each cycle."""
        if self._percept is not None:
            self._prev_confidence = self._percept.overall_confidence
        self._percept = percept
        self._loop_state = loop_state

    def reset(self) -> None:
        """Reset for a new game."""
        self._percept = None
        self._loop_state = {}
        self._injected = {}
        self._prev_confidence = 0.0
        self._recent_strategies = []

    # ------------------------------------------------------------------
    # Blackboard-compatible read (used by PhenomenologyLayer.compress)
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Blackboard-compatible ``get``."""
        # Injected values (written by PhenomenologyLayer.inject) win
        if key in self._injected:
            return self._injected[key]

        if self._percept is None:
            return default

        value = self._resolve(key)
        return value if value is not None else default

    # ------------------------------------------------------------------
    # Blackboard-compatible write (used by PhenomenologyLayer.inject)
    # ------------------------------------------------------------------

    def slot(
        self,
        key: str,
        value: Any = None,
        *,
        source_rung: str = "unknown",
        confidence: float = 1.0,
        source_primitive: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Any:
        """Blackboard-compatible ``slot`` (write when *value* given)."""
        if value is not None:
            self._injected[key] = value
            return value
        return self._injected.get(key)

    # ------------------------------------------------------------------
    # Slot resolution: maps blackboard key -> PerceptualField/loop state
    # ------------------------------------------------------------------

    def _resolve(self, key: str) -> Any:  # noqa: C901 — intentionally flat dispatch
        """Translate a single blackboard key to perception data."""
        p = self._percept
        s = self._loop_state
        if p is None:
            return None

        # -- Epistemic quadrant (derived from confidence) --
        if key == "epistemic_quadrant":
            c = p.overall_confidence
            if c > 0.7:
                return "KK"
            if c > 0.4:
                return "KU"
            if c > 0.2:
                return "UK"
            return "UU"

        # -- Theory / control --
        if key == "working_theory":
            return True if (p.has_plan or p.map_completeness > 0.5) else None
        if key == "controlled_object":
            return True if len(p.known_effects) > 2 else None

        # -- Threat signals --
        if key == "contradiction_detected":
            return p.surprise > 0.7
        if key == "cascade_failure":
            return False
        if key == "action_budget_critical":
            max_a = s.get("max_actions", 500)
            return p.actions_remaining < max_a * 0.1

        # -- Frame / delta --
        if key == "frame_delta_magnitude":
            eff = p.last_action_effect
            return eff.pixels_changed if eff else 0
        if key == "no_change_frames":
            return p.consecutive_no_change

        # -- Strategy stability --
        if key == "strategy_stability":
            strats = self._recent_strategies
            if len(strats) < 3:
                return 1.0
            recent = strats[-5:]
            same = sum(1 for a, b in zip(recent, recent[1:]) if a == b)
            return same / max(len(recent) - 1, 1)

        # -- Success rate --
        if key == "recent_success_rate":
            if p.actions_taken == 0:
                return 0.5
            return max(
                0.0,
                1.0 - p.consecutive_no_change / max(p.actions_taken, 1),
            )

        # -- Novelty / surprise --
        if key == "novelty_score":
            return p.surprise * 0.5
        if key == "surprise_score":
            return p.surprise
        if key == "pattern_break":
            return p.surprise > 0.5

        # -- Stuck --
        if key == "stuck_detected":
            return p.consecutive_no_change > 5

        # -- Game progress --
        if key == "levels_completed":
            return s.get("levels_completed", 0)
        if key == "total_levels":
            return s.get("total_levels", 6)
        if key == "death_count":
            return 0

        # -- Confidence delta --
        if key == "confidence_delta":
            return p.overall_confidence - self._prev_confidence

        # -- Score delta --
        if key == "score_delta":
            eff = p.last_action_effect
            return eff.score_delta if eff else 0

        # -- Open questions / unknowns --
        if key == "known_unknowns":
            return list(p.unexplored_positions)
        if key == "open_questions":
            return list(p.unexplored_positions)

        # -- Tick / path --
        if key == "current_tick":
            return s.get("actions_taken", 0)
        if key == "recent_path":
            return s.get("recent_path", [])

        return None


class CognitiveLoop:
    """
    Perceive -> Think -> Map -> Act orchestrator.

    Wraps the existing DecisionRungSystem with structured perception
    and causal reasoning. Produces observable CognitiveFrames.
    """

    def __init__(
        self,
        decision_system: Any = None,
        context_builder: Any = None,
        db: Any = None,
        verbose: bool = False,
    ):
        """
        Initialize the cognitive loop.

        Args:
            decision_system: DecisionRungSystem instance (for REASONED speed)
            context_builder: ContextBuilder instance (for backward compat context)
            db: Database interface for loading prior knowledge
            verbose: Print cognitive frames to console
        """
        self._decision_system = decision_system
        self._context_builder = context_builder
        self._db = db
        self._verbose = verbose

        # Core components
        self._perceiver = Perceiver()
        self._causal_map: Optional[CausalMap] = None

        # Phenomenology: blackboard adapter + compression layer
        self._bb_adapter = PerceptualBlackboardAdapter()
        self._phenomenology = PhenomenologyLayer(self._bb_adapter)  # type: ignore[arg-type]

        # Game state
        self._game_id: str = ""
        self._available_actions: List[int] = []
        self._max_actions: int = 500
        self._actions_taken: int = 0
        self._current_level: int = 1
        self._score: float = 0.0

        # Frame tracking
        self._prev_frame: Optional[np.ndarray] = None
        self._consecutive_no_change: int = 0

        # Replay
        self._frames: List[CognitiveFrame] = []
        self._current_frame: Optional[CognitiveFrame] = None

        # Last action info (for temporal perception)
        self._last_action_info: Optional[Dict[str, Any]] = None

        # Prior knowledge state
        self._prior_knowledge_loaded: bool = False
        self._prior_effects_count: int = 0  # How many position effects loaded from DB
        self._prior_rules_count: int = 0    # How many rules loaded from DB

    # ─── Game Lifecycle ───────────────────────────────────────────────

    def start_game(
        self,
        game_id: str,
        available_actions: List[int],
        max_actions: int = 500,
    ):
        """Initialize for a new game."""
        self._game_id = game_id
        self._available_actions = available_actions
        self._max_actions = max_actions
        self._actions_taken = 0
        self._current_level = 1
        self._score = 0.0
        self._prev_frame = None
        self._consecutive_no_change = 0
        self._last_action_info = None
        self._frames = []
        self._current_frame = None

        # Create fresh causal map for this game
        self._causal_map = CausalMap(game_id=game_id)

        # Reset perceiver
        self._perceiver.reset()

        # Reset phenomenology layer for fresh game
        self._bb_adapter.reset()
        self._phenomenology.reset()

        # Reset prior knowledge state
        self._prior_knowledge_loaded = False
        self._prior_effects_count = 0
        self._prior_rules_count = 0

        # ═══ LOAD PRIOR KNOWLEDGE FROM DATABASE ═══
        # This is the key difference from a blank-slate approach:
        # we seed the causal map with knowledge from prior games,
        # so the agent starts with understanding, not ignorance.
        self._load_prior_knowledge(game_id)

        # Import any existing causal knowledge from context builder
        if self._context_builder is not None:
            try:
                wm = getattr(self._context_builder, '_world_model', None)
                if wm:
                    self._causal_map.import_from_world_model(wm)
            except Exception:
                pass

        if self._verbose:
            print(f"\n[COGNITIVE-LOOP] Game started: {game_id}")
            print(f"    Available actions: {available_actions}")
            print(f"    Budget: {max_actions} actions")
            if self._prior_knowledge_loaded:
                print(
                    f"    Prior knowledge: {self._prior_effects_count} effects, "
                    f"{self._prior_rules_count} rules loaded"
                )
                print(f"    {self._causal_map.summary()}")
            else:
                print("    Prior knowledge: none (first encounter)")

    def end_game(self) -> List[CognitiveFrame]:
        """End the game and return the replay."""
        if self._verbose and self._frames:
            print(f"\n[COGNITIVE-LOOP] Game ended: {self._game_id}")
            print(f"    Actions: {self._actions_taken}")
            print(f"    Level: {self._current_level}")
            print(f"    Score: {self._score}")
            if self._causal_map:
                print(f"    {self._causal_map.summary()}")
        return self._frames

    # ─── Prior Knowledge Loading ──────────────────────────────────────

    def _load_prior_knowledge(self, game_id: str):
        """
        Load accumulated knowledge from the database into the causal map.

        This is what makes the system LEARN ACROSS GAMES rather than
        starting from scratch. We load:

        1. World model states — causal maps from prior sessions with
           this same game, containing position-effect mappings that
           were empirically discovered.

        2. Action effectiveness — which actions produce frame changes
           for this game type, so the agent knows what kinds of actions
           are productive before taking its first step.

        3. Game lessons — distilled insights from hundreds of games,
           like "clicking toggles neighbors" or "avoid edges."

        The loaded knowledge seeds the causal map with non-zero
        completeness, which shifts strategy from "explore" (random)
        to "experiment"/"exploit" (rung-system-informed), so the
        cognitive architecture actually gets used.
        """
        if self._db is None:
            return

        import json

        game_type = game_id[:4] if len(game_id) >= 4 else game_id
        effects_loaded = 0
        rules_loaded = 0

        # ─── 1. Load best causal map from prior sessions ─────────────
        try:
            # Get the most complete world model state for this game
            # (the one from the session with the most steps = most knowledge)
            rows = self._db.execute_query("""
                SELECT objects_json FROM world_model_states
                WHERE game_id = ?
                ORDER BY step_number DESC
                LIMIT 1
            """, (game_id,))

            if rows and rows[0]:
                obj_json = rows[0].get('objects_json') if isinstance(rows[0], dict) else rows[0][0]
                if obj_json:
                    data = json.loads(obj_json)
                    causal_data = data.get('causal_map', {})

                    for pos_key, effect_data in causal_data.items():
                        try:
                            if isinstance(pos_key, str):
                                parts = pos_key.strip('()').split(',')
                                pos = (int(parts[0].strip()), int(parts[1].strip()))
                            elif isinstance(pos_key, tuple):
                                pos = pos_key
                            else:
                                continue

                            # Import into causal map
                            observations = effect_data.get('observations', [])
                            if observations:
                                # Determine if this position produces changes
                                any_change = any(
                                    len(obs.get('changes', [])) > 0
                                    for obs in observations
                                )
                                affected = []
                                color_transitions = {}

                                for obs in observations:
                                    for ch in obs.get('changes', []):
                                        cell = (ch.get('x', 0), ch.get('y', 0))
                                        if cell not in affected:
                                            affected.append(cell)
                                        from_c = ch.get('from_color', 0)
                                        to_c = ch.get('to_color', 0)
                                        color_transitions[f"{cell}"] = {
                                            'from': from_c, 'to': to_c
                                        }

                                from engines.cognition.causal_map import TileEffect
                                self._causal_map._effects[pos] = TileEffect(
                                    position=pos,
                                    affected=affected,
                                    color_transitions=color_transitions,
                                    observation_count=len(observations),
                                    last_frame_changed=any_change,
                                )
                                self._causal_map._explored.add(pos)
                                self._causal_map._all_positions.add(pos)
                                effects_loaded += 1

                        except Exception:
                            continue

        except Exception as e:
            logger.debug(f"[PRIOR-KNOWLEDGE] World model load failed: {e}")

        # ─── 2. Load action effectiveness for this game ──────────────
        try:
            rows = self._db.execute_query("""
                SELECT action_number, success_rate, attempts, successes
                FROM action_effectiveness
                WHERE game_id = ?
            """, (game_id,))

            if rows:
                for row in rows:
                    if isinstance(row, dict):
                        action_num = row.get('action_number', 0)
                        success_rate = row.get('success_rate', 0.0)
                    else:
                        action_num = row[0]
                        success_rate = row[1] if len(row) > 1 else 0.0

                    # Store as a rule-like insight
                    if success_rate > 0.5:
                        from engines.cognition.causal_map import CausalRule
                        self._causal_map._rules.append(CausalRule(
                            rule_type=f"action{action_num}_effective",
                            description=(
                                f"ACTION{action_num} produces frame changes "
                                f"{success_rate:.0%} of the time"
                            ),
                            evidence_count=1,
                            confidence=min(0.8, success_rate),
                        ))
                        rules_loaded += 1

        except Exception as e:
            logger.debug(f"[PRIOR-KNOWLEDGE] Action effectiveness load failed: {e}")

        # ─── 3. Load game lessons ────────────────────────────────────
        try:
            rows = self._db.execute_query("""
                SELECT lesson_text, lesson_type, confidence, key_action
                FROM game_lessons_learned
                WHERE game_type = ? AND confidence > 0.5
                ORDER BY times_retrieved DESC, confidence DESC
                LIMIT 10
            """, (game_type,))

            if rows:
                for row in rows:
                    if isinstance(row, dict):
                        lesson = row.get('lesson_text', '')
                        lesson_type = row.get('lesson_type', 'info')
                        confidence = row.get('confidence', 0.5)
                    else:
                        lesson = row[0] if row else ''
                        lesson_type = row[1] if len(row) > 1 else 'info'
                        confidence = row[2] if len(row) > 2 else 0.5

                    # Store as rules in the causal map
                    from engines.cognition.causal_map import CausalRule
                    self._causal_map._rules.append(CausalRule(
                        rule_type=f"lesson_{lesson_type}",
                        description=str(lesson)[:200],
                        evidence_count=1,
                        confidence=float(confidence) * 0.7,  # Discount slightly
                    ))
                    rules_loaded += 1

        except Exception as e:
            logger.debug(f"[PRIOR-KNOWLEDGE] Game lessons load failed: {e}")

        # ─── 4. Load death zones as anti-knowledge ───────────────────
        try:
            rows = self._db.execute_query("""
                SELECT x_min, x_max, y_min, y_max, danger_score
                FROM death_zones
                WHERE game_type = ? AND is_active = 1
                ORDER BY danger_score DESC
                LIMIT 20
            """, (game_type,))

            if rows:
                for row in rows:
                    if isinstance(row, dict):
                        x_min = row.get('x_min', 0)
                        x_max = row.get('x_max', 0)
                        y_min = row.get('y_min', 0)
                        y_max = row.get('y_max', 0)
                    else:
                        x_min, x_max, y_min, y_max = row[0], row[1], row[2], row[3]

                    # Mark these positions as explored-and-dangerous
                    for x in range(x_min, x_max + 1):
                        for y in range(y_min, y_max + 1):
                            pos = (x, y)
                            self._causal_map._explored.add(pos)
                            self._causal_map._all_positions.add(pos)

        except Exception as e:
            logger.debug(f"[PRIOR-KNOWLEDGE] Death zones load failed: {e}")

        # ─── Summary ─────────────────────────────────────────────────
        if effects_loaded > 0 or rules_loaded > 0:
            self._prior_knowledge_loaded = True
            self._prior_effects_count = effects_loaded
            self._prior_rules_count = rules_loaded

    # ─── The Main Loop: Perceive -> Think -> Map -> Act ───────────────

    def cycle(
        self,
        frame: Any,
        obs: Any,
        agent_id: str = "",
        agent_role: str = "pioneer",
        w_A: float = 0.5,
        w_B: float = 0.5,
        **extra_context,
    ) -> Tuple[int, Optional[Dict], CognitiveFrame]:
        """
        Execute one complete Perceive-Think-Map-Act cycle.

        Args:
            frame: Raw game frame (64x64)
            obs: Full observation object from API
            agent_id: Agent identifier
            agent_role: Agent role
            w_A: Stream A weight
            w_B: Stream B weight
            **extra_context: Additional context passed to rung system

        Returns:
            (action_number, action_data, cognitive_frame)
            action_number: 1-7
            action_data: {x, y} for ACTION6, None otherwise
            cognitive_frame: Observable record of this cycle
        """
        cf = CognitiveFrame(
            action_number=self._actions_taken,
            timestamp=time.time(),
            level=self._current_level,
        )

        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: PERCEIVE
        # ═══════════════════════════════════════════════════════════════
        percept = self._perceive(frame, cf)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: THINK
        # ═══════════════════════════════════════════════════════════════
        strategy, certainty = self._think(percept, cf)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 3: MAP (consult, don't update yet — update after action)
        # ═══════════════════════════════════════════════════════════════
        plan_action = self._consult_map(percept, strategy, cf)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 4: ACT (three speeds)
        # ═══════════════════════════════════════════════════════════════
        action_num, action_data = self._act(
            percept, strategy, certainty, plan_action,
            obs, agent_id, agent_role, w_A, w_B, cf, **extra_context,
        )

        # Store frame and action info for next cycle
        frame_array = self._perceiver._to_numpy(frame)
        self._prev_frame = frame_array
        self._last_action_info = {
            'type': action_num,
            'x': action_data.get('x') if action_data else None,
            'y': action_data.get('y') if action_data else None,
            'frame_changed': False,  # Will be updated by record_result
            'score_delta': 0.0,
            'level_changed': False,
            'consecutive_no_change': self._consecutive_no_change,
        }

        self._actions_taken += 1
        self._current_frame = cf
        self._frames.append(cf)

        # NOTE: Don't print cf.to_log_line() here — frame_changed is not yet known.
        # The caller should print AFTER calling record_result().

        return action_num, action_data, cf

    def record_result(
        self,
        post_frame: Any,
        frame_changed: bool,
        score_delta: float,
        level_changed: bool,
        new_level: int = 0,
        new_score: float = 0.0,
    ):
        """
        Record the result of the last action.

        This is where MAP gets updated — we now know what our action DID.
        This closes the loop: the updated map will inform the next PERCEIVE.
        """
        cf = self._current_frame
        if cf is None:
            return

        # Update cognitive frame with result
        cf.frame_changed = frame_changed
        cf.score_delta = score_delta
        cf.level_changed = level_changed

        if frame_changed:
            self._consecutive_no_change = 0
        else:
            self._consecutive_no_change += 1

        # Calculate surprise
        if self._causal_map and self._last_action_info:
            click_pos = None
            if self._last_action_info.get('x') is not None:
                click_pos = (self._last_action_info['x'], self._last_action_info['y'])

            if click_pos and click_pos in self._causal_map._effects:
                # We had a prediction — how surprising is the result?
                expected_change = self._causal_map._effects[click_pos].last_frame_changed
                if expected_change == frame_changed:
                    cf.surprise = 0.1  # As expected
                else:
                    cf.surprise = 0.8  # Surprising!
            else:
                cf.surprise = 0.5  # No prediction, moderate surprise

        # ═══════════════════════════════════════════════════════════════
        # MAP UPDATE: Learn from the action's consequence
        # ═══════════════════════════════════════════════════════════════
        if self._causal_map and self._last_action_info:
            click_x = self._last_action_info.get('x')
            click_y = self._last_action_info.get('y')

            if click_x is not None and click_y is not None:
                pre = self._prev_frame
                post = self._perceiver._to_numpy(post_frame)

                self._causal_map.update_from_action(
                    click_pos=(click_x, click_y),
                    pre_frame=pre,
                    post_frame=post,
                    frame_changed=frame_changed,
                )

                cf.map_update = f"Recorded effect at ({click_x},{click_y})"
                if not frame_changed:
                    cf.map_update += " [no effect]"

                # Update map summary
                cf.map_completeness = self._causal_map.completeness
                cf.effects_known = len(self._causal_map._effects)
                cf.positions_explored = len(self._causal_map._explored)
                cf.map_summary = self._causal_map.summary()

        # Update last action info for next temporal perception
        if self._last_action_info:
            self._last_action_info['frame_changed'] = frame_changed
            self._last_action_info['score_delta'] = score_delta
            self._last_action_info['level_changed'] = level_changed
            self._last_action_info['consecutive_no_change'] = self._consecutive_no_change

        # Update game state
        if level_changed:
            self._current_level = new_level if new_level > 0 else self._current_level + 1
        self._score = new_score if new_score else self._score + score_delta

        # Build result summary
        parts = []
        if frame_changed:
            parts.append("Frame changed")
        else:
            parts.append(f"No change (x{self._consecutive_no_change})")
        if score_delta > 0:
            parts.append(f"score +{score_delta:.2f}")
        elif score_delta < 0:
            parts.append(f"score {score_delta:.2f}")
        if level_changed:
            parts.append("[LEVEL-UP]")
        cf.result_summary = " | ".join(parts)

    # ─── Phase Implementations ────────────────────────────────────────

    def _perceive(self, frame: Any, cf: CognitiveFrame) -> PerceptualField:
        """PHASE 1: Run all perception channels and integrate."""
        percept = self._perceiver.perceive(
            frame,
            last_action=self._last_action_info,
            causal_map=self._causal_map,
            available_actions=self._available_actions,
            actions_taken=self._actions_taken,
            max_actions=self._max_actions,
            game_id=self._game_id,
        )

        # ── Bridge: Feed perception back into the causal map ──────────
        if self._causal_map:
            # Register discovered positions so completeness can rise above 0%
            positions_to_register = []

            # From detected objects (centroid positions)
            # Filter to small objects (< 1/8 frame area) = likely interactive
            # tiles, not background panels. Large blobs add noise.
            frame_area = 64 * 64
            for obj in percept.objects:
                if obj.get('size', frame_area) >= frame_area // 8:
                    continue  # Skip large background regions
                cx = int(obj.get('centroid_x', obj.get('x', 0)))
                cy = int(obj.get('centroid_y', obj.get('y', 0)))
                if 0 < cx < 64 and 0 < cy < 64:
                    positions_to_register.append((cx, cy))

            # From tile grid (inferred cell centers)
            if percept.tile_count > 0 and percept.interactive_bounds:
                y_min, x_min, y_max, x_max = percept.interactive_bounds
                rows = max(1, percept.grid_rows)
                cols = max(1, percept.grid_cols)
                tile_h = (y_max - y_min) // rows
                tile_w = (x_max - x_min) // cols
                for r in range(rows):
                    for c in range(cols):
                        tx = x_min + c * tile_w + tile_w // 2
                        ty = y_min + r * tile_h + tile_h // 2
                        positions_to_register.append((tx, ty))

            if positions_to_register:
                self._causal_map.register_positions(positions_to_register)

            # Forward goal cells to causal map so plan_to_goal() can work
            if percept.has_goal and percept.goal_cells:
                self._causal_map.set_goal(percept.goal_cells)
            if percept.current_cells:
                self._causal_map.set_current_state(percept.current_cells)

        # Record in cognitive frame
        cf.perception_summary = percept.summary()
        cf.panel_count = percept.panel_count
        cf.tile_count = percept.tile_count
        cf.goal_progress = percept.goal_progress
        cf.delta_count = len(percept.delta)
        cf.colors_present = sorted(percept.colors_present)
        cf.puzzle_type = percept.puzzle_type
        cf.spatial_confidence = percept.spatial_confidence
        cf.overall_confidence = percept.overall_confidence

        return percept

    def _think(
        self, percept: PerceptualField, cf: CognitiveFrame
    ) -> Tuple[str, float]:
        """
        PHASE 2: Phenomenological compression + strategy selection.

        Delegates to PhenomenologyLayer.compress() which produces a 5-D
        FeltState (valence, arousal, certainty, agency, salience) with
        momentum, hysteresis stabilization, and trace logging.  The
        FeltState is then injected back into the adapter so that the
        next cycle's compression is informed by the previous one (the
        consciousness-like feedback loop).

        Strategy is derived from FeltState + game-specific signals.
        """
        # Prepare loop-level state for the adapter
        recent_path: List[Any] = [
            (f.action_x, f.action_y)
            for f in self._frames[-5:]
            if f.action_x is not None
        ]
        loop_state: Dict[str, Any] = {
            "levels_completed": max(0, self._current_level - 1),
            "total_levels": 6,
            "max_actions": self._max_actions,
            "actions_taken": self._actions_taken,
            "recent_path": recent_path,
        }

        # Feed fresh perception into adapter -> PhenomenologyLayer
        self._bb_adapter.update(percept, loop_state)

        # Compress perception to 5-D FeltState
        felt: FeltState = self._phenomenology.compress()

        # Inject back for feedback loop (writes felt_* into adapter)
        self._phenomenology.inject(felt)

        # Derive action strategy from FeltState + game signals
        strategy = self._derive_strategy(
            felt, percept, _prior_loaded=self._prior_knowledge_loaded
        )

        # Track strategy history for stability computation
        self._bb_adapter._recent_strategies.append(strategy)
        if len(self._bb_adapter._recent_strategies) > 10:
            self._bb_adapter._recent_strategies = (
                self._bb_adapter._recent_strategies[-10:]
            )

        # Record on cognitive frame
        cf.thought_summary = (
            f"{felt.valence.value.upper()} | "
            f"certainty:{felt.certainty:.2f} | "
            f"strategy:{strategy}"
        )
        cf.valence = felt.valence.value  # Valence enum -> string
        cf.arousal = felt.arousal
        cf.certainty = felt.certainty
        cf.agency = felt.agency
        cf.salience = felt.salience
        cf.momentum = felt.momentum
        cf.dominant_contributors = list(felt.dominant_contributors)
        cf.information_gain = felt.compression_ratio
        cf.strategy = strategy

        # Try to get epistemic state from cognitive router
        if self._decision_system:
            try:
                router = getattr(self._decision_system, '_cognitive_router', None)
                if router and hasattr(router, 'epistemic_tracker'):
                    cf.epistemic_state = (
                        router.epistemic_tracker.current_state.primary_quadrant.name
                    )
            except Exception:
                pass

        return strategy, felt.certainty

    # ------------------------------------------------------------------
    # Strategy derivation from FeltState
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_strategy(
        felt: FeltState,
        percept: PerceptualField,
        _prior_loaded: bool = False,
    ) -> str:
        """
        Derive action strategy from FeltState + game state.

        Strategy hierarchy (most to least committed):
          execute   - Plan exists, high certainty, favourable valence
          exploit   - Good understanding, use what we know
          experiment - Something is wrong, break out of local optimum
          explore   - Low understanding, gather information

        When prior knowledge is loaded, we lower the thresholds for
        exploit/experiment so the rung system gets used from the start
        instead of defaulting to pure exploration.
        """
        # EXECUTE: plan ready + confident + positive valence
        if (
            percept.has_plan
            and percept.map_completeness > 0.7
            and felt.valence in (Valence.OPPORTUNITY, Valence.STABILITY)
        ):
            return "execute"

        # EXPERIMENT: bored / stuck / confidently threatened
        if felt.valence == Valence.BOREDOM:
            return "experiment"
        if felt.valence == Valence.THREAT and felt.certainty > 0.5:
            return "experiment"
        if percept.consecutive_no_change > 8:
            return "experiment"

        # With prior knowledge, we start with enough understanding to
        # use the rung system (experiment/exploit) rather than random explore.
        if _prior_loaded:
            # EXPLOIT: even modest map coverage suffices with prior knowledge
            if percept.map_completeness > 0.1 or felt.certainty > 0.2:
                return "exploit"
            # EXPERIMENT: we have knowledge, try applying it
            return "experiment"

        # EXPLOIT: medium-high certainty with some map coverage
        if felt.certainty > 0.5 and percept.map_completeness > 0.4:
            return "exploit"
        if felt.valence == Valence.OPPORTUNITY and felt.agency > 0.5:
            return "exploit"

        # EXPLORE: default -- gather information
        return "explore"

    def _consult_map(
        self,
        percept: PerceptualField,
        strategy: str,
        cf: CognitiveFrame,
    ) -> Optional[PlannedAction]:
        """
        PHASE 3: Consult the causal map for planned actions.

        If strategy is "execute" and we have a plan, return the next step.
        Otherwise, return None and let ACT decide.
        """
        if self._causal_map is None:
            cf.map_summary = "[MAP] No causal map"
            return None

        # Record map state
        cf.map_completeness = self._causal_map.completeness
        cf.effects_known = len(self._causal_map._effects)
        cf.positions_explored = len(self._causal_map._explored)
        cf.positions_total = len(self._causal_map._all_positions)
        cf.rules_discovered = [r.rule_type for r in self._causal_map._rules]
        cf.has_plan = self._causal_map.has_plan
        cf.plan_length = len(self._causal_map._plan)
        cf.plan_step = self._causal_map.plan_step
        cf.map_summary = self._causal_map.summary()

        # If strategy is execute and we have a plan, return next step
        if strategy == "execute":
            plan_action = self._causal_map.get_next_plan_action()
            if plan_action:
                return plan_action

            # Try to generate a plan
            plan = self._causal_map.plan_to_goal()
            if plan:
                return plan[0]

        return None

    def _act(
        self,
        percept: PerceptualField,
        strategy: str,
        certainty: float,
        plan_action: Optional[PlannedAction],
        obs: Any,
        agent_id: str,
        agent_role: str,
        w_A: float,
        w_B: float,
        cf: CognitiveFrame,
        **extra_context,
    ) -> Tuple[int, Optional[Dict]]:
        """
        PHASE 4: Three-speed action selection.

        SPEED 1 - MAPPED (fast): Execute plan step from causal map
        SPEED 2 - REASONED (medium): Use rung system with enriched context
        SPEED 3 - EXPLORE (slow): Maximize information gain
        """
        action_num: int = 1
        action_data: Optional[Dict] = None

        # ─── SPEED 1: MAPPED ─────────────────────────────────────────
        if plan_action is not None and strategy == "execute":
            pos = plan_action.position
            action_num = 6  # Click action
            action_data = {'x': pos[0], 'y': pos[1]}

            cf.action_speed = "mapped"
            cf.action_type = 6
            cf.action_x = pos[0]
            cf.action_y = pos[1]
            cf.action_reason = plan_action.reason
            cf.action_confidence = plan_action.confidence
            cf.action_summary = (
                f"MAPPED: Click ({pos[0]},{pos[1]}) | "
                f"plan step {plan_action.step_number + 1}/{cf.plan_length}"
            )

            # Advance the plan
            if self._causal_map:
                self._causal_map.advance_plan()

            return action_num, action_data

        # ─── SPEED 2: REASONED (delegate to rung system) ─────────────
        if self._decision_system is not None and strategy in ("exploit", "experiment"):
            try:
                # Build context for the rung system (backward compatible)
                context = self._build_rung_context(
                    percept, obs, agent_id, agent_role, w_A, w_B, **extra_context
                )

                result = self._decision_system.decide(obs, context)
                if isinstance(result, tuple):
                    action_str, reason = result
                    if isinstance(action_str, str) and action_str.startswith('ACTION'):
                        action_num = int(action_str.replace('ACTION', ''))
                    else:
                        import random
                        action_num = random.choice(self._available_actions)

                    # Extract coordinates for ACTION6
                    if action_num == 6 and hasattr(self._decision_system, 'last_decision_metadata'):
                        metadata = self._decision_system.last_decision_metadata or {}
                        if 'pixel_position' in metadata:
                            px, py = metadata['pixel_position']
                            action_data = {'x': int(px), 'y': int(py)}
                        elif 'target' in metadata:
                            t = metadata['target']
                            action_data = {'x': int(t.get('x', 32)), 'y': int(t.get('y', 32))}
                        elif 'x' in metadata and 'y' in metadata:
                            action_data = {'x': int(metadata['x']), 'y': int(metadata['y'])}

                    cf.action_speed = "reasoned"
                    cf.action_type = action_num
                    cf.action_reason = reason[:100] if reason else "rung decision"
                    cf.rung_name = ""
                    if hasattr(self._decision_system, 'last_decision_metadata'):
                        md = self._decision_system.last_decision_metadata or {}
                        cf.rung_name = md.get('rung_name', md.get('rung', ''))
                        cf.action_confidence = md.get('confidence', 0.0)

                    if action_data:
                        cf.action_x = action_data.get('x')
                        cf.action_y = action_data.get('y')

                    cf.action_summary = (
                        f"REASONED: ACTION{action_num}"
                        + (f" @({cf.action_x},{cf.action_y})" if cf.action_x else "")
                        + (f" [{cf.rung_name}]" if cf.rung_name else "")
                    )

                    return action_num, action_data

            except Exception as e:
                logger.debug(f"[COGNITIVE-LOOP] Rung system failed: {e}")

        # ─── SPEED 3: EXPLORE (maximize information gain) ─────────────
        import random

        if self._causal_map and 6 in self._available_actions:
            # Click the position with highest information gain
            target = self._causal_map.best_exploration_target()
            if target:
                action_num = 6
                action_data = {'x': target[0], 'y': target[1]}
                info_gain = self._causal_map.information_gain(target)

                cf.action_speed = "explore"
                cf.action_type = 6
                cf.action_x = target[0]
                cf.action_y = target[1]
                cf.action_reason = f"Explore: info_gain={info_gain:.2f}"
                cf.action_confidence = info_gain
                cf.information_gain = info_gain
                cf.action_summary = f"EXPLORE: Click ({target[0]},{target[1]}) | info_gain={info_gain:.2f}"

                return action_num, action_data

        # Fallback for click games: use perception to find interesting targets
        if 6 in self._available_actions:
            # Use perception channels to find clickable positions
            target_x, target_y = self._find_explore_target(percept)
            action_num = 6
            action_data = {'x': target_x, 'y': target_y}

            cf.action_speed = "explore"
            cf.action_type = 6
            cf.action_x = target_x
            cf.action_y = target_y
            cf.action_reason = "Explore: perception-guided"
            cf.action_confidence = 0.2
            cf.action_summary = f"EXPLORE: Click ({target_x},{target_y}) | perception-guided"

            return action_num, action_data

        # Absolute fallback: random available action
        action_num = random.choice(self._available_actions)
        cf.action_speed = "random"
        cf.action_type = action_num
        cf.action_reason = "random fallback"
        cf.action_summary = f"RANDOM: ACTION{action_num}"

        return action_num, action_data

    # ─── Context Bridge ───────────────────────────────────────────────

    def _find_explore_target(
        self, percept: PerceptualField
    ) -> tuple:
        """
        Find an interesting position to click based on perception.

        Uses multiple strategies in priority order:
        1. Object centroids from perception
        2. Tile positions from spatial analysis
        3. Positions with non-background colors
        4. Random position within interactive bounds
        """
        import random

        # Strategy 1: Click objects we haven't clicked yet
        # For click games, prefer small discrete objects (tiles/buttons) over
        # large background regions. Sort by size ascending so we try tiles first.
        if percept.objects:
            explored = set()
            if self._causal_map:
                explored = self._causal_map._explored
            sorted_objects = sorted(
                percept.objects,
                key=lambda o: o.get('size', 9999),
            )
            for obj in sorted_objects:
                cx = int(obj.get('centroid_x', obj.get('x', 0)))
                cy = int(obj.get('centroid_y', obj.get('y', 0)))
                if (cx, cy) not in explored and 0 < cx < 64 and 0 < cy < 64:
                    return (cx, cy)

        # Strategy 2: Use tile positions if available
        if percept.tile_count > 0 and percept.interactive_bounds:
            y_min, x_min, y_max, x_max = percept.interactive_bounds
            rows = max(1, percept.grid_rows)
            cols = max(1, percept.grid_cols)
            tile_h = (y_max - y_min) // rows
            tile_w = (x_max - x_min) // cols
            tiles = []
            for r in range(rows):
                for c in range(cols):
                    tx = x_min + c * tile_w + tile_w // 2
                    ty = y_min + r * tile_h + tile_h // 2
                    tiles.append((tx, ty))
            explored = set()
            if self._causal_map:
                explored = self._causal_map._explored
            unexplored = [t for t in tiles if t not in explored]
            if unexplored:
                return random.choice(unexplored)
            if tiles:
                return random.choice(tiles)

        # Strategy 3: Find non-background pixels in the frame
        if percept.frame is not None:
            try:
                arr = self._perceiver._to_numpy(percept.frame)
                if arr is not None:
                    nonzero = list(zip(*np.where(arr > 0)))
                    if nonzero:
                        # Sample a few and pick one not yet explored
                        sample = random.sample(nonzero, min(20, len(nonzero)))
                        explored = set()
                        if self._causal_map:
                            explored = self._causal_map._explored
                        for (y, x) in sample:
                            if (int(x), int(y)) not in explored:
                                return (int(x), int(y))
                        y, x = sample[0]
                        return (int(x), int(y))
            except Exception:
                pass

        # Strategy 4: Random position within interactive bounds or full frame
        if percept.interactive_bounds:
            y_min, x_min, y_max, x_max = percept.interactive_bounds
            return (random.randint(x_min, x_max), random.randint(y_min, y_max))

        return (random.randint(5, 58), random.randint(5, 58))

    def _build_rung_context(
        self,
        percept: PerceptualField,
        obs: Any,
        agent_id: str,
        agent_role: str,
        w_A: float,
        w_B: float,
        **extra_context,
    ) -> Dict[str, Any]:
        """
        Build a context dict compatible with the existing rung system.

        This bridges the new PerceptualField to the old 60-key context dict.
        Existing rungs continue to work unchanged.

        NEW: Adds 'percept' key with the full PerceptualField,
        so rungs that want structured perception can use it.
        """
        # Start with context_builder output if available
        context: Dict[str, Any] = {}

        if self._context_builder is not None:
            try:
                dc = self._context_builder.build_from_runner_state(
                    game_id=self._game_id,
                    obs=obs,
                    agent_id=agent_id,
                    agent_role=agent_role,
                    w_A=w_A,
                    w_B=w_B,
                    actions_taken=self._actions_taken,
                    max_actions=self._max_actions,
                    available_actions=self._available_actions,
                    win_levels=self._current_level - 1,
                    score=self._score,
                    **{k: v for k, v in extra_context.items()
                       if k in {
                           'last_action', 'recent_actions', 'last_frame_changed',
                           'failed_actions', 'score_delta', 'last_outcome',
                           'has_full_win', 'active_sequence', 'sequence_position',
                           'is_replay_mode', 'has_level_sequence', 'stuck_count',
                           'tried_colors', 'frame_hash', 'level_start_action_index',
                           'session_id', 'scorecard_id',
                       }},
                )
                context = dc.to_dict()
            except Exception as e:
                logger.debug(f"[COGNITIVE-LOOP] Context builder failed: {e}")

        # Enrich with structured perception
        context['percept'] = percept
        context['perceptual_field'] = percept.to_dict()
        context['causal_map'] = self._causal_map

        # Ensure visual_scene is populated (backward compat)
        if percept.visual_scene_dict and 'visual_scene' not in context:
            context['visual_scene'] = percept.visual_scene_dict

        # Ensure world_model is populated
        if 'world_model' not in context:
            context['world_model'] = {}
        if self._causal_map:
            context['world_model']['causal_map_typed'] = self._causal_map
            context['world_model']['map_completeness'] = self._causal_map.completeness

        return context

    # ─── Replay Access ────────────────────────────────────────────────

    def get_replay(self) -> List[CognitiveFrame]:
        """Get all cognitive frames from this game session."""
        return self._frames

    def print_replay(self, start: int = 0, end: Optional[int] = None):
        """Print replay to console in dashboard format."""
        frames = self._frames[start:end]
        for cf in frames:
            print(cf.to_dashboard())
            print()

    def print_log(self, start: int = 0, end: Optional[int] = None):
        """Print replay to console in single-line log format."""
        frames = self._frames[start:end]
        for cf in frames:
            print(cf.to_log_line())

    @property
    def causal_map(self) -> Optional[CausalMap]:
        """Access the causal map for external inspection."""
        return self._causal_map
