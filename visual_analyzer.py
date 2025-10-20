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
from typing import List, Tuple, Optional, Dict, Any
from collections import Counter
import random

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """Analyzes game frames to find ACTION6 targets."""

    def __init__(self):
        """Initialize visual analyzer."""
        self.previous_frame = None
        self.clicked_coordinates = set()  # Track coordinates we've already tried
        self.last_action_changed_frame = False  # Did last action change the frame?
        self.consecutive_no_change_count = 0  # How many actions with no frame change?

    def update_frame_change_tracking(self, new_frame: List[List[int]]) -> bool:
        """Track whether the frame changed after an action.
        
        Args:
            new_frame: Frame after action was taken
            
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
        
        if changed:
            self.consecutive_no_change_count = 0
            logger.debug("Frame changed - action was productive!")
        else:
            self.consecutive_no_change_count += 1
            logger.debug(f"Frame unchanged ({self.consecutive_no_change_count} consecutive)")
        
        # Update previous frame
        self.previous_frame = [row[:] for row in new_frame]
        
        return changed
    
    def mark_coordinate_clicked(self, x: int, y: int):
        """Mark a coordinate as already clicked.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.clicked_coordinates.add((x, y))
        logger.debug(f"Marked ({x}, {y}) as clicked. Total clicked: {len(self.clicked_coordinates)}")
    
    def reset_clicked_coordinates(self):
        """Reset clicked coordinates (e.g., when starting new game)."""
        self.clicked_coordinates.clear()
        logger.debug("Cleared clicked coordinates")

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

                targets.append({
                    "x": avg_x,
                    "y": avg_y,
                    "type": "rare_color",
                    "color": color,
                    "count": len(positions),
                    "priority": 0.9,  # High priority - rare colors are interesting
                    "reason": f"Rare color {color} ({len(positions)} pixels)"
                })

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

        # Find background color
        all_colors = []
        for row in frame:
            all_colors.extend(row)
        color_counts = Counter(all_colors)
        background = color_counts.most_common(1)[0][0]

        # For each non-background color, find its clusters
        for color in color_counts.keys():
            if color == background:
                continue

            # Find all positions of this color
            positions = []
            for y in range(height):
                for x in range(width):
                    if frame[y][x] == color:
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
                            min_distance: int = 5) -> List[Dict[str, Any]]:
        """Remove duplicate targets that are too close together.

        Args:
            targets: List of target dictionaries
            min_distance: Minimum distance between targets

        Returns:
            Deduplicated and sorted targets
        """
        if not targets:
            return []

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

    def select_best_target(self, analysis: Dict[str, Any]) -> Optional[Tuple[int, int, str]]:
        """Select the best target from analysis, avoiding already-clicked coordinates.

        Args:
            analysis: Analysis results from analyze_frame

        Returns:
            Tuple of (x, y, reason) or None if no targets
        """
        targets = analysis.get("targets", [])

        if not targets:
            return None

        # Filter out already-clicked coordinates
        unclicked_targets = [
            t for t in targets 
            if (t["x"], t["y"]) not in self.clicked_coordinates
        ]
        
        # If we have unclicked targets, prefer those
        if unclicked_targets:
            best_target = unclicked_targets[0]
            logger.debug(f"Selected unclicked target: ({best_target['x']}, {best_target['y']})")
            return (best_target["x"], best_target["y"], best_target["reason"])
        
        # If all targets clicked, reset and try again (frame might have changed)
        if self.consecutive_no_change_count > 10:
            logger.info("All targets clicked and no frame changes - resetting clicked coordinates")
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

    def get_exploratory_coordinates(self, frame: List[List[int]],
                                   center_x: int = None,
                                   center_y: int = None,
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
