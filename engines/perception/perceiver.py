import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Perceiver - Multimodal Perception Integration.

Runs multiple perception channels in parallel on each frame,
then integrates them into a single PerceptualField.

Channels:
1. Spatial Structure (VisualCortex) — panels, grids, tiles
2. Object Inventory (ObjectDetector) — what objects exist, what changed
3. Goal State (reference panel) — what the target looks like
4. Temporal (frame diff + action history) — what just happened
5. Causal Context (CausalMap feedback) — what we already know

Integration is by mutual constraint satisfaction:
- Agreement between channels amplifies confidence
- Contradiction dampens confidence
- Causal context prunes impossible perceptions
"""

import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from engines.perception.perceptual_field import ActionEffect, CellDiff, PerceptualField

logger = logging.getLogger(__name__)

# Graceful imports — each channel degrades independently
try:
    from engines.perception.visual_cortex import VisualCortex
    VISUAL_CORTEX_AVAILABLE = True
except ImportError:
    VISUAL_CORTEX_AVAILABLE = False
    VisualCortex = None  # type: ignore[assignment, misc]

try:
    from engines.perception.object_detector import ObjectDetector
    OBJECT_DETECTOR_AVAILABLE = True
except ImportError:
    OBJECT_DETECTOR_AVAILABLE = False


class Perceiver:
    """
    Multimodal perception integration.

    Runs all available perception channels on each frame,
    integrates results into a PerceptualField.

    This replaces the scattered perception calls in ContextBuilder
    with a single, structured perception step.
    """

    def __init__(self):
        """Initialize perception channels."""
        # Channel 1: Spatial/structural
        self._visual_cortex = None
        if VISUAL_CORTEX_AVAILABLE:
            try:
                self._visual_cortex = VisualCortex()
                logger.info("[PERCEIVER] VisualCortex initialized (spatial channel)")
            except Exception as e:
                logger.warning(f"[PERCEIVER] VisualCortex init failed: {e}")

        # Channel 2: Object detection
        self._object_detector = None
        if OBJECT_DETECTOR_AVAILABLE:
            try:
                self._object_detector = ObjectDetector()
                logger.info("[PERCEIVER] ObjectDetector initialized (object channel)")
            except Exception as e:
                logger.warning(f"[PERCEIVER] ObjectDetector init failed: {e}")

        # State
        self._prev_frame: Optional[np.ndarray] = None
        self._prev_scene: Optional[Dict] = None
        self._last_scene_obj: Optional[Any] = None  # VisualScene for goal extraction
        self._action_count: int = 0

    def reset(self):
        """Reset state for a new game."""
        self._prev_frame = None
        self._prev_scene = None
        self._last_scene_obj = None
        self._action_count = 0

    def perceive(
        self,
        frame: Any,
        *,
        last_action: Optional[Dict[str, Any]] = None,
        causal_map: Optional[Any] = None,
        available_actions: Optional[List[int]] = None,
        actions_taken: int = 0,
        max_actions: int = 500,
        _game_id: str = "",
    ) -> PerceptualField:
        """
        Run all perception channels and integrate into a PerceptualField.

        Args:
            frame: Raw game frame (64x64 grid, numpy array or list-of-lists)
            last_action: Info about the last action taken
                         {type: int, x: int, y: int, frame_changed: bool, score_delta: float}
            causal_map: CausalMap instance for causal context channel
            available_actions: Which actions are available in this game
            actions_taken: How many actions taken so far
            max_actions: Maximum actions allowed
            game_id: Current game identifier

        Returns:
            PerceptualField with all channels integrated
        """
        pf = PerceptualField()
        pf.actions_taken = actions_taken
        pf.actions_remaining = max(0, max_actions - actions_taken)

        # Convert frame to usable formats
        frame_array = self._to_numpy(frame)
        frame_list = self._to_list(frame, frame_array)
        pf.frame = frame_array

        # === CHANNEL 1: Spatial Structure ===
        visual_scene_dict = self._run_spatial_channel(frame_list, pf)

        # === CHANNEL 2: Object Inventory ===
        self._run_object_channel(frame_array, visual_scene_dict, pf)

        # === CHANNEL 3: Goal State ===
        self._run_goal_channel(visual_scene_dict, frame_array, pf)

        # === CHANNEL 4: Temporal ===
        self._run_temporal_channel(frame_array, last_action, pf)

        # === CHANNEL 5: Causal Context ===
        self._run_causal_channel(causal_map, pf)

        # === INTEGRATE: Cross-channel validation ===
        self._integrate_channels(pf, available_actions)

        # Store for next frame comparison
        self._prev_frame = frame_array
        self._prev_scene = visual_scene_dict
        self._action_count = actions_taken

        return pf

    # ─── Channel Implementations ──────────────────────────────────────

    def _run_spatial_channel(
        self, frame_list: Optional[list], pf: PerceptualField
    ) -> Optional[Dict]:
        """Channel 1: Spatial structure from VisualCortex."""
        if self._visual_cortex is None or frame_list is None:
            return None

        try:
            scene = self._visual_cortex.analyze(frame_list)
            scene_dict = scene.to_dict()
            pf.visual_scene_dict = scene_dict
            self._last_scene_obj = scene  # Keep for goal channel panel access

            # Extract structured info
            pf.panel_count = scene_dict.get('panel_count', 0)
            pf.panel_layout = scene_dict.get('panel_layout', 'unknown')
            pf.panel_roles = scene_dict.get('panel_roles', [])

            grid_struct = scene_dict.get('grid_structure')
            if grid_struct:
                pf.grid_rows = grid_struct.get('grid_rows', 0)
                pf.grid_cols = grid_struct.get('grid_cols', 0)

            tile_grids = scene_dict.get('tile_grids', [])
            if tile_grids:
                pf.tile_count = sum(
                    tg.get('tile_rows', 0) * tg.get('tile_cols', 0)
                    for tg in tile_grids
                )

            pf.colors_present = set(scene_dict.get('colors_used', []))
            pf.unique_colors = len(pf.colors_present)
            pf.spatial_confidence = scene_dict.get('complexity_score', 0.5)

            # Extract narrative
            pf.narrative = scene_dict.get('scene_narrative', '')

            return scene_dict

        except Exception as e:
            logger.debug(f"[PERCEIVER] Spatial channel failed: {e}")
            return None

    def _run_object_channel(
        self,
        frame_array: Optional[np.ndarray],
        visual_scene_dict: Optional[Dict],
        pf: PerceptualField,
    ) -> None:
        """Channel 2: Object inventory from scene data or frame analysis."""
        try:
            raw_objects: List[Dict[str, Any]] = []

            if visual_scene_dict is not None:
                raw_objects = visual_scene_dict.get('objects', [])

            if not raw_objects and frame_array is not None:
                # Fallback: connected-component color cluster detection
                raw_objects = self._detect_color_clusters(frame_array)

            # Normalize objects to always have centroid_x / centroid_y
            # (VisualCortex may use 'centroid' tuple, fallback uses centroid_x/y)
            for obj in raw_objects:
                if 'centroid_x' not in obj:
                    centroid = obj.get('centroid')
                    if isinstance(centroid, (list, tuple)) and len(centroid) >= 2:
                        obj['centroid_x'] = float(centroid[0])
                        obj['centroid_y'] = float(centroid[1])
                    else:
                        obj['centroid_x'] = float(obj.get('x', 0))
                        obj['centroid_y'] = float(obj.get('y', 0))

            pf.objects = raw_objects
            pf.inventory_confidence = 0.6 if raw_objects else 0.1

            # Detect changes from previous frame
            if self._prev_frame is not None and frame_array is not None:
                changes = self._compute_frame_changes(self._prev_frame, frame_array)
                pf.object_changes = changes

        except Exception as e:
            logger.debug(f"[PERCEIVER] Object channel failed: {e}")

    def _run_goal_channel(
        self,
        visual_scene_dict: Optional[Dict],
        frame_array: Optional[np.ndarray],
        pf: PerceptualField,
    ) -> None:
        """Channel 3: Goal state from reference panel detection.

        When the VisualCortex detects a reference panel, this channel
        extracts cell-level goal state by comparing the reference panel
        to the workspace panel. This gives us the *delta* — exactly which
        cells need to change and to what color.
        """
        if visual_scene_dict is None or frame_array is None:
            return

        try:
            ref_panel_id = visual_scene_dict.get('reference_panel_id')
            transformations = visual_scene_dict.get('transformations', [])

            if ref_panel_id is not None:
                pf.has_goal = True
                pf.goal_confidence = 0.7

                # Try to extract cell-level goal state from panel pixel data
                self._extract_goal_from_panels(ref_panel_id, pf)

                # If panel extraction worked, boost confidence
                if pf.goal_cells:
                    pf.goal_confidence = 0.8

                # Fallback: estimate from tile grids
                if not pf.goal_cells:
                    tile_grids = visual_scene_dict.get('tile_grids', [])
                    if tile_grids:
                        total_cells = sum(
                            tg.get('tile_rows', 0) * tg.get('tile_cols', 0)
                            for tg in tile_grids
                        )
                        pf.cells_total = total_cells

            elif transformations:
                best_transform = max(transformations, key=lambda t: t.get('confidence', 0))
                if best_transform.get('confidence', 0) > 0.3:
                    pf.has_goal = True
                    pf.goal_confidence = best_transform['confidence'] * 0.5

        except Exception as e:
            logger.debug(f"[PERCEIVER] Goal channel failed: {e}")

    def _extract_goal_from_panels(
        self, ref_panel_id: int, pf: PerceptualField
    ) -> None:
        """Extract cell-level goal state by comparing reference and workspace panels.

        Uses the stored VisualScene object to access actual panel pixel data.
        For each tile position, samples the center pixel from both the reference
        panel and workspace panel to build goal_cells, current_cells, and delta.
        """
        scene = self._last_scene_obj
        if scene is None or not hasattr(scene, 'panels'):
            return

        panels = scene.panels
        if ref_panel_id >= len(panels):
            return

        ref_panel = panels[ref_panel_id]

        # Find the workspace/interactive panel (first non-reference panel)
        work_panel = None
        for i, p in enumerate(panels):
            if i != ref_panel_id and p.role in ('workspace', 'output', 'state', 'unknown'):
                work_panel = p
                break
        if work_panel is None:
            # Take any non-reference panel
            for i, p in enumerate(panels):
                if i != ref_panel_id:
                    work_panel = p
                    break
        if work_panel is None:
            return

        # Both panels should have similar structure
        # Try to detect tile grid within each panel and compare cell-by-cell
        ref_region = ref_panel.region
        work_region = work_panel.region

        if ref_region is None or work_region is None:
            return

        # Use tile_grids if available for cell boundaries
        tile_grids = getattr(scene, 'tile_grids', [])
        if tile_grids:
            tg = tile_grids[0]
            rows, cols = tg.tile_rows, tg.tile_cols
            tw, th = tg.tile_width, tg.tile_height

            if rows > 0 and cols > 0 and tw > 0 and th > 0:
                # Sample center pixel of each tile from both panels
                for r in range(rows):
                    for c in range(cols):
                        cy = r * th + th // 2
                        cx = c * tw + tw // 2

                        # Bounds check on both panels
                        if (cy < ref_region.shape[0] and cx < ref_region.shape[1]
                                and cy < work_region.shape[0] and cx < work_region.shape[1]):
                            goal_color = int(ref_region[cy, cx])
                            curr_color = int(work_region[cy, cx])

                            # Use pixel coords relative to the workspace panel
                            # so click targets align with actual frame positions
                            wy_min, wx_min = work_panel.bounds[0], work_panel.bounds[1]
                            abs_x = wx_min + cx
                            abs_y = wy_min + cy

                            pf.goal_cells[(abs_x, abs_y)] = goal_color
                            pf.current_cells[(abs_x, abs_y)] = curr_color

                            if goal_color != curr_color:
                                pf.delta.append(CellDiff(
                                    x=abs_x, y=abs_y,
                                    current_color=curr_color,
                                    goal_color=goal_color,
                                ))

                pf.cells_total = len(pf.goal_cells)
                pf.cells_matching_goal = pf.cells_total - len(pf.delta)
                pf.goal_progress = pf.cells_matching_goal / max(pf.cells_total, 1)
                return

        # Fallback: compare panels directly if same shape
        if ref_region.shape == work_region.shape:
            h, w = ref_region.shape[:2]
            wy_min, wx_min = work_panel.bounds[0], work_panel.bounds[1]
            for y in range(0, h, max(1, h // 8)):
                for x in range(0, w, max(1, w // 8)):
                    goal_color = int(ref_region[y, x])
                    curr_color = int(work_region[y, x])
                    abs_x = wx_min + x
                    abs_y = wy_min + y
                    pf.goal_cells[(abs_x, abs_y)] = goal_color
                    pf.current_cells[(abs_x, abs_y)] = curr_color
                    if goal_color != curr_color:
                        pf.delta.append(CellDiff(
                            x=abs_x, y=abs_y,
                            current_color=curr_color,
                            goal_color=goal_color,
                        ))

            pf.cells_total = len(pf.goal_cells)
            pf.cells_matching_goal = pf.cells_total - len(pf.delta)
            pf.goal_progress = pf.cells_matching_goal / max(pf.cells_total, 1)

    def _run_temporal_channel(
        self,
        frame_array: Optional[np.ndarray],
        last_action: Optional[Dict[str, Any]],
        pf: PerceptualField,
    ) -> None:
        """Channel 4: Temporal analysis — what just happened."""
        if last_action is None:
            pf.temporal_confidence = 0.3  # No action history yet
            return

        try:
            effect = ActionEffect(
                action_type=last_action.get('type', 0),
                x=last_action.get('x'),
                y=last_action.get('y'),
                frame_changed=last_action.get('frame_changed', False),
                score_delta=last_action.get('score_delta', 0.0),
                level_changed=last_action.get('level_changed', False),
            )

            # Count pixel changes
            if self._prev_frame is not None and frame_array is not None:
                diff = (self._prev_frame != frame_array)
                if hasattr(diff, 'sum'):
                    effect.pixels_changed = int(diff.sum())
                changes = self._compute_frame_changes(self._prev_frame, frame_array)
                effect.cells_changed = len(changes)
                effect.changes = [
                    (c.get('x', 0), c.get('y', 0), c.get('old_color', 0), c.get('new_color', 0))
                    for c in changes
                ]

            pf.last_action_effect = effect

            # Surprise: did the action produce the expected result?
            if effect.frame_changed:
                pf.surprise = 0.2  # Default mild surprise for any change
                pf.consecutive_no_change = 0
            else:
                pf.consecutive_no_change = last_action.get('consecutive_no_change', 0) + 1
                pf.surprise = 0.0  # No change = no surprise (or maybe high surprise if expected change)

            pf.temporal_confidence = 0.8

        except Exception as e:
            logger.debug(f"[PERCEIVER] Temporal channel failed: {e}")

    def _run_causal_channel(
        self,
        causal_map: Optional[Any],
        pf: PerceptualField,
    ) -> None:
        """Channel 5: Causal context — what we already know from the MAP."""
        if causal_map is None:
            return

        try:
            # Read from CausalMap
            if hasattr(causal_map, 'get_known_effects'):
                known = causal_map.get_known_effects()
                pf.known_effects = known
                pf.explored_positions = set(known.keys())

            if hasattr(causal_map, 'get_unexplored'):
                pf.unexplored_positions = causal_map.get_unexplored()

            if hasattr(causal_map, 'completeness'):
                pf.map_completeness = causal_map.completeness

            if hasattr(causal_map, 'has_plan'):
                pf.has_plan = causal_map.has_plan

            pf.causal_confidence = min(0.9, pf.map_completeness + 0.1)

        except Exception as e:
            logger.debug(f"[PERCEIVER] Causal channel failed: {e}")

    # ─── Integration ──────────────────────────────────────────────────

    def _integrate_channels(
        self,
        pf: PerceptualField,
        available_actions: Optional[List[int]] = None,
    ) -> None:
        """
        Cross-channel validation and confidence integration.

        This is the 'gradient descent' step — channels validate each other.
        Agreement amplifies confidence, contradiction dampens it.
        """
        confidences = [
            ('spatial', pf.spatial_confidence),
            ('inventory', pf.inventory_confidence),
            ('goal', pf.goal_confidence),
            ('temporal', pf.temporal_confidence),
            ('causal', pf.causal_confidence),
        ]

        # Weighted average (channels with more info get more weight)
        weights = {
            'spatial': 0.25,
            'inventory': 0.15,
            'goal': 0.25,
            'temporal': 0.15,
            'causal': 0.20,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        for name, conf in confidences:
            w = weights.get(name, 0.2)
            weighted_sum += conf * w
            total_weight += w

        pf.overall_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Cross-validation boosts
        # If spatial says "3x3 grid" and we see 9 objects, boost both
        if pf.tile_count > 0 and len(pf.objects) > 0:
            if abs(pf.tile_count - len(pf.objects)) <= 1:
                pf.spatial_confidence = min(1.0, pf.spatial_confidence + 0.1)
                pf.inventory_confidence = min(1.0, pf.inventory_confidence + 0.1)

        # If we have a goal and a causal map, boost goal confidence
        if pf.has_goal and pf.map_completeness > 0.5:
            pf.goal_confidence = min(1.0, pf.goal_confidence + 0.15)

        # ── Infer interactive_bounds from detected objects ──
        # For click games, the interactive region is where the small, discrete
        # objects are (tiles / buttons), not the large background blocks.
        # Filter to objects smaller than 1/8 of the frame area — these are
        # likely interactive tiles, not background panels.
        if pf.interactive_bounds is None and pf.objects:
            frame_area = 64 * 64
            small_objs = [
                o for o in pf.objects
                if o.get('size', frame_area) < frame_area // 8
            ]
            if small_objs:
                all_bounds = [o['bounds'] for o in small_objs if 'bounds' in o]
                if all_bounds:
                    y_min = min(b[0] for b in all_bounds)
                    x_min = min(b[1] for b in all_bounds)
                    y_max = max(b[2] for b in all_bounds)
                    x_max = max(b[3] for b in all_bounds)
                    pf.interactive_bounds = (y_min, x_min, y_max, x_max)

            # Also infer tile_count from small, similarly-sized objects
            if pf.tile_count == 0 and small_objs:
                sizes = [o.get('size', 0) for o in small_objs]
                if sizes:
                    median_size = sorted(sizes)[len(sizes) // 2]
                    # Objects within 2x of median size are likely tiles
                    tile_like = [
                        o for o, s in zip(small_objs, sizes)
                        if 0.3 * median_size <= s <= 3.0 * median_size
                    ]
                    if len(tile_like) >= 2:
                        pf.tile_count = len(tile_like)
                        # Estimate grid dimensions
                        import math
                        pf.grid_rows = max(1, round(math.sqrt(pf.tile_count)))
                        pf.grid_cols = max(1, (pf.tile_count + pf.grid_rows - 1) // pf.grid_rows)

        # Classify puzzle type from available actions
        actions_list = list(available_actions) if available_actions is not None else []
        if actions_list:
            if actions_list == [6]:
                pf.puzzle_type = 'click_only'
            elif 6 not in actions_list:
                pf.puzzle_type = 'movement'
            elif set(actions_list) == {1, 2, 3, 4, 5, 6, 7}:
                pf.puzzle_type = 'hybrid'
            else:
                pf.puzzle_type = 'mixed'

        # Determine game phase
        if pf.map_completeness > 0.8 and pf.has_plan:
            pf.game_phase = 'executing'
        elif pf.map_completeness > 0.4:
            pf.game_phase = 'exploiting'
        elif pf.actions_taken < 10:
            pf.game_phase = 'exploring'
        else:
            pf.game_phase = 'learning'

        # Build narrative
        pf.narrative = self._build_narrative(pf)

    def _build_narrative(self, pf: PerceptualField) -> str:
        """Build human-readable scene description from integrated perception."""
        parts = []

        # What do I see?
        if pf.panel_count > 0:
            parts.append(f"{pf.panel_count} panels ({pf.panel_layout})")
        if pf.tile_count > 0:
            parts.append(f"{pf.grid_rows}x{pf.grid_cols} grid with {pf.tile_count} tiles")
        if pf.unique_colors > 0:
            parts.append(f"{pf.unique_colors} colors")

        # What's the goal?
        if pf.has_goal:
            if pf.cells_total > 0:
                parts.append(
                    f"goal: {pf.cells_matching_goal}/{pf.cells_total} cells match "
                    f"({pf.goal_progress:.0%})"
                )
            else:
                parts.append("goal detected")

        # What just happened?
        if pf.last_action_effect:
            eff = pf.last_action_effect
            if eff.frame_changed:
                parts.append(f"last action changed {eff.cells_changed} cells")
            else:
                parts.append(f"last action: no change (x{pf.consecutive_no_change})")

        # How much do I know?
        parts.append(f"map: {pf.map_completeness:.0%}")
        parts.append(f"phase: {pf.game_phase}")

        return " | ".join(parts)

    # ─── Utilities ────────────────────────────────────────────────────

    @staticmethod
    def _to_numpy(frame: Any) -> Optional[np.ndarray]:
        """Convert frame to numpy array.

        The SDK often returns frame as [ndarray(64,64)] — a Python list
        wrapping a single numpy array. Unwrap before converting.
        """
        if frame is None:
            return None
        if isinstance(frame, np.ndarray):
            return frame
        # Unwrap [ndarray] -> ndarray
        if isinstance(frame, list) and len(frame) == 1 and isinstance(frame[0], np.ndarray):
            return frame[0]
        try:
            return np.array(frame, dtype=np.uint8)
        except Exception:
            return None

    @staticmethod
    def _to_list(frame: Any, frame_array: Optional[np.ndarray]) -> Optional[list]:
        """Convert frame to list-of-lists (pure Python ints).

        The VisualCortex expects list[list[int]], NOT list[ndarray].
        Always produce a deep-converted list to avoid numpy truthiness
        errors downstream.
        """
        if frame_array is not None:
            try:
                return frame_array.tolist()
            except Exception:
                pass
        if isinstance(frame, list):
            # If it's already a list of lists of ints, return as-is
            if frame and isinstance(frame[0], list):
                return frame
            # If it's [ndarray], convert
            if frame and isinstance(frame[0], np.ndarray):
                return frame[0].tolist()
        return None

    @staticmethod
    def _compute_frame_changes(
        prev: np.ndarray, curr: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Compute pixel-level changes between two frames."""
        changes = []
        try:
            if prev.shape != curr.shape:
                return []
            diff_mask = prev != curr
            if not diff_mask.any():
                return []
            ys, xs = np.where(diff_mask)
            # Limit to prevent explosion on large diffs
            max_changes = 500
            for i in range(min(len(ys), max_changes)):
                y, x = int(ys[i]), int(xs[i])
                changes.append({
                    'x': x, 'y': y,
                    'old_color': int(prev[y, x]),
                    'new_color': int(curr[y, x]),
                })
        except Exception:
            pass
        return changes

    @staticmethod
    def _label_connected_components(mask: np.ndarray) -> np.ndarray:
        """Label connected components in a binary mask (4-connected).

        Returns an array of the same shape where each connected region
        has a unique positive integer label (background is 0).
        Uses iterative BFS — fast enough for 64x64 frames.
        """
        labels = np.zeros(mask.shape, dtype=np.int32)
        h, w = mask.shape
        current_label = 0
        for sy in range(h):
            for sx in range(w):
                if mask[sy, sx] and labels[sy, sx] == 0:
                    current_label += 1
                    queue = [(sy, sx)]
                    labels[sy, sx] = current_label
                    qi = 0
                    while qi < len(queue):
                        cy, cx = queue[qi]
                        qi += 1
                        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                                labels[ny, nx] = current_label
                                queue.append((ny, nx))
        return labels

    @staticmethod
    def _detect_color_clusters(frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect individual color clusters (connected components) as objects.

        Unlike the old version that grouped ALL pixels of the same color
        into one object, this finds spatially distinct regions.  Each
        region gets its own centroid — critical for click games where
        each tile is a small, separate interactive target.

        Object dicts use 'centroid_x' and 'centroid_y' keys to match the
        format expected by _find_explore_target and _perceive.
        """
        objects: List[Dict[str, Any]] = []
        try:
            # Determine frame dimensionality
            if frame.ndim == 3:
                flat = frame[:, :, 0]  # Use first channel
            else:
                flat = frame

            unique_colors = np.unique(flat)
            # Background is most common color
            color_counts = Counter(flat.flatten())
            bg_color = color_counts.most_common(1)[0][0]

            obj_id = 0
            for color in unique_colors:
                if color == bg_color:
                    continue
                mask = (flat == color)
                labels = Perceiver._label_connected_components(mask)
                n_components = int(labels.max())
                for label_id in range(1, n_components + 1):
                    component = (labels == label_id)
                    ys, xs = np.where(component)
                    if len(ys) < 2:
                        continue  # Skip isolated single pixels
                    cx = float(np.mean(xs))
                    cy = float(np.mean(ys))
                    objects.append({
                        'id': obj_id,
                        'color': int(color),
                        'centroid_x': cx,
                        'centroid_y': cy,
                        'x': cx,
                        'y': cy,
                        'bounds': (int(ys.min()), int(xs.min()),
                                   int(ys.max()), int(xs.max())),
                        'size': int(len(ys)),
                        'is_rectangular': True,
                    })
                    obj_id += 1
        except Exception:
            pass
        return objects
