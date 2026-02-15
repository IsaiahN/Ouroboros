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

    # ─── GAP 4: RICH ACTION OUTCOME ──────────────────────────────────
    pixels_changed: int = 0            # Raw pixel count that changed
    goal_delta_before: int = 0         # Cells wrong before action
    goal_delta_after: int = 0          # Cells wrong after action
    goal_progress_delta: int = 0       # delta_before - delta_after (positive = good)
    was_productive: bool = False       # goal_progress_delta > 0
    was_destructive: bool = False      # goal_progress_delta < 0
    was_neutral: bool = False          # frame changed but goal didn't improve
    was_wasted: bool = False           # frame didn't change at all

    # ─── GAP 5: STATE TRACKING ───────────────────────────────────────
    timer_fraction: float = 1.0        # 0.0 to 1.0 (estimated from frame edges)
    timer_urgency: str = "safe"        # "safe", "moderate", "critical"
    hud_state_hash: int = 0            # Hash of HUD region for change detection
    hud_state_changed: bool = False    # Did the HUD change this step?

    # ─── GAP 1: GOAL-STATE FROM STABLE REGIONS ──────────────────────
    stable_region_detected: bool = False
    goal_cells_total: int = 0          # Total cells that must match
    goal_cells_correct: int = 0        # Currently matching cells
    goal_completion: float = 0.0       # correct / total

    def to_log_line(self) -> str:
        """Single-line log output for quick scanning."""
        act_str = f"A{self.action_type}"
        if self.action_x is not None:
            act_str += f"@({self.action_x},{self.action_y})"
        result = "OK" if self.frame_changed else "NO-CHG"
        if self.level_changed:
            result = "LEVEL-UP"
        # Append goal-progress indicator
        goal_tag = ""
        if self.goal_cells_total > 0:
            goal_tag = f" G:{self.goal_cells_correct}/{self.goal_cells_total}"
        if self.was_productive:
            goal_tag += "[+]"
        elif self.was_destructive:
            goal_tag += "[-]"
        return (
            f"[{self.action_number:3d}] "
            f"P:{self.perception_summary[:40]:40s} | "
            f"T:{self.strategy:8s} cert:{self.certainty:.2f} | "
            f"M:{self.map_completeness:.0%} | "
            f"{self.action_speed:8s} {act_str:12s} -> {result}{goal_tag}"
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
            # Gap 4: Rich action outcome
            'pixels_changed': self.pixels_changed,
            'goal_delta_before': self.goal_delta_before,
            'goal_delta_after': self.goal_delta_after,
            'goal_progress_delta': self.goal_progress_delta,
            'was_productive': self.was_productive,
            'was_destructive': self.was_destructive,
            'was_wasted': self.was_wasted,
            # Gap 5: State tracking
            'timer_urgency': self.timer_urgency,
            'hud_state_changed': self.hud_state_changed,
            # Gap 1: Goal-state
            'goal_cells_total': self.goal_cells_total,
            'goal_cells_correct': self.goal_cells_correct,
            'goal_completion': self.goal_completion,
        }
