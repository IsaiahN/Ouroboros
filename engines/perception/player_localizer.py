"""
Player Localizer - Discover which object the agent controls.

Part of Symbolic Reasoning Implementation (Phase 0).

The critical first step: Before an agent can learn about its player's properties,
it must DISCOVER which object/sprite/cell it controls. This is learned, not given.

For ARC games: Frame is a symbolic grid (H, W) with color indices 0-12
For Visual games: Frame is RGB image (H, W, 3) with pixel values 0-255

Method:
    1. Take action in direction (e.g., ACTION1 = "up")
    2. Compare frames before/after
    3. Look for grid cells that changed
    4. If change direction correlates with action direction, that's the player

This is UNSUPERVISED - we don't know what the player looks like.
We only know: "I pressed up, something moved up, that must be me"
"""

from typing import Optional, Tuple

import numpy as np


class PlayerLocalizer:
    """
    Discover and track which object the agent controls.

    Handles both ARC symbolic grids and RGB images.

    Key insight: The agent LEARNS its self-model through action-perception
    correlation. There's no hard-coded "the player is blue" knowledge.

    Usage:
        localizer = PlayerLocalizer()

        # After each action
        result = localizer.localize(
            frame_before=prev_frame,
            frame_after=curr_frame,
            action_taken='ACTION1',
            action_direction='up'  # or None for non-movement actions
        )

        if result['confidence'] > 0.7:
            player_position = result['position']
    """

    # Minimum confidence needed to trust localization
    MIN_CONFIDENCE = 0.5

    # Direction vectors for movement detection (row, col format for grids)
    DIRECTION_VECTORS = {
        'up': (-1, 0),     # Row decreases
        'down': (1, 0),    # Row increases
        'left': (0, -1),   # Column decreases
        'right': (0, 1),   # Column increases
    }

    # Action name to direction mapping
    ACTION_DIRECTIONS = {
        'ACTION1': 'up',
        'ACTION2': 'down',
        'ACTION3': 'left',
        'ACTION4': 'right',
        'ACTION5': None,
        'ACTION6': None,
        'ACTION7': None,
    }

    def __init__(self, confidence_threshold: float = 0.6, history_size: int = 10):
        """
        Args:
            confidence_threshold: Minimum confidence to return a player region.
            history_size: Number of recent localizations to track for smoothing
        """
        self.confidence_threshold = confidence_threshold
        self.history_size = history_size
        self._position_history: list = []
        self._confidence_history: list = []
        self._last_known_position: Optional[Tuple[int, int]] = None
        self._last_player_region: Optional[Tuple[int, int, int, int]] = None
        self._accumulated_confidence: float = 0.0
        self._observations: int = 0

    def localize(
        self,
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        action_taken: str,
        action_direction: Optional[str] = None
    ) -> dict:
        """
        Attempt to localize player by correlating action with movement.

        Args:
            frame_before: Frame before action (numpy array)
            frame_after: Frame after action (numpy array)
            action_taken: Action name (e.g., 'ACTION1')
            action_direction: Direction override ('up', 'down', 'left', 'right', None)

        Returns:
            {
                'position': (row, col) or None,
                'confidence': 0.0 to 1.0,
                'region': player bounding box (r1, c1, r2, c2) or None,
                'method': 'movement_correlation' | 'persistence' | 'none'
            }
        """
        self._observations += 1

        # Ensure frames are proper arrays
        frame_before = self._ensure_2d_grid(frame_before)
        frame_after = self._ensure_2d_grid(frame_after)

        if frame_before is None or frame_after is None:
            return self._no_detection('invalid_frames')

        # Determine direction from action or override
        if action_direction is None:
            action_direction = self.ACTION_DIRECTIONS.get(action_taken)

        # If no directional action, can't use movement correlation
        if action_direction is None or action_direction not in self.DIRECTION_VECTORS:
            return self._use_persistence('no_movement_action')

        # Find cells that changed
        changed_positions = self._find_changed_cells(frame_before, frame_after)

        if len(changed_positions) == 0:
            # No change - maybe blocked or invalid action
            return self._use_persistence('no_change_detected')

        if len(changed_positions) > 100:
            # Too much changed - probably a level transition
            return self._no_detection('level_transition')

        # Analyze movement direction
        result = self._analyze_movement(
            frame_before,
            frame_after,
            changed_positions,
            action_direction
        )

        if result['confidence'] > 0:
            self._update_history(result['position'], result['confidence'])

        return result

    def _ensure_2d_grid(self, frame) -> Optional[np.ndarray]:
        """Convert frame to 2D numpy array."""
        if frame is None:
            return None

        # Convert list to array
        if isinstance(frame, list):
            frame = np.array(frame)

        if not isinstance(frame, np.ndarray):
            return None

        # Handle (1, H, W) shape - squeeze first dimension
        if len(frame.shape) == 3 and frame.shape[0] == 1:
            frame = frame[0]

        # Handle (H, W, C) RGB - convert to single channel
        if len(frame.shape) == 3 and frame.shape[2] in [1, 3, 4]:
            if frame.shape[2] == 1:
                frame = frame[:, :, 0]
            else:
                # Convert RGB to grayscale index (take first channel)
                frame = frame[:, :, 0]

        if len(frame.shape) != 2:
            return None

        return frame

    def _find_changed_cells(
        self,
        before: np.ndarray,
        after: np.ndarray
    ) -> np.ndarray:
        """Find positions where cell values changed."""
        # Handle shape mismatch
        if before.shape != after.shape:
            return np.array([])

        # Find differences
        diff = before != after
        return np.argwhere(diff)

    def _analyze_movement(
        self,
        frame_before: np.ndarray,
        frame_after: np.ndarray,
        changed_positions: np.ndarray,
        expected_direction: str
    ) -> dict:
        """
        Analyze changed cells to find player movement.

        More robust approach for ARC games:
        1. Group changed cells by their before->after color transitions
        2. Find the transition that creates a coherent movement pattern
        3. Track the centroid of that movement

        Handles cases where player leaves a trail (different color behind).
        """
        expected_delta = self.DIRECTION_VECTORS[expected_direction]

        # Group cells by color transition
        transitions = {}  # (before_color, after_color) -> list of positions

        for pos in changed_positions:
            r, c = int(pos[0]), int(pos[1])
            val_before = int(frame_before[r, c])
            val_after = int(frame_after[r, c])

            key = (val_before, val_after)
            if key not in transitions:
                transitions[key] = []
            transitions[key].append((r, c))

        # Method 1: Classic approach - look for cells where specific color left/arrived
        cells_vacated = []  # Had specific value, now something else
        cells_occupied = []  # Was something else, now specific value

        # For each unique "arriving" color, check if there's a matching "departing" set
        for (before_color, after_color), positions in transitions.items():
            # Skip if this is background (0) on either side
            if before_color == 0 or after_color == 0:
                for r, c in positions:
                    if before_color != 0 and after_color == 0:
                        cells_vacated.append((r, c, before_color))
                    elif before_color == 0 and after_color != 0:
                        cells_occupied.append((r, c, after_color))

        # Look for matching movement pattern
        best_match = None
        best_confidence = 0.0

        for vac_r, vac_c, vac_val in cells_vacated:
            for occ_r, occ_c, occ_val in cells_occupied:
                # Check if the values match (same color moved)
                if vac_val != occ_val:
                    continue

                # Check if direction matches expected
                actual_dr = occ_r - vac_r
                actual_dc = occ_c - vac_c

                # Movement should be exactly 1 cell in expected direction
                if (actual_dr, actual_dc) == expected_delta:
                    confidence = 0.9
                elif self._direction_matches(actual_dr, actual_dc, expected_delta):
                    confidence = 0.7
                else:
                    continue

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (occ_r, occ_c)  # New position

        if best_match is not None:
            self._last_player_region = (
                best_match[0], best_match[1],
                best_match[0] + 1, best_match[1] + 1
            )
            return {
                'position': best_match,
                'confidence': best_confidence,
                'region': self._last_player_region,
                'method': 'movement_correlation'
            }

        # Method 2: Centroid-based detection for complex games (like ls20)
        # Find the most common "departing" transition and track its centroid
        if len(transitions) > 0:
            # Find the largest transition group that shows coherent movement
            for (before_color, after_color), positions in sorted(
                transitions.items(), key=lambda x: len(x[1]), reverse=True
            ):
                if len(positions) < 4:  # Need at least 4 cells for a meaningful group
                    continue

                # Calculate centroid of this transition
                rows = [p[0] for p in positions]
                cols = [p[1] for p in positions]
                centroid_r = sum(rows) / len(rows)
                centroid_c = sum(cols) / len(cols)

                # Check if there's a corresponding "arriving" transition
                # that moved in the expected direction
                for (before2, after2), positions2 in transitions.items():
                    if after2 == before_color and len(positions2) >= 4:
                        # This might be where the color came from
                        rows2 = [p[0] for p in positions2]
                        cols2 = [p[1] for p in positions2]
                        centroid2_r = sum(rows2) / len(rows2)
                        centroid2_c = sum(cols2) / len(cols2)

                        # Calculate movement vector
                        dr = centroid_r - centroid2_r
                        dc = centroid_c - centroid2_c

                        # Check if movement matches expected direction
                        if self._direction_matches_approx(dr, dc, expected_delta):
                            # Found coherent movement!
                            # Return centroid of the "arriving" position
                            new_pos = (int(centroid_r), int(centroid_c))
                            self._last_player_region = (
                                new_pos[0], new_pos[1],
                                new_pos[0] + 1, new_pos[1] + 1
                            )
                            return {
                                'position': new_pos,
                                'confidence': 0.6,  # Lower confidence for centroid method
                                'region': self._last_player_region,
                                'method': 'centroid_correlation'
                            }

        # Fallback: If we have persistence, use that
        return self._use_persistence('direction_mismatch')

    def _direction_matches_approx(
        self,
        actual_dr: float,
        actual_dc: float,
        expected: Tuple[int, int],
        tolerance: float = 2.0
    ) -> bool:
        """Check if movement direction approximately matches expected."""
        exp_dr, exp_dc = expected

        # Magnitude must be meaningful
        mag = (actual_dr**2 + actual_dc**2) ** 0.5
        if mag < 0.5:
            return False

        # For vertical movement (up/down)
        if exp_dr != 0 and exp_dc == 0:
            return abs(actual_dc) <= tolerance and (actual_dr * exp_dr > 0)

        # For horizontal movement (left/right)
        if exp_dc != 0 and exp_dr == 0:
            return abs(actual_dr) <= tolerance and (actual_dc * exp_dc > 0)

        return False

    def _direction_matches(
        self,
        actual_dr: int,
        actual_dc: int,
        expected: Tuple[int, int]
    ) -> bool:
        """Check if actual movement direction matches expected (allowing for magnitude differences)."""
        exp_dr, exp_dc = expected

        # Normalize to direction only (ignore magnitude)
        if exp_dr != 0 and exp_dc == 0:
            # Vertical expected
            return actual_dc == 0 and (actual_dr * exp_dr > 0)
        elif exp_dc != 0 and exp_dr == 0:
            # Horizontal expected
            return actual_dr == 0 and (actual_dc * exp_dc > 0)

        return False

    def _update_history(self, position: Tuple[int, int], confidence: float):
        """Update position history for temporal smoothing."""
        self._position_history.append(position)
        self._confidence_history.append(confidence)

        # Trim to history size
        if len(self._position_history) > self.history_size:
            self._position_history = self._position_history[-self.history_size:]
            self._confidence_history = self._confidence_history[-self.history_size:]

        self._last_known_position = position

        # Accumulate confidence (caps at 1.0)
        self._accumulated_confidence = min(1.0, self._accumulated_confidence + confidence * 0.1)

    def _use_persistence(self, reason: str = 'unknown') -> dict:
        """Use last known position when current detection fails."""
        if self._last_known_position is not None:
            pos = self._last_known_position
            # Decay confidence when using persistence
            self._accumulated_confidence *= 0.9
            return {
                'position': pos,
                'confidence': self._accumulated_confidence,
                'region': self._last_player_region,
                'method': f'persistence_{reason}'
            }
        return self._no_detection(reason)

    def _no_detection(self, reason: str = 'unknown') -> dict:
        """Return when no player detected."""
        return {
            'position': None,
            'confidence': 0.0,
            'region': None,
            'method': f'none_{reason}'
        }

    def reset(self):
        """Reset localizer state for new game/level."""
        self._position_history = []
        self._confidence_history = []
        self._last_known_position = None
        self._last_player_region = None
        self._accumulated_confidence = 0.0
        self._observations = 0

    def get_player_region(
        self,
        frame: np.ndarray,
        position: Optional[Tuple[int, int]] = None,
        radius: int = 3,
    ) -> Optional[np.ndarray]:
        """
        Extract player region from frame.

        Args:
            frame: Game frame (2D or 3D).
            position: (x, y) position override. If None, uses internal
                      last_known_position (requires confidence threshold).
            radius: Half-size of extraction window (default 3 → 7x7).

        Returns:
            Cropped 2D array around the player, or None.
        """
        if position is not None:
            px, py = position
        elif self._last_known_position is not None:
            if self._accumulated_confidence < self.confidence_threshold:
                return None
            py, px = self._last_known_position  # internal is (row, col)
        else:
            return None

        frame = self._ensure_2d_grid(frame)
        if frame is None:
            return None

        h, w = frame.shape
        # position is (x, y) but frame is [row, col]
        r, c = py, px
        if not (0 <= r < h and 0 <= c < w):
            return None

        r1 = max(0, r - radius)
        r2 = min(h, r + radius + 1)
        c1 = max(0, c - radius)
        c2 = min(w, c + radius + 1)
        return frame[r1:r2, c1:c2].copy()

    @property
    def is_confident(self) -> bool:
        """True if we have confident player localization."""
        return self._accumulated_confidence >= self.confidence_threshold

    @property
    def confidence(self) -> float:
        """Current localization confidence."""
        return self._accumulated_confidence

    @property
    def last_region(self) -> Optional[Tuple[int, int, int, int]]:
        """Last detected player region bbox, or None."""
        return self._last_player_region


# Action to direction mapping (game-agnostic defaults)
DEFAULT_ACTION_DIRECTIONS = {
    0: 'up',      # ACTION1
    1: 'down',    # ACTION2
    2: 'left',    # ACTION3
    3: 'right',   # ACTION4
    4: None,      # ACTION5 (often interact/fire)
    5: None,      # ACTION6
    6: None,      # ACTION7
}
