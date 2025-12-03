#!/usr/bin/env python3
"""
Object Detector - Phase 1
==========================

Detects and tracks objects in game frames.
Identifies distinct objects, their properties, and persistence across frames.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import uuid
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from database_interface import DatabaseInterface
from abstraction_config import is_abstraction_enabled
import logging

logger = logging.getLogger(__name__)


class ObjectDetector:
    """
    Detects and tracks objects in game frames.
    
    Converts pixel data into object representations for abstraction.
    """
    
    def __init__(self, db_path: str = "core_data.db"):
        """Initialize object detector."""
        self.db = DatabaseInterface(db_path)
        self.enabled = is_abstraction_enabled()
    
    def detect_objects_in_frame(
        self,
        frame: Dict,
        game_id: str,
        level: int,
        frame_index: int
    ) -> List[Dict]:
        """
        Detect distinct objects in a frame.
        
        Args:
            frame: Frame data (grid representation)
            game_id: Game identifier
            level: Level number
            frame_index: Frame index in sequence
        
        Returns:
            List of detected objects with properties
        """
        if not self.enabled or not frame:
            return []
        
        grid = frame.get('grid', [])
        if not grid:
            return []
        
        # Simple object detection: group contiguous same-color cells
        objects = []
        visited = set()
        
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                if (x, y) in visited:
                    continue
                
                color = grid[y][x]
                if color == 0:  # Skip background
                    continue
                
                # Flood fill to find object
                obj_cells = self._flood_fill(grid, x, y, color, visited)
                
                if obj_cells:
                    obj = self._create_object(
                        obj_cells, color, game_id, level, frame_index
                    )
                    objects.append(obj)
        
        return objects
    
    def _flood_fill(
        self,
        grid: List[List],
        x: int,
        y: int,
        color: int,
        visited: set
    ) -> List[Tuple[int, int]]:
        """
        Flood fill to find connected cells of same color.
        
        Returns list of (x, y) coordinates.
        """
        if x < 0 or x >= len(grid[0]) or y < 0 or y >= len(grid):
            return []
        
        if (x, y) in visited or grid[y][x] != color:
            return []
        
        visited.add((x, y))
        cells = [(x, y)]
        
        # Check 4 neighbors (up, down, left, right)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            cells.extend(self._flood_fill(grid, x + dx, y + dy, color, visited))
        
        return cells
    
    def _create_object(
        self,
        cells: List[Tuple[int, int]],
        color: int,
        game_id: str,
        level: int,
        frame_index: int
    ) -> Dict:
        """Create object representation from cells."""
        if not cells:
            return None
        
        # Calculate bounding box
        xs = [x for x, y in cells]
        ys = [y for x, y in cells]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Calculate size
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        obj_id = f"obj_{game_id}_{level}_{frame_index}_{uuid.uuid4().hex[:8]}"
        
        return {
            'object_id': obj_id,
            'game_id': game_id,
            'level_number': level,
            'frame_index': frame_index,
            'properties': json.dumps({
                'color': color,
                'cells': cells,
                'center': [center_x, center_y],
                'size': [width, height],
                'area': len(cells),
                'bbox': [min_x, min_y, max_x, max_y]
            }),
            'detected_at': datetime.now().isoformat()
        }
    
    def store_detected_objects(self, objects: List[Dict]):
        """Store detected objects in database."""
        if not self.enabled or not objects:
            return
        
        for obj in objects:
            try:
                self.db.execute_query("""
                    INSERT OR REPLACE INTO detected_objects
                    (object_id, game_id, level_number, frame_index, properties, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    obj['object_id'],
                    obj['game_id'],
                    obj['level_number'],
                    obj['frame_index'],
                    obj['properties'],
                    obj['detected_at']
                ))
            except Exception as e:
                logger.error(f"Failed to store object {obj['object_id']}: {e}")
    
    def track_objects_across_frames(
        self,
        frames: List[Dict],
        game_id: str,
        level: int
    ) -> List[Dict]:
        """
        Track objects across multiple frames.
        
        Identifies which objects persist and how they move.
        
        Returns list of object tracks.
        """
        if not self.enabled or not frames:
            return []
        
        # Detect objects in all frames
        all_objects = []
        for i, frame in enumerate(frames):
            objects = self.detect_objects_in_frame(frame, game_id, level, i)
            all_objects.extend(objects)
        
        # Build tracks by matching objects across frames
        tracks = []
        used_objects = set()
        
        for obj in all_objects:
            if obj['object_id'] in used_objects:
                continue
            
            track = self._build_track(obj, all_objects, used_objects)
            if track:
                tracks.append(track)
        
        return tracks
    
    def _build_track(
        self,
        start_obj: Dict,
        all_objects: List[Dict],
        used_objects: set
    ) -> Optional[Dict]:
        """Build a track starting from given object."""
        track_sequence = [start_obj]
        used_objects.add(start_obj['object_id'])
        
        current_frame = start_obj['frame_index']
        current_props = json.loads(start_obj['properties'])
        
        # Follow object through subsequent frames
        for next_frame_idx in range(current_frame + 1, current_frame + 10):
            next_obj = self._find_matching_object(
                current_props,
                all_objects,
                next_frame_idx,
                used_objects
            )
            
            if next_obj:
                track_sequence.append(next_obj)
                used_objects.add(next_obj['object_id'])
                current_frame = next_obj['frame_index']
                current_props = json.loads(next_obj['properties'])
            else:
                break
        
        # Determine lifecycle
        lifecycle = 'persistent' if len(track_sequence) > 3 else 'temporary'
        
        track_id = f"track_{uuid.uuid4().hex[:12]}"
        
        return {
            'track_id': track_id,
            'game_id': start_obj['game_id'],
            'level_number': start_obj['level_number'],
            'object_sequence': json.dumps([o['object_id'] for o in track_sequence]),
            'lifecycle': lifecycle,
            'created_at': datetime.now().isoformat()
        }
    
    def _find_matching_object(
        self,
        props: Dict,
        all_objects: List[Dict],
        target_frame: int,
        used_objects: set
    ) -> Optional[Dict]:
        """Find matching object in next frame."""
        candidates = [
            obj for obj in all_objects
            if obj['frame_index'] == target_frame
            and obj['object_id'] not in used_objects
        ]
        
        if not candidates:
            return None
        
        # Find closest match by position and size
        best_match = None
        best_score = float('inf')
        
        for candidate in candidates:
            cand_props = json.loads(candidate['properties'])
            
            # Must have same color
            if cand_props['color'] != props['color']:
                continue
            
            # Calculate distance between centers
            dx = cand_props['center'][0] - props['center'][0]
            dy = cand_props['center'][1] - props['center'][1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            # Size difference
            size_diff = abs(cand_props['area'] - props['area'])
            
            # Combined score (prefer nearby with similar size)
            score = distance + size_diff * 0.5
            
            if score < best_score and score < 5:  # Max distance threshold
                best_score = score
                best_match = candidate
        
        return best_match
    
    def store_tracks(self, tracks: List[Dict]):
        """Store object tracks in database."""
        if not self.enabled or not tracks:
            return
        
        for track in tracks:
            try:
                self.db.execute_query("""
                    INSERT OR REPLACE INTO object_tracks
                    (track_id, game_id, level_number, object_sequence, lifecycle, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    track['track_id'],
                    track['game_id'],
                    track['level_number'],
                    track['object_sequence'],
                    track['lifecycle'],
                    track['created_at']
                ))
            except Exception as e:
                logger.error(f"Failed to store track {track['track_id']}: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("OBJECT DETECTOR TEST")
    print("=" * 70)
    
    if not is_abstraction_enabled():
        print("\n[WARN]  ENABLE_ABSTRACTION is false")
        print("Set: ENABLE_ABSTRACTION=true to enable")
    else:
        detector = ObjectDetector()
        
        # Test with simple grid
        test_frame = {
            'grid': [
                [0, 0, 1, 1, 0],
                [0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0],
                [2, 2, 0, 3, 3],
                [2, 2, 0, 3, 3]
            ]
        }
        
        objects = detector.detect_objects_in_frame(
            test_frame, "test_game", 1, 0
        )
        
        print(f"\n[OK] Detected {len(objects)} objects")
        for obj in objects:
            props = json.loads(obj['properties'])
            print(f"  - Color {props['color']}: {props['area']} cells at {props['center']}")
        
        detector.store_detected_objects(objects)
        print("\n[OK] Objects stored in database")
