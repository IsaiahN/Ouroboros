from __future__ import annotations

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Must be early

"""RunContext scaffold for behavior-parity loop split.

Fields align with architecture/runtime/README.md and events.md. This is a holder for
attempt-level state passed through INIT/STEP/POST_STEP/FINALIZE. Guard enforcement and
DB writes remain outside; this object is purely in-memory.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BudgetState:
    actions_remaining: int
    game_actions_remaining: int


@dataclass
class HeartbeatState:
    step_idx: int = 0
    max_steps: Optional[int] = None


@dataclass
class GuardState:
    budget_ok: bool = True
    mode_ok: bool = True
    role_ok: bool = True


@dataclass
class RunContext:
    attempt_id: str
    game_id: str
    level: Optional[int]
    generation: Optional[int]
    agent_id: Optional[str]
    role: str
    mode: str  # LIVE, REPLAY_VALIDATION, EVAL
    budgets: BudgetState
    w_A_weight: Optional[float] = None
    w_B_weight: Optional[float] = None
    w_R_weight: Optional[float] = None
    sequence_source_id: Optional[str] = None
    operator_source_id: Optional[str] = None
    source_mode: Optional[str] = None
    available_actions: List[int] = field(default_factory=list)
    heartbeat: HeartbeatState = field(default_factory=HeartbeatState)
    guards: GuardState = field(default_factory=GuardState)
    attention_windows: Dict[int, Any] = field(default_factory=dict)
    hypothesis_context: Dict[str, Any] = field(default_factory=dict)
    biography_context: Dict[str, Any] = field(default_factory=dict)
    competence_rollup: Dict[str, Any] = field(default_factory=dict)

    def next_step(self) -> None:
        self.heartbeat.step_idx += 1

    def decrement_actions(self, delta: int = 1) -> None:
        self.budgets.actions_remaining -= delta
        self.budgets.game_actions_remaining -= delta
        self.guards.budget_ok = self.budgets.actions_remaining >= 0 and self.budgets.game_actions_remaining >= 0

    def set_available_actions(self, actions: List[int]) -> None:
        self.available_actions = actions

    def record_attention_window(self, step_idx: int, window: Any) -> None:
        self.attention_windows[step_idx] = window

    def guard_snapshot(self) -> Dict[str, bool]:
        return {
            "budget_ok": self.guards.budget_ok,
            "mode_ok": self.guards.mode_ok,
            "role_ok": self.guards.role_ok,
        }
