import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

"""
Action Handler

Provides clean interfaces for sending actions to the ARC-AGI-3 API.
Handles action validation, coordinate processing, and response parsing.

ARC-AGI-3 ACTION REFERENCE:
==========================
ACTION1: Context-specific action (often directional movement: UP)
ACTION2: Context-specific action (often directional movement: DOWN)  
ACTION3: Context-specific action (often directional movement: LEFT)
ACTION4: Context-specific action (often directional movement: RIGHT)
ACTION5: Context-specific interaction (SELECT/INTERACT/USE)
ACTION6: Universal targeting system - click/touch coordinates (x, y)
         Think of grid as touchscreen - ACTION6(x, y) = "touch pixel at (x, y)"
         Effects depend on what's at that location (buttons, objects, portals, etc.)
ACTION7: UNDO - reverts last action, potentially restoring previous state

STRATEGY FOR UNBEATEN GAMES:
===========================
For games with 0 level completions (sp80, ls20, etc.):
1. Try ALL actions 1-7 systematically for maximum exploration
2. Use ACTION6 with visual analysis to target interesting frame features
3. Actions 1-5,7 often have predictable effects, try these first
4. ACTION6 requires coordinate analysis - look for color anomalies, patterns, bright spots
5. Use increased action budgets (2x-3x) to allow thorough exploration
"""

import logging
import random
import asyncio
from typing import Dict, Any, Optional, List, Tuple

from arc_api_client import GameState
from visual_analyzer import VisualAnalyzer

logger = logging.getLogger(__name__)


class ActionHandler:
    """Handles action sending and validation for ARC games."""

    def __init__(self, session_manager):
        """Initialize action handler.

        Args:
            session_manager: GameSessionManager instance
        """
        self.session_manager = session_manager
        self.last_frame = None
        self.last_score = 0.0
        self.visual_analyzer = VisualAnalyzer()  # Add visual analyzer
        
        # Agent operating mode tracking (for mode-specific behavior)
        self.current_agent_mode = None  # 'pioneer', 'optimizer', 'generalist', 'exploiter', or None
        self.current_level = 1  # Current level being played (for pioneer oscillation checks)
        self.network_max_level = 0  # Network's max level for this game type (for pioneer checks)
        
        # Frame dimension tracking (expected 64x64 for ARC-AGI)
        self.expected_frame_size = (64, 64)  # (height, width)
        self.last_frame_size = None
        self.frame_size_warnings = 0
        
        # Action diversity tracking (similar to coordinate diversity)
        self.recent_actions = []  # Track last N actions
        self.max_action_history = 10
        self.action_stagnation_count = 0  # How many times same action repeated
        self.last_action = None
        self.consecutive_same_action = 0
        
        # Coordinate diversity tracking for ACTION6
        self.recent_coordinates = []  # Track last N coordinates
        self.max_coordinate_history = 15
        self.coordinate_spam_threshold = 3  # Max times to click similar coordinates
        self.last_coordinates = None
        self.consecutive_similar_coordinate = 0
        
        # Progressive spam tolerance based on game progress
        self.level_action_count = 0  # Actions taken in current level
        self.level_max_actions = 100  # Max actions per level (from config)
        self.spam_allowed_early = 10  # Allow up to 10 similar clicks early in level
        self.spam_allowed_late = 3   # Reduce to 3 similar clicks late in level
        
        # Escape mode coordinates (set by GameplayEngine when escaping stuck state)
        self._escape_click_coords: Optional[tuple] = None

    def set_agent_mode(self, mode: Optional[str], current_level: int = 1, network_max_level: int = 0):
        """Set the current agent operating mode for mode-specific behavior.
        
        Args:
            mode: Agent operating mode ('pioneer', 'optimizer', 'generalist', 'exploiter', or None)
            current_level: Current level being played (for pioneer oscillation checks)
            network_max_level: Network's max level for this game type (for pioneer checks)
        """
        self.current_agent_mode = mode
        self.current_level = current_level
        self.network_max_level = network_max_level
        logger.debug(f"ActionHandler agent mode set to: {mode} (Level {current_level}, Network max: {network_max_level})")

    def _validate_frame_dimensions(self, frame: List[List[int]], context: str = "") -> bool:
        """
        Validate frame dimensions and check if they match expected 64x64.
        Logs warnings if dimensions are unexpected.
        
        Args:
            frame: Frame to validate
            context: Context string for logging (e.g., "ACTION6 selection")
            
        Returns:
            True if frame is valid (has data), False if corrupted/empty
        """
        if not frame:
            logger.error(f"[FAIL] FRAME CORRUPTION: Empty frame {context}")
            return False
        
        if not frame[0]:
            logger.error(f"[FAIL] FRAME CORRUPTION: Frame has no columns {context}")
            return False
        
        height = len(frame)
        width = len(frame[0])
        current_size = (height, width)
        
        # Check if dimensions changed
        if self.last_frame_size and self.last_frame_size != current_size:
            logger.warning(f"[WARN] FRAME DIMENSION CHANGE: {self.last_frame_size} → {current_size} {context}")
            self.frame_size_warnings += 1
        
        # Check if dimensions are NOT the expected 64x64
        if current_size != self.expected_frame_size:
            logger.warning(
                f"🔍 NON-STANDARD FRAME SIZE: {height}x{width} (expected {self.expected_frame_size[0]}x{self.expected_frame_size[1]}) {context}"
            )
            
            # CRITICAL: Extremely small frames (like 2x64) indicate API error or corruption
            # Valid ARC frames should be at least 10x10 - anything smaller is corrupt
            MIN_VALID_DIMENSION = 10
            if height < MIN_VALID_DIMENSION or width < MIN_VALID_DIMENSION:
                logger.error(f"[FAIL] FRAME CORRUPTION: Frame too small ({height}x{width}), likely API error - aborting game {context}")
                return False
            
            # Double-check: verify frame structure is consistent
            inconsistent_rows = []
            for i, row in enumerate(frame):
                if len(row) != width:
                    inconsistent_rows.append((i, len(row)))
            
            if inconsistent_rows:
                logger.error(f"[FAIL] FRAME CORRUPTION: Inconsistent row widths at rows {inconsistent_rows[:5]} {context}")
                return False
            
            # Non-standard but consistent - might be legitimate level variation
            logger.info(f"[OK] Frame structure consistent at {height}x{width}, continuing {context}")
        
        # Update tracking
        self.last_frame_size = current_size
        
        return True

    def _validate_coordinates(self, x: int, y: int, frame: List[List[int]]) -> bool:
        """Validate that coordinates are within frame bounds.

        Args:
            x: X coordinate
            y: Y coordinate
            frame: Current game frame

        Returns:
            True if coordinates are valid
        """
        if not frame or not frame[0]:
            return False

        return 0 <= y < len(frame) and 0 <= x < len(frame[0])

    async def _attempt_frame_recovery(
        self,
        level_number: int = 1,
        max_attempts: int = 5,
        stage_pauses: Optional[List[Tuple[int, float]]] = None
    ) -> Optional['GameState']:
        """Attempt to recover from a corrupt frame by sending random simple actions.

        When we receive a corrupt frame (like 2x64 instead of 64x64), this is likely
        a transient API error or level transition glitch. We try to "flush" the bad
        state by sending random directional actions (ACTION1-5) which don't require
        coordinates.

        Args:
            level_number: Current level for logging
            max_attempts: Maximum number of recovery actions to try (default 5)
            stage_pauses: Optional list of (attempt_count, pause_seconds) to wait
                after specific attempt counts to allow the API to stabilize.

        Returns:
            New GameState if recovery successful, None otherwise
        """

        pause_after = {count: delay for count, delay in (stage_pauses or []) if count > 0 and delay > 0}

        for attempt in range(1, max_attempts + 1):
            # Try a random directional action (1-5) to flush the bad frame
            # These don't require coordinates so they should work even with corrupt frame
            recovery_action = random.choice([1, 2, 3, 4, 5])
            logger.info(f"[SYNC] FRAME RECOVERY [{attempt}/{max_attempts}]: Sending ACTION{recovery_action} to flush corrupt frame")

            try:
                # Send the recovery action through session_manager.client (the API client)
                # NOTE: send_action() already returns a GameState object, NOT a dict
                new_state = await self.session_manager.client.send_action(f"ACTION{recovery_action}")
                if new_state:
                    frame = new_state.frame

                    if frame and len(frame) >= 10 and frame[0] and len(frame[0]) >= 10:
                        logger.info(f"[OK] FRAME RECOVERY SUCCESS after {attempt} attempts! Frame: {len(frame)}x{len(frame[0])}")
                        return new_state
                    else:
                        frame_size = f"{len(frame)}x{len(frame[0])}" if frame and frame[0] else "None"
                        logger.warning(f"[SYNC] FRAME RECOVERY [{attempt}]: Frame still corrupt ({frame_size}), trying again...")
            except Exception as e:
                logger.warning(f"[SYNC] FRAME RECOVERY [{attempt}] error: {e}")

            # Stage pause hooks allow the API to settle before more attempts
            if attempt in pause_after:
                delay = pause_after[attempt]
                logger.info(f"[SYNC] FRAME RECOVERY pause after attempt {attempt} for {delay:.2f}s")
                try:
                    await asyncio.sleep(delay)
                except Exception:
                    pass

        logger.error(f"[FAIL] FRAME RECOVERY FAILED after {max_attempts} attempts")
        return None

    def _is_coordinate_similar(self, coord1: Tuple[int, int], coord2: Tuple[int, int], 
                              threshold: int = 5) -> bool:
        """Check if two coordinates are similar (within threshold distance).
        
        Args:
            coord1: First coordinate (x, y)
            coord2: Second coordinate (x, y)
            threshold: Distance threshold for similarity
            
        Returns:
            True if coordinates are within threshold distance
        """
        x1, y1 = coord1
        x2, y2 = coord2
        distance = abs(x1 - x2) + abs(y1 - y2)  # Manhattan distance
        return distance <= threshold
    
    def _check_coordinate_diversity(self, x: int, y: int) -> Dict[str, Any]:
        """Check if coordinate is diverse enough and detect spam/oscillation.
        
        Uses dynamic spam threshold based on level progress:
        - Early level (0-30%): Allow up to 10 similar clicks (pseudo-button sequences)
        - Mid level (30-70%): Moderate tolerance (5-7 clicks)
        - Late level (70-100%): Low tolerance (3 clicks) - should have progressed
        
        **PIONEER MODE EXEMPTION**: PIONEER agents are exempt from all oscillation
        and spam detection - they need maximum freedom to explore and discover.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Dict with diversity info: {
                'is_diverse': bool,
                'spam_detected': bool, 
                'oscillation_detected': bool,
                'reason': str,
                'threshold_used': int
            }
        """
        coord = (x, y)
        
        # PIONEER EXEMPTION: Level-aware oscillation checks
        # Lenient on frontier (unbeaten levels), strict on known levels
        if self.current_agent_mode == 'pioneer':
            current_level = getattr(self, 'current_level', 1)
            network_max_level = getattr(self, 'network_max_level', 0)
            
            # LENIENT on frontier (new territory) - pioneers need freedom to explore
            if current_level >= network_max_level:
                return {
                    'is_diverse': True,
                    'spam_detected': False,
                    'oscillation_detected': False,
                    'reason': f'PIONEER frontier (L{current_level} >= L{network_max_level}) - lenient',
                    'threshold_used': 999
                }
            # STRICT on known levels - pioneers should use sequences there
            # Fall through to normal oscillation checks below
        
        # Get dynamic threshold based on level progress
        dynamic_threshold = self._get_dynamic_spam_threshold()
        
        result = {
            'is_diverse': True,
            'spam_detected': False,
            'oscillation_detected': False,
            'reason': 'New coordinate',
            'threshold_used': dynamic_threshold
        }
        
        # Track coordinate history
        self.recent_coordinates.append(coord)
        if len(self.recent_coordinates) > self.max_coordinate_history:
            self.recent_coordinates.pop(0)
        
        # Check if frame is actually changing (productive spam vs unproductive)
        frame_changing = self.visual_analyzer.last_action_changed_frame
        
        # Check if similar to last coordinate
        if self.last_coordinates:
            if self._is_coordinate_similar(coord, self.last_coordinates, threshold=3):
                self.consecutive_similar_coordinate += 1
                
                # Spam detection: clicking same spot repeatedly beyond threshold
                if self.consecutive_similar_coordinate >= dynamic_threshold:
                    # If frame is changing, this might be productive pseudo-button spam
                    if frame_changing and self.consecutive_similar_coordinate < dynamic_threshold + 5:
                        result['reason'] = f'Productive spam: {self.consecutive_similar_coordinate} clicks (frame changing)'
                        logger.info(f"[OK] Productive pseudo-button spam at ({x}, {y}) - frame changing!")
                    else:
                        result['spam_detected'] = True
                        result['is_diverse'] = False
                        result['reason'] = f'Coordinate spam: {self.consecutive_similar_coordinate} clicks (threshold: {dynamic_threshold})'
                        logger.warning(f"[WARN] Coordinate spam detected at ({x}, {y}) - {self.consecutive_similar_coordinate} clicks")
            else:
                self.consecutive_similar_coordinate = 0
        
        # Oscillation detection: bouncing between 2-3 coordinates
        if len(self.recent_coordinates) >= 6:
            # Check if we're oscillating between recent coordinates
            last_6 = self.recent_coordinates[-6:]
            unique_coords = set(last_6)
            
            if len(unique_coords) <= 3:  # Only 2-3 unique coordinates in last 6 clicks
                # Count how many times each coordinate appears
                from collections import Counter
                coord_counts = Counter(last_6)
                max_count = max(coord_counts.values())
                
                # If frame is changing during oscillation, it might be productive
                if max_count >= 3:
                    if frame_changing:
                        result['reason'] = f'Productive oscillation: {len(unique_coords)} buttons (frame changing)'
                        logger.info(f"[OK] Productive pseudo-button oscillation - frame changing!")
                    else:
                        result['oscillation_detected'] = True
                        result['is_diverse'] = False
                        result['reason'] = f'Coordinate oscillation: bouncing between {len(unique_coords)} spots'
                        logger.warning(f"[WARN] Coordinate oscillation detected: {unique_coords}")
                        
                        # Signal visual analyzer about oscillation
                        self.visual_analyzer.oscillation_detected = True
        
        self.last_coordinates = coord
        return result
    
    def update_level_progress(self, level_action_count: int, max_actions_per_level: int):
        """Update level progress for dynamic spam tolerance.
        
        Args:
            level_action_count: Actions taken in current level
            max_actions_per_level: Max actions allowed per level
        """
        self.level_action_count = level_action_count
        self.level_max_actions = max_actions_per_level
    
    def _get_dynamic_spam_threshold(self) -> int:
        """Calculate dynamic spam threshold based on level progress.
        
        Early in level (0-30%): Allow more spam (pseudo-button sequences)
        Mid level (30-70%): Moderate spam tolerance
        Late in level (70-100%): Reduce spam (should have progressed by now)
        
        Returns:
            Dynamic threshold for consecutive similar clicks
        """
        if self.level_max_actions == 0:
            return self.coordinate_spam_threshold
        
        progress = self.level_action_count / self.level_max_actions
        
        if progress < 0.3:
            # Early game: Allow spam for pseudo-button sequences
            threshold = self.spam_allowed_early
        elif progress < 0.7:
            # Mid game: Moderate tolerance
            threshold = (self.spam_allowed_early + self.spam_allowed_late) // 2
        else:
            # Late game: Low tolerance, should have found solution
            threshold = self.spam_allowed_late
        
        return threshold

    def _detect_frame_changes(self, old_frame: List[List[int]],
                            new_frame: List[List[int]]) -> Tuple[bool, int]:
        """Detect changes between two frames.

        Args:
            old_frame: Previous frame
            new_frame: Current frame

        Returns:
            Tuple of (changed, num_changes)
        """
        if not old_frame or not new_frame:
            return False, 0

        if len(old_frame) != len(new_frame):
            return True, -1  # Structural change

        changes = 0
        for y in range(len(old_frame)):
            if len(old_frame[y]) != len(new_frame[y]):
                return True, -1  # Structural change

            for x in range(len(old_frame[y])):
                if old_frame[y][x] != new_frame[y][x]:
                    changes += 1

        return changes > 0, changes

    async def send_action_1(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION1 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION1", reasoning=reasoning, level_number=level_number, **kwargs)

    async def send_action_2(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION2 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION2", reasoning=reasoning, level_number=level_number, **kwargs)

    async def send_action_3(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION3 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION3", reasoning=reasoning, level_number=level_number, **kwargs)

    async def send_action_4(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION4 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION4", reasoning=reasoning, level_number=level_number, **kwargs)

    async def send_action_5(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION5 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION5", reasoning=reasoning, level_number=level_number, **kwargs)

    async def send_action_6(self, x: int, y: int, frame: Optional[List[List[int]]] = None, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1) -> GameState:
        """Send ACTION6 (coordinate-based action) to the game.

        Args:
            x: X coordinate
            y: Y coordinate
            frame: Current frame for validation (optional)
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        # Validate frame dimensions if provided
        if frame:
            if not self._validate_frame_dimensions(frame, context="at send_action_6"):
                # Frame corruption detected - try to recover with a random action
                logger.warning(f"[WARN] FRAME CORRUPTION: Attempting recovery with random action...")
                recovery_result = await self._attempt_frame_recovery(level_number)
                if recovery_result:
                    # Recovery successful - update frame and retry validation
                    new_frame = recovery_result.frame
                    if new_frame and self._validate_frame_dimensions(new_frame, context="after recovery"):
                        logger.info(f"[OK] FRAME RECOVERY successful! New frame: {len(new_frame)}x{len(new_frame[0]) if new_frame else 0}")
                        frame = new_frame
                        # Re-validate coordinates against new frame
                        if not self._validate_coordinates(x, y, frame):
                            logger.warning(f"Coordinates ({x}, {y}) invalid after recovery - using center of frame")
                            y = len(frame) // 2
                            x = len(frame[0]) // 2 if frame[0] else 0
                    else:
                        logger.error(f"[FAIL] FRAME RECOVERY failed - frame still corrupt after recovery action")
                        raise ValueError(f"Frame corruption detected - recovery failed")
                else:
                    raise ValueError(f"Frame corruption detected - recovery failed")
        
        # Validate coordinates if frame is provided
        if frame and not self._validate_coordinates(x, y, frame):
            logger.warning(f"Invalid coordinates ({x}, {y}) for frame size {len(frame)}x{len(frame[0]) if frame else 0}")
            raise ValueError(f"Coordinates ({x}, {y}) are outside frame bounds")

        # Include reasoning and level_number if provided
        kwargs = {'x': x, 'y': y, 'coordinates': [x, y], 'level_number': level_number}
        if reasoning:
            kwargs['reasoning'] = reasoning
        return await self._send_action_with_context("ACTION6", **kwargs)

    async def send_action_7(self, reasoning: Optional[Dict[str, Any]] = None, level_number: int = 1, **kwargs) -> GameState:
        """Send ACTION7 to the game.

        Args:
            reasoning: Optional reasoning dict/JSON for the action (≤16 KB)
            level_number: Current level number for trace logging

        Returns:
            New game state
        """
        return await self._send_action_with_context("ACTION7", reasoning=reasoning, level_number=level_number, **kwargs)

    async def _send_action_with_context(self, action: str, **kwargs) -> GameState:
        """Send action with context tracking.

        Args:
            action: Action name
            **kwargs: Action parameters

        Returns:
            New game state with context
        """
        # Prepare context for database logging
        context = {
            'frame_before': self.last_frame,
            'score_before': self.last_score
        }
        context.update(kwargs)

        # Send action
        game_state = await self.session_manager.send_action(action, **context)

        # Detect frame changes
        if self.last_frame:
            frame_changed, num_changes = self._detect_frame_changes(self.last_frame, game_state.frame)
            context['frame_changed'] = frame_changed
            context['num_changes'] = num_changes
            logger.debug(f"Frame changes detected: {frame_changed} ({num_changes} pixels)")

        # Update tracking
        self.last_frame = game_state.frame.copy() if game_state.frame else None
        self.last_score = game_state.score

        return game_state

    def get_random_action(self, available_actions: Optional[List[str]] = None,
                         exclude_actions: Optional[List[str]] = None,
                         prefer_full_action_set: bool = False) -> str:
        """Get a random action from available actions.
        
        ENHANCED: Now checks subgoal planning first (Competitive #3, +30% gain)

        Args:
            available_actions: List of available actions
            exclude_actions: Actions to exclude from selection
            prefer_full_action_set: If True, tries to use all actions 1-7 for exploration

        Returns:
            Random action name (or subgoal-guided action if available)
        """
        # SUBGOAL INTEGRATION: Check if subgoal activator suggests an action (Tier 1: +30%)
        if hasattr(self, 'subgoal_activator') and self.subgoal_activator:
            try:
                game_id = getattr(self, '_current_game_id', None)
                level_number = getattr(self, '_current_level', None)
                
                if game_id and level_number:
                    # Get current subgoal
                    current_subgoal = self.subgoal_activator.get_current_subgoal(game_id, level_number)
                    
                    if current_subgoal:
                        # Get subgoal-suggested action
                        suggested_action_num = self.subgoal_activator.suggest_action_for_subgoal(
                            current_subgoal=current_subgoal,
                            frame_data=getattr(self, '_current_frame', None),
                            available_actions=[1, 2, 3, 4, 5, 6, 7]
                        )
                        
                        if suggested_action_num:
                            suggested_action = f"ACTION{suggested_action_num}"
                            logger.info(f"[SUBGOAL] Using subgoal-guided action: {suggested_action} "
                                       f"(goal: {current_subgoal.get('description', 'unknown')})")
                            return suggested_action
            except Exception as e:
                logger.debug(f"Subgoal action selection failed: {e}")
        
        # Fallback to random action (original logic)
        if not available_actions:
            if prefer_full_action_set:
                # For unbeaten games, ensure we try all action types 1-7
                available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]
            else:
                # Default: exclude ACTION6 unless specifically requested
                available_actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION7"]

        if exclude_actions:
            available_actions = [a for a in available_actions if a not in exclude_actions]

        if not available_actions:
            raise ValueError("No actions available after exclusions")

        return random.choice(available_actions)

    def get_random_coordinates(self, frame: List[List[int]]) -> Tuple[int, int]:
        """Get random valid coordinates within the frame.

        Args:
            frame: Current game frame

        Returns:
            Tuple of (x, y) coordinates
        """
        if not frame or not frame[0]:
            raise ValueError("Invalid frame for coordinate generation")

        height = len(frame)
        width = len(frame[0])

        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        return x, y

    def get_smart_coordinates(self, frame: List[List[int]],
                            strategy: str = "visual") -> Tuple[int, int, str]:
        """Get intelligent coordinates for ACTION6 based on visual analysis.

        This is the CORRECT way to use ACTION6:
        1. Analyze the frame for interesting features
        2. Select coordinates based on what's visually salient
        3. Detect and avoid coordinate spam/oscillation
        4. Use pseudo-button pathfinding when oscillating
        5. "Click" on those features like a touchscreen

        Args:
            frame: Current game frame
            strategy: Selection strategy
                - "visual": Analyze frame for interesting targets (RECOMMENDED)
                - "exploratory": Systematic exploration pattern
                - "random": Random coordinates (fallback)

        Returns:
            Tuple of (x, y, reason)
        """
        # CRITICAL: Validate frame dimensions first
        if not self._validate_frame_dimensions(frame, context="at get_smart_coordinates entry"):
            logger.error("[FAIL] Frame validation failed, falling back to safe coordinates")
            # Return safe fallback coordinates
            return 32, 32, "Fallback center (frame validation failed)"
        
        if not frame or not frame[0]:
            raise ValueError("Invalid frame for coordinate generation")

        height = len(frame)
        width = len(frame[0])

        if strategy == "visual":
            # CORRECT: Analyze frame to find interesting targets
            analysis = self.visual_analyzer.analyze_frame(frame)
            target = self.visual_analyzer.select_best_target(analysis)

            if target:
                x, y, reason = target
                
                # Check coordinate diversity (spam/oscillation detection)
                diversity_check = self._check_coordinate_diversity(x, y)
                
                # Log progress and threshold info
                progress = (self.level_action_count / self.level_max_actions * 100) if self.level_max_actions > 0 else 0
                logger.debug(f"Level progress: {progress:.0f}%, Spam threshold: {diversity_check['threshold_used']}")
                
                if diversity_check['spam_detected']:
                    logger.warning(f"🚫 Coordinate spam detected (threshold: {diversity_check['threshold_used']}) - forcing new target")
                    # Force exploration to break out of spam pattern
                    x, y = self.visual_analyzer.get_exploratory_coordinates(
                        frame, 
                        radius=self.visual_analyzer.exploration_radius + 5
                    )
                    reason = f"Anti-spam exploration (was {self.consecutive_similar_coordinate} clicks)"
                    # Reset spam counter
                    self.consecutive_similar_coordinate = 0
                
                elif diversity_check['oscillation_detected']:
                    logger.warning(f"[SYNC] Coordinate oscillation detected (unproductive) - trying pseudo-button pathfinding")
                    # Try pathfinding between oscillating points
                    combination_target = self.visual_analyzer._find_combination_target(
                        analysis.get("targets", [])
                    )
                    if combination_target:
                        x, y, reason = combination_target
                        # CRITICAL: Validate coordinates are within frame bounds
                        if not self._validate_coordinates(x, y, frame):
                            logger.warning(f"[WARN] Pathfinding target ({x}, {y}) outside frame bounds, using exploratory")
                            x, y = self.visual_analyzer.get_exploratory_coordinates(
                                frame,
                                radius=self.visual_analyzer.exploration_radius
                            )
                            reason = "Exploratory (invalid pathfinding target)"
                        else:
                            reason = f"Pseudo-button pathfinding: {reason}"
                            logger.info(f"[TARGET] Pathfinding target: ({x}, {y})")
                    else:
                        # Force wide exploration
                        self.visual_analyzer.exploration_radius = min(
                            self.visual_analyzer.exploration_radius + 5,
                            self.visual_analyzer.max_exploration_radius
                        )
                        x, y = self.visual_analyzer.get_exploratory_coordinates(
                            frame,
                            radius=self.visual_analyzer.exploration_radius + 10
                        )
                        reason = "Anti-oscillation wide search"
                    
                    # Reset oscillation detection after handling
                    self.visual_analyzer.oscillation_detected = False
                    self.consecutive_similar_coordinate = 0
                
                elif 'Productive spam' in diversity_check['reason'] or 'Productive oscillation' in diversity_check['reason']:
                    # Log productive spam/oscillation (frame is changing)
                    logger.info(f"[OK] {diversity_check['reason']} at ({x}, {y})")
                
                # FINAL VALIDATION: Ensure coordinates are within bounds before returning
                if not self._validate_coordinates(x, y, frame):
                    logger.error(f"[FAIL] Final validation failed: ({x}, {y}) outside bounds for frame {len(frame)}x{len(frame[0]) if frame else 0}")
                    # Fallback to safe center coordinates
                    x = len(frame[0]) // 2 if frame and frame[0] else 0
                    y = len(frame) // 2 if frame else 0
                    reason = "Fallback to center (validation failed)"
                    logger.warning(f"[WARN] Using fallback coordinates: ({x}, {y})")
                
                # Mark this coordinate as clicked to avoid spamming
                self.visual_analyzer.mark_coordinate_clicked(x, y)
                logger.info(f"ACTION6 target found: ({x}, {y}) - {reason}")
                return x, y, reason
            else:
                # No obvious targets, use exploratory
                logger.debug("No visual targets found, using exploratory mode")
                x, y = self.visual_analyzer.get_exploratory_coordinates(frame)
                self.visual_analyzer.mark_coordinate_clicked(x, y)
                
                # Still check diversity even for exploratory
                diversity_check = self._check_coordinate_diversity(x, y)
                
                return x, y, "Exploratory search (no obvious targets)"

        elif strategy == "exploratory":
            # Systematic exploration around frame center
            x, y = self.visual_analyzer.get_exploratory_coordinates(frame)
            
            # Check diversity
            diversity_check = self._check_coordinate_diversity(x, y)
            if diversity_check['spam_detected'] or diversity_check['oscillation_detected']:
                # Expand search radius
                x, y = self.visual_analyzer.get_exploratory_coordinates(
                    frame,
                    radius=15
                )
            
            return x, y, "Systematic exploration"

        elif strategy == "random":
            # Fallback: random coordinates (NOT RECOMMENDED)
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            logger.warning("Using random ACTION6 coordinates - this is suboptimal!")
            return x, y, "Random fallback"

        else:
            raise ValueError(f"Unknown coordinate strategy: {strategy}")

    async def send_random_action(self, available_actions: Optional[List[str]] = None,
                               exclude_actions: Optional[List[str]] = None,
                               frame: Optional[List[List[int]]] = None) -> GameState:
        """Send a random action.

        Args:
            available_actions: List of available actions
            exclude_actions: Actions to exclude
            frame: Current frame for ACTION6 coordinates

        Returns:
            New game state
        """
        action = self.get_random_action(available_actions, exclude_actions)

        if action == "ACTION6":
            if not frame:
                raise ValueError("Frame required for ACTION6")
            x, y = self.get_random_coordinates(frame)
            random_reasoning = {
                'action': 'ACTION6',
                'reasoning': 'Random action selection',
                'coordinate': {'x': x, 'y': y}
            }
            return await self.send_action_6(x, y, frame, reasoning=random_reasoning)
        else:
            method_name = f"send_{action.lower()}"
            method = getattr(self, method_name)
            random_reasoning = {
                'action': action,
                'reasoning': 'Random action selection'
            }
            return await method(reasoning=random_reasoning)

    def analyze_action_effectiveness(self, game_id: str) -> Dict[str, Any]:
        """Analyze action effectiveness for a game.

        Args:
            game_id: Game ID to analyze

        Returns:
            Action effectiveness analysis
        """
        effectiveness_data = self.session_manager.db.get_action_effectiveness(game_id)

        if not effectiveness_data:
            return {"message": "No action effectiveness data found"}

        analysis = {
            "game_id": game_id,
            "total_actions": len(effectiveness_data),
            "actions": {}
        }

        for data in effectiveness_data:
            action_num = data['action_number']
            analysis["actions"][f"ACTION{action_num}"] = {
                "attempts": data['attempts'],
                "successes": data['successes'],
                "success_rate": data['success_rate'],
                "avg_score_impact": data['avg_score_impact']
            }

        # Find best and worst actions
        if effectiveness_data:
            best_action = max(effectiveness_data, key=lambda x: x['success_rate'])
            worst_action = min(effectiveness_data, key=lambda x: x['success_rate'])

            analysis["best_action"] = f"ACTION{best_action['action_number']}"
            analysis["best_success_rate"] = best_action['success_rate']
            analysis["worst_action"] = f"ACTION{worst_action['action_number']}"
            analysis["worst_success_rate"] = worst_action['success_rate']

        return analysis

    def get_action_traces(self, game_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get action traces for analysis.

        Args:
            game_id: Optional game ID filter
            limit: Maximum number of traces to return

        Returns:
            List of action traces
        """
        return self.session_manager.db.get_action_traces(
            game_id=game_id,
            limit=limit
        )

    def get_score_progression(self, game_id: str) -> List[Dict[str, Any]]:
        """Get score progression for a game.

        Args:
            game_id: Game ID

        Returns:
            List of score progression data
        """
        return self.session_manager.db.get_score_history(game_id=game_id)

    async def smart_action_selection(self, game_state: GameState,
                                   strategy: str = "balanced", 
                                   is_unbeaten_game: bool = False) -> str:
        """Select action using basic strategy with diversity tracking.

        Args:
            game_state: Current game state
            strategy: Selection strategy ('random', 'balanced', 'conservative', 'unbeaten_exploration')
            is_unbeaten_game: True if this game has never had level completions by any agent

        Returns:
            Selected action
        """
        # Normalize available_actions to string format (API may return ints or strings)
        raw_available = game_state.available_actions or [1, 2, 3, 4, 5, 6, 7]
        available = [f"ACTION{a}" if isinstance(a, int) else a for a in raw_available]

        # Track action diversity to prevent spamming same action
        selected_action = None

        if strategy == "unbeaten_exploration" or is_unbeaten_game:
            # For unbeaten games: Ensure ALL available actions 1-7 are tried
            # This gives maximum exploration for difficult games
            logger.info(f"[TARGET] UNBEATEN GAME MODE: Trying full action set for exploration")
            
            # Check if we've been missing any action types
            all_possible = ["ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"]
            untried_actions = [a for a in all_possible if a in available and a not in self.recent_actions]
            
            if untried_actions:
                # Prioritize actions we haven't tried recently
                selected_action = random.choice(untried_actions)
                logger.info(f"[NEW] Trying untested action: {selected_action}")
            else:
                # All actions tried recently, use normal diversity selection but include ACTION6
                selected_action = self._select_with_diversity(available)

        elif strategy == "random":
            selected_action = self._select_with_diversity(available)

        elif strategy == "conservative":
            # Prefer actions 1-5, avoid ACTION6 unless specifically needed
            safe_actions = [a for a in available if a != "ACTION6"]
            selected_action = self._select_with_diversity(safe_actions if safe_actions else available)

        elif strategy == "balanced":
            # Use effectiveness data if available
            if self.session_manager.current_game_id:
                effectiveness = self.session_manager.db.get_action_effectiveness(
                    self.session_manager.current_game_id
                )

                if effectiveness:
                    # Weight actions by success rate
                    weights = {}
                    for data in effectiveness:
                        action_name = f"ACTION{data['action_number']}"
                        if action_name in available:
                            weights[action_name] = max(0.1, data['success_rate'])

                    if weights:
                        # Weighted random selection with diversity
                        selected_action = self._select_with_diversity(
                            list(weights.keys()), 
                            weights=list(weights.values())
                        )

            # Fall back to diverse random selection
            if selected_action is None:
                selected_action = self._select_with_diversity(available)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Track this action
        self._track_action(selected_action)
        
        return selected_action
    
    def _select_with_diversity(self, available_actions: List[str], 
                               weights: Optional[List[float]] = None) -> str:
        """Select action with diversity to avoid spamming same action.
        
        Args:
            available_actions: List of available actions
            weights: Optional weights for each action
            
        Returns:
            Selected action with diversity enforcement
        """
        if not available_actions:
            raise ValueError("No actions available")
        
        # Only apply diversity enforcement if there are multiple actions available
        if len(available_actions) <= 1:
            # If only one action available (e.g., ACTION6 only games), just use it
            return available_actions[0]
        
        # Check for action stagnation (same action repeated too many times)
        if self.consecutive_same_action >= 5:
            # Force diversity - exclude the stagnant action
            diverse_actions = [a for a in available_actions if a != self.last_action]
            if diverse_actions:
                logger.info(f"Action stagnation detected ({self.last_action} x{self.consecutive_same_action}) - forcing diversity")
                # Reset counter
                self.consecutive_same_action = 0
                # Select from diverse actions
                if weights and len(weights) == len(available_actions):
                    # Adjust weights to exclude stagnant action
                    diverse_weights = [w for a, w in zip(available_actions, weights) if a != self.last_action]
                    return random.choices(diverse_actions, weights=diverse_weights)[0]
                else:
                    return random.choice(diverse_actions)
        
        # Check recent action history for oscillation
        # Only check if we have multiple actions available
        if len(self.recent_actions) >= self.max_action_history:
            unique_recent = len(set(self.recent_actions))
            # Only warn about oscillation if we have multiple actions but keep using 1-2
            if unique_recent <= 2 and len(available_actions) > 2:
                # Oscillating between only 1-2 actions when more are available - force diversity
                logger.warning(f"Action oscillation detected! Only {unique_recent} unique actions in last {self.max_action_history} (but {len(available_actions)} available)")
                # Exclude recently used actions
                recent_set = set(self.recent_actions[-5:])  # Last 5 actions
                diverse_actions = [a for a in available_actions if a not in recent_set]
                if diverse_actions:
                    logger.info(f"Breaking oscillation - trying different action")
                    return random.choice(diverse_actions)
        
        # Normal selection with optional weights
        if weights:
            return random.choices(available_actions, weights=weights)[0]
        else:
            return random.choice(available_actions)
    
    def _track_action(self, action: str):
        """Track action for diversity monitoring.
        
        Args:
            action: Action that was selected
        """
        # Track consecutive same action
        if action == self.last_action:
            self.consecutive_same_action += 1
        else:
            self.consecutive_same_action = 1
            self.last_action = action
        
        # Track action history
        self.recent_actions.append(action)
        if len(self.recent_actions) > self.max_action_history:
            self.recent_actions.pop(0)
        
        # Log if action is being repeated
        if self.consecutive_same_action >= 3:
            logger.debug(f"Action {action} repeated {self.consecutive_same_action} times")