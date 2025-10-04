"""
Shared game context structures for strategy system.
"""
from disable_pycache import *

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

@dataclass
class GameContext:
    """Standardized game context for strategy decisions"""
    game_id: str = ""
    session_id: str = ""
    current_score: float = 0.0
    win_score: float = 100.0
    actions_taken: int = 0
    available_actions: List[int] = None
    game_state: str = "NOT_FINISHED"

    # Analysis results
    score_momentum: str = "stable"  # 'increasing', 'decreasing', 'stable'
    risk_level: str = "medium"     # 'low', 'medium', 'high'
    emergency_detected: bool = False

    # Historical context
    recent_scores: List[float] = None
    recent_actions: List[str] = None
    frame_data: Dict = None

    # Pattern matching
    action_history: List[str] = None
    score_history: List[float] = None

    # Game type and difficulty
    game_type: str = "unknown"
    difficulty_level: str = "medium"

    def __post_init__(self):
        if self.available_actions is None:
            self.available_actions = []
        if self.recent_scores is None:
            self.recent_scores = []
        if self.recent_actions is None:
            self.recent_actions = []
        if self.frame_data is None:
            self.frame_data = {}
        if self.action_history is None:
            self.action_history = []
        if self.score_history is None:
            self.score_history = []

    @property
    def score_progress(self) -> float:
        """Calculate progress toward win score (0.0 to 1.0)"""
        if self.win_score <= 0:
            return 0.0
        return min(1.0, self.current_score / self.win_score)

    @property
    def is_near_victory(self) -> bool:
        """Check if close to winning"""
        return self.score_progress >= 0.8

    @property
    def is_struggling(self) -> bool:
        """Check if performance is poor"""
        return (self.actions_taken > 10 and
                self.score_progress < 0.3 and
                self.score_momentum == "decreasing")

    @property
    def actions_remaining_estimate(self) -> int:
        """Estimate actions remaining based on typical game length"""
        typical_game_length = 25  # Estimate
        return max(0, typical_game_length - self.actions_taken)

    @property
    def time_pressure(self) -> bool:
        """Check if under time pressure"""
        return self.actions_remaining_estimate < 5

    def update_from_game_state(self, game_state):
        """Update context from game state object"""
        try:
            # Handle various score formats
            score = getattr(game_state, 'score', 0.0)
            if isinstance(score, (list, tuple)):
                score = score[0] if len(score) > 0 else 0.0
            self.current_score = float(score)

            # Handle win score
            win_score = getattr(game_state, 'win_score', 100.0)
            if isinstance(win_score, (list, tuple)):
                win_score = win_score[0] if len(win_score) > 0 else 100.0
            self.win_score = float(win_score)

            self.available_actions = getattr(game_state, 'available_actions', [])
            self.game_state = getattr(game_state, 'state', 'NOT_FINISHED')
            self.frame_data = getattr(game_state, 'frame', {})

            # Update score history
            if self.current_score not in self.score_history:
                self.score_history.append(self.current_score)
                # Keep last 10 scores
                if len(self.score_history) > 10:
                    self.score_history.pop(0)

        except Exception as e:
            # Fallback to safe defaults
            pass

    def add_action(self, action: str):
        """Add action to history"""
        self.action_history.append(action)
        self.actions_taken += 1
        # Keep last 10 actions
        if len(self.action_history) > 10:
            self.action_history.pop(0)

    def get_recent_action_sequence(self, length: int = 3) -> List[str]:
        """Get recent action sequence"""
        return self.action_history[-length:] if len(self.action_history) >= length else self.action_history

    def get_pattern_signature(self) -> str:
        """Generate a hash signature for current game state pattern"""
        try:
            pattern_data = {
                'score_progress': round(self.score_progress, 2),
                'score_momentum': self.score_momentum,
                'recent_actions': self.get_recent_action_sequence(),
                'available_actions': sorted(self.available_actions),
                'game_type': self.game_type
            }
            pattern_str = json.dumps(pattern_data, sort_keys=True)
            return hashlib.md5(pattern_str.encode()).hexdigest()[:16]
        except:
            return "unknown_pattern"

    def calculate_score_momentum(self) -> str:
        """Calculate score momentum from history"""
        if len(self.score_history) < 3:
            return 'stable'

        recent = self.score_history[-3:]

        # Check for clear trends
        if recent[-1] > recent[-2] and recent[-2] > recent[-3]:
            return 'increasing'
        elif recent[-1] < recent[-2] and recent[-2] < recent[-3]:
            return 'decreasing'
        else:
            return 'stable'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'game_id': self.game_id,
            'session_id': self.session_id,
            'current_score': self.current_score,
            'win_score': self.win_score,
            'actions_taken': self.actions_taken,
            'available_actions': self.available_actions,
            'game_state': self.game_state,
            'score_momentum': self.score_momentum,
            'risk_level': self.risk_level,
            'emergency_detected': self.emergency_detected,
            'score_progress': self.score_progress,
            'game_type': self.game_type,
            'difficulty_level': self.difficulty_level
        }