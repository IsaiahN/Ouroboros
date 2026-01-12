#!/usr/bin/env python3
"""
Unit tests for SafeDatabaseCleaner
"""
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from safe_cleanup import SafeDatabaseCleaner


class TestSafeDatabaseCleaner(unittest.TestCase):
    """Test SafeDatabaseCleaner functionality."""
    
    def setUp(self):
        """Create a temporary test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create test tables
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # game_results table
        c.execute('''
            CREATE TABLE game_results (
                game_id TEXT,
                final_score INTEGER,
                session_id TEXT
            )
        ''')
        
        # score_history table
        c.execute('''
            CREATE TABLE score_history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                score INTEGER
            )
        ''')
        
        # system_logs table
        c.execute('''
            CREATE TABLE system_logs (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                message TEXT
            )
        ''')
        
        # navigation_state_history table
        c.execute('''
            CREATE TABLE navigation_state_history (
                history_id INTEGER PRIMARY KEY,
                state_timestamp TEXT,
                state TEXT
            )
        ''')
        
        # action_traces table
        c.execute('''
            CREATE TABLE action_traces (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                action TEXT
            )
        ''')
        
        # sensation_learning_events table
        c.execute('''
            CREATE TABLE sensation_learning_events (
                event_id INTEGER PRIMARY KEY,
                event_timestamp TEXT,
                event TEXT
            )
        ''')
        
        # agent_operating_modes table
        c.execute('''
            CREATE TABLE agent_operating_modes (
                mode_id INTEGER PRIMARY KEY,
                assigned_timestamp TEXT,
                mode TEXT
            )
        ''')
        
        # winning_sequences table (should never be touched)
        c.execute('''
            CREATE TABLE winning_sequences (
                sequence_id TEXT PRIMARY KEY,
                is_active INTEGER,
                action_sequence TEXT
            )
        ''')
        
        # agents table (should never be touched)
        c.execute('''
            CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY,
                is_active INTEGER,
                genome TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.cleaner = SafeDatabaseCleaner(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up temporary database."""
        try:
            os.unlink(self.db_path)
        except Exception:
            pass
    
    def _insert_game_results(self, zero_count, positive_count):
        """Insert test game results."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for i in range(zero_count):
            c.execute('INSERT INTO game_results VALUES (?, ?, ?)', 
                     (f'game_{i}', 0, f'session_{i}'))
        for i in range(positive_count):
            c.execute('INSERT INTO game_results VALUES (?, ?, ?)', 
                     (f'game_pos_{i}', i + 1, f'session_pos_{i}'))
        conn.commit()
        conn.close()
    
    def _insert_timestamped_data(self, table, id_col, ts_col, count, days_old=0):
        """Insert timestamped test data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        ts = (datetime.now() - timedelta(days=days_old)).isoformat()
        for i in range(count):
            c.execute(f'INSERT INTO {table} ({ts_col}) VALUES (?)', (ts,))
        conn.commit()
        conn.close()
    
    def _get_count(self, table):
        """Get row count for a table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f'SELECT COUNT(*) FROM {table}')
        count = c.fetchone()[0]
        conn.close()
        return count
    
    # =========================================================================
    # Test: Zero-score game cleanup
    # =========================================================================
    
    def test_zero_score_games_deleted(self):
        """Zero-score games should be deleted."""
        self._insert_game_results(zero_count=50, positive_count=10)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['game_results']['deleted'], 50)
        self.assertEqual(self._get_count('game_results'), 10)
    
    def test_positive_score_games_preserved(self):
        """Positive-score games should NOT be deleted."""
        self._insert_game_results(zero_count=0, positive_count=100)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['game_results']['deleted'], 0)
        self.assertEqual(self._get_count('game_results'), 100)
    
    # =========================================================================
    # Test: Score history cleanup (7 day retention)
    # =========================================================================
    
    def test_old_score_history_deleted(self):
        """Score history older than 7 days should be deleted."""
        self._insert_timestamped_data('score_history', 'id', 'timestamp', 100, days_old=10)
        self._insert_timestamped_data('score_history', 'id', 'timestamp', 50, days_old=1)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['score_history']['deleted'], 100)
        self.assertEqual(self._get_count('score_history'), 50)
    
    def test_recent_score_history_preserved(self):
        """Score history within 7 days should be preserved."""
        self._insert_timestamped_data('score_history', 'id', 'timestamp', 100, days_old=3)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['score_history']['deleted'], 0)
        self.assertEqual(self._get_count('score_history'), 100)
    
    # =========================================================================
    # Test: System logs cleanup (keep 50000)
    # =========================================================================
    
    def test_excess_system_logs_deleted(self):
        """Excess system logs beyond 50000 should be deleted."""
        self._insert_timestamped_data('system_logs', 'id', 'timestamp', 55000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['system_logs']['deleted'], 5000)
        self.assertEqual(self._get_count('system_logs'), 50000)
    
    def test_system_logs_under_limit_preserved(self):
        """System logs under 50000 should all be preserved."""
        self._insert_timestamped_data('system_logs', 'id', 'timestamp', 3000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['system_logs']['deleted'], 0)
        self.assertEqual(self._get_count('system_logs'), 3000)
    
    # =========================================================================
    # Test: Dry run mode
    # =========================================================================
    
    def test_dry_run_no_changes(self):
        """Dry run should not delete anything."""
        self._insert_game_results(zero_count=100, positive_count=50)
        
        results = self.cleaner.cleanup(dry_run=True, verbose=False)
        
        self.assertTrue(results['dry_run'])
        self.assertEqual(results['tables_cleaned']['game_results']['deleted'], 0)
        self.assertEqual(self._get_count('game_results'), 150)  # All preserved
    
    def test_dry_run_reports_counts(self):
        """Dry run should report what would be deleted."""
        self._insert_game_results(zero_count=100, positive_count=50)
        
        results = self.cleaner.cleanup(dry_run=True, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['game_results']['found'], 100)
    
    # =========================================================================
    # Test: Critical data preservation
    # =========================================================================
    
    def test_winning_sequences_never_touched(self):
        """Winning sequences should NEVER be deleted."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO winning_sequences VALUES (?, ?, ?)', 
                 ('seq1', 1, '[1,2,3]'))
        c.execute('INSERT INTO winning_sequences VALUES (?, ?, ?)', 
                 ('seq2', 1, '[4,5,6]'))
        conn.commit()
        conn.close()
        
        # Add data that would trigger cleanup
        self._insert_game_results(zero_count=100, positive_count=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(self._get_count('winning_sequences'), 2)
    
    def test_agents_never_touched(self):
        """Agents should NEVER be deleted by this cleaner."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO agents VALUES (?, ?, ?)', 
                 ('agent1', 1, '{"type": "test"}'))
        c.execute('INSERT INTO agents VALUES (?, ?, ?)', 
                 ('agent2', 1, '{"type": "test2"}'))
        conn.commit()
        conn.close()
        
        # Add data that would trigger cleanup
        self._insert_game_results(zero_count=100, positive_count=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(self._get_count('agents'), 2)
    
    # =========================================================================
    # Test: Verify critical data method
    # =========================================================================
    
    def test_verify_critical_data(self):
        """verify_critical_data should return correct counts."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO winning_sequences VALUES (?, ?, ?)', 
                 ('seq1', 1, '[1,2,3]'))
        c.execute('INSERT INTO agents VALUES (?, ?, ?)', 
                 ('agent1', 1, '{}'))
        c.execute('INSERT INTO game_results VALUES (?, ?, ?)', 
                 ('game1', 5, 'session1'))
        conn.commit()
        conn.close()
        
        stats = self.cleaner.verify_critical_data(verbose=False)
        
        self.assertEqual(stats['sequences'], 1)
        self.assertEqual(stats['agents'], 1)
        self.assertEqual(stats['good_games'], 1)
    
    # =========================================================================
    # Test: Total deleted count
    # =========================================================================
    
    def test_total_deleted_aggregated(self):
        """Total deleted should be sum of all table deletions."""
        self._insert_game_results(zero_count=50, positive_count=10)
        self._insert_timestamped_data('score_history', 'id', 'timestamp', 100, days_old=10)
        # System logs retention is 50000, so insert 55000 to get 5000 deleted
        self._insert_timestamped_data('system_logs', 'id', 'timestamp', 55000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        expected_total = 50 + 100 + 5000  # games + history + logs
        self.assertEqual(results['total_deleted'], expected_total)
    
    # =========================================================================
    # Test: All retention limits
    # =========================================================================
    
    def test_navigation_history_retention(self):
        """Navigation history should keep 50,000 entries."""
        self._insert_timestamped_data('navigation_state_history', 'history_id', 
                                      'state_timestamp', 60000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['navigation_state_history']['deleted'], 10000)
        self.assertEqual(self._get_count('navigation_state_history'), 50000)
    
    def test_action_traces_retention(self):
        """Action traces should keep 50,000 entries."""
        self._insert_timestamped_data('action_traces', 'id', 'timestamp', 60000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['action_traces']['deleted'], 10000)
        self.assertEqual(self._get_count('action_traces'), 50000)
    
    def test_sensation_events_retention(self):
        """Sensation events should keep 200,000 entries."""
        self._insert_timestamped_data('sensation_learning_events', 'event_id', 
                                      'event_timestamp', 210000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['sensation_learning_events']['deleted'], 10000)
        self.assertEqual(self._get_count('sensation_learning_events'), 200000)
    
    def test_operating_modes_retention(self):
        """Operating modes should keep 100,000 entries."""
        self._insert_timestamped_data('agent_operating_modes', 'mode_id', 
                                      'assigned_timestamp', 110000, days_old=0)
        
        results = self.cleaner.cleanup(dry_run=False, verbose=False)
        
        self.assertEqual(results['tables_cleaned']['agent_operating_modes']['deleted'], 10000)
        self.assertEqual(self._get_count('agent_operating_modes'), 100000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
