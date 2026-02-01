from types import SimpleNamespace

import pytest

from core_gameplay import GameplayEngine


@pytest.fixture
def engine(monkeypatch):
    # Bypass heavy __init__ to avoid database connections; only sanity guard is tested
    engine = GameplayEngine.__new__(GameplayEngine)
    engine.game_config = {'agent_id': None, 'run_context': None}
    engine.session_manager = SimpleNamespace(current_game_id=None, current_session_id=None)
    yield engine


def make_state(frame):
    return SimpleNamespace(frame=frame, score=0, state="RUNNING", available_actions=["ACTION1"], current_level=1)


def test_frame_sanity_none_ok(engine):
    engine._assert_frame_sanity(None)


def test_frame_sanity_empty_raises(engine):
    with pytest.raises(RuntimeError, match="FRAME_SANITY_FAIL"):
        engine._assert_frame_sanity([])


def test_frame_sanity_ragged_raises(engine):
    frame = [[0, 1], [1]]
    with pytest.raises(RuntimeError, match="FRAME_SANITY_FAIL"):
        engine._assert_frame_sanity(frame)


def test_frame_sanity_out_of_range_cell(engine):
    frame = [[0, 256]]
    with pytest.raises(RuntimeError, match="FRAME_SANITY_FAIL"):
        engine._assert_frame_sanity(frame)


def test_frame_sanity_too_large(engine):
    big_frame = [[0] * 129 for _ in range(2)]
    with pytest.raises(RuntimeError, match="FRAME_SANITY_FAIL"):
        engine._assert_frame_sanity(big_frame)


def test_frame_sanity_valid_passes(engine):
    frame = [[0, 1, 2], [3, 4, 5]]
    engine._assert_frame_sanity(frame)


def test_select_action_uses_sanity(engine, monkeypatch):
    bad_frame = [[0, 1], [1]]
    state = make_state(bad_frame)
    with pytest.raises(RuntimeError, match="FRAME_SANITY_FAIL"):
        # Call directly; we don't need full async stack for the sanity check
        import asyncio
        asyncio.get_event_loop().run_until_complete(engine._select_action(state))
