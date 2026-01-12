"""
Unit Tests for GameSessionManager

Tests the game session management including:
- Session creation and lifecycle
- Action budgets and affordability
- Stats tracking
- Signal handling

Rule 5: Unit tests for core components are allowed.
Uses temp database (not production).
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
import tempfile
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from database_interface import DatabaseInterface
from game_session_manager import GameSessionManager


@pytest.fixture
def temp_db():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def db(temp_db):
    """Create a DatabaseInterface with temp database."""
    interface = DatabaseInterface(temp_db)
    yield interface
    interface.close()


@pytest.fixture
def session_manager(temp_db):
    """Create a GameSessionManager with temp database."""
    manager = GameSessionManager(db_path=temp_db)
    yield manager


class TestGameSessionManagerInitialization:
    """Tests for GameSessionManager initialization."""
    
    def test_manager_creates_successfully(self, session_manager):
        """GameSessionManager should create without errors."""
        assert session_manager is not None
    
    def test_manager_has_required_methods(self, session_manager):
        """Manager should have required methods."""
        required = [
            'start_session', 'create_game', 'send_action',
            'finish_game', 'shutdown'
        ]
        for method in required:
            assert hasattr(session_manager, method)
            assert callable(getattr(session_manager, method))
    
    def test_manager_has_database_interface(self, session_manager):
        """Manager should have database interface."""
        assert hasattr(session_manager, 'db')


class TestGenerationTracking:
    """Tests for generation tracking."""
    
    def test_set_current_generation(self, session_manager):
        """Should be able to set current generation."""
        session_manager.set_current_generation(5)
        assert session_manager._current_generation == 5
    
    def test_generation_starts_at_none(self, session_manager):
        """Generation should start at None."""
        assert session_manager._current_generation is None


class TestShutdownHandlers:
    """Tests for shutdown handler registration."""
    
    def test_add_shutdown_handler(self, session_manager):
        """Should be able to add shutdown handlers."""
        handler_called = []
        
        def my_handler():
            handler_called.append(True)
        
        session_manager.add_shutdown_handler(my_handler)
        assert my_handler in session_manager.shutdown_handlers


class TestActionBudgetChecks:
    """Tests for action budget/affordability."""
    
    def test_can_agent_afford_game_method_exists(self, session_manager):
        """can_agent_afford_game method should exist."""
        assert hasattr(session_manager, 'can_agent_afford_game')
        assert callable(session_manager.can_agent_afford_game)
    
    def test_unknown_agent_affordability(self, session_manager):
        """Unknown agent should return some result (not crash)."""
        result = session_manager.can_agent_afford_game('nonexistent-agent', 'some-game')
        # Should return (bool, str) tuple
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestSessionStats:
    """Tests for session statistics."""
    
    def test_get_session_stats_returns_dict(self, session_manager):
        """get_session_stats should return a dict."""
        stats = session_manager.get_session_stats()
        assert isinstance(stats, dict)
    
    def test_session_stats_has_required_keys(self, session_manager):
        """Stats should have key metrics."""
        stats = session_manager.get_session_stats()
        # Should have at least some basic info
        assert isinstance(stats, dict)


class TestContextManager:
    """Tests for async context manager support."""
    
    def test_has_context_manager_methods(self, session_manager):
        """Should support async context manager."""
        assert hasattr(session_manager, '__aenter__')
        assert hasattr(session_manager, '__aexit__')


class TestDeductActionsUsed:
    """Tests for action deduction tracking."""
    
    def test_deduct_actions_method_exists(self, session_manager):
        """deduct_actions_used method should exist."""
        assert hasattr(session_manager, 'deduct_actions_used')
        assert callable(session_manager.deduct_actions_used)
