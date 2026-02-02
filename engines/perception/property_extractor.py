"""
Property Extractor - Extract learnable symbolic properties from player sprite.

Part of Symbolic Reasoning Implementation (Phase 1).

For ARC games, the frame is a symbolic grid of color indices (0-12), not RGB pixels.
This extractor handles both:
- Symbolic grids (ARC games): Track dominant color index, shape signature
- RGB images (visual games): Track dominant RGB color, perceptual hash

Extracts:
- Dominant color (most frequent color index or RGB value)
- Shape signature (hash of non-background cells)
- Orientation (coarse: based on center of mass)
"""

from typing import Optional

import numpy as np


class PropertyExtractor:
    """
    Extract learnable properties from player sprite region.

    Handles both symbolic grids (ARC) and RGB images.

    For symbolic grids:
    - Dominant color = most frequent color index
    - Shape = hash of cell positions

    For RGB images:
    - Dominant color = hex color string
    - Shape = perceptual hash
    """

    # ARC color palette mapping (for reference)
    ARC_COLORS = {
        0: 'black', 1: 'blue', 2: 'red', 3: 'green', 4: 'yellow',
        5: 'grey', 6: 'pink', 7: 'orange', 8: 'cyan', 9: 'brown',
        10: 'white', 11: 'maroon', 12: 'purple'
    }

    def __init__(self, color_quantization: int = 16):
        """
        Args:
            color_quantization: Number of color levels per channel for RGB (16 = 4096 colors)
        """
        self.color_quantization = color_quantization
        self._color_step = 256 // color_quantization

    def extract_properties(self, player_region: np.ndarray) -> Optional[dict]:
        """
        Extract symbolic properties from player sprite region.

        Args:
            player_region: Player sprite pixels. Can be:
                - (H, W) grid of color indices (ARC)
                - (H, W, C) RGB image

        Returns:
            {
                'dominant_color': color index (int) or '#RRGGBB' hex string,
                'shape_signature': binary string representing shape,
                'orientation': 0, 90, 180, or 270 degrees,
                'size': (height, width),
                'is_symbolic': bool - True if ARC grid, False if RGB
            }
            or None if input is invalid.
        """
        if player_region is None:
            return None
        if not isinstance(player_region, np.ndarray):
            return None
        if player_region.size == 0:
            return None
        if player_region.shape[0] < 2 or (len(player_region.shape) > 1 and player_region.shape[1] < 2):
            return None

        # Detect if this is symbolic (ARC) or RGB
        is_symbolic = len(player_region.shape) == 2 or (
            len(player_region.shape) == 3 and player_region.shape[0] == 1
        )

        if is_symbolic:
            # Handle ARC symbolic grid
            return self._extract_from_symbolic_grid(player_region)
        else:
            # Handle RGB image
            return self._extract_from_rgb_image(player_region)

    def _extract_from_symbolic_grid(self, grid: np.ndarray) -> dict:
        """Extract properties from ARC-style symbolic grid."""
        # Squeeze if shape is (1, H, W)
        if len(grid.shape) == 3 and grid.shape[0] == 1:
            grid = grid[0]

        # Dominant color = most frequent non-zero color index
        unique, counts = np.unique(grid, return_counts=True)

        # Filter out background (0) for dominant color
        non_zero_mask = unique != 0
        if np.any(non_zero_mask):
            non_zero_unique = unique[non_zero_mask]
            non_zero_counts = counts[non_zero_mask]
            dominant_color = int(non_zero_unique[non_zero_counts.argmax()])
        else:
            dominant_color = 0  # All background

        # Shape signature = hash of non-background cell positions
        non_zero_positions = np.argwhere(grid != 0)
        if len(non_zero_positions) > 0:
            # Normalize positions relative to centroid
            centroid = non_zero_positions.mean(axis=0)
            relative = non_zero_positions - centroid
            # Create binary signature from position pattern
            shape_sig = self._positions_to_signature(relative)
        else:
            shape_sig = '0' * 64  # Empty shape

        # Orientation based on center of mass offset
        orientation = self._detect_coarse_orientation_symbolic(grid)

        return {
            'dominant_color': dominant_color,
            'shape_signature': shape_sig,
            'orientation': orientation,
            'size': (grid.shape[0], grid.shape[1]),
            'is_symbolic': True
        }

    def _extract_from_rgb_image(self, region: np.ndarray) -> dict:
        """Extract properties from RGB image."""
        # Handle grayscale
        if len(region.shape) == 2:
            region = np.stack([region, region, region], axis=-1)

        # Ensure 3 channels (handle RGBA)
        if region.shape[2] == 4:
            region = region[:, :, :3]

        return {
            'dominant_color': self._extract_dominant_color_rgb(region),
            'shape_signature': self._compute_perceptual_hash(region),
            'orientation': self._detect_coarse_orientation_rgb(region),
            'size': (region.shape[0], region.shape[1]),
            'is_symbolic': False
        }

    def _positions_to_signature(self, relative_positions: np.ndarray) -> str:
        """
        Convert relative positions to a 64-bit signature.

        Quantizes positions into 8x8 grid and creates binary string.
        """
        if len(relative_positions) == 0:
            return '0' * 64

        # Normalize to [-4, 4] range
        max_extent = max(1, np.abs(relative_positions).max())
        normalized = relative_positions / max_extent * 3.5

        # Quantize to 8x8 grid
        signature = np.zeros((8, 8), dtype=bool)
        for pos in normalized:
            y = int(pos[0] + 4)
            x = int(pos[1] + 4) if len(pos) > 1 else 4
            y = max(0, min(7, y))
            x = max(0, min(7, x))
            signature[y, x] = True

        return ''.join(['1' if b else '0' for b in signature.flatten()])

    def _detect_coarse_orientation_symbolic(self, grid: np.ndarray) -> int:
        """Detect orientation from symbolic grid."""
        non_zero = np.argwhere(grid != 0)
        if len(non_zero) == 0:
            return 0

        h, w = grid.shape[:2]
        center_y, center_x = h / 2, w / 2

        com_y = non_zero[:, 0].mean()
        com_x = non_zero[:, 1].mean() if non_zero.shape[1] > 1 else center_x

        dy = com_y - center_y
        dx = com_x - center_x

        if abs(dy) > abs(dx):
            return 0 if dy < 0 else 180
        else:
            return 90 if dx > 0 else 270

    def _extract_dominant_color_rgb(self, region: np.ndarray) -> str:
        """Extract dominant RGB color as hex string."""
        quantized = (region // self._color_step) * self._color_step
        pixels = quantized.reshape(-1, 3)

        color_ints = pixels[:, 0].astype(np.int32) * 65536 + \
                     pixels[:, 1].astype(np.int32) * 256 + \
                     pixels[:, 2].astype(np.int32)

        unique, counts = np.unique(color_ints, return_counts=True)
        dominant_int = unique[counts.argmax()]

        r = (dominant_int >> 16) & 0xFF
        g = (dominant_int >> 8) & 0xFF
        b = dominant_int & 0xFF

        return f'#{r:02x}{g:02x}{b:02x}'

    def _compute_perceptual_hash(self, region: np.ndarray) -> str:
        """Compute perceptual hash for RGB image."""
        if len(region.shape) == 3:
            if region.shape[2] == 4:
                region = region[:, :, :3]
            gray = np.mean(region, axis=2).astype(np.uint8)
        else:
            gray = region.astype(np.uint8)

        small = self._resize_simple(gray, (8, 8))
        avg = small.mean()
        bits = (small > avg).flatten()

        return ''.join(['1' if b else '0' for b in bits])

    def _detect_coarse_orientation_rgb(self, region: np.ndarray) -> int:
        """Detect orientation from RGB image."""
        if len(region.shape) == 3:
            gray = np.mean(region, axis=2)
        else:
            gray = region.astype(np.float32)

        h, w = gray.shape
        total = gray.sum()
        if total < 1:
            return 0

        y_coords, x_coords = np.mgrid[0:h, 0:w]
        com_y = (y_coords * gray).sum() / total
        com_x = (x_coords * gray).sum() / total

        dy = com_y - h / 2
        dx = com_x - w / 2

        if abs(dy) > abs(dx):
            return 0 if dy < 0 else 180
        else:
            return 90 if dx > 0 else 270

    def _resize_simple(self, image: np.ndarray, target_size: tuple) -> np.ndarray:
        """Simple image resize without opencv."""
        target_h, target_w = target_size
        h, w = image.shape[:2]

        block_h = max(1, h // target_h)
        block_w = max(1, w // target_w)

        result = np.zeros((target_h, target_w), dtype=np.float32)

        for i in range(target_h):
            for j in range(target_w):
                y_start = i * block_h
                y_end = min((i + 1) * block_h, h)
                x_start = j * block_w
                x_end = min((j + 1) * block_w, w)

                block = image[y_start:y_end, x_start:x_end]
                if block.size > 0:
                    result[i, j] = block.mean()

        return result

    def properties_changed(self, before: Optional[dict], after: Optional[dict]) -> dict:
        """
        Detect which properties changed between two extractions.
        """
        if before is None or after is None:
            return {}

        changes = {}

        for key in ['dominant_color', 'shape_signature', 'orientation']:
            old_val = before.get(key)
            new_val = after.get(key)

            if old_val != new_val:
                changes[key] = {'from': old_val, 'to': new_val}

        return changes

    def signature_distance(self, sig1: str, sig2: str) -> int:
        """Hamming distance between two shape signatures."""
        if len(sig1) != len(sig2):
            return 64
        return sum(c1 != c2 for c1, c2 in zip(sig1, sig2))

    def colors_same(self, color1, color2) -> bool:
        """Check if two colors are the same (handles int or hex)."""
        return color1 == color2


def properties_to_json(props: Optional[dict]) -> Optional[str]:
    """Convert properties dict to JSON string for database storage."""
    if props is None:
        return None

    import json
    serializable = {
        'dominant_color': props.get('dominant_color'),
        'shape_signature': props.get('shape_signature'),
        'orientation': props.get('orientation'),
        'size': list(props.get('size', (0, 0))),
        'is_symbolic': props.get('is_symbolic', True)
    }
    return json.dumps(serializable)


def properties_from_json(json_str: Optional[str]) -> Optional[dict]:
    """Convert JSON string back to properties dict."""
    if json_str is None:
        return None

    import json
    try:
        data = json.loads(json_str)
        if 'size' in data:
            data['size'] = tuple(data['size'])
        return data
    except (json.JSONDecodeError, TypeError):
        return None
