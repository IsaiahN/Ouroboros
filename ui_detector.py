"""
UI Detector for ARC Games
=========================
SYMBOLIC MECHANICS - Universal Component

Detects and parses UI elements in game frames:
- Health bars / life indicators
- Action limit counters
- Score displays
- Timer indicators

Many ARC games have HUD elements that constrain gameplay.
Agents must understand these to plan effectively.

Applicable to ALL games, not just specific game types.

Author: Claude (Ouroboros Oracle)
Date: 2026-01-19
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class UIRegion:
    """Represents a detected UI region in the game frame."""
    region_type: str  # 'counter', 'bar', 'indicator', 'unknown'
    bbox: List[int]  # [x1, y1, x2, y2]
    position: str  # 'top', 'bottom', 'left', 'right', 'corner'
    color: Optional[int] = None
    current_value: int = 0
    max_value: int = 0
    meaning: Optional[str] = None  # 'health', 'actions', 'lives', 'score', 'timer'
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'region_type': self.region_type,
            'bbox': self.bbox,
            'position': self.position,
            'color': self.color,
            'current_value': self.current_value,
            'max_value': self.max_value,
            'meaning': self.meaning,
            'confidence': self.confidence
        }


@dataclass
class UIChangeEvent:
    """Represents a change in a UI element."""
    region: UIRegion
    old_value: int
    new_value: int
    change_type: str  # 'decrease', 'increase', 'reset'
    trigger_action: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'region': self.region.to_dict(),
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change_type': self.change_type,
            'trigger_action': self.trigger_action
        }


class UIDetector:
    """
    Detects and tracks UI elements in game frames.
    
    UI elements are typically:
    - At screen edges (top/bottom rows, left/right columns)
    - Small, regularly spaced dots or squares
    - Consistent color within the element
    - Static position across frames (don't move with player)
    """
    
    def __init__(self, game_type: Optional[str] = None):
        self.game_type = game_type
        self.detected_regions: List[UIRegion] = []
        self.ui_history: List[Dict[str, Any]] = []
        self.learned_meanings: Dict[str, str] = {}  # region_key -> meaning
        self.max_observed_values: Dict[str, int] = {}
        
    def detect_ui_regions(self, frame: List[List[int]]) -> List[UIRegion]:
        """
        Detect all UI regions in a frame.
        
        UI elements are typically found at screen edges and consist
        of regularly-spaced colored pixels (dots for counters, bars for health).
        """
        regions = []
        
        if not frame or not frame[0]:
            return regions
        
        height = len(frame)
        width = len(frame[0])
        
        # Check top edge (first 2 rows)
        top_regions = self._scan_edge_region(frame, 'top', 0, 2, 0, width)
        regions.extend(top_regions)
        
        # Check bottom edge (last 2 rows)
        bottom_regions = self._scan_edge_region(frame, 'bottom', height - 2, height, 0, width)
        regions.extend(bottom_regions)
        
        # Check left edge (first 2 columns)
        left_regions = self._scan_edge_region(frame, 'left', 0, height, 0, 2)
        regions.extend(left_regions)
        
        # Check right edge (last 2 columns)
        right_regions = self._scan_edge_region(frame, 'right', 0, height, width - 2, width)
        regions.extend(right_regions)
        
        # Check corners for special indicators
        corner_regions = self._scan_corners(frame)
        regions.extend(corner_regions)
        
        self.detected_regions = regions
        return regions
    
    def _scan_edge_region(
        self, 
        frame: List[List[int]], 
        position: str,
        y_start: int, 
        y_end: int, 
        x_start: int, 
        x_end: int
    ) -> List[UIRegion]:
        """Scan an edge region for UI elements."""
        regions = []
        height = len(frame)
        width = len(frame[0])
        
        # Clamp bounds
        y_start = max(0, y_start)
        y_end = min(height, y_end)
        x_start = max(0, x_start)
        x_end = min(width, x_end)
        
        # Count pixels by color in this region
        color_pixels: Dict[int, List[Tuple[int, int]]] = {}
        
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                c = frame[y][x]
                if c != 0:  # Non-background
                    if c not in color_pixels:
                        color_pixels[c] = []
                    color_pixels[c].append((x, y))
        
        # Analyze each color group
        for color, pixels in color_pixels.items():
            if len(pixels) >= 2:  # Need at least 2 pixels to be a counter
                region = self._analyze_pixel_group(pixels, color, position)
                if region:
                    regions.append(region)
        
        return regions
    
    def _analyze_pixel_group(
        self, 
        pixels: List[Tuple[int, int]], 
        color: int, 
        position: str
    ) -> Optional[UIRegion]:
        """Analyze a group of same-colored pixels to determine if it's a UI element."""
        if len(pixels) < 2:
            return None
        
        xs = [p[0] for p in pixels]
        ys = [p[1] for p in pixels]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Determine region type based on shape
        pixel_count = len(pixels)
        
        if width >= 3 and height <= 2:
            # Horizontal dots/bar - likely a counter
            region_type = 'counter'
            meaning = 'actions' if position == 'top' else 'health'
        elif height >= 3 and width <= 2:
            # Vertical dots/bar
            region_type = 'counter'
            meaning = 'lives' if position in ['left', 'right'] else 'unknown'
        elif pixel_count <= 4:
            # Small group - could be an indicator
            region_type = 'indicator'
            meaning = 'unknown'
        else:
            # Larger region - might be decorative
            region_type = 'unknown'
            meaning = None
        
        # Calculate confidence based on regularity
        # UI elements tend to have regular spacing
        if region_type == 'counter':
            confidence = 0.7
        elif region_type == 'indicator':
            confidence = 0.5
        else:
            confidence = 0.3
        
        return UIRegion(
            region_type=region_type,
            bbox=[min_x, min_y, max_x + 1, max_y + 1],
            position=position,
            color=color,
            current_value=pixel_count,
            max_value=pixel_count,  # Will be updated as we observe changes
            meaning=meaning,
            confidence=confidence
        )
    
    def _scan_corners(self, frame: List[List[int]]) -> List[UIRegion]:
        """Scan corners for special UI indicators."""
        regions = []
        height = len(frame)
        width = len(frame[0])
        
        # Check each corner (3x3 area)
        corner_areas = [
            ('top-left', 0, 3, 0, 3),
            ('top-right', 0, 3, width - 3, width),
            ('bottom-left', height - 3, height, 0, 3),
            ('bottom-right', height - 3, height, width - 3, width)
        ]
        
        for corner_name, y_start, y_end, x_start, x_end in corner_areas:
            # Clamp bounds
            y_start = max(0, y_start)
            y_end = min(height, y_end)
            x_start = max(0, x_start)
            x_end = min(width, x_end)
            
            # Count colored pixels
            colored_pixels = []
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    if frame[y][x] != 0:
                        colored_pixels.append((x, y, frame[y][x]))
            
            if 1 <= len(colored_pixels) <= 5:
                # Small indicator in corner
                xs = [p[0] for p in colored_pixels]
                ys = [p[1] for p in colored_pixels]
                color = colored_pixels[0][2]
                
                regions.append(UIRegion(
                    region_type='indicator',
                    bbox=[min(xs), min(ys), max(xs) + 1, max(ys) + 1],
                    position=corner_name,
                    color=color,
                    current_value=len(colored_pixels),
                    max_value=len(colored_pixels),
                    meaning='unknown',
                    confidence=0.4
                ))
        
        return regions
    
    def detect_ui_change(
        self, 
        frame_before: List[List[int]], 
        frame_after: List[List[int]],
        action_taken: Optional[int] = None
    ) -> List[UIChangeEvent]:
        """
        Detect changes in UI regions between two frames.
        
        This is key for learning what UI elements mean:
        - If counter decreases after every action -> action limit
        - If counter decreases only on damage -> health
        - If counter increases on pickup -> collectible counter
        """
        changes = []
        
        if not frame_before or not frame_after:
            return changes
        
        # Detect regions in both frames
        regions_before = self.detect_ui_regions(frame_before)
        regions_after = self.detect_ui_regions(frame_after)
        
        # Match regions by position and color
        for region_before in regions_before:
            # Find matching region in after frame
            matching = None
            for region_after in regions_after:
                if (region_before.position == region_after.position and
                    region_before.color == region_after.color):
                    matching = region_after
                    break
            
            if matching:
                if region_before.current_value != matching.current_value:
                    change_type = 'decrease' if matching.current_value < region_before.current_value else 'increase'
                    
                    changes.append(UIChangeEvent(
                        region=matching,
                        old_value=region_before.current_value,
                        new_value=matching.current_value,
                        change_type=change_type,
                        trigger_action=action_taken
                    ))
                    
                    # Update max observed value
                    region_key = f"{matching.position}_{matching.color}"
                    current_max = self.max_observed_values.get(region_key, 0)
                    self.max_observed_values[region_key] = max(
                        current_max, 
                        region_before.current_value, 
                        matching.current_value
                    )
        
        # Store in history
        if changes:
            self.ui_history.append({
                'action': action_taken,
                'changes': [c.to_dict() for c in changes]
            })
        
        return changes
    
    def learn_meaning_from_changes(self) -> Dict[str, str]:
        """
        Infer UI element meanings from observed changes.
        
        Heuristics:
        - Decreases on EVERY action -> 'action_limit'
        - Decreases only sometimes -> 'health' or 'resource'
        - Increases on specific positions -> 'collectible_counter'
        - Never changes -> 'decorative' or 'score'
        """
        if not self.ui_history:
            return self.learned_meanings
        
        # Count change patterns per region
        region_patterns: Dict[str, Dict[str, int]] = {}
        
        for entry in self.ui_history:
            for change in entry.get('changes', []):
                region = change.get('region', {})
                region_key = f"{region.get('position')}_{region.get('color')}"
                
                if region_key not in region_patterns:
                    region_patterns[region_key] = {
                        'decrease_count': 0,
                        'increase_count': 0,
                        'total_observations': 0
                    }
                
                region_patterns[region_key]['total_observations'] += 1
                if change.get('change_type') == 'decrease':
                    region_patterns[region_key]['decrease_count'] += 1
                elif change.get('change_type') == 'increase':
                    region_patterns[region_key]['increase_count'] += 1
        
        # Infer meanings
        for region_key, patterns in region_patterns.items():
            total = patterns['total_observations']
            if total == 0:
                continue
            
            decrease_ratio = patterns['decrease_count'] / total
            increase_ratio = patterns['increase_count'] / total
            
            if decrease_ratio > 0.9:
                # Almost always decreases -> action limit
                self.learned_meanings[region_key] = 'action_limit'
            elif decrease_ratio > 0.5:
                # Frequently decreases -> health/resource
                self.learned_meanings[region_key] = 'health'
            elif increase_ratio > 0.5:
                # Frequently increases -> collectible
                self.learned_meanings[region_key] = 'collectible'
            else:
                self.learned_meanings[region_key] = 'unknown'
        
        return self.learned_meanings
    
    def get_action_limit_status(self, frame: List[List[int]]) -> Dict[str, Any]:
        """
        Get status of action limit indicators if detected.
        
        Returns:
            Dict with remaining_actions, max_actions, is_critical
        """
        result = {
            'has_action_limit': False,
            'remaining_actions': None,
            'max_actions': None,
            'is_critical': False
        }
        
        regions = self.detect_ui_regions(frame)
        
        for region in regions:
            region_key = f"{region.position}_{region.color}"
            meaning = self.learned_meanings.get(region_key, region.meaning)
            
            if meaning in ['action_limit', 'actions']:
                result['has_action_limit'] = True
                result['remaining_actions'] = region.current_value
                result['max_actions'] = self.max_observed_values.get(
                    region_key, region.max_value
                )
                # FIX (Feedback 9): Use percentage-based threshold, not absolute
                # Critical when < 10% actions remaining (was: <= 2 which is way too late)
                max_actions = result['max_actions']
                remaining = region.current_value
                if max_actions and max_actions > 0 and remaining is not None:
                    pct_remaining = remaining / max_actions
                    result['is_critical'] = pct_remaining < 0.10
                    # NEW: Add specific thresholds for proactive reset
                    result['should_proactive_reset'] = remaining <= 2  # 1-2 actions left
                    result['actions_until_empty'] = remaining
                else:
                    result['is_critical'] = (remaining or 0) <= 2  # Fallback
                    result['should_proactive_reset'] = (remaining or 0) <= 2
                    result['actions_until_empty'] = remaining
                break
        
        return result
    
    def get_health_status(self, frame: List[List[int]]) -> Dict[str, Any]:
        """Get status of health indicators if detected."""
        result = {
            'has_health': False,
            'current_health': None,
            'max_health': None,
            'is_critical': False
        }
        
        regions = self.detect_ui_regions(frame)
        
        for region in regions:
            region_key = f"{region.position}_{region.color}"
            meaning = self.learned_meanings.get(region_key, region.meaning)
            
            if meaning in ['health', 'lives']:
                result['has_health'] = True
                result['current_health'] = region.current_value
                result['max_health'] = self.max_observed_values.get(
                    region_key, region.max_value
                )
                result['is_critical'] = region.current_value <= 1
                break
        
        return result
    
    def should_proactive_reset(
        self, 
        frame: List[List[int]],
        exploration_coverage: Optional[float] = None,
        has_made_progress: bool = False,
        # NEW: For games without visible HUD
        current_action_count: Optional[int] = None,
        learned_budget: Optional[Dict[str, Any]] = None,
        consecutive_no_change: int = 0
    ) -> Dict[str, Any]:
        """
        Determine if a proactive level reset should be triggered.
        
        PROACTIVE RESET: Reset BEFORE the game ends to preserve all learned knowledge
        and continue playing with a fresh action budget.
        
        Works for TWO types of games:
        1. Games WITH visible HUD (like LS20's purple bar) - uses UI detection
        2. Games WITHOUT visible HUD - uses learned_budget + action_count
        
        The key insight is: if we're near the learned end-of-game threshold,
        it's better to reset NOW (keeping all memory/exploration state) than to:
        1. Use the last action randomly and die
        2. Lose the game and start fresh
        
        Args:
            frame: Current game frame
            exploration_coverage: % of map explored (0-100), from NetworkExplorationTracker
            has_made_progress: Whether score increased since last reset
            current_action_count: How many actions taken this attempt (for no-HUD games)
            learned_budget: Dict from _get_learned_budget() with min/max/avg actions
            consecutive_no_change: How many actions with no frame change (stuck detection)
            
        Returns:
            Dict with:
            - should_reset: bool - whether to reset now
            - reason: str - why reset is recommended
            - urgency: str - 'immediate', 'soon', 'not_needed'
            - source: str - 'hud', 'learned_budget', 'stuck_detection'
            - knowledge_to_preserve: dict - summary of what we've learned
        """
        result = {
            'should_reset': False,
            'reason': 'No reset needed',
            'urgency': 'not_needed',
            'source': 'none',
            'knowledge_to_preserve': {
                'ui_meanings_learned': len(self.learned_meanings),
                'exploration_coverage': exploration_coverage,
                'has_progress': has_made_progress
            }
        }
        
        # ===================================================================
        # METHOD 1: HUD-BASED DETECTION (games with visible action counter)
        # ===================================================================
        action_status = self.get_action_limit_status(frame)
        health_status = self.get_health_status(frame)
        
        remaining_actions = action_status.get('actions_until_empty')
        remaining_health = health_status.get('current_health')
        
        # If we have HUD data, use it (most reliable)
        if remaining_actions is not None:
            # CASE 1: Very low actions (1-2 left) - IMMEDIATE reset
            if remaining_actions <= 2:
                if has_made_progress:
                    result['should_reset'] = remaining_actions <= 1
                    result['urgency'] = 'immediate' if remaining_actions <= 1 else 'soon'
                    result['reason'] = f"HUD shows {remaining_actions} actions left, made progress - reset to preserve knowledge"
                else:
                    result['should_reset'] = True
                    result['urgency'] = 'immediate'
                    result['reason'] = f"HUD shows only {remaining_actions} actions left with no progress - reset now"
                result['source'] = 'hud'
                return result
            
            # CASE 2: Low health AND low actions
            if remaining_health is not None and remaining_health <= 1 and remaining_actions <= 5:
                result['should_reset'] = True
                result['urgency'] = 'soon'
                result['reason'] = f"Low health ({remaining_health}) + low actions ({remaining_actions}) - reset before double failure"
                result['source'] = 'hud'
                return result
        
        # ===================================================================
        # METHOD 2: LEARNED BUDGET DETECTION (games without visible HUD)
        # ===================================================================
        # Use historical data about when games typically end
        if learned_budget and current_action_count is not None:
            confidence = learned_budget.get('confidence', 0)
            avg_actions = learned_budget.get('avg_actions', 2000)
            max_actions = learned_budget.get('max_actions', 2000)
            
            # Only use learned budget if we have enough confidence
            if confidence >= 0.3 and learned_budget.get('observations', 0) >= 3:
                # Calculate how close we are to the learned limit
                # Use avg_actions as the typical game end point
                actions_until_typical_end = avg_actions - current_action_count
                
                # CASE 3: Approaching learned game end (within 5% or 10 actions)
                threshold = max(10, avg_actions * 0.05)  # 5% of typical game or 10 actions
                
                if actions_until_typical_end <= threshold and actions_until_typical_end > 0:
                    if has_made_progress:
                        result['should_reset'] = actions_until_typical_end <= 3
                        result['urgency'] = 'soon' if actions_until_typical_end > 3 else 'immediate'
                    else:
                        result['should_reset'] = True
                        result['urgency'] = 'immediate' if actions_until_typical_end <= 5 else 'soon'
                    
                    result['reason'] = (f"Learned budget: games typically end around {avg_actions:.0f} actions, "
                                       f"currently at {current_action_count} ({actions_until_typical_end:.0f} remaining)")
                    result['source'] = 'learned_budget'
                    result['knowledge_to_preserve']['learned_budget_confidence'] = confidence
                    return result
        
        # ===================================================================
        # METHOD 3: STUCK DETECTION (fallback for completely unknown games)
        # ===================================================================
        # If no HUD and no learned budget, use stuck detection as proxy
        # Many games end when you're stuck in a loop
        
        STUCK_THRESHOLD_FOR_RESET = 50  # 50 consecutive no-change actions = likely stuck
        
        if consecutive_no_change >= STUCK_THRESHOLD_FOR_RESET:
            # Been stuck for a while - might be approaching game end
            result['should_reset'] = True
            result['urgency'] = 'soon'
            result['reason'] = f"Stuck for {consecutive_no_change} actions - likely near game end, reset to try different approach"
            result['source'] = 'stuck_detection'
            return result
        
        # ===================================================================
        # METHOD 4: EXPLORATION-BASED (high coverage but no progress)
        # ===================================================================
        if (exploration_coverage is not None and exploration_coverage > 80 and
            not has_made_progress and current_action_count and current_action_count > 100):
            # Explored most of map but stuck - reset might help
            result['should_reset'] = True
            result['urgency'] = 'soon'
            result['reason'] = f"Explored {exploration_coverage:.0f}% of map but no progress after {current_action_count} actions"
            result['source'] = 'exploration_coverage'
            return result
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize detector state."""
        return {
            'game_type': self.game_type,
            'detected_regions': [r.to_dict() for r in self.detected_regions],
            'learned_meanings': self.learned_meanings,
            'max_observed_values': self.max_observed_values,
            'history_length': len(self.ui_history)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIDetector':
        """Deserialize detector state."""
        detector = cls(game_type=data.get('game_type'))
        detector.learned_meanings = data.get('learned_meanings', {})
        detector.max_observed_values = data.get('max_observed_values', {})
        return detector
    
    # =========================================================================
    # NETWORK PERSISTENCE (LS20 Defeat Plan Gap Fix)
    # =========================================================================
    # Share learned UI layouts to network so other agents don't have to
    # re-discover HUD elements for the same game type.
    # =========================================================================
    
    def save_to_network(
        self, 
        db_path: str = "core_data.db",
        agent_id: Optional[str] = None,
        generation: Optional[int] = None,
        min_confidence: float = 0.6
    ) -> int:
        """
        Save learned UI layouts to network database.
        
        Only saves regions with high-confidence learned meanings.
        
        Args:
            db_path: Path to database
            agent_id: Agent that discovered this
            generation: Current generation
            min_confidence: Minimum observation ratio to save
            
        Returns:
            Number of regions saved
        """
        import sqlite3
        import json
        
        if not self.game_type or not self.learned_meanings:
            return 0
        
        saved = 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for region in self.detected_regions:
                region_key = f"{region.position}_{region.color}"
                meaning = self.learned_meanings.get(region_key)
                
                if not meaning or meaning == 'unknown':
                    continue
                
                # Calculate confidence based on observation history
                relevant_history = [
                    h for h in self.ui_history 
                    if any(r.get('position') == region.position and r.get('color') == region.color 
                           for r in h.get('regions', []))
                ]
                observation_count = len(relevant_history)
                
                if observation_count < 3:
                    continue  # Need 3+ observations
                
                # Determine depletion trigger based on history analysis
                depletes_on = 'action'  # Default
                if meaning in ['health', 'lives']:
                    depletes_on = 'damage'
                elif meaning in ['timer']:
                    depletes_on = 'time'
                
                # Save to ui_layout_hypotheses
                cursor.execute("""
                    INSERT OR REPLACE INTO ui_layout_hypotheses (
                        game_type, ui_region, indicator_type, indicator_color,
                        meaning, max_value, depletes_on, refills_on,
                        confidence, observation_count, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                """, (
                    self.game_type,
                    json.dumps(region.bbox),  # Already [x1, y1, x2, y2]
                    region.region_type,
                    region.color,
                    meaning,
                    self.max_observed_values.get(region_key, region.max_value),
                    depletes_on,
                    'pickup_purple' if meaning in ['actions', 'health'] else 'level_complete',
                    min(0.95, 0.5 + observation_count * 0.1),  # Confidence grows with observations
                    observation_count
                ))
                saved += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"UI save to network failed: {e}")
        
        return saved
    
    def load_from_network(self, db_path: str = "core_data.db") -> int:
        """
        Load UI layout knowledge from network for this game type.
        
        Returns:
            Number of regions loaded
        """
        import sqlite3
        import json
        
        if not self.game_type:
            return 0
        
        loaded = 0
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ui_region, indicator_type, indicator_color, meaning, max_value
                FROM ui_layout_hypotheses
                WHERE game_type = ? AND is_active = TRUE AND confidence > 0.5
                ORDER BY observation_count DESC
            """, (self.game_type,))
            
            for row in cursor.fetchall():
                region_bbox = json.loads(row['ui_region'])
                region_key = f"{row['indicator_type']}_{row['indicator_color']}"
                
                # Pre-load learned meanings
                self.learned_meanings[region_key] = row['meaning']
                self.max_observed_values[region_key] = row['max_value']
                loaded += 1
            
            conn.close()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"UI load from network failed: {e}")
        
        return loaded


def create_ui_detector(game_type: Optional[str] = None, db_path: str = "core_data.db") -> UIDetector:
    """Factory function to create a UI detector with optional network knowledge."""
    detector = UIDetector(game_type=game_type)
    
    # Try to load existing network knowledge for this game type
    if game_type:
        loaded = detector.load_from_network(db_path)
        if loaded > 0:
            import logging
            logging.getLogger(__name__).info(f"UI detector loaded {loaded} regions from network for {game_type}")
    
    return detector
