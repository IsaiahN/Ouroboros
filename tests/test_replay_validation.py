import asyncio
import json
import os
from types import SimpleNamespace

import pytest

from core_gameplay import GameplayEngine


class DummySpine:
    def __init__(self):
        self.starts = []
        self.ends = []

    def record_attempt_start(self, **kwargs):
        self.starts.append(kwargs)

    def record_attempt_end(self, **kwargs):
        self.ends.append(kwargs)


def make_engine_with_mode(db_rows):
    engine = GameplayEngine.__new__(GameplayEngine)
    engine.game_config = {
        'mode': 'REPLAY_VALIDATION',
        'agent_role': 'generalist',
        'generation': 1,
        'max_total_actions': 1,
    }
    # Initialize required attributes that would normally be set in __init__
    engine._games_played = 0
    engine._total_wins = 0

    # Create minimal config with defaults
    class MinimalConfig:
        default_max_actions = 2000
        default_render_mode = None
        verbose = False

    engine._config = MinimalConfig()

    class DummyDB:
        def execute_query(self, *args, **kwargs):
            return db_rows

    engine.db = DummyDB()
    engine.spine_emitter = DummySpine()
    engine.session_manager = SimpleNamespace(is_running=False)
    return engine


@pytest.mark.skip(reason="Replay validation mode not implemented - tests require full engine initialization")
def test_replay_validation_returns_pointer_when_present():
    replay_entry = {
        'replay_id': 'r1',
        'scorecard_id': 's1',
        'arc_game_id': 'as66-1',
        'tags': 't1'
    }
    engine = make_engine_with_mode([replay_entry])

    state = asyncio.run(engine.play_single_game('as66-1'))

    assert state['final_state'] == 'REPLAY_POINTER'
    assert state['replay_id'] == 'r1'
    assert engine.spine_emitter.starts and engine.spine_emitter.ends


@pytest.mark.skip(reason="Replay validation mode not implemented - tests require full engine initialization")
def test_replay_validation_missing_pointer():
    engine = make_engine_with_mode([])

    state = asyncio.run(engine.play_single_game('as66-1'))

    assert state['final_state'] == 'REPLAY_MISSING'
    assert state['replay_available'] is False
    assert engine.spine_emitter.starts and engine.spine_emitter.ends


def test_replay_drift_guardrails_optional():
    """Optional drift check: compare replay metrics to a baseline if provided.

    CI can set REPLAY_BASELINE_PATH and REPLAY_METRICS_PATH to JSON files with
    {"action_counts": {...}, "guard_counts": {...}}. If not set, skip.
    """

    baseline_path = os.getenv('REPLAY_BASELINE_PATH')
    metrics_path = os.getenv('REPLAY_METRICS_PATH')
    if not baseline_path or not metrics_path:
        pytest.skip("Replay drift check requires REPLAY_BASELINE_PATH and REPLAY_METRICS_PATH")

    def _load_counts(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('action_counts', {}), data.get('guard_counts', {})

    baseline_actions, baseline_guards = _load_counts(baseline_path)
    metrics_actions, metrics_guards = _load_counts(metrics_path)

    def _max_delta(current, baseline):
        keys = set(current) | set(baseline)
        return max(
            abs(float(current.get(k, 0)) - float(baseline.get(k, 0))) for k in keys
        ) if keys else 0.0

    action_delta = _max_delta(metrics_actions, baseline_actions)
    guard_delta = _max_delta(metrics_guards, baseline_guards)

    assert action_delta <= 0.05, f"Replay action distribution drift too high: {action_delta:.3f}"
    assert guard_delta <= 2, f"Replay guard incidence drift too high: {guard_delta}"
