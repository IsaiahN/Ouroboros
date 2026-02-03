"""
Sparse Grid Representation - Efficient frame encoding for ARC puzzles.

Based on ARC-AGI-2 insights:
"Representing grids as sparse dictionaries (only non-zero cells) enables
more efficient structural comparisons and pattern matching."

Benefits:
1. Memory efficient: Only store non-background cells
2. Comparison efficient: Compare only relevant cells
3. Pattern matching: Find structural similarities across frames
4. Transformation tracking: Easily identify what changed between frames
5. Object isolation: Extract objects as sub-grids naturally

Key Operations:
- from_dense(frame) -> SparseGrid
- to_dense() -> np.ndarray
- diff(other) -> SparseGridDiff (additions, removals, changes)
- find_pattern(pattern) -> List[Match]
- structural_hash() -> str (position-invariant hash)
"""

import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class CellChangeType(Enum):
    """Type of change in a cell between two grids."""
    ADDED = "added"        # Was background, now has color
    REMOVED = "removed"    # Had color, now background
    CHANGED = "changed"    # Had color A, now has color B


@dataclass(frozen=True)
class Cell:
    """A single non-background cell in the grid."""
    y: int
    x: int
    color: int

    def __hash__(self) -> int:
        return hash((self.y, self.x, self.color))

    def position(self) -> Tuple[int, int]:
        return (self.y, self.x)

    def offset(self, dy: int, dx: int) -> "Cell":
        """Return new cell offset by (dy, dx)."""
        return Cell(self.y + dy, self.x + dx, self.color)


@dataclass
class CellChange:
    """A change to a single cell."""
    y: int
    x: int
    change_type: CellChangeType
    old_color: Optional[int] = None  # For REMOVED and CHANGED
    new_color: Optional[int] = None  # For ADDED and CHANGED

    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': (self.y, self.x),
            'type': self.change_type.value,
            'old_color': self.old_color,
            'new_color': self.new_color,
        }


@dataclass
class SparseGridDiff:
    """Difference between two sparse grids."""
    added: List[Cell]          # Cells that appeared (background -> color)
    removed: List[Cell]        # Cells that disappeared (color -> background)
    changed: List[CellChange]  # Cells that changed color

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    @property
    def is_empty(self) -> bool:
        return self.total_changes == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'added': [(c.y, c.x, c.color) for c in self.added],
            'removed': [(c.y, c.x, c.color) for c in self.removed],
            'changed': [c.to_dict() for c in self.changed],
            'total_changes': self.total_changes,
        }

    def get_affected_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions that changed."""
        positions = set()
        for c in self.added:
            positions.add((c.y, c.x))
        for c in self.removed:
            positions.add((c.y, c.x))
        for c in self.changed:
            positions.add((c.y, c.x))
        return positions

    def get_color_flow(self) -> Dict[Tuple[Optional[int], Optional[int]], int]:
        """Get count of color transitions (old_color -> new_color)."""
        flows: Dict[Tuple[Optional[int], Optional[int]], int] = {}

        for c in self.added:
            key = (0, c.color)  # background -> color
            flows[key] = flows.get(key, 0) + 1

        for c in self.removed:
            key = (c.color, 0)  # color -> background
            flows[key] = flows.get(key, 0) + 1

        for c in self.changed:
            key = (c.old_color, c.new_color)
            flows[key] = flows.get(key, 0) + 1

        return flows


@dataclass
class PatternMatch:
    """A match of a pattern within a grid."""
    offset_y: int              # Y offset where pattern was found
    offset_x: int              # X offset where pattern was found
    matched_cells: List[Cell]  # Cells that matched
    match_score: float         # 0.0 to 1.0, how well it matched

    def to_dict(self) -> Dict[str, Any]:
        return {
            'offset': (self.offset_y, self.offset_x),
            'matched_count': len(self.matched_cells),
            'score': self.match_score,
        }


@dataclass
class SparseGrid:
    """
    Sparse representation of an ARC grid.

    Only stores non-background (non-zero) cells.
    Enables efficient comparison and pattern matching.
    """
    cells: Dict[Tuple[int, int], int]  # (y, x) -> color
    height: int
    width: int
    background_color: int = 0

    # Cached properties
    _colors: Optional[Set[int]] = field(default=None, repr=False)
    _bounding_box: Optional[Tuple[int, int, int, int]] = field(default=None, repr=False)
    _structural_hash: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_dense(
        cls,
        frame: np.ndarray,
        background_color: int = 0
    ) -> "SparseGrid":
        """
        Create sparse grid from dense numpy array.

        Args:
            frame: 2D numpy array of colors
            background_color: Color to treat as background (default 0)

        Returns:
            SparseGrid instance
        """
        if frame is None or len(frame) == 0:
            return cls(cells={}, height=0, width=0, background_color=background_color)

        frame = np.asarray(frame)
        if frame.ndim != 2:
            raise ValueError(f"Expected 2D array, got {frame.ndim}D")

        height, width = frame.shape
        cells: Dict[Tuple[int, int], int] = {}

        # Find all non-background cells
        non_bg = np.argwhere(frame != background_color)
        for pos in non_bg:
            y, x = int(pos[0]), int(pos[1])
            cells[(y, x)] = int(frame[y, x])

        return cls(
            cells=cells,
            height=height,
            width=width,
            background_color=background_color,
        )

    @classmethod
    def from_cells(
        cls,
        cells: List[Cell],
        height: Optional[int] = None,
        width: Optional[int] = None,
        background_color: int = 0,
    ) -> "SparseGrid":
        """Create sparse grid from list of cells."""
        cell_dict = {(c.y, c.x): c.color for c in cells}

        if height is None or width is None:
            if cells:
                max_y = max(c.y for c in cells)
                max_x = max(c.x for c in cells)
                height = height or (max_y + 1)
                width = width or (max_x + 1)
            else:
                height = height or 0
                width = width or 0

        return cls(
            cells=cell_dict,
            height=height,
            width=width,
            background_color=background_color,
        )

    def to_dense(self) -> np.ndarray:
        """Convert back to dense numpy array."""
        frame = np.full((self.height, self.width), self.background_color, dtype=np.int32)
        for (y, x), color in self.cells.items():
            if 0 <= y < self.height and 0 <= x < self.width:
                frame[y, x] = color
        return frame

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def cell_count(self) -> int:
        """Number of non-background cells."""
        return len(self.cells)

    @property
    def is_empty(self) -> bool:
        """True if no non-background cells."""
        return len(self.cells) == 0

    @property
    def colors(self) -> Set[int]:
        """Set of unique colors (excluding background)."""
        if self._colors is None:
            self._colors = set(self.cells.values())
        return self._colors

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """
        Bounding box of all non-background cells.

        Returns:
            (min_y, min_x, max_y, max_x) or (0, 0, 0, 0) if empty
        """
        if self._bounding_box is None:
            if self.is_empty:
                self._bounding_box = (0, 0, 0, 0)
            else:
                ys = [y for y, x in self.cells.keys()]
                xs = [x for y, x in self.cells.keys()]
                self._bounding_box = (min(ys), min(xs), max(ys), max(xs))
        return self._bounding_box

    # =========================================================================
    # Cell Access
    # =========================================================================

    def get(self, y: int, x: int) -> int:
        """Get color at position, returns background_color if not set."""
        return self.cells.get((y, x), self.background_color)

    def __getitem__(self, key: Tuple[int, int]) -> int:
        """Get color at position via indexing: grid[y, x]."""
        return self.get(key[0], key[1])

    def __contains__(self, key: Tuple[int, int]) -> bool:
        """Check if position has non-background cell."""
        return key in self.cells

    def __iter__(self) -> Iterator[Cell]:
        """Iterate over all cells."""
        for (y, x), color in self.cells.items():
            yield Cell(y, x, color)

    def __len__(self) -> int:
        """Number of non-background cells."""
        return len(self.cells)

    def cells_by_color(self, color: int) -> List[Cell]:
        """Get all cells of a specific color."""
        return [Cell(y, x, c) for (y, x), c in self.cells.items() if c == color]

    # =========================================================================
    # Comparison Operations
    # =========================================================================

    def diff(self, other: "SparseGrid") -> SparseGridDiff:
        """
        Compute difference between this grid and another.

        Returns what changed from self -> other.

        Args:
            other: Grid to compare against

        Returns:
            SparseGridDiff with added, removed, and changed cells
        """
        added: List[Cell] = []
        removed: List[Cell] = []
        changed: List[CellChange] = []

        all_positions = set(self.cells.keys()) | set(other.cells.keys())

        for pos in all_positions:
            self_color = self.cells.get(pos)
            other_color = other.cells.get(pos)

            if self_color is None and other_color is not None:
                # Cell was added
                added.append(Cell(pos[0], pos[1], other_color))
            elif self_color is not None and other_color is None:
                # Cell was removed
                removed.append(Cell(pos[0], pos[1], self_color))
            elif self_color != other_color:
                # Cell changed color
                changed.append(CellChange(
                    y=pos[0],
                    x=pos[1],
                    change_type=CellChangeType.CHANGED,
                    old_color=self_color,
                    new_color=other_color,
                ))

        return SparseGridDiff(added=added, removed=removed, changed=changed)

    def __eq__(self, other: object) -> bool:
        """Check if two grids are identical."""
        if not isinstance(other, SparseGrid):
            return False
        return (
            self.height == other.height and
            self.width == other.width and
            self.cells == other.cells
        )

    def structural_equals(self, other: "SparseGrid", ignore_colors: bool = False) -> bool:
        """
        Check if two grids have the same structure.

        Args:
            other: Grid to compare
            ignore_colors: If True, only check positions match

        Returns:
            True if structures match
        """
        if len(self.cells) != len(other.cells):
            return False

        if ignore_colors:
            return set(self.cells.keys()) == set(other.cells.keys())

        return self.cells == other.cells

    # =========================================================================
    # Hashing for Pattern Matching
    # =========================================================================

    def structural_hash(self) -> str:
        """
        Position-invariant structural hash.

        Two grids with the same shape but different positions will
        have the same structural hash.

        Returns:
            MD5 hash string
        """
        if self._structural_hash is not None:
            return self._structural_hash

        if self.is_empty:
            self._structural_hash = "empty"
            return self._structural_hash

        # Normalize to origin (0, 0)
        min_y, min_x, _, _ = self.bounding_box
        normalized = []
        for (y, x), color in sorted(self.cells.items()):
            normalized.append((y - min_y, x - min_x, color))

        # Create hash
        data = str(normalized).encode()
        self._structural_hash = hashlib.md5(data).hexdigest()[:16]
        return self._structural_hash

    def color_invariant_hash(self) -> str:
        """
        Hash that ignores specific colors but preserves structure.

        Maps colors to their relative order of appearance.
        """
        if self.is_empty:
            return "empty"

        min_y, min_x, _, _ = self.bounding_box
        color_map: Dict[int, int] = {}
        next_color = 1

        normalized = []
        for (y, x), color in sorted(self.cells.items()):
            if color not in color_map:
                color_map[color] = next_color
                next_color += 1
            normalized.append((y - min_y, x - min_x, color_map[color]))

        data = str(normalized).encode()
        return hashlib.md5(data).hexdigest()[:16]

    # =========================================================================
    # Pattern Matching
    # =========================================================================

    def find_pattern(
        self,
        pattern: "SparseGrid",
        color_flexible: bool = False,
        min_score: float = 1.0,
    ) -> List[PatternMatch]:
        """
        Find all occurrences of a pattern in this grid.

        Args:
            pattern: Pattern to search for
            color_flexible: If True, match structure ignoring exact colors
            min_score: Minimum match score (0.0-1.0)

        Returns:
            List of PatternMatch objects
        """
        if pattern.is_empty:
            return []

        matches: List[PatternMatch] = []
        p_min_y, p_min_x, p_max_y, p_max_x = pattern.bounding_box
        p_height = p_max_y - p_min_y + 1
        p_width = p_max_x - p_min_x + 1

        # Slide pattern across grid
        for start_y in range(self.height - p_height + 1):
            for start_x in range(self.width - p_width + 1):
                match = self._check_pattern_at(
                    pattern, start_y, start_x,
                    p_min_y, p_min_x, color_flexible
                )
                if match and match.match_score >= min_score:
                    matches.append(match)

        return matches

    def _check_pattern_at(
        self,
        pattern: "SparseGrid",
        start_y: int,
        start_x: int,
        p_min_y: int,
        p_min_x: int,
        color_flexible: bool,
    ) -> Optional[PatternMatch]:
        """Check if pattern matches at a specific position."""
        matched_cells: List[Cell] = []
        total_cells = len(pattern.cells)
        color_mapping: Dict[int, int] = {}  # pattern_color -> grid_color

        for (py, px), p_color in pattern.cells.items():
            # Translate pattern position to grid position
            gy = start_y + (py - p_min_y)
            gx = start_x + (px - p_min_x)

            g_color = self.get(gy, gx)

            if color_flexible:
                # Check if colors are consistent
                if p_color in color_mapping:
                    if color_mapping[p_color] != g_color:
                        return None
                else:
                    color_mapping[p_color] = g_color
            else:
                if g_color != p_color:
                    return None

            matched_cells.append(Cell(gy, gx, g_color))

        return PatternMatch(
            offset_y=start_y,
            offset_x=start_x,
            matched_cells=matched_cells,
            match_score=1.0,
        )

    def find_repeated_structures(self, min_size: int = 2) -> List[Tuple["SparseGrid", List[PatternMatch]]]:
        """
        Find repeated structures within the grid.

        Returns list of (pattern, matches) for structures that appear 2+ times.
        """
        # Extract connected components as potential patterns
        components = self.extract_connected_components()

        # Group by structural hash
        hash_to_components: Dict[str, List["SparseGrid"]] = {}
        for comp in components:
            if comp.cell_count >= min_size:
                h = comp.structural_hash()
                if h not in hash_to_components:
                    hash_to_components[h] = []
                hash_to_components[h].append(comp)

        # Return patterns with 2+ occurrences
        repeated: List[Tuple["SparseGrid", List[PatternMatch]]] = []
        for h, comps in hash_to_components.items():
            if len(comps) >= 2:
                # Use first as pattern, create matches for others
                pattern = comps[0]
                matches = []
                for comp in comps:
                    min_y, min_x, _, _ = comp.bounding_box
                    matches.append(PatternMatch(
                        offset_y=min_y,
                        offset_x=min_x,
                        matched_cells=list(comp),
                        match_score=1.0,
                    ))
                repeated.append((pattern, matches))

        return repeated

    # =========================================================================
    # Extraction Operations
    # =========================================================================

    def extract_connected_components(self) -> List["SparseGrid"]:
        """
        Extract connected components as separate sparse grids.

        Uses 4-connectivity (up, down, left, right).
        """
        if self.is_empty:
            return []

        visited: Set[Tuple[int, int]] = set()
        components: List["SparseGrid"] = []

        for pos in self.cells.keys():
            if pos in visited:
                continue

            # BFS to find connected component
            component_cells: Dict[Tuple[int, int], int] = {}
            queue = [pos]

            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                if curr not in self.cells:
                    continue

                visited.add(curr)
                component_cells[curr] = self.cells[curr]

                # Check 4-neighbors
                y, x = curr
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (y + dy, x + dx)
                    if neighbor in self.cells and neighbor not in visited:
                        queue.append(neighbor)

            if component_cells:
                components.append(SparseGrid(
                    cells=component_cells,
                    height=self.height,
                    width=self.width,
                    background_color=self.background_color,
                ))

        return components

    def extract_by_color(self, color: int) -> "SparseGrid":
        """Extract all cells of a specific color as a new grid."""
        cells = {pos: c for pos, c in self.cells.items() if c == color}
        return SparseGrid(
            cells=cells,
            height=self.height,
            width=self.width,
            background_color=self.background_color,
        )

    def extract_subgrid(
        self,
        min_y: int,
        min_x: int,
        max_y: int,
        max_x: int
    ) -> "SparseGrid":
        """Extract a rectangular region as a new sparse grid."""
        cells: Dict[Tuple[int, int], int] = {}
        for (y, x), color in self.cells.items():
            if min_y <= y <= max_y and min_x <= x <= max_x:
                # Translate to new coordinates
                cells[(y - min_y, x - min_x)] = color

        return SparseGrid(
            cells=cells,
            height=max_y - min_y + 1,
            width=max_x - min_x + 1,
            background_color=self.background_color,
        )

    # =========================================================================
    # Transformation Operations
    # =========================================================================

    def translate(self, dy: int, dx: int) -> "SparseGrid":
        """Return new grid with all cells translated by (dy, dx)."""
        cells = {(y + dy, x + dx): c for (y, x), c in self.cells.items()}
        return SparseGrid(
            cells=cells,
            height=self.height,
            width=self.width,
            background_color=self.background_color,
        )

    def normalize_to_origin(self) -> "SparseGrid":
        """Return new grid with bounding box starting at (0, 0)."""
        if self.is_empty:
            return SparseGrid(
                cells={},
                height=0,
                width=0,
                background_color=self.background_color,
            )

        min_y, min_x, max_y, max_x = self.bounding_box
        return self.translate(-min_y, -min_x)

    def apply_color_mapping(self, mapping: Dict[int, int]) -> "SparseGrid":
        """Return new grid with colors remapped according to mapping."""
        cells = {}
        for pos, color in self.cells.items():
            new_color = mapping.get(color, color)
            if new_color != self.background_color:
                cells[pos] = new_color

        return SparseGrid(
            cells=cells,
            height=self.height,
            width=self.width,
            background_color=self.background_color,
        )

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for context passing."""
        return {
            'cells': [(y, x, c) for (y, x), c in self.cells.items()],
            'height': self.height,
            'width': self.width,
            'cell_count': self.cell_count,
            'colors': list(self.colors),
            'bounding_box': self.bounding_box,
            'structural_hash': self.structural_hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SparseGrid":
        """Create from dictionary."""
        cells = {(y, x): c for y, x, c in data.get('cells', [])}
        return cls(
            cells=cells,
            height=data.get('height', 0),
            width=data.get('width', 0),
            background_color=data.get('background_color', 0),
        )

    def __repr__(self) -> str:
        return f"SparseGrid({self.height}x{self.width}, {self.cell_count} cells, colors={self.colors})"


# =============================================================================
# Convenience Functions
# =============================================================================

def sparse_from_frame(frame: np.ndarray) -> SparseGrid:
    """Convert dense frame to sparse grid."""
    return SparseGrid.from_dense(frame)


def sparse_diff(frame1: np.ndarray, frame2: np.ndarray) -> Dict[str, Any]:
    """
    Compute difference between two frames.

    Returns dict suitable for context passing.
    """
    grid1 = SparseGrid.from_dense(frame1)
    grid2 = SparseGrid.from_dense(frame2)
    diff = grid1.diff(grid2)
    return diff.to_dict()


def find_common_structure(frames: List[np.ndarray]) -> Optional[Dict[str, Any]]:
    """
    Find structural patterns common to all frames.

    Useful for identifying invariants across examples.
    """
    if not frames:
        return None

    grids = [SparseGrid.from_dense(f) for f in frames]

    # Get structural hashes of all components in first frame
    first_components = grids[0].extract_connected_components()
    first_hashes = {c.structural_hash() for c in first_components}

    # Find hashes that appear in all frames
    common_hashes = first_hashes
    for grid in grids[1:]:
        components = grid.extract_connected_components()
        hashes = {c.structural_hash() for c in components}
        common_hashes &= hashes

    return {
        'common_structure_count': len(common_hashes),
        'common_hashes': list(common_hashes),
        'total_structures_in_first': len(first_hashes),
    }


def compare_grids_detailed(frame1: np.ndarray, frame2: np.ndarray) -> Dict[str, Any]:
    """
    Detailed comparison of two frames.

    Returns comprehensive analysis suitable for context.
    """
    grid1 = SparseGrid.from_dense(frame1)
    grid2 = SparseGrid.from_dense(frame2)
    diff = grid1.diff(grid2)

    return {
        'grid1': {
            'cell_count': grid1.cell_count,
            'colors': list(grid1.colors),
            'bounding_box': grid1.bounding_box,
        },
        'grid2': {
            'cell_count': grid2.cell_count,
            'colors': list(grid2.colors),
            'bounding_box': grid2.bounding_box,
        },
        'diff': diff.to_dict(),
        'same_structure': grid1.structural_equals(grid2),
        'same_shape': grid1.structural_equals(grid2, ignore_colors=True),
        'color_flow': {
            f"{k[0]}->{k[1]}": v
            for k, v in diff.get_color_flow().items()
        },
    }
