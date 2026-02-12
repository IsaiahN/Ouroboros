#!/usr/bin/env python3
"""
Shared data types for evolution system (Phase 4.1 extraction).

AgentState and GameResult are used by:
- evolution_runner.py (thin orchestrator)
- game_player.py (creates GameResult)
- result_recorder.py (consumes GameResult)
- generation_orchestrator.py (manages AgentState population)
"""

import os
import sys

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from dataclasses import dataclass, field
from typing import List


@dataclass
class AgentState:
    """Minimal agent state for evolution."""

    agent_id: str
    generation: int = 0
    total_score: float = 0.0
    games_played: int = 0
    wins: int = 0

    @property
    def avg_score(self) -> float:
        return self.total_score / max(1, self.games_played)

    @property
    def win_rate(self) -> float:
        return self.wins / max(1, self.games_played)


@dataclass
class GameResult:
    """Result of a single game."""

    game_id: str
    agent_id: str
    score: float
    levels_completed: int
    total_levels: int
    is_win: bool
    actions_taken: int
    action_sequence: List[str] = field(default_factory=list)
    frame_changes: int = 0
    coordinate_attempts: int = 0
    coordinate_successes: int = 0
