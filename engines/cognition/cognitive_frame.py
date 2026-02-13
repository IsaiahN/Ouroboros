import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

"""
Cognitive Frame - Observable record of one P-T-M-A cycle.

This is what you watch in replay. Every action produces a CognitiveFrame
that records what the agent perceived, thought, mapped, and did.

Stored in memory during gameplay, can be dumped to database or
rendered to a live dashboard / replay viewer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CognitiveFrame:
    """One complete cycle of the Perceive-Think-Map-Act loop."""

    # ─── When ─────────────────────────────────────────────────────────
    action_number: int = 0
    timestamp: float = 0.0
    level: int = 1

    # ─── PERCEIVE ─────────────────────────────────────────────────────
    perception_summary: str = ""
    # e.g. "3x3 grid | 4 panels | goal: 6/9 match | 3 colors"
    panel_count: int = 0
    tile_count: int = 0
    goal_progress: float = 0.0         # 0-1
    delta_count: int = 0               # Cells differing from goal
    colors_present: List[int] = field(default_factory=list)
    puzzle_type: str = "unknown"
    spatial_confidence: float = 0.0
    overall_confidence: float = 0.0

    # ─── THINK ────────────────────────────────────────────────────────
    thought_summary: str = ""
    # e.g. "OPPORTUNITY | certainty:0.72 | strategy:exploit"
    valence: str = "neutral"           # "threat", "opportunity", "stability", "confusion", "boredom"
    arousal: float = 0.0               # 0-1
    certainty: float = 0.0             # 0-1
    agency: float = 0.0                # 0-1
    salience: float = 0.0              # 0-1 (attention-grabbing level)
    momentum: float = 0.0             # -1 to 1 (getting better vs worse)
    dominant_contributors: List[str] = field(default_factory=list)
    strategy: str = "explore"          # "explore", "exploit", "execute", "experiment"
    epistemic_state: str = "UU"        # KK/KU/UK/UU
    information_gain: float = 0.0

    # ─── MAP ──────────────────────────────────────────────────────────
    map_summary: str = ""
    # e.g. "9/9 positions explored | rule: von_neumann | plan: 3 steps"
    map_completeness: float = 0.0      # 0-1
    effects_known: int = 0
    positions_explored: int = 0
    positions_total: int = 0
    rules_discovered: List[str] = field(default_factory=list)
    has_plan: bool = False
    plan_length: int = 0
    plan_step: int = 0
    map_update: str = ""               # What was learned THIS action

    # ─── ACT ──────────────────────────────────────────────────────────
    action_summary: str = ""
    # e.g. "MAPPED: Click (52,36) | plan step 1/3"
    action_speed: str = "explore"      # "mapped", "reasoned", "explore"
    action_type: int = 0               # 1-7
    action_x: Optional[int] = None     # For click actions
    action_y: Optional[int] = None
    action_reason: str = ""
    rung_name: str = ""                # Which rung decided (for REASONED speed)
    action_confidence: float = 0.0

    # ─── RESULT (filled after action executes) ────────────────────────
    frame_changed: bool = False
    score_delta: float = 0.0
    level_changed: bool = False
    surprise: float = 0.0             # How unexpected was the result
    result_summary: str = ""
    # e.g. "Frame changed | 2 cells flipped | score +0.1 | [PROGRESS]"

    def to_log_line(self) -> str:
        """Single-line log output for quick scanning."""
        act_str = f"A{self.action_type}"
        if self.action_x is not None:
            act_str += f"@({self.action_x},{self.action_y})"
        result = "OK" if self.frame_changed else "NO-CHG"
        if self.level_changed:
            result = "LEVEL-UP"
        return (
            f"[{self.action_number:3d}] "
            f"P:{self.perception_summary[:40]:40s} | "
            f"T:{self.strategy:8s} cert:{self.certainty:.2f} | "
            f"M:{self.map_completeness:.0%} | "
            f"{self.action_speed:8s} {act_str:12s} -> {result}"
        )

    def to_dashboard(self) -> str:
        """Multi-line dashboard format for live viewing."""
        lines = [
            f"{'=' * 66}",
            f"  Action {self.action_number}  |  Level {self.level}  |  {self.puzzle_type}",
            f"{'=' * 66}",
            f" PERCEIVE  {self.perception_summary}",
            f"           confidence: {self.overall_confidence:.2f}",
            f"{'-' * 66}",
            f" THINK     {self.thought_summary}",
            f"           strategy: {self.strategy}  |  epistemic: {self.epistemic_state}",
            f"{'-' * 66}",
            f" MAP       {self.map_summary}",
        ]
        if self.map_update:
            lines.append(f"           update: {self.map_update}")
        lines.extend([
            f"{'-' * 66}",
            f" ACT       {self.action_summary}",
            f"           speed: {self.action_speed}  |  reason: {self.action_reason[:60]}",
        ])
        if self.result_summary:
            lines.extend([
                f"{'-' * 66}",
                f" RESULT    {self.result_summary}",
            ])
        lines.append(f"{'=' * 66}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database storage."""
        return {
            'action_number': self.action_number,
            'timestamp': self.timestamp,
            'level': self.level,
            'perception_summary': self.perception_summary,
            'thought_summary': self.thought_summary,
            'map_summary': self.map_summary,
            'action_summary': self.action_summary,
            'action_speed': self.action_speed,
            'action_type': self.action_type,
            'action_x': self.action_x,
            'action_y': self.action_y,
            'frame_changed': self.frame_changed,
            'score_delta': self.score_delta,
            'level_changed': self.level_changed,
            'surprise': self.surprise,
            'map_completeness': self.map_completeness,
            'certainty': self.certainty,
            'strategy': self.strategy,
            'overall_confidence': self.overall_confidence,
            'puzzle_type': self.puzzle_type,
            'salience': self.salience,
            'momentum': self.momentum,
            'dominant_contributors': self.dominant_contributors,
        }
