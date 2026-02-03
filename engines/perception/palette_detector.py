"""
Palette/Legend Detector - Detect multi-colored reference blocks that encode rules.

Based on ARC-AGI-2 solution insights:
"~70% of models cluster around wrong solutions where they use the 'palette'
as top-to-bottom instead of inside-out. The object-transformation approach
generates the correct solution by identifying things like: 'multi-colored
palette/key grids serving as reference blocks'"

This module explicitly extracts palette/legend structures BEFORE transformation
detection, enabling correct interpretation of color mapping rules.

Key detection patterns:
- 2-row (horizontal) or 2-column (vertical) multi-colored blocks
- Isolated from main content (surrounded by background)
- Contains multiple distinct colors
- Orientation determines mapping direction:
  - Wide blocks: map vertically (Top->Bottom if at top, Bottom->Top if at bottom)
  - Tall blocks: map horizontally (Left->Right)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class PaletteType(Enum):
    """Types of palette/legend structures."""
    HORIZONTAL_2ROW = "horizontal_2row"  # 2 rows, multiple columns (wide)
    VERTICAL_2COL = "vertical_2col"      # 2 columns, multiple rows (tall)
    GRID = "grid"                        # NxM grid of color mappings
    SINGLE_ROW = "single_row"            # Single row of colors (sequence)
    SINGLE_COLUMN = "single_column"      # Single column of colors (sequence)
    UNKNOWN = "unknown"


class MappingDirection(Enum):
    """Direction to read color mappings from palette."""
    TOP_TO_BOTTOM = "top_to_bottom"
    BOTTOM_TO_TOP = "bottom_to_top"
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    INSIDE_OUT = "inside_out"           # For nested/concentric patterns
    OUTSIDE_IN = "outside_in"
    UNKNOWN = "unknown"


@dataclass
class PaletteInfo:
    """Information about a detected palette/legend."""
    palette_type: PaletteType
    bounding_box: Tuple[int, int, int, int]  # (min_y, min_x, max_y, max_x)

    # Color mapping
    key_colors: List[int]                    # Source colors (frame colors to match)
    value_colors: List[int]                  # Target colors (what to fill/transform to)
    color_mapping: Dict[int, int]            # key_color -> value_color

    # Interpretation
    mapping_direction: MappingDirection
    position_in_frame: str                   # 'top', 'bottom', 'left', 'right', 'center'

    # Confidence and metadata
    confidence: float
    is_isolated: bool                        # Surrounded by background?
    contains_all_frame_colors: bool          # Does it contain all colors in frame?
    unique_colors: int                       # Number of unique colors in palette

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for context passing."""
        return {
            'palette_type': self.palette_type.value,
            'bounding_box': self.bounding_box,
            'key_colors': self.key_colors,
            'value_colors': self.value_colors,
            'color_mapping': self.color_mapping,
            'mapping_direction': self.mapping_direction.value,
            'position_in_frame': self.position_in_frame,
            'confidence': self.confidence,
            'is_isolated': self.is_isolated,
            'contains_all_frame_colors': self.contains_all_frame_colors,
            'unique_colors': self.unique_colors,
        }


@dataclass
class ExtractedObject:
    """An object extracted from the frame (Stage 1 output)."""
    object_id: str
    color: int
    positions: List[Tuple[int, int]]         # List of (y, x) positions
    bounding_box: Tuple[int, int, int, int]  # (min_y, min_x, max_y, max_x)
    centroid: Tuple[float, float]            # (y, x)
    size: int                                # Number of pixels

    # Shape properties
    is_hollow: bool = False                  # Has interior empty space?
    is_rectangular: bool = False             # Rectangular boundary?
    has_interior_fill: bool = False          # Contains other colors inside?

    # Role classification
    possible_roles: List[str] = field(default_factory=list)  # 'palette', 'frame', 'fill', 'background'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'object_id': self.object_id,
            'color': self.color,
            'positions': self.positions[:10] if len(self.positions) > 10 else self.positions,  # Truncate for context
            'bounding_box': self.bounding_box,
            'centroid': self.centroid,
            'size': self.size,
            'is_hollow': self.is_hollow,
            'is_rectangular': self.is_rectangular,
            'has_interior_fill': self.has_interior_fill,
            'possible_roles': self.possible_roles,
        }


@dataclass
class DetectedTransformation:
    """A transformation detected between objects (Stage 2 output)."""
    transformation_type: str                 # 'color_fill', 'color_swap', 'position_shift', etc.
    source_objects: List[str]                # Object IDs involved
    target_objects: List[str]                # Object IDs affected

    # Transformation details
    color_mapping: Optional[Dict[int, int]] = None  # For color transformations
    position_delta: Optional[Tuple[int, int]] = None  # For movement

    # Rule
    rule_description: str = ""               # Human-readable rule
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'transformation_type': self.transformation_type,
            'source_objects': self.source_objects,
            'target_objects': self.target_objects,
            'color_mapping': self.color_mapping,
            'position_delta': self.position_delta,
            'rule_description': self.rule_description,
            'confidence': self.confidence,
        }


class PaletteDetector:
    """
    Detect multi-colored reference blocks that encode transformation rules.

    This implements the two-stage insight: explicitly extracting palette/legend
    structures as a FIRST STEP before any transformation detection.

    Two-Stage Architecture:
    - Stage 1: Extract all objects (hollow frames, interior fills, palettes)
    - Stage 2: Identify transformations based on extracted objects
    """

    def __init__(
        self,
        min_palette_colors: int = 2,
        max_palette_width: int = 16,
        max_palette_height: int = 16,
        isolation_threshold: int = 1,  # Pixels of background around palette
    ):
        """
        Initialize the palette detector.

        Args:
            min_palette_colors: Minimum colors needed to be a palette
            max_palette_width: Maximum width of a palette region
            max_palette_height: Maximum height of a palette region
            isolation_threshold: Background pixels needed for isolation
        """
        self.min_palette_colors = min_palette_colors
        self.max_palette_width = max_palette_width
        self.max_palette_height = max_palette_height
        self.isolation_threshold = isolation_threshold

        # Object tracking counter
        self._object_counter = 0

    # =========================================================================
    # STAGE 1: Object Extraction
    # =========================================================================

    def extract_objects(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        STAGE 1: Extract all objects from frame.

        This is the FIRST step - identify all distinct objects before
        attempting any transformation detection.

        Args:
            frame: 2D numpy array (height x width) of color values

        Returns:
            Dict with categorized objects:
            {
                'palettes': List[ExtractedObject],      # Potential legend/key objects
                'hollow_frames': List[ExtractedObject], # Rectangular frames with holes
                'filled_shapes': List[ExtractedObject], # Solid shapes
                'irregular_shapes': List[ExtractedObject],
                'background': ExtractedObject or None,
                'all_objects': List[ExtractedObject],
            }
        """
        if frame is None or len(frame) == 0:
            return self._empty_extraction_result()

        frame = np.array(frame)
        height, width = frame.shape

        # Find all connected components per color
        all_objects = []

        for color in range(10):  # ARC uses colors 0-9
            if color == 0:
                continue  # Skip background in initial extraction

            mask = (frame == color)
            if not np.any(mask):
                continue

            # Find connected components
            objects_of_color = self._find_connected_components(frame, mask, color)
            all_objects.extend(objects_of_color)

        # Classify objects into categories
        result = self._classify_objects(all_objects, frame)
        result['all_objects'] = all_objects

        return result

    def _find_connected_components(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        color: int
    ) -> List[ExtractedObject]:
        """Find connected components in a binary mask."""
        try:
            from scipy import ndimage
            result = ndimage.label(mask)
            labeled: np.ndarray = result[0]
            num_features: int = int(result[1])
        except ImportError:
            # Fallback without scipy
            return self._find_connected_components_fallback(frame, mask, color)

        objects = []
        for label_id in range(1, num_features + 1):
            positions = np.argwhere(labeled == label_id)
            if len(positions) < 1:
                continue

            positions_list = [(int(p[0]), int(p[1])) for p in positions]

            # Calculate bounding box
            ys = [p[0] for p in positions_list]
            xs = [p[1] for p in positions_list]
            bbox = (min(ys), min(xs), max(ys), max(xs))

            # Calculate centroid
            centroid = (float(np.mean(ys)), float(np.mean(xs)))

            # Check if hollow
            is_hollow = self._check_if_hollow(positions_list, bbox, frame)

            # Check if rectangular
            is_rectangular = self._check_if_rectangular(positions_list, bbox)

            self._object_counter += 1
            obj = ExtractedObject(
                object_id=f"obj_{color}_{self._object_counter}",
                color=color,
                positions=positions_list,
                bounding_box=bbox,
                centroid=centroid,
                size=len(positions_list),
                is_hollow=is_hollow,
                is_rectangular=is_rectangular,
            )
            objects.append(obj)

        return objects

    def _find_connected_components_fallback(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        color: int
    ) -> List[ExtractedObject]:
        """Fallback connected component finder without scipy."""
        height, width = mask.shape
        visited = np.zeros_like(mask, dtype=bool)
        objects = []

        def flood_fill(start_y: int, start_x: int) -> List[Tuple[int, int]]:
            stack = [(start_y, start_x)]
            component = []

            while stack:
                y, x = stack.pop()
                if y < 0 or y >= height or x < 0 or x >= width:
                    continue
                if visited[y, x] or not mask[y, x]:
                    continue

                visited[y, x] = True
                component.append((y, x))

                # 4-connectivity
                stack.extend([(y-1, x), (y+1, x), (y, x-1), (y, x+1)])

            return component

        for y in range(height):
            for x in range(width):
                if mask[y, x] and not visited[y, x]:
                    positions_list = flood_fill(y, x)
                    if positions_list:
                        ys = [p[0] for p in positions_list]
                        xs = [p[1] for p in positions_list]
                        bbox = (min(ys), min(xs), max(ys), max(xs))
                        centroid = (float(np.mean(ys)), float(np.mean(xs)))

                        is_hollow = self._check_if_hollow(positions_list, bbox, frame)
                        is_rectangular = self._check_if_rectangular(positions_list, bbox)

                        self._object_counter += 1
                        obj = ExtractedObject(
                            object_id=f"obj_{color}_{self._object_counter}",
                            color=color,
                            positions=positions_list,
                            bounding_box=bbox,
                            centroid=centroid,
                            size=len(positions_list),
                            is_hollow=is_hollow,
                            is_rectangular=is_rectangular,
                        )
                        objects.append(obj)

        return objects

    def _check_if_hollow(
        self,
        positions: List[Tuple[int, int]],
        bbox: Tuple[int, int, int, int],
        frame: np.ndarray
    ) -> bool:
        """Check if object has interior empty space (hollow frame)."""
        min_y, min_x, max_y, max_x = bbox
        height = max_y - min_y + 1
        width = max_x - min_x + 1

        # Too small to be hollow
        if height < 3 or width < 3:
            return False

        positions_set = set(positions)

        # Check interior for background (color 0)
        interior_background = 0
        interior_total = 0

        for y in range(min_y + 1, max_y):
            for x in range(min_x + 1, max_x):
                interior_total += 1
                if (y, x) not in positions_set and frame[y, x] == 0:
                    interior_background += 1

        if interior_total == 0:
            return False

        return interior_background / interior_total > 0.5

    def _check_if_rectangular(
        self,
        positions: List[Tuple[int, int]],
        bbox: Tuple[int, int, int, int]
    ) -> bool:
        """Check if object has rectangular boundary."""
        min_y, min_x, max_y, max_x = bbox
        expected_size = (max_y - min_y + 1) * (max_x - min_x + 1)

        # If object fills most of its bounding box, it's rectangular
        fill_ratio = len(positions) / expected_size if expected_size > 0 else 0
        return fill_ratio > 0.8

    def _classify_objects(
        self,
        objects: List[ExtractedObject],
        frame: np.ndarray
    ) -> Dict[str, Any]:
        """Classify objects into categories."""
        result = {
            'palettes': [],
            'hollow_frames': [],
            'filled_shapes': [],
            'irregular_shapes': [],
            'background': None,
        }

        for obj in objects:
            # Check if potential palette
            if self._is_potential_palette(obj, frame):
                obj.possible_roles.append('palette')
                result['palettes'].append(obj)

            # Check if hollow frame
            if obj.is_hollow:
                obj.possible_roles.append('hollow_frame')
                result['hollow_frames'].append(obj)

            # Check if filled shape
            elif obj.is_rectangular and not obj.is_hollow:
                obj.possible_roles.append('filled_shape')
                result['filled_shapes'].append(obj)

            # Otherwise irregular
            else:
                obj.possible_roles.append('irregular')
                result['irregular_shapes'].append(obj)

        return result

    def _is_potential_palette(self, obj: ExtractedObject, frame: np.ndarray) -> bool:
        """Check if object could be a palette/legend."""
        min_y, min_x, max_y, max_x = obj.bounding_box
        height = max_y - min_y + 1
        width = max_x - min_x + 1

        # Size constraints
        if height > self.max_palette_height or width > self.max_palette_width:
            return False

        # Palettes are typically small relative to frame
        frame_height, frame_width = frame.shape
        if obj.size > (frame_height * frame_width) * 0.25:
            return False

        # Check for isolation (surrounded by background)
        if self._is_isolated(obj.bounding_box, frame):
            return True

        # Check for multiple colors in a small, organized region
        region = frame[min_y:max_y+1, min_x:max_x+1]
        unique_colors = set(region.flatten()) - {0}
        if len(unique_colors) >= self.min_palette_colors:
            return True

        return False

    def _is_isolated(self, bbox: Tuple[int, int, int, int], frame: np.ndarray) -> bool:
        """Check if region is surrounded by background."""
        min_y, min_x, max_y, max_x = bbox
        height, width = frame.shape

        # Check all sides for background
        sides_clear = 0

        # Top
        if min_y >= self.isolation_threshold:
            top_clear = all(frame[min_y - i - 1, x] == 0
                          for i in range(self.isolation_threshold)
                          for x in range(max(0, min_x), min(width, max_x + 1))
                          if min_y - i - 1 >= 0)
            if top_clear:
                sides_clear += 1
        else:
            sides_clear += 1  # At edge counts as isolated

        # Bottom
        if max_y < height - self.isolation_threshold:
            bottom_clear = all(frame[max_y + i + 1, x] == 0
                              for i in range(self.isolation_threshold)
                              for x in range(max(0, min_x), min(width, max_x + 1))
                              if max_y + i + 1 < height)
            if bottom_clear:
                sides_clear += 1
        else:
            sides_clear += 1

        # At least 2 sides must be clear
        return sides_clear >= 2

    def _empty_extraction_result(self) -> Dict[str, Any]:
        """Return empty extraction result."""
        return {
            'palettes': [],
            'hollow_frames': [],
            'filled_shapes': [],
            'irregular_shapes': [],
            'background': None,
            'all_objects': [],
        }

    # =========================================================================
    # STAGE 1.5: Palette Detection (specialized)
    # =========================================================================

    def detect_palette(self, frame: np.ndarray) -> Optional[PaletteInfo]:
        """
        Detect the most likely palette/legend in the frame.

        This is the KEY function that the two-stage insight addresses:
        identifying the reference block that encodes transformation rules.

        Args:
            frame: 2D numpy array

        Returns:
            PaletteInfo if found, None otherwise
        """
        if frame is None or len(frame) == 0:
            return None

        frame = np.array(frame)
        height, width = frame.shape

        # Get all unique colors in frame (excluding background)
        all_frame_colors = set(frame.flatten()) - {0}

        # Strategy 1: Look for small, isolated, multi-colored regions
        candidates = self._find_palette_candidates(frame, all_frame_colors)

        if not candidates:
            return None

        # Score and select best candidate
        best_candidate = max(candidates, key=lambda c: c.confidence)

        if best_candidate.confidence < 0.3:
            return None

        return best_candidate

    def _find_palette_candidates(
        self,
        frame: np.ndarray,
        all_frame_colors: Set[int]
    ) -> List[PaletteInfo]:
        """Find all potential palette regions in frame."""
        height, width = frame.shape
        candidates = []

        # Strategy 1: Scan for 2-row horizontal palettes
        for y in range(height - 1):
            candidates.extend(
                self._scan_for_horizontal_palette(frame, y, all_frame_colors)
            )

        # Strategy 2: Scan for 2-column vertical palettes
        for x in range(width - 1):
            candidates.extend(
                self._scan_for_vertical_palette(frame, x, all_frame_colors)
            )

        # Strategy 3: Look for small grid patterns (NxM)
        candidates.extend(self._find_grid_palettes(frame, all_frame_colors))

        return candidates

    def _scan_for_horizontal_palette(
        self,
        frame: np.ndarray,
        start_y: int,
        all_frame_colors: Set[int]
    ) -> List[PaletteInfo]:
        """Scan for 2-row horizontal palettes starting at y."""
        height, width = frame.shape
        candidates = []

        # Look for runs of non-background in both rows
        x = 0
        while x < width:
            # Find start of non-background
            while x < width and frame[start_y, x] == 0 and frame[start_y + 1, x] == 0:
                x += 1

            if x >= width:
                break

            start_x = x

            # Find end of non-background run
            while x < width and (frame[start_y, x] != 0 or frame[start_y + 1, x] != 0):
                x += 1

            end_x = x - 1
            run_width = end_x - start_x + 1

            # Check if this could be a palette (at least 2 columns)
            if run_width >= 2 and run_width <= self.max_palette_width:
                palette_info = self._analyze_horizontal_palette(
                    frame, start_y, start_x, end_x, all_frame_colors
                )
                if palette_info:
                    candidates.append(palette_info)

        return candidates

    def _analyze_horizontal_palette(
        self,
        frame: np.ndarray,
        y: int,
        start_x: int,
        end_x: int,
        all_frame_colors: Set[int]
    ) -> Optional[PaletteInfo]:
        """Analyze a potential 2-row horizontal palette."""
        height, width = frame.shape

        # Extract the two rows
        row1 = [frame[y, x] for x in range(start_x, end_x + 1)]
        row2 = [frame[y + 1, x] for x in range(start_x, end_x + 1)]

        # Count unique colors (excluding 0)
        colors_row1 = [c for c in row1 if c != 0]
        colors_row2 = [c for c in row2 if c != 0]
        all_colors = set(colors_row1 + colors_row2)

        if len(all_colors) < self.min_palette_colors:
            return None

        # Determine key/value rows
        # Heuristic: row with more unique colors is likely keys
        if len(set(colors_row1)) >= len(set(colors_row2)):
            key_colors = colors_row1
            value_colors = colors_row2
        else:
            key_colors = colors_row2
            value_colors = colors_row1

        # Build color mapping (column-wise)
        color_mapping = {}
        for i in range(min(len(row1), len(row2))):
            if row1[i] != 0 and row2[i] != 0:
                color_mapping[row1[i]] = row2[i]

        # Determine mapping direction based on position
        position = 'top' if y < height / 3 else ('bottom' if y > height * 2/3 else 'middle')

        if position == 'top':
            mapping_direction = MappingDirection.TOP_TO_BOTTOM
        elif position == 'bottom':
            mapping_direction = MappingDirection.BOTTOM_TO_TOP
        else:
            mapping_direction = MappingDirection.TOP_TO_BOTTOM

        # Check isolation
        bbox = (y, start_x, y + 1, end_x)
        is_isolated = self._is_isolated(bbox, frame)

        # Calculate confidence
        confidence = 0.3
        if is_isolated:
            confidence += 0.3
        if all_colors <= all_frame_colors:
            confidence += 0.2
        if len(color_mapping) >= 2:
            confidence += 0.2

        return PaletteInfo(
            palette_type=PaletteType.HORIZONTAL_2ROW,
            bounding_box=bbox,
            key_colors=key_colors,
            value_colors=value_colors,
            color_mapping=color_mapping,
            mapping_direction=mapping_direction,
            position_in_frame=position,
            confidence=min(1.0, confidence),
            is_isolated=is_isolated,
            contains_all_frame_colors=(all_colors == all_frame_colors),
            unique_colors=len(all_colors),
        )

    def _scan_for_vertical_palette(
        self,
        frame: np.ndarray,
        start_x: int,
        all_frame_colors: Set[int]
    ) -> List[PaletteInfo]:
        """Scan for 2-column vertical palettes starting at x."""
        height, width = frame.shape
        candidates = []

        y = 0
        while y < height:
            while y < height and frame[y, start_x] == 0 and frame[y, start_x + 1] == 0:
                y += 1

            if y >= height:
                break

            start_y = y

            while y < height and (frame[y, start_x] != 0 or frame[y, start_x + 1] != 0):
                y += 1

            end_y = y - 1
            run_height = end_y - start_y + 1

            if run_height >= 2 and run_height <= self.max_palette_height:
                palette_info = self._analyze_vertical_palette(
                    frame, start_x, start_y, end_y, all_frame_colors
                )
                if palette_info:
                    candidates.append(palette_info)

        return candidates

    def _analyze_vertical_palette(
        self,
        frame: np.ndarray,
        x: int,
        start_y: int,
        end_y: int,
        all_frame_colors: Set[int]
    ) -> Optional[PaletteInfo]:
        """Analyze a potential 2-column vertical palette."""
        height, width = frame.shape

        col1 = [frame[y, x] for y in range(start_y, end_y + 1)]
        col2 = [frame[y, x + 1] for y in range(start_y, end_y + 1)]

        colors_col1 = [c for c in col1 if c != 0]
        colors_col2 = [c for c in col2 if c != 0]
        all_colors = set(colors_col1 + colors_col2)

        if len(all_colors) < self.min_palette_colors:
            return None

        # Build mapping
        color_mapping = {}
        for i in range(min(len(col1), len(col2))):
            if col1[i] != 0 and col2[i] != 0:
                color_mapping[col1[i]] = col2[i]

        position = 'left' if x < width / 3 else ('right' if x > width * 2/3 else 'middle')
        mapping_direction = MappingDirection.LEFT_TO_RIGHT

        bbox = (start_y, x, end_y, x + 1)
        is_isolated = self._is_isolated(bbox, frame)

        confidence = 0.3
        if is_isolated:
            confidence += 0.3
        if all_colors <= all_frame_colors:
            confidence += 0.2
        if len(color_mapping) >= 2:
            confidence += 0.2

        return PaletteInfo(
            palette_type=PaletteType.VERTICAL_2COL,
            bounding_box=bbox,
            key_colors=colors_col1,
            value_colors=colors_col2,
            color_mapping=color_mapping,
            mapping_direction=mapping_direction,
            position_in_frame=position,
            confidence=min(1.0, confidence),
            is_isolated=is_isolated,
            contains_all_frame_colors=(all_colors == all_frame_colors),
            unique_colors=len(all_colors),
        )

    def _find_grid_palettes(
        self,
        frame: np.ndarray,
        all_frame_colors: Set[int]
    ) -> List[PaletteInfo]:
        """Find small grid patterns that could be palettes."""
        # Simplified: look for small rectangular regions with multiple colors
        # This could be expanded for more complex grid patterns
        return []  # TODO: Implement grid palette detection

    # =========================================================================
    # STAGE 2: Transformation Detection
    # =========================================================================

    def detect_transformations(
        self,
        extracted_objects: Dict[str, Any],
        palette: Optional[PaletteInfo],
        frame: np.ndarray
    ) -> List[DetectedTransformation]:
        """
        STAGE 2: Detect transformations based on extracted objects.

        This runs AFTER object extraction and palette detection.

        Args:
            extracted_objects: Output from extract_objects()
            palette: Detected palette (if any)
            frame: Original frame

        Returns:
            List of detected transformations
        """
        transformations = []

        # If we have a palette, look for color fill transformations
        if palette and palette.color_mapping:
            fill_transform = self._detect_color_fill_transformation(
                extracted_objects, palette, frame
            )
            if fill_transform:
                transformations.append(fill_transform)

        # Look for position-based transformations
        # (objects that should be moved/aligned)
        position_transforms = self._detect_position_transformations(
            extracted_objects, frame
        )
        transformations.extend(position_transforms)

        return transformations

    def _detect_color_fill_transformation(
        self,
        extracted_objects: Dict[str, Any],
        palette: PaletteInfo,
        frame: np.ndarray
    ) -> Optional[DetectedTransformation]:
        """
        Detect color fill transformation pattern.

        Pattern: Hollow frames with colors in palette keys
        should have their interiors filled with mapped value colors.
        """
        hollow_frames = extracted_objects.get('hollow_frames', [])

        # Find frames whose colors are in the palette
        matching_frames = []
        for frame_obj in hollow_frames:
            if frame_obj.color in palette.color_mapping:
                matching_frames.append(frame_obj)

        if not matching_frames:
            return None

        # Build rule description
        rule_parts = []
        for key, value in palette.color_mapping.items():
            rule_parts.append(f"color {key} -> fill with {value}")

        return DetectedTransformation(
            transformation_type='color_fill',
            source_objects=[f.object_id for f in matching_frames],
            target_objects=[f.object_id for f in matching_frames],
            color_mapping=palette.color_mapping,
            rule_description=f"Fill hollow frames: {'; '.join(rule_parts)}",
            confidence=palette.confidence,
        )

    def _detect_position_transformations(
        self,
        extracted_objects: Dict[str, Any],
        frame: np.ndarray
    ) -> List[DetectedTransformation]:
        """Detect position-based transformations."""
        # TODO: Implement position transformation detection
        return []


# Convenience functions for direct use
def detect_palette(frame: np.ndarray) -> Optional[Dict[str, Any]]:
    """
    Convenience function to detect palette in a frame.

    Returns dictionary (or None) for easy context passing.
    """
    detector = PaletteDetector()
    palette = detector.detect_palette(frame)
    return palette.to_dict() if palette else None


def extract_objects(frame: np.ndarray) -> Dict[str, Any]:
    """
    Convenience function to extract objects from a frame.

    Returns dictionary with categorized objects.
    """
    detector = PaletteDetector()
    result = detector.extract_objects(frame)

    # Convert to serializable format
    return {
        'palettes': [o.to_dict() for o in result.get('palettes', [])],
        'hollow_frames': [o.to_dict() for o in result.get('hollow_frames', [])],
        'filled_shapes': [o.to_dict() for o in result.get('filled_shapes', [])],
        'irregular_shapes': [o.to_dict() for o in result.get('irregular_shapes', [])],
        'all_objects': [o.to_dict() for o in result.get('all_objects', [])],
    }


def two_stage_analysis(frame: np.ndarray) -> Dict[str, Any]:
    """
    Perform full two-stage analysis.

    Stage 1: Extract objects
    Stage 2: Detect palette and transformations

    Returns complete analysis for context.
    """
    detector = PaletteDetector()

    # Stage 1: Extract objects
    extracted = detector.extract_objects(frame)

    # Stage 1.5: Detect palette
    palette = detector.detect_palette(frame)

    # Stage 2: Detect transformations
    transformations = detector.detect_transformations(extracted, palette, frame)

    return {
        'extracted_objects': {
            'palettes': [o.to_dict() for o in extracted.get('palettes', [])],
            'hollow_frames': [o.to_dict() for o in extracted.get('hollow_frames', [])],
            'filled_shapes': [o.to_dict() for o in extracted.get('filled_shapes', [])],
            'irregular_shapes': [o.to_dict() for o in extracted.get('irregular_shapes', [])],
            'object_count': len(extracted.get('all_objects', [])),
        },
        'detected_palette': palette.to_dict() if palette else None,
        'detected_transformations': [t.to_dict() for t in transformations],
        'analysis_complete': True,
    }
