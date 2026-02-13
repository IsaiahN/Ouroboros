import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Perceptual Field - The integrated output of multimodal perception.

This is what the agent 'sees' after all perception channels have been
fused. It's not raw pixels — it's structured understanding:
panels, objects, goals, changes, and causal predictions.

Every field has a confidence. Channels validate each other:
spatial structure agreeing with object detection raises both confidences.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class CellDiff:
    """A single cell that differs between current state and goal."""
    x: int
    y: int
    current_color: int
    goal_color: int


@dataclass
class ActionEffect:
    """What happened when the agent last acted."""
    action_type: int                    # 1-7
    x: Optional[int] = None            # Click position (ACTION6)
    y: Optional[int] = None
    pixels_changed: int = 0            # How many pixels changed
    cells_changed: int = 0             # How many logical cells changed
    changes: List[Tuple[int, int, int, int]] = field(default_factory=list)
    # Each change: (x, y, old_color, new_color)
    frame_changed: bool = False
    level_changed: bool = False
    score_delta: float = 0.0


@dataclass
class TilePosition:
    """A position in the logical tile grid."""
    x: int
    y: int
    pixel_x: int                        # Center pixel coordinate
    pixel_y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if not isinstance(other, TilePosition):
            return False
        return self.x == other.x and self.y == other.y


@dataclass
class KnownEffect:
    """What we know about clicking a specific position."""
    position: TilePosition
    affected_positions: List[TilePosition]  # Positions that change
    color_cycle: List[int]                  # Color sequence for the clicked cell
    observation_count: int                  # How many times we've observed this
    confidence: float                       # 0-1: how sure are we


@dataclass
class PerceptualField:
    """
    The integrated output of all perception channels.

    This is what the THINK phase receives. It's not raw data —
    it's structured understanding with confidence scores.

    Think of this as the agent's 'visual working memory':
    everything it currently perceives, organized for reasoning.
    """

    # === Channel 1: Spatial Structure (from VisualCortex) ===
    panel_count: int = 0
    panel_layout: str = "unknown"         # "single", "quadrant", "horizontal", etc.
    panel_roles: List[str] = field(default_factory=list)  # ["input", "goal", "state", "interactive"]
    grid_rows: int = 0
    grid_cols: int = 0
    tile_count: int = 0
    interactive_bounds: Optional[Tuple[int, int, int, int]] = None  # (y_min, x_min, y_max, x_max)
    spatial_confidence: float = 0.0

    # === Channel 2: Object Inventory (from ObjectDetector / VisualCortex) ===
    objects: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {id, color, centroid, bounds, size, is_rectangular}
    colors_present: Set[int] = field(default_factory=set)
    unique_colors: int = 0
    object_changes: List[Dict[str, Any]] = field(default_factory=list)
    # Each: {position, old_color, new_color}
    inventory_confidence: float = 0.0

    # === Channel 3: Goal State (from reference panel detection) ===
    has_goal: bool = False
    goal_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # {(x, y): target_color}
    current_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)
    # {(x, y): current_color}
    delta: List[CellDiff] = field(default_factory=list)
    cells_matching_goal: int = 0
    cells_total: int = 0
    goal_progress: float = 0.0           # 0-1: fraction matching goal
    goal_confidence: float = 0.0

    # === Channel 4: Temporal (from action history) ===
    last_action_effect: Optional[ActionEffect] = None
    actions_taken: int = 0
    actions_remaining: int = 0
    surprise: float = 0.0                # How unexpected was last result
    # 0.0 = exactly as predicted, 1.0 = completely unexpected
    consecutive_no_change: int = 0       # Actions in a row with no frame change
    temporal_confidence: float = 0.0

    # === Channel 5: Causal Context (MAP feeds back into PERCEIVE) ===
    known_effects: Dict[Tuple[int, int], KnownEffect] = field(default_factory=dict)
    explored_positions: Set[Tuple[int, int]] = field(default_factory=set)
    unexplored_positions: List[Tuple[int, int]] = field(default_factory=list)
    map_completeness: float = 0.0        # 0-1: how much of the game we understand
    has_plan: bool = False               # True if causal map can generate a goal plan
    causal_confidence: float = 0.0

    # === Integrated Meta ===
    overall_confidence: float = 0.0      # Weighted average of all channel confidences
    puzzle_type: str = "unknown"         # "click_toggle", "movement", "transformation", etc.
    game_phase: str = "exploring"        # "exploring", "learning", "exploiting"
    narrative: str = ""                  # Human-readable scene description

    # === Raw data references (for rungs that need them) ===
    frame: Optional[Any] = None          # Raw frame data
    visual_scene_dict: Optional[Dict] = None  # VisualCortex output dict (backward compat)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for backward compatibility with existing context system."""
        return {
            'panel_count': self.panel_count,
            'panel_layout': self.panel_layout,
            'grid_rows': self.grid_rows,
            'grid_cols': self.grid_cols,
            'tile_count': self.tile_count,
            'interactive_bounds': self.interactive_bounds,
            'object_count': len(self.objects),
            'colors_present': sorted(self.colors_present),
            'unique_colors': self.unique_colors,
            'has_goal': self.has_goal,
            'goal_progress': round(self.goal_progress, 3),
            'cells_matching_goal': self.cells_matching_goal,
            'cells_total': self.cells_total,
            'delta_count': len(self.delta),
            'actions_taken': self.actions_taken,
            'actions_remaining': self.actions_remaining,
            'surprise': round(self.surprise, 3),
            'map_completeness': round(self.map_completeness, 3),
            'has_plan': self.has_plan,
            'overall_confidence': round(self.overall_confidence, 3),
            'puzzle_type': self.puzzle_type,
            'game_phase': self.game_phase,
            'narrative': self.narrative,
        }

    def summary(self) -> str:
        """One-line summary for logging."""
        goal_str = f"goal:{self.cells_matching_goal}/{self.cells_total}" if self.has_goal else "no-goal"
        map_str = f"map:{self.map_completeness:.0%}"
        phase_str = self.game_phase
        conf_str = f"conf:{self.overall_confidence:.2f}"
        return f"[{self.puzzle_type}] {goal_str} | {map_str} | {phase_str} | {conf_str}"
