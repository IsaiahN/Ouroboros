import asyncio
from types import SimpleNamespace

import pytest

from core_gameplay import GameplayEngine


def make_engine_with_minimum_state():
    engine = GameplayEngine.__new__(GameplayEngine)
    engine.game_config = {
        'agent_id': 'test_agent',
        'run_context': SimpleNamespace(attempt_id='attempt-1', heartbeat=SimpleNamespace(attempt_id='attempt-1', step_idx=0)),
        'strategy': 'balanced',
    }
    engine.session_manager = SimpleNamespace(current_game_id=None, current_session_id=None)
    engine.action_handler = SimpleNamespace()
    engine._assert_frame_sanity = lambda frame: None
    engine.event_bus = SimpleNamespace(subscribe=lambda *a, **k: None, set_hook_failure_event=lambda *a, **k: None)
    engine.spine_emitter = SimpleNamespace(
        log_action_proposal=lambda **kwargs: None,
    )
    engine._prepare_action6_target = lambda *a, **k: None
    engine._prefer_non_action6 = GameplayEngine._prefer_non_action6.__get__(engine, GameplayEngine)
    engine.cods_engine = None
    engine.science_engine = None
    engine.sensation_engine = None
    engine.knowledge_synthesis = None
    engine.rule_engine = None
    engine.network_contributor = None
    engine.primitive_helper = SimpleNamespace(available=False)
    engine.sensation_engine = None
    engine.terminal_detector = None
    engine.abstraction_engine = None
    engine.weaving_reporter = None
    engine.breakthrough_detector = SimpleNamespace()
    engine.budget_allocator = SimpleNamespace()
    engine.subgoal_activator = SimpleNamespace(inject_subgoal_planner=lambda *a, **k: None)
    engine.matching_pipeline = SimpleNamespace()
    engine.subgoal_planner = None
    engine.agent_self_model = SimpleNamespace(get_discovery_phase_actions=lambda **kwargs: None)
    engine.object_detector = SimpleNamespace()
    engine.prestige_engine = SimpleNamespace()
    engine.sensation_engine = None
    engine.budget_allocator = SimpleNamespace()
    engine.breakthrough_detector = SimpleNamespace()
    engine.action_handler.subgoal_activator = None
    return engine


def test_ladder_records_escape_noop_trace():
    engine = make_engine_with_minimum_state()
    engine._forced_escape_action = 7
    state = SimpleNamespace(frame=None, score=0, available_actions=["ACTION1"], current_level=1)

    action, reason = asyncio.get_event_loop().run_until_complete(engine._select_action(state))

    assert action == "ACTION7"
    assert engine._last_ladder_rung == 'heuristic'
    ladder = engine._last_ladder_trace
    assert ladder['heuristic']['status'] == 'selected'
    assert ladder['noop']['status'] == 'skipped'
    assert ladder['sequence']['status'] in {'pending', 'skipped'}
    assert ladder['cods']['status'] in {'pending', 'skipped'}


def test_action6_fallback_prefers_movement(monkeypatch):
    engine = make_engine_with_minimum_state()

    async def smart_action_selection(game_state, strategy, is_unbeaten):
        return "ACTION6"

    engine.action_handler.smart_action_selection = smart_action_selection
    state = SimpleNamespace(frame=None, score=0, available_actions=["ACTION6", "ACTION1"], current_level=1)

    action, reason = asyncio.get_event_loop().run_until_complete(engine._select_action(state))

    assert action == "ACTION1"
    assert engine._last_ladder_rung == 'heuristic'
    ladder = engine._last_ladder_trace
    assert ladder['heuristic']['status'] == 'selected'
    assert ladder['noop']['status'] == 'skipped'


def test_action6_fallback_traces_reason(monkeypatch):
    engine = make_engine_with_minimum_state()

    async def smart_action_selection(game_state, strategy, is_unbeaten):
        return "ACTION6"

    engine.action_handler.smart_action_selection = smart_action_selection
    # Force salience target to be missing so fallback path triggers
    engine._prepare_action6_target = lambda *a, **k: None
    state = SimpleNamespace(frame=None, score=0, available_actions=["ACTION6", "ACTION1"], current_level=1)

    action, reason = asyncio.get_event_loop().run_until_complete(engine._select_action(state))

    assert action == "ACTION1"
    assert engine._last_ladder_rung == 'heuristic'
    ladder = engine._last_ladder_trace
    assert ladder['heuristic']['status'] == 'selected'
    assert 'Prefer movement over blind ACTION6' in ladder['heuristic']['reason']
    assert ladder['noop']['status'] == 'skipped'


def test_action_source_empty_returns_noop(monkeypatch):
    engine = make_engine_with_minimum_state()

    async def smart_action_selection(game_state, strategy, is_unbeaten):
        return None

    engine.action_handler.smart_action_selection = smart_action_selection
    state = SimpleNamespace(frame=None, score=0, available_actions=["ACTION7"], current_level=1)

    action, reason = asyncio.get_event_loop().run_until_complete(engine._select_action(state))

    assert action == "ACTION7"
    assert engine._last_ladder_rung == 'noop'
    ladder = engine._last_ladder_trace
    assert ladder['noop']['status'] == 'selected'
    assert ladder['heuristic']['status'] in {'pending', 'skipped'}
