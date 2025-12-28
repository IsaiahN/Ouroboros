"""
Console Metrics Capture - Real-time metrics from console output
================================================================

Captures structured metrics during gameplay without needing API access
to reasoning logs. Uses in-memory aggregation during each generation.

Rule 1: Disable pycache
Rule 2: All data in database (final metrics stored)
Rule 11: No unicode emojis
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class GameMetrics:
    """Metrics for a single game."""
    game_id: str
    game_type: str
    agent_id: str
    final_score: float = 0.0
    levels_completed: int = 0
    total_actions: int = 0
    cods_activations: int = 0
    escape_attempts: int = 0
    sequence_replays: int = 0
    stuck_detections: int = 0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None


@dataclass
class GenerationMetrics:
    """Aggregated metrics for a generation."""
    generation: int
    games_played: int = 0
    total_score: float = 0.0
    total_levels: int = 0
    total_actions: int = 0
    total_cods_activations: int = 0
    total_escape_attempts: int = 0
    total_sequence_replays: int = 0
    total_stuck_detections: int = 0
    level_completions: int = 0  # Games with at least 1 level completed
    positive_scores: int = 0    # Games with score > 0
    max_score: float = 0.0
    max_levels: int = 0
    games_by_type: Dict[str, int] = field(default_factory=dict)
    scores_by_type: Dict[str, float] = field(default_factory=dict)
    
    def add_game(self, game: GameMetrics):
        """Add game metrics to generation totals."""
        self.games_played += 1
        self.total_score += game.final_score
        self.total_levels += game.levels_completed
        self.total_actions += game.total_actions
        self.total_cods_activations += game.cods_activations
        self.total_escape_attempts += game.escape_attempts
        self.total_sequence_replays += game.sequence_replays
        self.total_stuck_detections += game.stuck_detections
        
        if game.levels_completed > 0:
            self.level_completions += 1
        
        if game.final_score > 0:
            self.positive_scores += 1
        
        self.max_score = max(self.max_score, game.final_score)
        self.max_levels = max(self.max_levels, game.levels_completed)
        
        # Track by game type
        game_type = game.game_type
        if game_type not in self.games_by_type:
            self.games_by_type[game_type] = 0
            self.scores_by_type[game_type] = 0.0
        self.games_by_type[game_type] += 1
        self.scores_by_type[game_type] += game.final_score
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics for health monitoring."""
        games = max(self.games_played, 1)  # Avoid division by zero
        
        return {
            'generation': self.generation,
            'games_played': self.games_played,
            'avg_score': self.total_score / games,
            'avg_levels': self.total_levels / games,
            'avg_actions': self.total_actions / games,
            'max_score': self.max_score,
            'max_levels': self.max_levels,
            'level_completions': self.level_completions,
            'positive_scores': self.positive_scores,
            'level_completion_rate': self.level_completions / games,
            'positive_score_rate': self.positive_scores / games,
            'cods_activations': self.total_cods_activations,
            'cods_rate': self.total_cods_activations / games,
            'escape_attempts': self.total_escape_attempts,
            'sequence_replays': self.total_sequence_replays,
            'stuck_detections': self.total_stuck_detections,
            'games_by_type': self.games_by_type,
            'avg_score_by_type': {
                gt: self.scores_by_type[gt] / count
                for gt, count in self.games_by_type.items()
            }
        }


class ConsoleMetricsCapture:
    """
    Capture and aggregate metrics during evolution.
    
    This class is designed to be called from within the evolution loop
    to record metrics as games are played, providing real-time data
    without needing to query the database.
    
    Usage:
        capture = ConsoleMetricsCapture(generation=5)
        
        # During game loop:
        capture.start_game(game_id, game_type, agent_id)
        capture.record_cods_activation(game_id)
        capture.record_escape_attempt(game_id)
        capture.end_game(game_id, score, levels, actions)
        
        # After generation:
        summary = capture.get_generation_summary()
    """
    
    def __init__(self, generation: int = 0):
        self.generation = generation
        self.current_games: Dict[str, GameMetrics] = {}
        self.completed_games: List[GameMetrics] = []
        self.generation_metrics = GenerationMetrics(generation=generation)
        self._started_at = datetime.now()
    
    def reset(self, generation: int):
        """Reset for a new generation."""
        self.generation = generation
        self.current_games = {}
        self.completed_games = []
        self.generation_metrics = GenerationMetrics(generation=generation)
        self._started_at = datetime.now()
    
    # =========================================================================
    # GAME LIFECYCLE
    # =========================================================================
    
    def start_game(self, game_id: str, game_type: str, agent_id: str):
        """Record game start."""
        self.current_games[game_id] = GameMetrics(
            game_id=game_id,
            game_type=game_type,
            agent_id=agent_id
        )
    
    def end_game(
        self,
        game_id: str,
        final_score: float,
        levels_completed: int,
        total_actions: int
    ):
        """Record game end and finalize metrics."""
        if game_id not in self.current_games:
            # Game wasn't started with start_game, create entry
            game = GameMetrics(
                game_id=game_id,
                game_type=game_id[:4] if len(game_id) >= 4 else 'unknown',
                agent_id='unknown',
                final_score=final_score,
                levels_completed=levels_completed,
                total_actions=total_actions
            )
        else:
            game = self.current_games.pop(game_id)
            game.final_score = final_score
            game.levels_completed = levels_completed
            game.total_actions = total_actions
        
        game.ended_at = datetime.now().isoformat()
        self.completed_games.append(game)
        self.generation_metrics.add_game(game)
    
    # =========================================================================
    # IN-GAME EVENTS
    # =========================================================================
    
    def record_cods_activation(self, game_id: str):
        """Record CODS suggesting an action."""
        if game_id in self.current_games:
            self.current_games[game_id].cods_activations += 1
    
    def record_escape_attempt(self, game_id: str):
        """Record stuck detection escape attempt."""
        if game_id in self.current_games:
            self.current_games[game_id].escape_attempts += 1
    
    def record_sequence_replay(self, game_id: str):
        """Record sequence being replayed."""
        if game_id in self.current_games:
            self.current_games[game_id].sequence_replays += 1
    
    def record_stuck_detection(self, game_id: str):
        """Record stuck state detection."""
        if game_id in self.current_games:
            self.current_games[game_id].stuck_detections += 1
    
    def record_action(self, game_id: str, action: str):
        """Record an action (optional - for detailed tracking)."""
        if game_id in self.current_games:
            self.current_games[game_id].total_actions += 1
    
    # =========================================================================
    # SUMMARIES
    # =========================================================================
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary metrics for Oracle health monitoring."""
        summary = self.generation_metrics.get_summary()
        
        # Add timing info
        duration = (datetime.now() - self._started_at).total_seconds()
        summary['duration_seconds'] = duration
        summary['games_per_minute'] = (summary['games_played'] / duration * 60) if duration > 0 else 0
        
        return summary
    
    def get_game_metrics(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific game."""
        # Check current games
        if game_id in self.current_games:
            game = self.current_games[game_id]
            return {
                'game_id': game.game_id,
                'game_type': game.game_type,
                'agent_id': game.agent_id,
                'final_score': game.final_score,
                'levels_completed': game.levels_completed,
                'total_actions': game.total_actions,
                'cods_activations': game.cods_activations,
                'escape_attempts': game.escape_attempts,
                'sequence_replays': game.sequence_replays,
                'stuck_detections': game.stuck_detections,
                'status': 'in_progress'
            }
        
        # Check completed games
        for game in self.completed_games:
            if game.game_id == game_id:
                return {
                    'game_id': game.game_id,
                    'game_type': game.game_type,
                    'agent_id': game.agent_id,
                    'final_score': game.final_score,
                    'levels_completed': game.levels_completed,
                    'total_actions': game.total_actions,
                    'cods_activations': game.cods_activations,
                    'escape_attempts': game.escape_attempts,
                    'sequence_replays': game.sequence_replays,
                    'stuck_detections': game.stuck_detections,
                    'status': 'completed'
                }
        
        return None
    
    def get_by_game_type(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics broken down by game type."""
        by_type = defaultdict(lambda: {
            'games': 0,
            'total_score': 0.0,
            'total_levels': 0,
            'total_actions': 0,
            'cods_activations': 0,
            'level_completions': 0
        })
        
        for game in self.completed_games:
            gt = game.game_type
            by_type[gt]['games'] += 1
            by_type[gt]['total_score'] += game.final_score
            by_type[gt]['total_levels'] += game.levels_completed
            by_type[gt]['total_actions'] += game.total_actions
            by_type[gt]['cods_activations'] += game.cods_activations
            if game.levels_completed > 0:
                by_type[gt]['level_completions'] += 1
        
        # Calculate averages
        result = {}
        for gt, data in by_type.items():
            games = max(data['games'], 1)
            result[gt] = {
                'games': data['games'],
                'avg_score': data['total_score'] / games,
                'avg_levels': data['total_levels'] / games,
                'avg_actions': data['total_actions'] / games,
                'cods_rate': data['cods_activations'] / games,
                'level_completion_rate': data['level_completions'] / games
            }
        
        return result
    
    def print_summary(self):
        """Print generation summary to console."""
        summary = self.get_generation_summary()
        
        print(f"\n[METRICS] Generation {summary['generation']} Summary")
        print("-" * 50)
        print(f"  Games Played: {summary['games_played']}")
        print(f"  Avg Score: {summary['avg_score']:.2f} (max: {summary['max_score']:.1f})")
        print(f"  Avg Levels: {summary['avg_levels']:.2f} (max: {summary['max_levels']})")
        print(f"  Avg Actions: {summary['avg_actions']:.0f}")
        print(f"  Level Completions: {summary['level_completions']}/{summary['games_played']} "
              f"({summary['level_completion_rate']:.1%})")
        print(f"  Positive Scores: {summary['positive_scores']}/{summary['games_played']} "
              f"({summary['positive_score_rate']:.1%})")
        print(f"  CODS Activations: {summary['cods_activations']} "
              f"({summary['cods_rate']:.1f}/game)")
        print(f"  Escape Attempts: {summary['escape_attempts']}")
        print(f"  Stuck Detections: {summary['stuck_detections']}")
        print(f"  Duration: {summary['duration_seconds']:.0f}s "
              f"({summary['games_per_minute']:.1f} games/min)")
        
        if summary['games_by_type']:
            print(f"\n  By Game Type:")
            avg_by_type = summary.get('avg_score_by_type', {})
            for gt, count in sorted(summary['games_by_type'].items()):
                avg = avg_by_type.get(gt, 0)
                print(f"    {gt}: {count} games, avg score {avg:.2f}")
        
        print("-" * 50)


# =============================================================================
# SINGLETON FOR GLOBAL ACCESS
# =============================================================================

_global_capture: Optional[ConsoleMetricsCapture] = None


def get_metrics_capture(generation: int = 0) -> ConsoleMetricsCapture:
    """Get or create global metrics capture instance."""
    global _global_capture
    
    if _global_capture is None:
        _global_capture = ConsoleMetricsCapture(generation=generation)
    elif _global_capture.generation != generation:
        # New generation, reset
        _global_capture.reset(generation)
    
    return _global_capture


def reset_metrics_capture(generation: int):
    """Reset global metrics capture for new generation."""
    global _global_capture
    
    if _global_capture is None:
        _global_capture = ConsoleMetricsCapture(generation=generation)
    else:
        _global_capture.reset(generation)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def record_game_start(game_id: str, game_type: str, agent_id: str):
    """Record game start (uses global capture)."""
    if _global_capture:
        _global_capture.start_game(game_id, game_type, agent_id)


def record_game_end(game_id: str, score: float, levels: int, actions: int):
    """Record game end (uses global capture)."""
    if _global_capture:
        _global_capture.end_game(game_id, score, levels, actions)


def record_cods(game_id: str):
    """Record CODS activation (uses global capture)."""
    if _global_capture:
        _global_capture.record_cods_activation(game_id)


def record_escape(game_id: str):
    """Record escape attempt (uses global capture)."""
    if _global_capture:
        _global_capture.record_escape_attempt(game_id)


def record_stuck(game_id: str):
    """Record stuck detection (uses global capture)."""
    if _global_capture:
        _global_capture.record_stuck_detection(game_id)


def get_summary() -> Optional[Dict[str, Any]]:
    """Get generation summary (uses global capture)."""
    if _global_capture:
        return _global_capture.get_generation_summary()
    return None


if __name__ == "__main__":
    # Quick test
    capture = ConsoleMetricsCapture(generation=1)
    
    # Simulate some games
    for i in range(5):
        game_id = f"sp80-test{i}"
        capture.start_game(game_id, "sp80", f"agent_{i}")
        capture.record_cods_activation(game_id)
        capture.record_cods_activation(game_id)
        capture.record_stuck_detection(game_id)
        capture.record_escape_attempt(game_id)
        capture.end_game(game_id, i * 0.5, i, 100 + i * 50)
    
    capture.print_summary()
    
    print("\nBy game type:")
    for gt, data in capture.get_by_game_type().items():
        print(f"  {gt}: {data}")
