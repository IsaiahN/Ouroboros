import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Visual Frame Analyzer

Analyzes ARC game frames to identify interesting targets for ACTION6.
Finds salient features like:
- Unique colors (rare colors standing out)
- Color clusters (groups of same-colored pixels = objects)
- Changed regions (things that moved)
- Isolated pixels (potential buttons/targets)
"""

import logging
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """Analyzes game frames to find ACTION6 targets."""

    def __init__(self):
        """Initialize visual analyzer."""
        self.previous_frame = None
        self.clicked_coordinates = set()  # Track coordinates we've already tried
        self.last_action_changed_frame = False  # Did last action change the frame?
        self.consecutive_no_change_count = 0  # How many actions with no frame change?
        self.grid_exploration_index = 0  # For systematic grid walking

        # Agent mode tracking (for mode-specific behavior)
        self.current_agent_mode = None  # 'pioneer', 'optimizer', 'generalist', or None

        # CRITICAL FIX: Priority targeting from reasoning system (Q3)
        # When the agent learns "color 11 worked before", this tells the visual_analyzer
        # to prioritize that color instead of cycling through random rare colors
        self.priority_color: Optional[int] = None  # Color that worked before
        self.priority_color_reason: str = ""  # Why this color is prioritized
        self.colors_that_worked: Dict[int, int] = {}  # color -> success_count (persistent learning)

        # Adaptive exploration parameters
        self.exploration_radius = 8  # Start with broader exploration
        self.min_exploration_radius = 6  # Was 3 - too restrictive, trapped agents in local regions
        self.max_exploration_radius = 20
        self._expansion_step = 2  # Accelerates: +2, +3, +4, +5... (urgency increases when stuck)
        self.stagnation_threshold = 8  # Actions without improvement to trigger expansion
        self.improvement_threshold = 5  # Actions with improvement to trigger contraction
        self.recent_scores = []  # Track recent scores to detect stagnation
        self.actions_since_improvement = 0
        self.actions_since_decline = 0

        # Pattern oscillation detection
        self.recent_targets = []  # Track all targets during game
        # Full game memory - keep all targets (was 10 goldfish window)
        self.max_target_history = 20000
        self.oscillation_detected = False
        self.total_actions_this_game = 0  # Track actions for early-game contraction protection
        self.map_coverage_percent = 0.0  # Estimated map coverage for radius decisions

    def set_priority_color(self, color: int, reason: str = "learned from previous success"):
        """Set a priority color to target based on what worked before.

        Called by reasoning system when Q3 identifies a successful color.
        This breaks the random rare-color cycling.

        Args:
            color: The color value that should be prioritized
            reason: Why this color is prioritized (for logging)
        """
        self.priority_color = color
        self.priority_color_reason = reason
        logger.info(f"[PRIORITY] Visual analyzer will prioritize color {color}: {reason}")

    def record_color_success(self, color: int):
        """Record that clicking on a color led to success (level advance, score increase).

        Builds persistent memory of what colors work across levels.

        Args:
            color: The color that was clicked when success occurred
        """
        self.colors_that_worked[color] = self.colors_that_worked.get(color, 0) + 1
        # Auto-set as priority if it worked multiple times
        if self.colors_that_worked[color] >= 2:
            self.set_priority_color(color, f"worked {self.colors_that_worked[color]} times")
        logger.info(f"[SUCCESS] Color {color} worked! (count: {self.colors_that_worked[color]})")

    def clear_priority_on_new_game(self):
        """Clear priority and reset action counter when starting a new game (but keep colors_that_worked)."""
        self.priority_color = None
        self.priority_color_reason = ""
        self.total_actions_this_game = 0  # Reset for early-game contraction protection
        self.map_coverage_percent = 0.0  # Reset coverage estimate

    def get_effective_radius(self, purpose: str = "deduplication") -> int:
        """Get radius based on agent mode, game phase, and purpose.

        Different purposes need different radii:
        - 'deduplication': Used to filter out nearby duplicate targets (can be smaller)
        - 'selection': Used to prioritize distant targets (should be larger)
        - 'generation': Used for target generation (should be largest)

        Args:
            purpose: What the radius will be used for

        Returns:
            Effective radius for the given purpose
        """
        base_radius = self.exploration_radius

        # PIONEER MODE: Always use expanded radius for maximum exploration
        if self.current_agent_mode == 'pioneer':
            if purpose == 'generation':
                return max(base_radius, 15)  # Very broad target generation
            elif purpose == 'selection':
                return max(base_radius, 12)  # Prefer distant targets
            else:  # deduplication
                return max(base_radius, 10)  # Minimal deduplication

        # EARLY GAME (first 50 actions): Force broad exploration
        if self.total_actions_this_game < 50:
            if purpose == 'generation':
                return max(base_radius, 12)
            elif purpose == 'selection':
                return max(base_radius, 10)
            else:  # deduplication
                return max(base_radius, 8)

        # LOW COVERAGE: If we haven't explored much, stay broad
        if self.map_coverage_percent < 30:
            if purpose == 'generation':
                return max(base_radius, 10)
            elif purpose == 'selection':
                return max(base_radius, 8)
            else:  # deduplication
                return base_radius

        # OPTIMIZER/GENERALIST with good coverage: Can use tighter radius
        if self.current_agent_mode in ('optimizer', 'generalist'):
            # These modes are refining, not exploring - allow contraction
            return base_radius

        # DEFAULT: Use base radius
        return base_radius

    def update_coverage_estimate(self, clicked_count: int, frame_width: int, frame_height: int):
        """Update estimated map coverage based on clicked coordinates.

        Args:
            clicked_count: Number of unique coordinates clicked
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
        """
        total_cells = frame_width * frame_height
        if total_cells > 0:
            # Each click "covers" roughly a radius-sized area
            covered_area = clicked_count * (self.exploration_radius ** 2) * 3.14
            self.map_coverage_percent = min(100, (covered_area / total_cells) * 100)
            logger.debug(f"Map coverage estimate: {self.map_coverage_percent:.1f}%")

    def update_frame_change_tracking(self, new_frame: List[List[int]], current_score: Optional[float] = None) -> bool:
        """Track whether the frame changed after an action.

        Args:
            new_frame: Frame after action was taken
            current_score: Current game score (if available) to track improvement

        Returns:
            True if frame changed, False otherwise
        """
        if self.previous_frame is None:
            self.previous_frame = [row[:] for row in new_frame] if new_frame else None
            self.last_action_changed_frame = False
            return False

        # Compare frames
        changed = False
        if len(new_frame) != len(self.previous_frame):
            changed = True
        else:
            for i, row in enumerate(new_frame):
                if row != self.previous_frame[i]:
                    changed = True
                    break

        self.last_action_changed_frame = changed

        # Track score changes for adaptive exploration
        if current_score is not None:
            self._update_score_tracking(current_score)

        if changed:
            self.consecutive_no_change_count = 0
            self.actions_since_decline = 0
            logger.debug("Frame changed - action was productive!")
        else:
            self.consecutive_no_change_count += 1
            self.actions_since_decline += 1
            logger.debug(f"Frame unchanged ({self.consecutive_no_change_count} consecutive)")

        # Track total actions for early-game protection
        self.total_actions_this_game += 1

        # Track total actions for early-game protection
        self.total_actions_this_game += 1

        # Adapt exploration based on stagnation
        self._adapt_exploration_radius()

        # Update previous frame
        self.previous_frame = [row[:] for row in new_frame]

        return changed

    def _update_score_tracking(self, current_score: float):
        """Track recent scores to detect improvement or stagnation.

        Args:
            current_score: Current game score
        """
        self.recent_scores.append(current_score)

        # Full game memory - keep all scores (was 10 goldfish window)
        # Safety cap at 20000 for pathological cases only
        if len(self.recent_scores) > 20000:
            self.recent_scores.pop(0)

        # Check if score improved
        if len(self.recent_scores) >= 2:
            if current_score > self.recent_scores[-2]:
                self.actions_since_improvement = 0
                logger.debug(f"Score improved to {current_score}")
            else:
                self.actions_since_improvement += 1

    def _adapt_exploration_radius(self):
        """Adapt exploration radius based on stagnation/improvement.

        When stuck (no changes, no improvement): EXPAND exploration
        When improving: CONTRACT to exploit current strategy
        """
        # Expand if stagnating - ACCELERATING expansion (urgency increases the longer stuck)
        # Sequence: 5 -> 7 (+2) -> 10 (+3) -> 14 (+4) -> 19 (+5) -> 20 (max in 5 triggers)
        if self.actions_since_decline >= self.stagnation_threshold:
            old_radius = self.exploration_radius
            self.exploration_radius = min(
                self.exploration_radius + self._expansion_step,
                self.max_exploration_radius
            )
            if old_radius != self.exploration_radius:
                logger.info(f"Stagnation detected - expanding exploration radius: {old_radius} -> {self.exploration_radius} (+{self._expansion_step})")
                # Reset clicked coordinates to explore new areas
                self.reset_clicked_coordinates()
                self.actions_since_decline = 0
                # Accelerate next expansion (more urgent the longer stuck)
                self._expansion_step = min(self._expansion_step + 1, 10)

        # Contract if improving - also reset expansion step (no longer desperate)
        # PROTECTIONS against premature contraction:
        # 1. PIONEER EXEMPTION: Pioneers need maximum exploration freedom
        # 2. EARLY GAME PROTECTION: First 50 actions need broad discovery
        # 3. Only contract if actually improving (score increase, not just frame change)
        elif self.actions_since_improvement == 0 and self.exploration_radius > self.min_exploration_radius:
            if self.current_agent_mode == 'pioneer':
                # Pioneers don't contract - they need maximum exploration freedom
                # Just reset the expansion urgency since we're making some progress
                self._expansion_step = 2
            elif self.total_actions_this_game < 50:
                # Early game - don't contract, need broad discovery first
                # Just reset expansion urgency
                self._expansion_step = 2
                logger.debug(f"Early game ({self.total_actions_this_game} actions) - skipping contraction")
            else:
                old_radius = self.exploration_radius
                self.exploration_radius = max(
                    self.exploration_radius - 1,
                    self.min_exploration_radius
                )
                if old_radius != self.exploration_radius:
                    logger.info(f"Improvement detected - contracting exploration radius: {old_radius} -> {self.exploration_radius}")
                    # Reset expansion urgency since we're making progress
                    self._expansion_step = 2

    def mark_coordinate_clicked(self, x: int, y: int, frame_changed: bool = False):
        """Mark a coordinate as already clicked.

        NOTE: dead_coordinates system was REMOVED (2026-02-08).
        ARC games require re-clicking coordinates (toggles, state cycling,
        level transitions change meaning). The frame_changed signal is also
        unreliable for ACTION6-only games (frame hash comparison misses
        game state changes). The dead list was filtering out winning
        coordinates, preventing any wins across 5000+ generations.

        Args:
            x: X coordinate
            y: Y coordinate
            frame_changed: Whether clicking this coordinate changed the frame
        """
        self.clicked_coordinates.add((x, y))

        # Track target history for oscillation detection
        self.recent_targets.append((x, y))
        if len(self.recent_targets) > self.max_target_history:
            self.recent_targets.pop(0)

        # Detect oscillation (clicking same few coordinates repeatedly)
        self._detect_oscillation()

        logger.debug(f"Marked ({x}, {y}) as clicked. Total clicked: {len(self.clicked_coordinates)}")

    def set_agent_mode(self, mode: Optional[str]):
        """Set the current agent operating mode for mode-specific behavior.

        Args:
            mode: Agent operating mode ('pioneer', 'optimizer', 'generalist', or None)
        """
        self.current_agent_mode = mode
        logger.debug(f"VisualAnalyzer agent mode set to: {mode}")

    def _detect_oscillation(self):
        """Detect if we're oscillating between the same targets.

        If we're repeatedly clicking the same small set of coordinates,
        expand exploration to break the pattern.

        **PIONEER MODE EXEMPTION**: PIONEER agents are exempt from oscillation
        detection - they need maximum freedom to explore and discover.
        """
        # PIONEER EXEMPTION: No oscillation detection for pioneers
        if self.current_agent_mode == 'pioneer':
            return

        if len(self.recent_targets) < self.max_target_history:
            return

        # Count unique coordinates in recent history
        unique_recent = len(set(self.recent_targets))

        # If only hitting 2-3 coordinates repeatedly, we're oscillating
        if unique_recent <= 3:
            if not self.oscillation_detected:
                logger.warning(f"Oscillation detected! Only {unique_recent} unique targets in last {self.max_target_history} actions")
                logger.warning(f"Recent targets: {self.recent_targets[-5:]}")
                self.oscillation_detected = True

                # Force expansion to break oscillation
                old_radius = self.exploration_radius
                self.exploration_radius = min(
                    self.exploration_radius + 5,  # Bigger jump to break pattern
                    self.max_exploration_radius
                )
                logger.info(f"Breaking oscillation - expanding radius: {old_radius} → {self.exploration_radius}")

                # Clear clicked coordinates to force new exploration
                self.reset_clicked_coordinates()
        else:
            self.oscillation_detected = False

    def reset_clicked_coordinates(self):
        """Reset clicked coordinates (e.g., when starting new game)."""
        self.clicked_coordinates.clear()
        self.grid_exploration_index = 0
        logger.debug("Cleared clicked coordinates")

    # =========================================================================
    # PUBLIC INTERFACE METHODS (Used by Decision Rungs)
    # =========================================================================

    def get_priority_targets(
        self,
        frame: Optional[List[List[int]]]
    ) -> List[Dict[str, Any]]:
        """
        Get prioritized click targets from frame analysis.

        This is the public interface for VisualAnalyzerRung.

        Args:
            frame: Current game frame (64x64 grid)

        Returns:
            List of dicts with 'x', 'y', 'confidence', 'reason'
        """
        if not frame:
            return []

        # Use existing analyze_frame and extract targets
        analysis = self.analyze_frame(frame)
        targets = analysis.get('targets', [])

        # Convert internal priority to confidence if needed
        result = []
        for t in targets:
            result.append({
                'x': t.get('x', 0),
                'y': t.get('y', 0),
                'confidence': t.get('priority', 0.5),
                'reason': t.get('reason', 'visual target'),
                'type': t.get('type', 'unknown'),
                'color': t.get('color', 0)
            })

        return result

    def get_grid_exploration_targets(self) -> List[Dict[str, Any]]:
        """
        Get systematic grid walk targets when stuck.

        This is the public interface for GridExplorationRung.

        Returns:
            List of dicts with 'x', 'y', 'grid_index'
        """
        # Generate grid targets using the previous frame if available
        frame = self.previous_frame
        if not frame:
            # If no frame available, generate a default 64x64 grid walk
            targets = []
            grid_step = 8
            for y in range(grid_step // 2, 64, grid_step):
                for x in range(grid_step // 2, 64, grid_step):
                    coord = (x, y)
                    if coord not in self.clicked_coordinates:
                            targets.append({
                                'x': x,
                                'y': y,
                                'grid_index': self.grid_exploration_index
                            })
            # Rotate through grid
            start_idx = self.grid_exploration_index % max(1, len(targets))
            self.grid_exploration_index += 5
            return targets[start_idx:start_idx + 5] if targets else []

        # Use internal generator with current frame
        raw_targets = self._generate_grid_exploration_targets(frame)

        # Convert to expected format
        result = []
        for t in raw_targets:
            result.append({
                'x': t.get('x', 0),
                'y': t.get('y', 0),
                'grid_index': self.grid_exploration_index
            })

        return result

    def analyze_frame(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Analyze a frame for interesting features.

        The frame is always a 64x64 grid from the ARC API.
        Frame is already unwrapped by GameState.from_dict() in arc_api_client.py

        Args:
            frame: Frame data (unwrapped 64x64 grid)

        Returns:
            Analysis results with potential targets
        """
        if not frame:
            return {"targets": [], "analysis": "Empty frame"}

        if not isinstance(frame, list):
            return {"targets": [], "analysis": "Invalid frame structure"}

        # Frame should already be unwrapped to 64x64 grid
        height = len(frame)
        if height == 0:
            return {"targets": [], "analysis": "Empty frame"}

        # Get width from first row
        width = len(frame[0]) if isinstance(frame[0], list) else 0
        if width == 0:
            return {"targets": [], "analysis": "Empty frame rows"}

        # Debug: Log frame dimensions
        logger.debug(f"Frame dimensions: {height}x{width}")

        analysis = {
            "width": width,
            "height": height,
            "targets": [],
            "features": {}
        }

        # 1. Find unique/rare colors (objects that stand out)
        color_targets = self._find_color_anomalies(frame)
        if color_targets:
            analysis["targets"].extend(color_targets)
            analysis["features"]["color_anomalies"] = len(color_targets)

        # 2. Find color clusters (groups of same color = objects)
        cluster_targets = self._find_color_clusters(frame)
        if cluster_targets:
            analysis["targets"].extend(cluster_targets)
            analysis["features"]["clusters"] = len(cluster_targets)

        # 3. Find changed regions (if we have previous frame)
        if self.previous_frame is not None:
            changed_targets = self._find_frame_changes(self.previous_frame, frame)
            if changed_targets:
                analysis["targets"].extend(changed_targets)
                analysis["features"]["changed_regions"] = len(changed_targets)

        # 4. Add grid-walking targets when stuck (systematic exploration)
        # This ensures we explore beyond just the 3 rare color targets
        if self.consecutive_no_change_count >= 10:
            grid_targets = self._generate_grid_exploration_targets(frame)
            if grid_targets:
                analysis["targets"].extend(grid_targets)
                analysis["features"]["grid_exploration"] = len(grid_targets)

        # Deduplicate and sort targets by priority
        analysis["targets"] = self._deduplicate_targets(analysis["targets"])

        # Store frame for next comparison
        self.previous_frame = [row[:] for row in frame]  # Deep copy

        return analysis

    def _find_color_anomalies(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """Find pixels with rare colors that stand out.

        Args:
            frame: 2D grid

        Returns:
            List of target dictionaries
        """
        targets = []
        height = len(frame)
        width = len(frame[0])

        # Count all colors
        color_positions = {}  # color -> list of (x, y)
        for y in range(height):
            for x in range(width):
                color = frame[y][x]
                # Handle case where color might be a list (convert to hashable tuple)
                if isinstance(color, list):
                    color = tuple(color) if color else 0
                elif not isinstance(color, (int, float, str, tuple)):
                    color = 0  # Fallback to background

                if color not in color_positions:
                    color_positions[color] = []
                color_positions[color].append((x, y))

        # Find background (most common color)
        background_color = max(color_positions.keys(), key=lambda c: len(color_positions[c]))
        total_pixels = height * width

        # Find rare colors (< 5% of frame)
        rare_threshold = total_pixels * 0.05

        for color, positions in color_positions.items():
            if color != background_color and len(positions) < rare_threshold and len(positions) > 0:
                # Calculate centroid of all pixels with this color
                avg_x = sum(pos[0] for pos in positions) // len(positions)
                avg_y = sum(pos[1] for pos in positions) // len(positions)

                # Clamp to frame bounds
                avg_x = max(0, min(width - 1, avg_x))
                avg_y = max(0, min(height - 1, avg_y))

                # CRITICAL FIX: Priority boost for colors that worked before
                base_priority = 0.9  # High priority - rare colors are interesting

                # Boost priority for priority_color (from Q3 reasoning)
                if self.priority_color is not None and color == self.priority_color:
                    base_priority = 1.5  # Much higher - we KNOW this works!
                    logger.info(f"[PRIORITY] Boosting color {color} (learned: {self.priority_color_reason})")

                # Boost priority for colors with success history
                elif color in self.colors_that_worked:
                    success_count = self.colors_that_worked[color]
                    base_priority = 0.9 + (0.1 * min(success_count, 5))  # Up to 1.4 priority
                    logger.debug(f"[LEARNED] Color {color} has {success_count} successes, priority={base_priority:.2f}")

                targets.append({
                    "x": avg_x,
                    "y": avg_y,
                    "type": "rare_color",
                    "color": color,
                    "count": len(positions),
                    "priority": base_priority,
                    "reason": f"Rare color {color} ({len(positions)} pixels)"
                })

        return targets

    def _generate_grid_exploration_targets(self, frame: List[List[int]], grid_step: int = 8) -> List[Dict[str, Any]]:
        """Generate systematic grid-walking targets for exploration.

        When stuck with only 3 rare-color targets that don't work,
        this generates additional targets by walking a grid across the frame.
        This ensures the agent tries clicking on different areas, not just
        the same 3 rare-color centroids.

        Args:
            frame: Current frame
            grid_step: Step size for grid (smaller = more targets)

        Returns:
            List of grid exploration targets
        """
        targets = []
        height = len(frame) if frame else 64
        width = len(frame[0]) if frame and frame[0] else 64

        # Generate grid points, skipping already-dead coordinates
        grid_points = []
        for y in range(grid_step // 2, height, grid_step):
            for x in range(grid_step // 2, width, grid_step):
                coord = (x, y)
                grid_points.append(coord)

        # Start from where we left off (rotating through grid)
        num_points = len(grid_points)
        if num_points == 0:
            return targets  # No grid points available

        # Get next few grid points to try (rotate through them)
        start_idx = self.grid_exploration_index % num_points
        points_to_try = []
        for i in range(min(5, num_points)):  # Add up to 5 grid targets
            idx = (start_idx + i) % num_points
            points_to_try.append(grid_points[idx])

        self.grid_exploration_index += 5  # Advance for next time

        # Create targets from grid points
        for x, y in points_to_try:
            # Skip if already clicked this session
            if (x, y) in self.clicked_coordinates:
                continue

            # Get the color at this grid point for context
            try:
                color = frame[y][x] if isinstance(frame[y][x], int) else 0
            except (IndexError, TypeError):
                color = 0

            targets.append({
                "x": x,
                "y": y,
                "type": "grid_exploration",
                "color": color,
                "priority": 0.6,  # Lower than rare colors but still useful
                "reason": f"Grid exploration ({x},{y}) - systematic search"
            })

        if targets:
            logger.info(f"[GRID] Generated {len(targets)} grid exploration targets (index={self.grid_exploration_index})")

        return targets

    def _find_color_clusters(self, frame: List[List[int]]) -> List[Dict[str, Any]]:
        """Find clusters of same-colored pixels (objects).

        Args:
            frame: 2D grid

        Returns:
            List of target dictionaries
        """
        targets = []
        height = len(frame)
        width = len(frame[0])

        # Find background color - handle nested lists
        all_colors = []
        for row in frame:
            for cell in row:
                # Handle case where cell might be a list
                if isinstance(cell, list):
                    # If it's a list, take the first element (shouldn't happen but defensive)
                    all_colors.append(cell[0] if cell else 0)
                else:
                    all_colors.append(cell)

        color_counts = Counter(all_colors)
        background = color_counts.most_common(1)[0][0] if color_counts else 0

        # For each non-background color, find its clusters
        for color in color_counts.keys():
            if color == background:
                continue

            # Find all positions of this color
            positions = []
            for y in range(height):
                for x in range(width):
                    cell_value = frame[y][x]
                    # Handle nested lists
                    if isinstance(cell_value, list):
                        cell_value = cell_value[0] if cell_value else 0

                    if cell_value == color:
                        positions.append((x, y))

            if len(positions) >= 3:  # At least 3 pixels to be interesting
                # Calculate centroid
                avg_x = sum(p[0] for p in positions) // len(positions)
                avg_y = sum(p[1] for p in positions) // len(positions)

                # Clamp to actual frame bounds
                avg_x = max(0, min(width - 1, avg_x))
                avg_y = max(0, min(height - 1, avg_y))

                # Calculate how "tight" the cluster is
                total_dist = sum(abs(p[0] - avg_x) + abs(p[1] - avg_y) for p in positions)
                avg_dist = total_dist / len(positions)

                # Tighter clusters (objects) are more interesting
                tightness = max(0.1, 1.0 - (avg_dist / max(width, height)))

                targets.append({
                    "x": avg_x,
                    "y": avg_y,
                    "type": "cluster",
                    "color": color,
                    "size": len(positions),
                    "tightness": tightness,
                    "priority": 0.7 + tightness * 0.2,  # Tighter = higher priority
                    "reason": f"Cluster of {len(positions)} pixels (color={color})"
                })

        return targets

    def _find_frame_changes(self, old_frame: List[List[int]],
                           new_frame: List[List[int]]) -> List[Dict[str, Any]]:
        """Find regions that changed between frames (things that moved).

        Args:
            old_frame: Previous frame
            new_frame: Current frame

        Returns:
            List of target dictionaries
        """
        targets = []

        if len(old_frame) != len(new_frame) or len(old_frame[0]) != len(new_frame[0]):
            return targets

        height = len(new_frame)
        width = len(new_frame[0])

        # Find all changed pixels
        changed_positions = []
        for y in range(height):
            for x in range(width):
                if old_frame[y][x] != new_frame[y][x]:
                    changed_positions.append((x, y))

        if len(changed_positions) > 0:
            # Calculate centroid of changed region
            avg_x = sum(p[0] for p in changed_positions) // len(changed_positions)
            avg_y = sum(p[1] for p in changed_positions) // len(changed_positions)

            # Clamp to frame bounds
            avg_x = max(0, min(width - 1, avg_x))
            avg_y = max(0, min(height - 1, avg_y))

            targets.append({
                "x": avg_x,
                "y": avg_y,
                "type": "frame_change",
                "num_changes": len(changed_positions),
                "priority": 0.95,  # Very high priority - things that moved are interactive!
                "reason": f"Region changed ({len(changed_positions)} pixels) - something moved!"
            })

        return targets

    def _deduplicate_targets(self, targets: List[Dict[str, Any]],
                            min_distance: Optional[int] = None) -> List[Dict[str, Any]]:
        """Remove duplicate targets that are too close together.

        Uses get_effective_radius() for mode-specific deduplication that
        preserves more targets for pioneers and early-game exploration.

        Args:
            targets: List of target dictionaries
            min_distance: Minimum distance between targets (uses get_effective_radius if None)

        Returns:
            Deduplicated and sorted targets
        """
        if not targets:
            return []

        # Use mode-aware effective radius for deduplication
        # This is intentionally less aggressive than raw exploration_radius
        if min_distance is None:
            min_distance = self.get_effective_radius(purpose='deduplication')

        # Sort by priority (highest first)
        sorted_targets = sorted(targets, key=lambda t: t["priority"], reverse=True)

        # Keep targets that are far enough apart
        unique_targets = []
        for target in sorted_targets:
            x, y = target["x"], target["y"]

            # Check distance to all kept targets
            too_close = False
            for kept in unique_targets:
                dx = abs(x - kept["x"])
                dy = abs(y - kept["y"])
                distance = (dx**2 + dy**2) ** 0.5

                if distance < min_distance:
                    too_close = True
                    break

            if not too_close:
                unique_targets.append(target)

        return unique_targets

    def select_best_target(self, analysis: Dict[str, Any],
                           agent_position: Optional[Tuple[int, int]] = None) -> Optional[Tuple[int, int, str]]:
        """Select the best target from analysis, avoiding already-clicked coordinates.

        Uses mode-specific radius and prioritizes distant targets for exploration.
        DECOUPLED from deduplication - selection considers exploration needs separately.

        Args:
            analysis: Analysis results from analyze_frame
            agent_position: Current agent position (x, y) for distance calculations

        Returns:
            Tuple of (x, y, reason) or None if no targets
        """
        targets = analysis.get("targets", [])

        if not targets:
            return None

        # Update coverage estimate
        frame_width = analysis.get("width", 64)
        frame_height = analysis.get("height", 64)
        self.update_coverage_estimate(len(self.clicked_coordinates), frame_width, frame_height)

        # Filter out already-clicked coordinates
        unclicked_targets = [
            t for t in targets
            if (t["x"], t["y"]) not in self.clicked_coordinates
        ]

        # If oscillating, try to find targets between previous clicks
        if self.oscillation_detected and len(self.recent_targets) >= 2:
            combination_target = self._find_combination_target(targets)
            if combination_target:
                logger.info(f"Oscillation detected - trying combination point: {combination_target}")
                return combination_target

        # DECOUPLED TARGET SELECTION: Prioritize based on exploration needs
        if unclicked_targets:
            selection_radius = self.get_effective_radius(purpose='selection')

            # For PIONEERS or early game: Prefer DISTANT targets to maximize exploration
            if self.current_agent_mode == 'pioneer' or self.total_actions_this_game < 50:
                distant_targets = self._sort_by_exploration_value(
                    unclicked_targets, agent_position, selection_radius
                )
                if distant_targets:
                    best_target = distant_targets[0]
                    logger.debug(f"Selected exploration target: ({best_target['x']}, {best_target['y']}) "
                               f"[mode={self.current_agent_mode}, radius={selection_radius}]")
                    return (best_target["x"], best_target["y"], best_target["reason"])

            # For OPTIMIZERS: Prefer high-priority (known good) targets
            best_target = unclicked_targets[0]
            logger.debug(f"Selected unclicked target: ({best_target['x']}, {best_target['y']}) [radius={self.exploration_radius}]")
            return (best_target["x"], best_target["y"], best_target["reason"])

        # If all targets clicked and stagnating, force expansion
        if self.consecutive_no_change_count > 10:
            logger.info("All targets clicked and no frame changes - forcing exploration expansion")
            self.exploration_radius = min(
                self.exploration_radius + 3,
                self.max_exploration_radius
            )
            self.reset_clicked_coordinates()
            if targets:
                best_target = targets[0]
                return (best_target["x"], best_target["y"], best_target["reason"])

        # Fallback: use best target even if clicked
        if targets:
            best_target = targets[0]
            logger.debug(f"Using already-clicked target: ({best_target['x']}, {best_target['y']})")
            return (best_target["x"], best_target["y"], best_target["reason"])

        return None

    def _sort_by_exploration_value(self, targets: List[Dict[str, Any]],
                                    agent_position: Optional[Tuple[int, int]],
                                    selection_radius: int) -> List[Dict[str, Any]]:
        """Sort targets by exploration value - prioritize distant, unexplored areas.

        DECOUPLED from deduplication: This method decides which targets are best
        for exploration, independent of how close targets are to each other.

        Exploration value considers:
        1. Distance from agent position (farther = better for exploration)
        2. Distance from recently clicked areas (farther = less explored)
        3. Target priority (still matters, but weighted less)

        Args:
            targets: List of target dictionaries
            agent_position: Current agent position (x, y), or None
            selection_radius: Radius threshold for "distant" classification

        Returns:
            Targets sorted by exploration value (best first)
        """
        if not targets:
            return []

        def exploration_score(target: Dict[str, Any]) -> float:
            x, y = target["x"], target["y"]
            base_priority = target.get("priority", 0.5)

            # Distance from agent (if known)
            agent_distance_score = 0.0
            if agent_position:
                dx = abs(x - agent_position[0])
                dy = abs(y - agent_position[1])
                agent_distance = (dx**2 + dy**2) ** 0.5
                # Normalize: targets beyond selection_radius get bonus
                if agent_distance > selection_radius:
                    agent_distance_score = min(1.0, agent_distance / 50.0)  # Cap at 50 pixels

            # Distance from clicked coordinates (avoid re-exploring same areas)
            min_click_distance = float('inf')
            for clicked_x, clicked_y in self.clicked_coordinates:
                dx = abs(x - clicked_x)
                dy = abs(y - clicked_y)
                dist = (dx**2 + dy**2) ** 0.5
                min_click_distance = min(min_click_distance, dist)

            # Normalize click distance (farther from clicks = better)
            if min_click_distance == float('inf'):
                click_distance_score = 1.0  # No clicks yet, all areas equal
            else:
                click_distance_score = min(1.0, min_click_distance / 30.0)

            # Combined score: prioritize exploration over raw priority
            # Weights: 40% distance from agent, 40% distance from clicks, 20% priority
            return (agent_distance_score * 0.4 +
                    click_distance_score * 0.4 +
                    base_priority * 0.2)

        # Sort by exploration score (highest first)
        return sorted(targets, key=exploration_score, reverse=True)

    def _find_combination_target(self, targets: List[Dict[str, Any]]) -> Optional[Tuple[int, int, str]]:
        """Find a target between recent clicks to explore combinations.

        When oscillating between pseudo-buttons, try clicking between them
        or in patterns that might trigger different behavior.

        Args:
            targets: Available targets

        Returns:
            Tuple of (x, y, reason) or None
        """
        if len(self.recent_targets) < 2:
            return None

        # Get last two unique targets
        last_target = self.recent_targets[-1]
        prev_target = self.recent_targets[-2]

        # Skip if they're the same
        if last_target == prev_target:
            return None

        # Try midpoint between oscillating targets
        mid_x = (last_target[0] + prev_target[0]) // 2
        mid_y = (last_target[1] + prev_target[1]) // 2

        # Clamp to frame bounds
        mid_x = max(0, min(63, mid_x))
        mid_y = max(0, min(63, mid_y))

        # Check if we haven't tried this combination yet
        if (mid_x, mid_y) not in self.clicked_coordinates:
            return (mid_x, mid_y, f"Combination point between oscillating targets")

        # Try varied offset points using adaptive radius for spacing
        # Use larger, more varied offsets to truly escape oscillation
        radius = self.exploration_radius
        offsets = [
            (radius, 0),
            (-radius, 0),
            (0, radius),
            (0, -radius),
            (radius, radius),
            (-radius, -radius),
            (radius, -radius),
            (-radius, radius),
            # Additional diagonal and far offsets
            (radius * 2, radius),
            (radius, radius * 2),
            (-radius * 2, -radius),
            (-radius, -radius * 2),
            # Try completely random nearby areas
            (radius + 5, radius + 3),
            (-radius - 5, radius + 3),
            (radius + 3, -radius - 5),
            (-radius - 3, -radius - 5)
        ]

        for dx, dy in offsets:
            test_x = max(0, min(63, mid_x + dx))
            test_y = max(0, min(63, mid_y + dy))

            if (test_x, test_y) not in self.clicked_coordinates:
                return (test_x, test_y, f"Exploration around oscillation pattern (offset={dx},{dy})")

        # If all offsets tried, force a random unexplored coordinate
        import random
        for _ in range(20):  # Try 20 random attempts
            rand_x = random.randint(0, 63)
            rand_y = random.randint(0, 63)
            if (rand_x, rand_y) not in self.clicked_coordinates:
                return (rand_x, rand_y, f"Random exploration to break oscillation deadlock")

        return None

    def get_exploratory_coordinates(self, frame: List[List[int]],
                                   center_x: Optional[int] = None,
                                   center_y: Optional[int] = None,
                                   radius: int = 8) -> Tuple[int, int]:
        """Get coordinates for exploratory search pattern.

        Args:
            frame: Current frame
            center_x: Center X for search (default: middle of frame)
            center_y: Center Y for search (default: middle of frame)
            radius: Search radius

        Returns:
            Tuple of (x, y) for exploration
        """
        if not frame or not frame[0]:
            return (0, 0)

        height = len(frame)
        width = len(frame[0])

        # Use frame center if not specified
        if center_x is None:
            center_x = width // 2
        if center_y is None:
            center_y = height // 2

        # Random offset within radius
        dx = random.randint(-radius, radius)
        dy = random.randint(-radius, radius)

        # Clamp to bounds
        x = max(0, min(width - 1, center_x + dx))
        y = max(0, min(height - 1, center_y + dy))

        return (x, y)
