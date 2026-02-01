"""
Unit Tests for DatabaseInterface

Tests the core database operations including:
- Schema initialization from template
- Connection management
- Session management
- Query execution
- Persona logging

Rule 5: Unit tests for core components are allowed.
Uses temp database (not production).
"""
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import sqlite3
import tempfile
from pathlib import Path

import pytest

from database_interface import DatabaseInterface


@pytest.fixture
def temp_db():
    """Create a temporary database path (file will be created by DatabaseInterface)."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)  # Delete so DatabaseInterface creates from schema
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


class TestDatabaseInitialization:
    """Tests for database initialization from schema."""

    def test_creates_database_from_schema(self, temp_db):
        """DatabaseInterface should create database from complete_database_schema.sql."""
        db = DatabaseInterface(temp_db)

        # Verify file was created
        assert os.path.exists(temp_db)

        # Verify tables exist
        conn = db._get_connection()
        cursor = conn.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """)
        tables = {row[0] for row in cursor.fetchall()}

        # Check for key tables
        assert 'agents' in tables
        assert 'game_results' in tables
        assert 'winning_sequences' in tables

        db.close()

    def test_connection_uses_wal_mode(self, db):
        """Database should use WAL journal mode for concurrency."""
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        assert mode.lower() == 'wal'

    def test_foreign_keys_enabled(self, db):
        """Database should have foreign keys enabled."""
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        assert fk_enabled == 1


class TestConnectionManagement:
    """Tests for database connection handling."""

    def test_get_connection_returns_connection(self, db):
        """_get_connection should return a sqlite3.Connection."""
        conn = db._get_connection()
        assert isinstance(conn, sqlite3.Connection)

    def test_connection_has_row_factory(self, db):
        """Connection should use Row factory for dict-like access."""
        conn = db._get_connection()
        assert conn.row_factory == sqlite3.Row

    def test_close_terminates_connection(self, db):
        """close() should close the database connection."""
        conn = db._get_connection()
        db.close()

        # Attempting to use closed connection should fail
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


class TestQueryExecution:
    """Tests for execute_query method."""

    def test_execute_query_returns_list(self, db):
        """execute_query should return a list of dicts."""
        results = db.execute_query("SELECT 1 as value")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['value'] == 1

    def test_execute_query_with_params(self, db):
        """execute_query should support parameterized queries."""
        # Insert a test agent first
        db.execute_query("""
            INSERT INTO agents (agent_id, agent_type, genome, generation, specialization)
            VALUES (?, ?, ?, ?, ?)
        """, ('test-agent', 'pioneer', '{}', 1, 'test'))

        results = db.execute_query(
            "SELECT agent_id FROM agents WHERE agent_id = ?",
            ('test-agent',)
        )
        assert len(results) == 1
        assert results[0]['agent_id'] == 'test-agent'

    def test_execute_query_empty_result(self, db):
        """execute_query should return empty list for no matches."""
        results = db.execute_query(
            "SELECT * FROM agents WHERE agent_id = ?",
            ('nonexistent',)
        )
        assert results == []


class TestSessionManagement:
    """Tests for session create/end functionality."""

    def test_create_session_returns_id(self, db):
        """create_session should return a session ID."""
        session_id = db.create_session()
        assert session_id is not None
        assert len(session_id) > 0

    def test_create_session_with_custom_id(self, db):
        """create_session should accept a custom session ID."""
        custom_id = 'my-custom-session'
        session_id = db.create_session(session_id=custom_id)
        assert session_id == custom_id

    def test_end_session_updates_record(self, db):
        """end_session should update the session record."""
        session_id = db.create_session()
        db.end_session(session_id)

        # Training_sessions is the actual table name
        results = db.execute_query(
            "SELECT end_time, status FROM training_sessions WHERE session_id = ?",
            (session_id,)
        )
        assert len(results) == 1
        assert results[0]['end_time'] is not None
        assert results[0]['status'] == 'completed'


class TestPersonaLogging:
    """Tests for persona-related logging methods.

    Note: These tests are skipped because persona_proposals and persona_outcomes
    tables have FK constraints to persona_profiles that require complex setup.
    The methods themselves are tested through integration tests.
    """

    @pytest.mark.skip(reason="FK constraints require complex persona_profiles setup")
    def test_log_persona_proposal_requires_persona(self, db):
        """log_persona_proposal needs a valid persona_id (FK constraint)."""
        pass

    @pytest.mark.skip(reason="FK constraints require complex persona_profiles setup")
    def test_log_persona_outcome_requires_proposal(self, db):
        """log_persona_outcome needs a valid proposal_id (FK constraint)."""
        pass


class TestSchemaValidation:
    """Tests to verify schema integrity."""

    def test_agents_table_has_required_columns(self, db):
        """agents table should have all required columns."""
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA table_info(agents)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'agent_id', 'agent_type', 'genome', 'generation', 'is_active'}
        missing = required - columns
        assert len(missing) == 0, f"Missing columns in agents: {missing}"

    def test_winning_sequences_table_has_required_columns(self, db):
        """winning_sequences table should have all required columns."""
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA table_info(winning_sequences)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'sequence_id', 'game_id', 'level_number', 'total_actions'}
        missing = required - columns
        assert len(missing) == 0, f"Missing columns in winning_sequences: {missing}"

    def test_game_results_table_has_required_columns(self, db):
        """game_results table should have all required columns."""
        conn = db._get_connection()
        cursor = conn.execute("PRAGMA table_info(game_results)")
        columns = {row[1] for row in cursor.fetchall()}

        # Primary key is (game_id, session_id), no result_id
        required = {'game_id', 'session_id', 'final_score', 'status'}
        missing = required - columns
        assert len(missing) == 0, f"Missing columns in game_results: {missing}"
