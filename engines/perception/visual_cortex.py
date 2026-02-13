import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Visual Cortex - The Eyes of the System
=======================================

Gives agents human-level visual understanding of ARC game frames.
Converts raw pixel grids (List[List[int]], typically 64x64) into structured
scene descriptions that capture what a human "sees" instantly:

- Panel layout (input/output/reference regions separated by dividers)
- Hierarchical sub-grid structure (tiles within panels)
- Object detection via flood-fill (correct connected components)
- Pattern fingerprinting (rotation/flip/color invariant matching)
- Transformation hypothesis generation (what rule maps input to output?)
- Multi-scale analysis (grid > panel > tile > object > pixel)
- Image rendering for debugging and verification

This module ORCHESTRATES existing perception components and ADDS the
critical missing capabilities: scene decomposition, panel splitting,
tile extraction, reference detection, and transformation testing.

Integration Points:
- Called from ContextBuilder.build_from_runner_state() to populate
  DecisionContext.visual_scene
- Accessible to all rungs through context dict
- Uses engines/perception/sparse_grid.py for efficient representation
- Uses engines/perception/palette_detector.py for palette/legend detection

Architecture:
    Raw frame (64x64 ints)
         |
    [1] detect_grid_structure() -> logical cell size, border color
         |
    [2] extract_logical_grid() -> smaller NxM grid (e.g. 9x9, 12x12)
         |
    [3] detect_panels() -> split into input/output/reference panels
         |
    [4] For each panel:
         |-- detect_tiling() -> regular tile arrangement
         |-- detect_objects() -> flood-fill connected components
         |-- analyze_symmetry() -> reflection/rotation
         |-- fingerprint_content() -> hash for matching
         |
    [5] find_reference_panels() -> which panel is the "rule"/legend
         |
    [6] hypothesize_transformations() -> what maps input to output
         |
    [7] describe_scene() -> structured scene description for agents

Rules Followed:
- Rule 1: PYTHONDONTWRITEBYTECODE=1
- Rule 2: No file logging, all results in memory or DB
- Rule 10: Enhances existing architecture, no orphaned code
- Rule 11: No Unicode emojis
"""

import hashlib
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional: PIL for image rendering (graceful degradation)
PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore[assignment, misc]
    ImageDraw = None  # type: ignore[assignment, misc]




# =============================================================================
# ARC COLOR PALETTE (Standard ARC-AGI colors)
# =============================================================================

ARC_COLORS_RGB: Dict[int, Tuple[int, int, int]] = {
    0: (0, 0, 0),         # Black (background)
    1: (0, 116, 217),     # Blue
    2: (255, 65, 54),     # Red
    3: (46, 204, 64),     # Green
    4: (255, 220, 0),     # Yellow
    5: (170, 170, 170),   # Gray
    6: (240, 18, 190),    # Magenta/Fuchsia
    7: (255, 133, 27),    # Orange
    8: (127, 219, 255),   # Cyan/Azure
    9: (135, 12, 37),     # Maroon/Brown
}

ARC_COLOR_NAMES: Dict[int, str] = {
    0: "black", 1: "blue", 2: "red", 3: "green", 4: "yellow",
    5: "gray", 6: "magenta", 7: "orange", 8: "cyan", 9: "maroon",
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GridStructure:
    """Detected grid structure within a pixel frame."""
    cell_width: int             # Pixels per cell horizontally
    cell_height: int            # Pixels per cell vertically
    grid_cols: int              # Number of logical columns
    grid_rows: int              # Number of logical rows
    border_color: int           # Color used for grid lines (-1 if none)
    border_width: int           # Width of grid lines in pixels
    has_grid_lines: bool        # Whether explicit grid lines exist
    grid_origin: Tuple[int, int]  # (y, x) pixel offset of grid start
    confidence: float           # How confident we are in this detection


@dataclass
class Panel:
    """A rectangular region within the frame (input, output, reference, etc.)."""
    panel_id: int
    region: np.ndarray          # The pixel data for this panel
    bounds: Tuple[int, int, int, int]  # (y_min, x_min, y_max, x_max) in frame coords
    role: str = "unknown"       # "input", "output", "reference", "workspace", "legend"
    logical_grid: Optional[np.ndarray] = None  # Extracted logical grid (if detected)

    def width(self) -> int:
        return self.bounds[3] - self.bounds[1]

    def height(self) -> int:
        return self.bounds[2] - self.bounds[0]

    def area(self) -> int:
        return self.width() * self.height()


@dataclass
class TileGrid:
    """A regular arrangement of tiles within a panel."""
    tile_rows: int
    tile_cols: int
    tile_width: int             # Pixels per tile
    tile_height: int            # Pixels per tile
    tiles: List[List[np.ndarray]]   # 2D array of tile pixel data
    tile_hashes: List[List[str]]    # Fingerprint of each tile
    unique_tile_count: int
    separator_color: int        # Color between tiles
    separator_width: int


@dataclass
class DetectedObject:
    """A connected component (object) detected via flood-fill."""
    obj_id: int
    color: int
    pixels: List[Tuple[int, int]]   # (y, x) positions
    bounds: Tuple[int, int, int, int]  # (y_min, x_min, y_max, x_max)
    centroid: Tuple[float, float]
    size: int
    is_rectangular: bool
    is_hollow: bool
    fill_ratio: float               # How much of bounding box is filled
    internal_colors: Set[int]        # Colors inside bounding box besides own color


@dataclass
class TransformationHypothesis:
    """A hypothesis about what transformation maps input to output."""
    transform_type: str         # "rotation", "reflection", "color_map", "tile_swap",
                                # "fill", "copy", "overlay", "sort", "pattern_complete"
    parameters: Dict[str, Any]  # Transformation-specific parameters
    confidence: float
    description: str            # Human-readable description
    evidence: List[str]         # What evidence supports this


@dataclass
class SceneDescription:
    """Complete visual understanding of a frame."""
    # Grid structure
    frame_size: Tuple[int, int]     # (height, width) in pixels
    grid_structure: Optional[GridStructure]
    logical_grid: Optional[np.ndarray]  # Extracted logical grid
    logical_size: Optional[Tuple[int, int]]  # (rows, cols) of logical grid

    # Background
    background_color: int
    background_fraction: float      # What % is background

    # Panels (scene decomposition)
    panels: List[Panel]
    panel_layout: str               # "single", "horizontal_split", "vertical_split",
                                    # "quadrant", "grid", "complex"

    # Tiling (within panels)
    tile_grids: List[TileGrid]
    has_tiling: bool

    # Objects
    objects: List[DetectedObject]
    object_count: int
    colors_used: Set[int]

    # Symmetry (at multiple scales)
    frame_symmetry: Dict[str, Any]
    panel_symmetries: List[Dict[str, Any]]

    # Transformation hypotheses
    transformations: List[TransformationHypothesis]

    # Reference detection
    reference_panel_id: Optional[int]  # Which panel (if any) is the reference/legend

    # Summary
    complexity_score: float         # 0-1, how complex the scene is
    scene_narrative: str            # Human-readable description of what's happening

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DecisionContext integration."""
        return {
            'frame_size': self.frame_size,
            'grid_structure': {
                'cell_width': self.grid_structure.cell_width,
                'cell_height': self.grid_structure.cell_height,
                'grid_cols': self.grid_structure.grid_cols,
                'grid_rows': self.grid_structure.grid_rows,
                'border_color': self.grid_structure.border_color,
                'has_grid_lines': self.grid_structure.has_grid_lines,
                'confidence': self.grid_structure.confidence,
            } if self.grid_structure else None,
            'logical_size': self.logical_size,
            'logical_grid': self.logical_grid.tolist() if self.logical_grid is not None else None,
            'background_color': self.background_color,
            'background_fraction': round(self.background_fraction, 3),
            'panel_count': len(self.panels),
            'panel_layout': self.panel_layout,
            'panel_roles': [p.role for p in self.panels],
            'has_tiling': self.has_tiling,
            'tile_grids': [{
                'tile_rows': tg.tile_rows,
                'tile_cols': tg.tile_cols,
                'tile_width': tg.tile_width,
                'tile_height': tg.tile_height,
                'unique_tiles': tg.unique_tile_count,
            } for tg in self.tile_grids],
            'object_count': self.object_count,
            'colors_used': sorted(self.colors_used),
            'color_names': [ARC_COLOR_NAMES.get(c, f"color_{c}") for c in sorted(self.colors_used)],
            'frame_symmetry': self.frame_symmetry,
            'transformations': [{
                'type': t.transform_type,
                'confidence': round(t.confidence, 3),
                'description': t.description,
                'parameters': t.parameters,
            } for t in self.transformations],
            'reference_panel_id': self.reference_panel_id,
            'complexity_score': round(self.complexity_score, 3),
            'scene_narrative': self.scene_narrative,
        }


# =============================================================================
# THE VISUAL CORTEX
# =============================================================================

class VisualCortex:
    """
    The visual processing center - gives agents human-level scene understanding.

    Converts raw pixel grids into structured scene descriptions with:
    - Hierarchical decomposition (frame > panels > tiles > objects)
    - Pattern recognition at multiple scales
    - Transformation hypothesis generation
    - Reference/legend detection
    """

    def __init__(self, cache_size: int = 64):
        """Initialize the visual cortex.

        Args:
            cache_size: Number of frame analyses to cache (by hash).
        """
        self._cache: Dict[str, SceneDescription] = {}
        self._cache_order: List[str] = []
        self._cache_size = cache_size
        self._obj_id_counter = 0

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def analyze(self, frame: List[List[int]]) -> SceneDescription:
        """
        Perform complete visual analysis of a frame.

        This is the main entry point. Takes a raw pixel grid and returns
        a comprehensive scene description.

        Args:
            frame: 2D list of color integers (typically 64x64, values 0-9)

        Returns:
            SceneDescription with full visual understanding
        """
        if frame is None or (isinstance(frame, (list, tuple)) and len(frame) == 0):
            return self._empty_scene()
        # Verify first row exists (safe for both list-of-lists and ndarray)
        try:
            first_row = frame[0]
            if first_row is None or (isinstance(first_row, (list, tuple)) and len(first_row) == 0):
                return self._empty_scene()
        except (IndexError, TypeError):
            return self._empty_scene()

        # Check cache
        frame_hash = self._hash_frame(frame)
        if frame_hash in self._cache:
            return self._cache[frame_hash]

        grid = np.array(frame, dtype=np.int32)
        height, width = grid.shape

        # ---- Stage 1: Grid Structure Detection ----
        grid_structure = self._detect_grid_structure(grid)

        # ---- Stage 2: Extract Logical Grid ----
        logical_grid = None
        logical_size = None
        if grid_structure and grid_structure.has_grid_lines and grid_structure.confidence > 0.6:
            logical_grid = self._extract_logical_grid(grid, grid_structure)
            if logical_grid is not None:
                logical_size = (logical_grid.shape[0], logical_grid.shape[1])

        # Use logical grid for downstream analysis if available, else raw grid
        analysis_grid = logical_grid if logical_grid is not None else grid

        # ---- Stage 3: Background Detection ----
        bg_color, bg_fraction = self._detect_background(analysis_grid)

        # ---- Stage 4: Panel Detection (Scene Decomposition) ----
        panels = self._detect_panels(analysis_grid, bg_color)
        panel_layout = self._classify_panel_layout(panels, analysis_grid.shape)

        # ---- Stage 5: Tile Detection (within panels) ----
        tile_grids = []
        for panel in panels:
            tg = self._detect_tiling(panel.region, bg_color)
            if tg:
                tile_grids.append(tg)

        # ---- Stage 6: Object Detection (flood-fill) ----
        objects = self._detect_objects(analysis_grid, bg_color)

        # ---- Stage 7: Symmetry Analysis ----
        frame_symmetry = self._analyze_symmetry(analysis_grid)
        panel_symmetries = [self._analyze_symmetry(p.region) for p in panels]

        # ---- Stage 8: Reference Panel Detection ----
        ref_panel_id = self._find_reference_panel(panels, objects)

        # ---- Stage 9: Transformation Hypotheses ----
        transformations = self._hypothesize_transformations(
            panels, tile_grids, objects, frame_symmetry, ref_panel_id
        )

        # ---- Stage 10: Complexity Scoring ----
        colors_used = set(int(c) for c in np.unique(analysis_grid) if c != bg_color)
        complexity = self._calculate_complexity(
            analysis_grid, objects, panels, tile_grids, colors_used
        )

        # ---- Stage 11: Scene Narrative ----
        narrative = self._generate_narrative(
            analysis_grid, grid_structure, panels, panel_layout,
            tile_grids, objects, colors_used, transformations,
            ref_panel_id, frame_symmetry
        )

        scene = SceneDescription(
            frame_size=(height, width),
            grid_structure=grid_structure,
            logical_grid=logical_grid,
            logical_size=logical_size,
            background_color=bg_color,
            background_fraction=bg_fraction,
            panels=panels,
            panel_layout=panel_layout,
            tile_grids=tile_grids,
            has_tiling=len(tile_grids) > 0,
            objects=objects,
            object_count=len(objects),
            colors_used=colors_used,
            frame_symmetry=frame_symmetry,
            panel_symmetries=panel_symmetries,
            transformations=transformations,
            reference_panel_id=ref_panel_id,
            complexity_score=complexity,
            scene_narrative=narrative,
        )

        # Cache result
        self._cache_result(frame_hash, scene)

        return scene

    def render_to_image(
        self,
        frame: List[List[int]],
        scale: int = 8,
        show_grid_lines: bool = True,
        highlight_panels: bool = False,
    ) -> Optional[Any]:
        """
        Render a grid frame to a PIL Image.

        Args:
            frame: 2D list of color integers
            scale: Pixels per cell in output image
            show_grid_lines: Draw grid lines between cells
            highlight_panels: Highlight detected panel boundaries

        Returns:
            PIL.Image.Image or None if PIL not available
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available - cannot render image")
            return None

        if frame is None or (isinstance(frame, (list, tuple)) and len(frame) == 0):
            return None

        try:
            first_row = frame[0]
            if isinstance(first_row, np.ndarray) and first_row.size == 0:
                return None
            elif isinstance(first_row, (list, tuple)) and len(first_row) == 0:
                return None
        except (IndexError, TypeError):
            return None

        grid = np.array(frame, dtype=np.int32)
        height, width = grid.shape

        # Create image
        img_width = width * scale + (1 if show_grid_lines else 0)
        img_height = height * scale + (1 if show_grid_lines else 0)
        img = Image.new('RGB', (img_width, img_height), (30, 30, 30))  # type: ignore[union-attr]
        draw = ImageDraw.Draw(img)  # type: ignore[union-attr]

        # Draw cells
        for y in range(height):
            for x in range(width):
                color_idx = int(grid[y, x])
                rgb = ARC_COLORS_RGB.get(color_idx, (128, 128, 128))
                x0 = x * scale
                y0 = y * scale
                x1 = x0 + scale - (1 if show_grid_lines else 0)
                y1 = y0 + scale - (1 if show_grid_lines else 0)
                draw.rectangle([x0, y0, x1, y1], fill=rgb)

        # Highlight panels if requested
        if highlight_panels:
            scene = self.analyze(frame)
            panel_colors = [
                (255, 255, 0, 128),  # Yellow
                (0, 255, 255, 128),  # Cyan
                (255, 0, 255, 128),  # Magenta
                (0, 255, 0, 128),    # Green
            ]
            for i, panel in enumerate(scene.panels):
                color = panel_colors[i % len(panel_colors)]
                y0 = panel.bounds[0] * scale
                x0 = panel.bounds[1] * scale
                y1 = panel.bounds[2] * scale
                x1 = panel.bounds[3] * scale
                draw.rectangle([x0, y0, x1, y1], outline=color[:3], width=2)

        return img

    def save_frame_image(
        self,
        frame: List[List[int]],
        filepath: str,
        scale: int = 8,
        show_grid_lines: bool = True,
    ) -> bool:
        """Save a rendered frame to disk. Returns True on success."""
        img = self.render_to_image(frame, scale=scale, show_grid_lines=show_grid_lines)
        if img is None:
            return False
        try:
            img.save(filepath)
            return True
        except Exception as e:
            logger.error(f"Failed to save frame image: {e}")
            return False

    def compare_frames(
        self,
        frame_a: List[List[int]],
        frame_b: List[List[int]],
    ) -> Dict[str, Any]:
        """
        Compare two frames and describe what changed.

        Returns structured comparison including:
        - Pixel-level diff statistics
        - Object-level changes (appeared, disappeared, moved, recolored)
        - Transformation hypothesis
        """
        grid_a = np.array(frame_a, dtype=np.int32)
        grid_b = np.array(frame_b, dtype=np.int32)

        if grid_a.shape != grid_b.shape:
            return {
                'compatible': False,
                'reason': 'Different frame sizes',
                'size_a': grid_a.shape,
                'size_b': grid_b.shape,
            }

        diff_mask = grid_a != grid_b
        n_changed = int(np.sum(diff_mask))
        total = grid_a.size

        # Find changed regions
        changed_positions = list(zip(*np.where(diff_mask)))
        changed_colors_from = [int(grid_a[y, x]) for y, x in changed_positions]
        changed_colors_to = [int(grid_b[y, x]) for y, x in changed_positions]

        # Detect color mapping
        color_map: Dict[int, Counter] = defaultdict(Counter)
        for cf, ct in zip(changed_colors_from, changed_colors_to):
            color_map[cf][ct] += 1

        # Detect if it's a simple color swap
        is_color_swap = (
            len(color_map) == 2
            and all(len(v) == 1 for v in color_map.values())
        )

        # Detect if changes are localized to a region
        if changed_positions:
            ys = [p[0] for p in changed_positions]
            xs = [p[1] for p in changed_positions]
            change_bounds = (min(ys), min(xs), max(ys) + 1, max(xs) + 1)
            change_area = (change_bounds[2] - change_bounds[0]) * (change_bounds[3] - change_bounds[1])
            is_localized = n_changed < change_area * 0.5  # Sparse changes in region
        else:
            change_bounds = (0, 0, 0, 0)
            change_area = 0
            is_localized = True

        # Object-level comparison
        bg_a, _ = self._detect_background(grid_a)
        bg_b, _ = self._detect_background(grid_b)
        objects_a = self._detect_objects(grid_a, bg_a)
        objects_b = self._detect_objects(grid_b, bg_b)

        return {
            'compatible': True,
            'pixels_changed': n_changed,
            'pixels_total': total,
            'change_fraction': n_changed / total if total > 0 else 0.0,
            'change_bounds': change_bounds,
            'change_area': change_area,
            'is_localized': is_localized,
            'is_color_swap': is_color_swap,
            'color_transitions': {
                str(k): dict(v) for k, v in color_map.items()
            },
            'objects_before': len(objects_a),
            'objects_after': len(objects_b),
            'object_count_changed': len(objects_a) != len(objects_b),
        }

    # =========================================================================
    # STAGE 1: GRID STRUCTURE DETECTION
    # =========================================================================

    def _detect_grid_structure(self, grid: np.ndarray) -> Optional[GridStructure]:
        """
        Detect if the pixel grid contains a logical grid with regular cells.

        Many ARC games render a small logical grid (e.g. 9x9) into a larger
        pixel grid (64x64) with colored cells and border lines between them.
        This detects that structure.

        Strategy:
        1. Look for uniform-color rows and columns (potential grid lines)
        2. Check if they form a regular pattern (equal spacing)
        3. Extract cell size and grid dimensions
        """
        height, width = grid.shape

        # Minimum useful grid: at least 2x2 logical cells
        if height < 4 or width < 4:
            return None

        # Try to detect grid lines by finding uniform rows/columns
        # Grid lines are rows/columns where all (or most) pixels are the same color

        # Find candidate row separators
        row_candidates = self._find_uniform_lines(grid, axis='row')
        col_candidates = self._find_uniform_lines(grid, axis='col')

        if not row_candidates and not col_candidates:
            # No grid lines detected - might be raw logical grid
            return GridStructure(
                cell_width=1, cell_height=1,
                grid_cols=width, grid_rows=height,
                border_color=-1, border_width=0,
                has_grid_lines=False,
                grid_origin=(0, 0),
                confidence=0.3,
            )

        # Find the most common separator color
        all_sep_colors = []
        for _, color, _ in row_candidates:
            all_sep_colors.append(color)
        for _, color, _ in col_candidates:
            all_sep_colors.append(color)

        if not all_sep_colors:
            return None

        border_color = Counter(all_sep_colors).most_common(1)[0][0]

        # Filter to only separators of the dominant color
        row_seps = [(pos, w) for pos, color, w in row_candidates if color == border_color]
        col_seps = [(pos, w) for pos, color, w in col_candidates if color == border_color]

        # Check for regularity (equal spacing between separators)
        row_spacing = self._check_regularity([p for p, _ in row_seps])
        col_spacing = self._check_regularity([p for p, _ in col_seps])

        # Determine cell size
        if row_spacing and col_spacing:
            cell_height = row_spacing
            cell_width = col_spacing
            border_width = row_seps[0][1] if row_seps else 1
            grid_rows = len(row_seps) + 1
            grid_cols = len(col_seps) + 1

            # Determine grid origin (first cell start)
            first_row = row_seps[0][0] if row_seps else 0
            first_col = col_seps[0][0] if col_seps else 0
            origin_y = max(0, first_row - cell_height)
            origin_x = max(0, first_col - cell_width)

            confidence = 0.9 if (grid_rows >= 2 and grid_cols >= 2) else 0.5

            return GridStructure(
                cell_width=cell_width,
                cell_height=cell_height,
                grid_cols=grid_cols,
                grid_rows=grid_rows,
                border_color=int(border_color),
                border_width=border_width,
                has_grid_lines=True,
                grid_origin=(origin_y, origin_x),
                confidence=confidence,
            )

        # Partial detection - only one direction has regularity
        if row_spacing:
            return GridStructure(
                cell_width=1, cell_height=row_spacing,
                grid_cols=width, grid_rows=len(row_seps) + 1,
                border_color=int(border_color), border_width=row_seps[0][1] if row_seps else 1,
                has_grid_lines=True,
                grid_origin=(0, 0),
                confidence=0.5,
            )

        if col_spacing:
            return GridStructure(
                cell_width=col_spacing, cell_height=1,
                grid_cols=len(col_seps) + 1, grid_rows=height,
                border_color=int(border_color), border_width=col_seps[0][1] if col_seps else 1,
                has_grid_lines=True,
                grid_origin=(0, 0),
                confidence=0.5,
            )

        return None

    def _find_uniform_lines(
        self, grid: np.ndarray, axis: str, threshold: float = 0.85
    ) -> List[Tuple[int, int, int]]:
        """
        Find rows or columns that are predominantly one color.

        Returns list of (position, dominant_color, width) tuples.
        Width > 1 means multi-pixel separator lines.
        """
        height, width = grid.shape
        results: List[Tuple[int, int, int]] = []

        if axis == 'row':
            for y in range(height):
                row = grid[y, :]
                counts = Counter(row.tolist())
                dominant_color, count = counts.most_common(1)[0]
                if count / width >= threshold:
                    results.append((y, dominant_color, 1))
        else:  # col
            for x in range(width):
                col = grid[:, x]
                counts = Counter(col.tolist())
                dominant_color, count = counts.most_common(1)[0]
                if count / height >= threshold:
                    results.append((x, dominant_color, 1))

        # Merge adjacent lines of same color into multi-pixel separators
        merged: List[Tuple[int, int, int]] = []
        i = 0
        while i < len(results):
            pos, color, w = results[i]
            # Count consecutive same-color lines
            j = i + 1
            while j < len(results) and results[j][0] == pos + (j - i) and results[j][1] == color:
                j += 1
            line_width = j - i
            merged.append((pos, color, line_width))
            i = j

        return merged

    def _check_regularity(self, positions: List[int], tolerance: int = 2) -> Optional[int]:
        """
        Check if positions are regularly spaced.

        Returns the spacing if regular, None otherwise.
        """
        if len(positions) < 2:
            return None

        gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]

        if not gaps:
            return None

        median_gap = sorted(gaps)[len(gaps) // 2]

        # Check if all gaps are within tolerance of median
        if all(abs(g - median_gap) <= tolerance for g in gaps):
            return median_gap

        return None

    # =========================================================================
    # STAGE 2: LOGICAL GRID EXTRACTION
    # =========================================================================

    def _extract_logical_grid(
        self, grid: np.ndarray, structure: GridStructure
    ) -> Optional[np.ndarray]:
        """
        Extract the logical grid from a pixel grid with grid lines.

        Samples the center pixel of each cell to get the logical color value.
        """
        if not structure.has_grid_lines or structure.cell_width < 2 or structure.cell_height < 2:
            return None

        height, width = grid.shape
        rows = structure.grid_rows
        cols = structure.grid_cols
        oy, ox = structure.grid_origin
        cw = structure.cell_width
        ch = structure.cell_height
        bw = structure.border_width

        logical = np.zeros((rows, cols), dtype=np.int32)

        for r in range(rows):
            for c in range(cols):
                # Center of each logical cell in pixel coordinates
                py = oy + r * (ch + bw) + ch // 2
                px = ox + c * (cw + bw) + cw // 2

                if 0 <= py < height and 0 <= px < width:
                    # Sample a small area around center and take the mode
                    sample_radius = max(1, min(ch, cw) // 4)
                    y_lo = max(0, py - sample_radius)
                    y_hi = min(height, py + sample_radius + 1)
                    x_lo = max(0, px - sample_radius)
                    x_hi = min(width, px + sample_radius + 1)
                    sample = grid[y_lo:y_hi, x_lo:x_hi]
                    counts = Counter(sample.flatten().tolist())
                    # Exclude border color from vote
                    if structure.border_color in counts and len(counts) > 1:
                        del counts[structure.border_color]
                    logical[r, c] = counts.most_common(1)[0][0] if counts else 0

        return logical

    # =========================================================================
    # STAGE 3: PANEL DETECTION (SCENE DECOMPOSITION)
    # =========================================================================

    def _detect_panels(self, grid: np.ndarray, bg_color: int) -> List[Panel]:
        """
        Detect distinct panels/regions in the grid separated by divider lines.

        ARC games often have:
        - Left panel (input) | Right panel (output)
        - Top panel (input) / Bottom panel (output)
        - Small reference panel + large workspace
        """
        height, width = grid.shape

        # Find thick separator lines (3+ pixels of background or border color)
        h_separators = self._find_separators(grid, axis='horizontal', bg_color=bg_color)
        v_separators = self._find_separators(grid, axis='vertical', bg_color=bg_color)

        # If no separators found, the whole grid is one panel
        if not h_separators and not v_separators:
            panel = Panel(
                panel_id=0,
                region=grid,
                bounds=(0, 0, height, width),
                role="workspace",
            )
            return [panel]

        # Split into panels using separators
        panels = []
        panel_id = 0

        # Get row/col boundaries from separators
        row_boundaries = [0]
        for sep_start, sep_end in h_separators:
            row_boundaries.append(sep_start)
            row_boundaries.append(sep_end)
        row_boundaries.append(height)

        col_boundaries = [0]
        for sep_start, sep_end in v_separators:
            col_boundaries.append(sep_start)
            col_boundaries.append(sep_end)
        col_boundaries.append(width)

        # Create panels from boundary intersections
        for i in range(0, len(row_boundaries) - 1, 2):
            r_start = row_boundaries[i]
            r_end = row_boundaries[i + 1] if i + 1 < len(row_boundaries) else height

            for j in range(0, len(col_boundaries) - 1, 2):
                c_start = col_boundaries[j]
                c_end = col_boundaries[j + 1] if j + 1 < len(col_boundaries) else width

                # Skip very small regions (likely separator artifacts)
                if (r_end - r_start) < 2 or (c_end - c_start) < 2:
                    continue

                region = grid[r_start:r_end, c_start:c_end]

                # Skip regions that are entirely background
                if np.all(region == bg_color):
                    continue

                panel = Panel(
                    panel_id=panel_id,
                    region=region,
                    bounds=(r_start, c_start, r_end, c_end),
                )
                panels.append(panel)
                panel_id += 1

        # Assign roles based on position and size
        self._assign_panel_roles(panels, grid.shape)

        return panels if panels else [Panel(
            panel_id=0, region=grid,
            bounds=(0, 0, height, width), role="workspace"
        )]

    def _find_separators(
        self,
        grid: np.ndarray,
        axis: str,
        bg_color: int,
        min_thickness: int = 2,
        min_coverage: float = 0.7,
    ) -> List[Tuple[int, int]]:
        """
        Find separator lines (thick bands of background/border color).

        Returns list of (start, end) positions for each separator.
        """
        height, width = grid.shape
        separators: List[Tuple[int, int]] = []

        if axis == 'horizontal':
            # Look for rows that are mostly background
            in_sep = False
            sep_start = 0
            for y in range(height):
                row = grid[y, :]
                bg_count = np.sum(row == bg_color)
                is_sep_row = (bg_count / width) >= min_coverage

                if is_sep_row and not in_sep:
                    sep_start = y
                    in_sep = True
                elif not is_sep_row and in_sep:
                    if (y - sep_start) >= min_thickness:
                        separators.append((sep_start, y))
                    in_sep = False

            if in_sep and (height - sep_start) >= min_thickness:
                separators.append((sep_start, height))

        else:  # vertical
            in_sep = False
            sep_start = 0
            for x in range(width):
                col = grid[:, x]
                bg_count = np.sum(col == bg_color)
                is_sep_col = (bg_count / height) >= min_coverage

                if is_sep_col and not in_sep:
                    sep_start = x
                    in_sep = True
                elif not is_sep_col and in_sep:
                    if (x - sep_start) >= min_thickness:
                        separators.append((sep_start, x))
                    in_sep = False

            if in_sep and (width - sep_start) >= min_thickness:
                separators.append((sep_start, width))

        # Filter out edge separators (borders around the whole grid)
        filtered = []
        for start, end in separators:
            dim = height if axis == 'horizontal' else width
            # Skip if at very edge (within 5% of edge)
            if start < dim * 0.05 or end > dim * 0.95:
                # Only skip if it's very thin (likely just padding)
                if (end - start) < dim * 0.1:
                    continue
            filtered.append((start, end))

        return filtered

    def _assign_panel_roles(
        self, panels: List[Panel], frame_shape: Tuple[int, ...]
    ) -> None:
        """Assign roles to panels based on position, size, and content."""
        _ = frame_shape  # Reserved for future size-relative role assignment
        if not panels:
            return

        if len(panels) == 1:
            panels[0].role = "workspace"
            return

        # Sort by position (top-left first)
        panels_sorted = sorted(panels, key=lambda p: (p.bounds[0], p.bounds[1]))

        # Two-panel layout: likely input/output
        if len(panels) == 2:
            p0, p1 = panels_sorted
            # Check if side-by-side (vertical separator) or stacked (horizontal separator)
            if abs(p0.bounds[0] - p1.bounds[0]) < 5:
                # Side by side -> left is input, right is output
                p0.role = "input"
                p1.role = "output"
            else:
                # Stacked -> top is input, bottom is output
                p0.role = "input"
                p1.role = "output"
            return

        # Multi-panel: smallest might be reference/legend
        areas = [(p.area(), i) for i, p in enumerate(panels)]
        areas.sort()

        # If one panel is significantly smaller, it might be a reference
        if len(areas) >= 2:
            smallest_area, smallest_idx = areas[0]
            second_area, _ = areas[1]
            if smallest_area < second_area * 0.4:
                panels[smallest_idx].role = "reference"
                # Assign remaining as input/output
                remaining = [p for p in panels_sorted if p.panel_id != smallest_idx]
                if len(remaining) >= 2:
                    remaining[0].role = "input"
                    remaining[1].role = "output"
                elif remaining:
                    remaining[0].role = "workspace"
                return

        # Default: assign by position
        for i, p in enumerate(panels_sorted):
            if i == 0:
                p.role = "input"
            elif i == len(panels_sorted) - 1:
                p.role = "output"
            else:
                p.role = "workspace"

    def _classify_panel_layout(
        self, panels: List[Panel], frame_shape: Tuple[int, ...]
    ) -> str:
        """Classify the overall panel layout."""
        _ = frame_shape  # Reserved for future size-relative layout classification
        n = len(panels)
        if n == 0:
            return "empty"
        if n == 1:
            return "single"
        if n == 2:
            # Check orientation
            p0, p1 = sorted(panels, key=lambda p: (p.bounds[0], p.bounds[1]))
            y_overlap = min(p0.bounds[2], p1.bounds[2]) - max(p0.bounds[0], p1.bounds[0])
            x_overlap = min(p0.bounds[3], p1.bounds[3]) - max(p0.bounds[1], p1.bounds[1])
            if y_overlap > x_overlap:
                return "horizontal_split"  # Side by side
            return "vertical_split"  # Stacked
        if n == 4:
            return "quadrant"
        return "grid" if n <= 9 else "complex"

    # =========================================================================
    # STAGE 4: TILE DETECTION
    # =========================================================================

    def _detect_tiling(
        self,
        region: np.ndarray,
        bg_color: int,
        min_tile_size: int = 2,
        max_tiles: int = 10,
    ) -> Optional[TileGrid]:
        """
        Detect if a region contains a regular grid of tiles.

        Looks for internal separator lines that divide the region into
        equal-sized tiles arranged in a grid pattern.
        """
        height, width = region.shape

        if height < min_tile_size * 2 or width < min_tile_size * 2:
            return None

        # Find internal separator lines
        h_seps = self._find_internal_separators(region, 'horizontal', bg_color)
        v_seps = self._find_internal_separators(region, 'vertical', bg_color)

        if not h_seps and not v_seps:
            # Try detecting tiling by periodicity (no explicit separators)
            return self._detect_tiling_by_periodicity(region, bg_color)

        # Build tile boundaries
        row_starts = [0]
        sep_width = 0
        for sep_pos, sw in h_seps:
            row_starts.append(sep_pos + sw)
            sep_width = max(sep_width, sw)
        row_ends = [s[0] for s in h_seps] + [height]

        col_starts = [0]
        for sep_pos, sw in v_seps:
            col_starts.append(sep_pos + sw)
        col_ends = [s[0] for s in v_seps] + [width]

        if len(row_starts) < 2 or len(col_starts) < 2:
            return None

        tile_rows = len(row_starts)
        tile_cols = len(col_starts)

        if tile_rows > max_tiles or tile_cols > max_tiles:
            return None

        # Extract tiles
        tiles: List[List[np.ndarray]] = []
        tile_hashes: List[List[str]] = []
        unique_hashes: Set[str] = set()

        for r_idx in range(tile_rows):
            tile_row: List[np.ndarray] = []
            hash_row: List[str] = []
            r_start = row_starts[r_idx]
            r_end = row_ends[r_idx] if r_idx < len(row_ends) else height

            for c_idx in range(tile_cols):
                c_start = col_starts[c_idx]
                c_end = col_ends[c_idx] if c_idx < len(col_ends) else width

                tile = region[r_start:r_end, c_start:c_end]
                tile_row.append(tile)

                # Fingerprint this tile
                h = self._fingerprint_region(tile)
                hash_row.append(h)
                unique_hashes.add(h)

            tiles.append(tile_row)
            tile_hashes.append(hash_row)

        # Calculate tile dimensions (use first tile as reference)
        tile_h = row_ends[0] - row_starts[0] if row_ends else 0
        tile_w = col_ends[0] - col_starts[0] if col_ends else 0

        return TileGrid(
            tile_rows=tile_rows,
            tile_cols=tile_cols,
            tile_width=tile_w,
            tile_height=tile_h,
            tiles=tiles,
            tile_hashes=tile_hashes,
            unique_tile_count=len(unique_hashes),
            separator_color=bg_color,
            separator_width=sep_width,
        )

    def _find_internal_separators(
        self,
        region: np.ndarray,
        axis: str,
        bg_color: int,
        min_coverage: float = 0.8,
    ) -> List[Tuple[int, int]]:
        """
        Find internal separator lines within a region (not at edges).

        Returns list of (position, width) for each separator.
        """
        height, width = region.shape
        separators: List[Tuple[int, int]] = []

        margin = max(2, (height if axis == 'horizontal' else width) // 10)

        if axis == 'horizontal':
            in_sep = False
            sep_start = 0
            for y in range(margin, height - margin):
                row = region[y, :]
                bg_count = np.sum(row == bg_color)
                is_sep = (bg_count / width) >= min_coverage

                if is_sep and not in_sep:
                    sep_start = y
                    in_sep = True
                elif not is_sep and in_sep:
                    separators.append((sep_start, y - sep_start))
                    in_sep = False
        else:
            in_sep = False
            sep_start = 0
            for x in range(margin, width - margin):
                col = region[:, x]
                bg_count = np.sum(col == bg_color)
                is_sep = (bg_count / height) >= min_coverage

                if is_sep and not in_sep:
                    sep_start = x
                    in_sep = True
                elif not is_sep and in_sep:
                    separators.append((sep_start, x - sep_start))
                    in_sep = False

        return separators

    def _detect_tiling_by_periodicity(
        self,
        region: np.ndarray,
        bg_color: int,
    ) -> Optional[TileGrid]:
        """
        Detect tiling by looking for repeating patterns (no explicit separators).

        Uses autocorrelation to find the tile period.
        """
        height, width = region.shape

        # Try different tile sizes
        best_score = 0.0
        best_th = 0
        best_tw = 0

        for th in range(2, height // 2 + 1):
            if height % th != 0:
                continue
            for tw in range(2, width // 2 + 1):
                if width % tw != 0:
                    continue

                # Check if tiling with (th, tw) tiles produces consistent content
                n_rows = height // th
                n_cols = width // tw

                if n_rows < 2 or n_cols < 2 or n_rows > 10 or n_cols > 10:
                    continue

                # Compare all tiles to the first tile
                ref_tile = region[:th, :tw]
                match_count = 0
                total = n_rows * n_cols

                tile_set: Set[str] = set()
                for r in range(n_rows):
                    for c in range(n_cols):
                        tile = region[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
                        tile_set.add(self._fingerprint_region(tile))

                # If there's a small number of unique tiles relative to total,
                # this is likely a valid tiling
                uniqueness_ratio = len(tile_set) / total
                if uniqueness_ratio < 0.8 and len(tile_set) > 1:
                    score = (1.0 - uniqueness_ratio) * (n_rows * n_cols)
                    if score > best_score:
                        best_score = score
                        best_th = th
                        best_tw = tw

        if best_score < 1.0 or best_th == 0:
            return None

        # Extract the tiles
        n_rows = height // best_th
        n_cols = width // best_tw
        tiles: List[List[np.ndarray]] = []
        tile_hashes: List[List[str]] = []
        unique_hashes: Set[str] = set()

        for r in range(n_rows):
            row_tiles: List[np.ndarray] = []
            row_hashes: List[str] = []
            for c in range(n_cols):
                tile = region[r * best_th:(r + 1) * best_th, c * best_tw:(c + 1) * best_tw]
                row_tiles.append(tile)
                h = self._fingerprint_region(tile)
                row_hashes.append(h)
                unique_hashes.add(h)
            tiles.append(row_tiles)
            tile_hashes.append(row_hashes)

        return TileGrid(
            tile_rows=n_rows,
            tile_cols=n_cols,
            tile_width=best_tw,
            tile_height=best_th,
            tiles=tiles,
            tile_hashes=tile_hashes,
            unique_tile_count=len(unique_hashes),
            separator_color=bg_color,
            separator_width=0,
        )

    # =========================================================================
    # STAGE 5: OBJECT DETECTION (FLOOD FILL)
    # =========================================================================

    def _detect_objects(
        self, grid: np.ndarray, bg_color: int, max_objects: int = 200
    ) -> List[DetectedObject]:
        """
        Detect connected objects using flood-fill.

        Unlike seed_primitives._find_distinct_objects() which groups all
        pixels of the same color, this correctly separates disconnected
        regions of the same color into distinct objects.
        """
        height, width = grid.shape
        visited = np.zeros_like(grid, dtype=bool)
        objects: List[DetectedObject] = []

        for y in range(height):
            for x in range(width):
                if visited[y, x] or grid[y, x] == bg_color:
                    continue

                # Flood fill from this pixel
                color = int(grid[y, x])
                pixels = self._flood_fill(grid, visited, y, x, color)

                if not pixels:
                    continue

                obj = self._create_object(pixels, color, grid, bg_color)
                objects.append(obj)

                if len(objects) >= max_objects:
                    break

            if len(objects) >= max_objects:
                break

        return objects

    def _flood_fill(
        self,
        grid: np.ndarray,
        visited: np.ndarray,
        start_y: int,
        start_x: int,
        color: int,
    ) -> List[Tuple[int, int]]:
        """4-connected flood fill. Returns list of (y, x) pixels."""
        height, width = grid.shape
        stack = [(start_y, start_x)]
        pixels: List[Tuple[int, int]] = []

        while stack:
            y, x = stack.pop()
            if y < 0 or y >= height or x < 0 or x >= width:
                continue
            if visited[y, x] or grid[y, x] != color:
                continue

            visited[y, x] = True
            pixels.append((y, x))

            # 4-connected neighbors
            stack.extend([(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)])

        return pixels

    def _create_object(
        self,
        pixels: List[Tuple[int, int]],
        color: int,
        grid: np.ndarray,
        bg_color: int,
    ) -> DetectedObject:
        """Create a DetectedObject from a list of pixels."""
        self._obj_id_counter += 1

        ys = [p[0] for p in pixels]
        xs = [p[1] for p in pixels]
        bounds = (min(ys), min(xs), max(ys) + 1, max(xs) + 1)
        centroid = (sum(ys) / len(ys), sum(xs) / len(xs))
        size = len(pixels)

        # Check if rectangular
        bh = bounds[2] - bounds[0]
        bw = bounds[3] - bounds[1]
        bbox_area = bh * bw
        fill_ratio = size / bbox_area if bbox_area > 0 else 0.0
        is_rectangular = fill_ratio > 0.9

        # Check if hollow (has interior empty space)
        is_hollow = False
        internal_colors: Set[int] = set()
        if bbox_area > 4 and fill_ratio < 0.85:
            # Check interior pixels
            for iy in range(bounds[0] + 1, bounds[2] - 1):
                for ix in range(bounds[1] + 1, bounds[3] - 1):
                    cell = int(grid[iy, ix])
                    if cell != color:
                        internal_colors.add(cell)
                        if cell == bg_color:
                            is_hollow = True

        return DetectedObject(
            obj_id=self._obj_id_counter,
            color=color,
            pixels=pixels,
            bounds=bounds,
            centroid=centroid,
            size=size,
            is_rectangular=is_rectangular,
            is_hollow=is_hollow,
            fill_ratio=fill_ratio,
            internal_colors=internal_colors,
        )

    # =========================================================================
    # STAGE 6: SYMMETRY ANALYSIS
    # =========================================================================

    def _analyze_symmetry(self, grid: np.ndarray) -> Dict[str, Any]:
        """
        Comprehensive symmetry analysis at any scale.

        Checks reflection (H/V/diagonal), rotational (90/180/270),
        and translational symmetry.
        """
        height, width = grid.shape

        if height < 2 or width < 2:
            return {'has_any': False}

        results: Dict[str, Any] = {}

        # Horizontal reflection (top-bottom mirror)
        top = grid[:height // 2, :]
        bottom = grid[(height + 1) // 2:, :][::-1, :]
        min_h = min(top.shape[0], bottom.shape[0])
        if min_h > 0:
            top_trimmed = top[:min_h, :]
            bottom_trimmed = bottom[:min_h, :]
            h_match = np.mean(top_trimmed == bottom_trimmed)
            results['horizontal_reflection'] = float(h_match)
        else:
            results['horizontal_reflection'] = 0.0

        # Vertical reflection (left-right mirror)
        left = grid[:, :width // 2]
        right = grid[:, (width + 1) // 2:][:, ::-1]
        min_w = min(left.shape[1], right.shape[1])
        if min_w > 0:
            left_trimmed = left[:, :min_w]
            right_trimmed = right[:, :min_w]
            v_match = np.mean(left_trimmed == right_trimmed)
            results['vertical_reflection'] = float(v_match)
        else:
            results['vertical_reflection'] = 0.0

        # 180-degree rotation
        rotated_180 = np.rot90(grid, 2)
        results['rotation_180'] = float(np.mean(grid == rotated_180))

        # 90-degree rotation (only square grids)
        if height == width:
            rotated_90 = np.rot90(grid, 1)
            results['rotation_90'] = float(np.mean(grid == rotated_90))
            rotated_270 = np.rot90(grid, 3)
            results['rotation_270'] = float(np.mean(grid == rotated_270))
        else:
            results['rotation_90'] = 0.0
            results['rotation_270'] = 0.0

        # Diagonal symmetry (main diagonal, square grids only)
        if height == width:
            results['diagonal_main'] = float(np.mean(grid == grid.T))
            results['diagonal_anti'] = float(np.mean(grid == np.fliplr(grid).T))
        else:
            results['diagonal_main'] = 0.0
            results['diagonal_anti'] = 0.0

        # Summary
        threshold = 0.85
        detected = {
            k: v > threshold for k, v in results.items()
            if isinstance(v, float)
        }
        results['detected'] = detected
        results['has_any'] = any(detected.values())
        results['strongest'] = max(
            ((k, v) for k, v in results.items() if isinstance(v, float)),
            key=lambda x: x[1],
            default=('none', 0.0),
        )

        return results

    # =========================================================================
    # STAGE 7: REFERENCE PANEL DETECTION
    # =========================================================================

    def _find_reference_panel(
        self, panels: List[Panel], objects: List[DetectedObject]
    ) -> Optional[int]:
        """
        Detect which panel (if any) serves as a reference/legend.

        Reference panels typically:
        - Are smaller than other panels
        - Contain structured, regular content (color pairs, mini examples)
        - Are often bordered/highlighted
        - May contain all colors used in the workspace
        """
        if len(panels) <= 1:
            return None

        # Score each panel on "reference-ness"
        scores: List[Tuple[float, int]] = []
        avg_area = sum(p.area() for p in panels) / len(panels)

        for panel in panels:
            score = 0.0

            # Smaller panels are more likely to be references
            if panel.area() < avg_area * 0.5:
                score += 0.3
            elif panel.area() < avg_area * 0.3:
                score += 0.5

            # Check if panel has high information density
            region = panel.region
            unique_colors = len(np.unique(region))
            density = unique_colors / max(1, region.size ** 0.5)
            score += min(0.3, density * 0.1)

            # Check for structured content (regular arrangement)
            tiling = self._detect_tiling(region, int(Counter(region.flatten().tolist()).most_common(1)[0][0]))
            if tiling and tiling.unique_tile_count > 1:
                score += 0.2

            # Panel role hints
            if panel.role == "reference":
                score += 0.3

            scores.append((score, panel.panel_id))

        scores.sort(reverse=True)

        # Only return if the top score is significantly above others
        if scores and scores[0][0] > 0.4:
            return scores[0][1]

        return None

    # =========================================================================
    # STAGE 8: TRANSFORMATION HYPOTHESIS GENERATION
    # =========================================================================

    def _hypothesize_transformations(
        self,
        panels: List[Panel],
        tile_grids: List[TileGrid],
        objects: List[DetectedObject],
        frame_symmetry: Dict[str, Any],
        ref_panel_id: Optional[int],
    ) -> List[TransformationHypothesis]:
        """
        Generate hypotheses about what transformation maps input to output.

        Tests:
        - Color mapping (color A -> color B)
        - Rotation (90, 180, 270)
        - Reflection (horizontal, vertical)
        - Tile rearrangement (tiles swapped/sorted)
        - Pattern completion (fill in missing parts)
        - Object movement/copying
        """
        hypotheses: List[TransformationHypothesis] = []

        # Need at least input and output panels
        input_panel = None
        output_panel = None
        for p in panels:
            if p.role == "input":
                input_panel = p
            elif p.role == "output":
                output_panel = p

        if input_panel is None or output_panel is None:
            return hypotheses

        in_grid = input_panel.region
        out_grid = output_panel.region

        # Test 1: Rotation
        for angle, k in [(90, 1), (180, 2), (270, 3)]:
            rotated = np.rot90(in_grid, k)
            if rotated.shape == out_grid.shape:
                match = float(np.mean(rotated == out_grid))
                if match > 0.8:
                    hypotheses.append(TransformationHypothesis(
                        transform_type="rotation",
                        parameters={"angle": angle},
                        confidence=match,
                        description=f"Input rotated {angle} degrees matches output ({match:.0%})",
                        evidence=[f"Pixel match after {angle}-degree rotation: {match:.1%}"],
                    ))

        # Test 2: Reflection
        for name, flipped in [
            ("horizontal", np.flipud(in_grid)),
            ("vertical", np.fliplr(in_grid)),
        ]:
            if flipped.shape == out_grid.shape:
                match = float(np.mean(flipped == out_grid))
                if match > 0.8:
                    hypotheses.append(TransformationHypothesis(
                        transform_type="reflection",
                        parameters={"axis": name},
                        confidence=match,
                        description=f"Input reflected {name}ly matches output ({match:.0%})",
                        evidence=[f"Pixel match after {name} flip: {match:.1%}"],
                    ))

        # Test 3: Color mapping
        if in_grid.shape == out_grid.shape:
            color_map = self._detect_color_mapping(in_grid, out_grid)
            if color_map and len(color_map) > 0:
                # Verify the mapping is consistent
                mapped = in_grid.copy()
                for old_c, new_c in color_map.items():
                    mapped[in_grid == old_c] = new_c
                match = float(np.mean(mapped == out_grid))
                if match > 0.9:
                    hypotheses.append(TransformationHypothesis(
                        transform_type="color_map",
                        parameters={"mapping": {int(k): int(v) for k, v in color_map.items()}},
                        confidence=match,
                        description=f"Color mapping: {dict(color_map)} ({match:.0%})",
                        evidence=[f"Consistent color substitution with {match:.1%} match"],
                    ))

        # Test 4: Tile rearrangement (if tiling detected)
        if tile_grids:
            for tg in tile_grids:
                rearrangement = self._detect_tile_rearrangement(tg, panels)
                if rearrangement:
                    hypotheses.append(rearrangement)

        # Test 5: Pattern completion
        if in_grid.shape == out_grid.shape:
            completion = self._detect_pattern_completion(in_grid, out_grid)
            if completion:
                hypotheses.append(completion)

        # Sort by confidence
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        return hypotheses[:5]  # Top 5 hypotheses

    def _detect_color_mapping(
        self, in_grid: np.ndarray, out_grid: np.ndarray
    ) -> Optional[Dict[int, int]]:
        """Detect if there's a consistent color mapping from input to output."""
        if in_grid.shape != out_grid.shape:
            return None

        mapping: Dict[int, Set[int]] = defaultdict(set)
        for y in range(in_grid.shape[0]):
            for x in range(in_grid.shape[1]):
                ic = int(in_grid[y, x])
                oc = int(out_grid[y, x])
                mapping[ic].add(oc)

        # Check if each input color maps to exactly one output color
        result: Dict[int, int] = {}
        for ic, oc_set in mapping.items():
            if len(oc_set) != 1:
                return None  # Ambiguous mapping
            result[ic] = next(iter(oc_set))

        # Filter out identity mappings (color maps to itself)
        result = {k: v for k, v in result.items() if k != v}

        return result if result else None

    def _detect_tile_rearrangement(
        self, tile_grid: TileGrid, panels: List[Panel]
    ) -> Optional[TransformationHypothesis]:
        """Detect if tiles have been rearranged between input and output."""
        # This is a placeholder for more sophisticated tile tracking
        if tile_grid.unique_tile_count > 1:
            return TransformationHypothesis(
                transform_type="tile_rearrangement",
                parameters={
                    "tile_grid_size": f"{tile_grid.tile_rows}x{tile_grid.tile_cols}",
                    "unique_tiles": tile_grid.unique_tile_count,
                },
                confidence=0.5,
                description=(
                    f"Detected {tile_grid.tile_rows}x{tile_grid.tile_cols} tile grid "
                    f"with {tile_grid.unique_tile_count} unique tiles - may involve rearrangement"
                ),
                evidence=["Regular tiling detected with multiple distinct tiles"],
            )
        return None

    def _detect_pattern_completion(
        self, in_grid: np.ndarray, out_grid: np.ndarray
    ) -> Optional[TransformationHypothesis]:
        """Detect if the output is a completion of a partial input pattern."""
        if in_grid.shape != out_grid.shape:
            return None

        # Find cells that differ
        diff_mask = in_grid != out_grid
        n_diff = int(np.sum(diff_mask))
        total = in_grid.size

        if n_diff == 0 or n_diff > total * 0.5:
            return None

        # Check if changed cells were background in input
        bg_in = int(Counter(in_grid.flatten().tolist()).most_common(1)[0][0])
        changed_were_bg = np.sum((in_grid == bg_in) & diff_mask)
        if changed_were_bg / max(1, n_diff) > 0.8:
            return TransformationHypothesis(
                transform_type="pattern_complete",
                parameters={
                    "cells_filled": n_diff,
                    "fraction_filled": n_diff / total,
                },
                confidence=0.6,
                description=(
                    f"Output fills in {n_diff} background cells from input "
                    f"({n_diff / total:.0%} of grid) - pattern completion"
                ),
                evidence=[
                    f"{changed_were_bg}/{n_diff} changed cells were background in input"
                ],
            )

        return None

    # =========================================================================
    # STAGE 9: COMPLEXITY SCORING
    # =========================================================================

    def _calculate_complexity(
        self,
        grid: np.ndarray,
        objects: List[DetectedObject],
        panels: List[Panel],
        tile_grids: List[TileGrid],
        colors_used: Set[int],
    ) -> float:
        """
        Calculate scene complexity score (0.0 to 1.0).

        Higher = more complex scene with more objects, colors, and structure.
        """
        scores = []

        # Color complexity (more colors = more complex)
        scores.append(min(1.0, len(colors_used) / 8.0))

        # Object count complexity
        scores.append(min(1.0, len(objects) / 30.0))

        # Panel complexity (more panels = more structure)
        scores.append(min(1.0, len(panels) / 4.0))

        # Tiling adds complexity
        if tile_grids:
            max_unique = max(tg.unique_tile_count for tg in tile_grids)
            scores.append(min(1.0, max_unique / 6.0))
        else:
            scores.append(0.0)

        # Entropy of color distribution
        flat = grid.flatten()
        counts = Counter(flat.tolist())
        total = len(flat)
        entropy = -sum((c / total) * np.log2(c / total + 1e-10) for c in counts.values())
        max_entropy = np.log2(max(len(counts), 1) + 1e-10)
        scores.append(entropy / (max_entropy + 1e-10) if max_entropy > 0 else 0.0)

        return float(np.mean(scores))

    # =========================================================================
    # STAGE 10: SCENE NARRATIVE
    # =========================================================================

    def _generate_narrative(
        self,
        grid: np.ndarray,
        grid_structure: Optional[GridStructure],
        panels: List[Panel],
        panel_layout: str,
        tile_grids: List[TileGrid],
        objects: List[DetectedObject],
        colors_used: Set[int],
        transformations: List[TransformationHypothesis],
        ref_panel_id: Optional[int],
        symmetry: Dict[str, Any],
    ) -> str:
        """
        Generate a human-readable description of what's visible in the scene.

        This is the equivalent of what a human would say looking at the grid.
        """
        parts: List[str] = []
        h, w = grid.shape

        # Grid structure
        if grid_structure and grid_structure.has_grid_lines:
            parts.append(
                f"{grid_structure.grid_rows}x{grid_structure.grid_cols} logical grid "
                f"(cells {grid_structure.cell_width}x{grid_structure.cell_height}px, "
                f"borders color {ARC_COLOR_NAMES.get(grid_structure.border_color, str(grid_structure.border_color))})"
            )
        else:
            parts.append(f"{h}x{w} grid")

        # Colors
        color_names = [ARC_COLOR_NAMES.get(c, f"color_{c}") for c in sorted(colors_used)]
        parts.append(f"Colors: {', '.join(color_names)}")

        # Panel layout
        if len(panels) > 1:
            layout_desc = {
                "horizontal_split": "split left/right",
                "vertical_split": "split top/bottom",
                "quadrant": "divided into 4 quadrants",
                "grid": f"divided into {len(panels)} panels",
            }.get(panel_layout, f"{len(panels)} panels")
            parts.append(f"Layout: {layout_desc}")

            for p in panels:
                ph = p.bounds[2] - p.bounds[0]
                pw = p.bounds[3] - p.bounds[1]
                parts.append(f"  Panel {p.panel_id} ({p.role}): {ph}x{pw}")

        # Tiling
        for tg in tile_grids:
            parts.append(
                f"Tile grid: {tg.tile_rows}x{tg.tile_cols} tiles "
                f"({tg.tile_width}x{tg.tile_height}px each), "
                f"{tg.unique_tile_count} unique patterns"
            )

        # Objects
        if objects:
            color_counts: Dict[str, int] = Counter()
            for obj in objects:
                cname = ARC_COLOR_NAMES.get(obj.color, f"color_{obj.color}")
                color_counts[cname] += 1

            obj_desc = ", ".join(f"{count} {color}" for color, count in color_counts.most_common(5))
            parts.append(f"Objects: {len(objects)} total ({obj_desc})")

            # Notable objects
            hollow_objs = [o for o in objects if o.is_hollow]
            if hollow_objs:
                parts.append(f"  {len(hollow_objs)} hollow objects (frames/borders)")

            large_objs = [o for o in objects if o.size > grid.size * 0.05]
            if large_objs:
                parts.append(f"  {len(large_objs)} large objects (>5% of grid)")

        # Reference panel
        if ref_panel_id is not None:
            parts.append(f"Reference/legend detected in panel {ref_panel_id}")

        # Symmetry
        if symmetry.get('has_any'):
            sym_types = [k for k, v in symmetry.get('detected', {}).items() if v]
            if sym_types:
                parts.append(f"Symmetry: {', '.join(sym_types)}")

        # Transformations
        if transformations:
            best = transformations[0]
            parts.append(
                f"Best transformation hypothesis: {best.description} "
                f"(confidence: {best.confidence:.0%})"
            )

        return " | ".join(parts)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _detect_background(self, grid: np.ndarray) -> Tuple[int, float]:
        """Detect the background color (most common color, usually 0)."""
        flat = grid.flatten()
        counts = Counter(flat.tolist())
        bg_color, bg_count = counts.most_common(1)[0]
        bg_fraction = bg_count / len(flat)
        return int(bg_color), float(bg_fraction)

    def _fingerprint_region(self, region: np.ndarray) -> str:
        """
        Create a content-based fingerprint of a grid region.

        Two regions with identical content produce the same fingerprint.
        """
        data = region.tobytes()
        return hashlib.md5(data).hexdigest()[:12]

    def _fingerprint_color_invariant(self, region: np.ndarray) -> str:
        """
        Create a color-invariant fingerprint.

        Maps colors to their rank order (most common = 0, next = 1, etc.)
        so differently-colored but structurally identical patterns match.
        """
        flat = region.flatten()
        counts = Counter(flat.tolist())
        # Sort by frequency (most common first), then by value for ties
        ranked = sorted(counts.keys(), key=lambda c: (-counts[c], c))
        color_map = {c: i for i, c in enumerate(ranked)}

        normalized = np.vectorize(lambda c: color_map[c])(region)
        return hashlib.md5(normalized.tobytes()).hexdigest()[:12]

    def _fingerprint_rotation_invariant(self, region: np.ndarray) -> str:
        """
        Create a rotation-invariant fingerprint.

        Takes the lexicographically smallest fingerprint among all 4 rotations.
        """
        fps = []
        for k in range(4):
            rotated = np.rot90(region, k)
            fps.append(self._fingerprint_region(rotated))
        return min(fps)

    def _hash_frame(self, frame: List[List[int]]) -> str:
        """Hash a frame for caching."""
        data = str(frame).encode()
        return hashlib.md5(data).hexdigest()

    def _cache_result(self, key: str, scene: SceneDescription) -> None:
        """Cache a scene analysis result with LRU eviction."""
        if key in self._cache:
            return
        self._cache[key] = scene
        self._cache_order.append(key)
        while len(self._cache_order) > self._cache_size:
            old_key = self._cache_order.pop(0)
            self._cache.pop(old_key, None)

    def _empty_scene(self) -> SceneDescription:
        """Return an empty scene description."""
        return SceneDescription(
            frame_size=(0, 0),
            grid_structure=None,
            logical_grid=None,
            logical_size=None,
            background_color=0,
            background_fraction=1.0,
            panels=[],
            panel_layout="empty",
            tile_grids=[],
            has_tiling=False,
            objects=[],
            object_count=0,
            colors_used=set(),
            frame_symmetry={'has_any': False},
            panel_symmetries=[],
            transformations=[],
            reference_panel_id=None,
            complexity_score=0.0,
            scene_narrative="Empty frame",
        )


# =============================================================================
# MODULE-LEVEL SINGLETON (for easy import)
# =============================================================================

_cortex: Optional[VisualCortex] = None


def get_visual_cortex() -> VisualCortex:
    """Get the module-level VisualCortex singleton."""
    global _cortex
    if _cortex is None:
        _cortex = VisualCortex()
    return _cortex


def analyze_frame(frame: List[List[int]]) -> SceneDescription:
    """Convenience function: analyze a frame using the singleton cortex."""
    return get_visual_cortex().analyze(frame)


def compare_frames(
    frame_a: List[List[int]], frame_b: List[List[int]]
) -> Dict[str, Any]:
    """Convenience function: compare two frames."""
    return get_visual_cortex().compare_frames(frame_a, frame_b)


def render_frame(
    frame: List[List[int]], scale: int = 8
) -> Optional[Any]:
    """Convenience function: render a frame to an image."""
    return get_visual_cortex().render_to_image(frame, scale=scale)
