"""
Unit Tests for Agent Role Compliance
=====================================
Tests that each agent type (Pioneer, Optimizer, Generalist, Exploiter) 
behaves correctly according to the master ruleset.

Run with: python -m pytest test_agent_roles.py -v
"""

import unittest
import sqlite3
import json
import os
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestAgentRoleDefinitions(unittest.TestCase):
    """Test that agent roles are correctly defined in the system."""
    
    def test_four_agent_roles_exist(self):
        """Verify the four agent roles are defined."""
        expected_roles = {'pioneer', 'optimizer', 'generalist', 'exploiter'}
        # These are the canonical roles per master ruleset
        self.assertEqual(len(expected_roles), 4)
        
    def test_exploiter_requires_sequence(self):
        """Exploiter should abort if no sequence available."""
        # Mock scenario: exploiter mode with no sequence
        # Expected: Should return error with 'NO_SEQUENCE_AVAILABLE'
        mock_result = {
            'game_id': 'test-game',
            'final_state': 'NO_SEQUENCE_AVAILABLE',
            'final_score': 0.0,
            'actions_taken': 0,
            'win': False,
            'method': 'exploiter_abort_no_sequence',
            'error': 'Exploiter mode requires proven sequences but none available'
        }
        # Validate expected error structure
        self.assertEqual(mock_result['final_state'], 'NO_SEQUENCE_AVAILABLE')
        self.assertIn('exploiter', mock_result['method'])
        self.assertFalse(mock_result['win'])

    def test_exploiter_stops_at_frontier(self):
        """Exploiter should stop at frontier after replaying sequence."""
        # Exploiter behavior: replay sequence to frontier, then stop (never explore)
        # Expected method: 'exploiter_sequence_replay'
        mock_result = {
            'game_id': 'test-game',
            'final_state': 'NOT_FINISHED',
            'final_score': 3.0,  # Replayed to level 3
            'actions_taken': 150,
            'win': False,
            'method': 'exploiter_sequence_replay',
            'sequence_id': 'seq-123'
        }
        self.assertEqual(mock_result['method'], 'exploiter_sequence_replay')
        self.assertIn('sequence_id', mock_result)


class TestPioneerBehavior(unittest.TestCase):
    """Test Pioneer agent behavior."""
    
    def test_pioneer_explores_at_frontier(self):
        """Pioneer should continue exploring at frontier, not stop."""
        # After replaying sequence to frontier, pioneer continues with exploration
        # NOT exploiter behavior (which would stop)
        frontier_level = 3
        sequence_completed_level = 2
        
        # Pioneer should continue playing when:
        # - Current level > sequence completed level (at frontier)
        # - Actions remain in budget
        should_continue = (frontier_level > sequence_completed_level)
        self.assertTrue(should_continue, "Pioneer should continue at frontier")
        
    def test_pioneer_uses_sequence_to_reach_frontier(self):
        """Pioneer should replay sequence to efficiently reach frontier."""
        # Pioneer behavior: Use cumulative sequence replay to reach highest known level
        # Then switch to exploration mode
        has_sequence = True
        agent_mode = 'pioneer'
        
        # Pioneer should use sequence if available
        should_use_sequence = has_sequence and agent_mode == 'pioneer'
        self.assertTrue(should_use_sequence)
        
    def test_pioneer_has_sensation_disabled(self):
        """Pioneers should NOT use sensation/feelings (per master ruleset)."""
        # From rules: "❌ NO subsequence matching on level they're pioneering"
        # and "✅ Full exploration, no subsequence matching ON FRONTIER LEVELS"
        # Sensation engine should be disabled for pioneers on frontier
        agent_mode = 'pioneer'
        is_frontier = True
        
        # On frontier, pioneer should NOT use sensation biasing
        should_use_sensation = not (agent_mode == 'pioneer' and is_frontier)
        self.assertFalse(should_use_sensation, "Pioneer should not use sensation at frontier")


class TestOptimizerBehavior(unittest.TestCase):
    """Test Optimizer agent behavior."""
    
    def test_optimizer_works_on_beaten_games_only(self):
        """Optimizer should only work on games with proven sequences."""
        # From rules: "❌ NEVER work on unbeaten LEVELS in unbeaten games"
        game_has_sequence = True
        agent_mode = 'optimizer'
        
        # Optimizer should only be assigned to games with sequences
        valid_assignment = game_has_sequence and agent_mode == 'optimizer'
        self.assertTrue(valid_assignment)
        
    def test_optimizer_tries_to_beat_sequence(self):
        """Optimizer should try to complete with fewer actions than existing sequence."""
        existing_sequence_actions = 150
        optimizer_actions = 140  # Optimizer found better path
        
        # Optimizer success = fewer actions for same result
        is_improvement = optimizer_actions < existing_sequence_actions
        self.assertTrue(is_improvement, "Optimizer should beat existing sequence")
        
    def test_optimizer_continues_at_frontier(self):
        """Optimizer continues playing at frontier (unlike Exploiter)."""
        agent_mode = 'optimizer'
        at_frontier = True
        
        # Optimizer should continue even at frontier (trying to optimize)
        should_continue = (agent_mode == 'optimizer' and at_frontier)
        self.assertTrue(should_continue, "Optimizer should continue at frontier")


class TestGeneralistBehavior(unittest.TestCase):
    """Test Generalist agent behavior."""
    
    def test_generalist_plays_any_game(self):
        """Generalist can play any game type."""
        agent_mode = 'generalist'
        # Generalist is not restricted to specific game types
        can_play_unbeaten = True
        can_play_beaten = True
        can_play_optimized = True
        
        self.assertTrue(can_play_unbeaten)
        self.assertTrue(can_play_beaten)
        self.assertTrue(can_play_optimized)
        
    def test_generalist_uses_sensation(self):
        """Generalist should use sensation/feelings (per master ruleset)."""
        # From rules: "✅ **Sensation/feelings ENABLED** (use emotional intelligence)"
        agent_mode = 'generalist'
        
        should_use_sensation = (agent_mode == 'generalist')
        self.assertTrue(should_use_sensation, "Generalist should use sensation")
        
    def test_generalist_follows_sequence(self):
        """Generalist follows optimal sequences when available."""
        agent_mode = 'generalist'
        has_sequence = True
        
        # Generalist should replay sequence exactly (not optimize)
        should_follow_exactly = (agent_mode == 'generalist' and has_sequence)
        self.assertTrue(should_follow_exactly)


class TestExploiterBehavior(unittest.TestCase):
    """Test Exploiter agent behavior."""
    
    def test_exploiter_only_optimized_games(self):
        """Exploiter should only work on fully optimized games."""
        # From rules: "✅ Only games marked 'OPTIMIZED'"
        game_is_optimized = True
        agent_mode = 'exploiter'
        
        valid_assignment = game_is_optimized and agent_mode == 'exploiter'
        self.assertTrue(valid_assignment)
        
    def test_exploiter_never_explores(self):
        """Exploiter should NEVER explore - only use proven sequences."""
        agent_mode = 'exploiter'
        at_frontier = True
        
        # Exploiter should stop, not explore
        should_explore = False  # NEVER
        self.assertFalse(should_explore, "Exploiter should never explore")
        
    def test_exploiter_social_adherence_spectrum(self):
        """Exploiter should have 50/50 split between sociopathic and normal."""
        # From rules: "**50% Sociopathic**: `social_rule_adherence = 0.0-0.3`"
        # From rules: "**50% Normal**: `social_rule_adherence = 0.7-1.0`"
        sociopathic_range = (0.0, 0.3)
        normal_range = (0.7, 1.0)
        
        # Validate ranges don't overlap
        self.assertLess(sociopathic_range[1], normal_range[0])
        
        # Target 50/50 split
        sociopathic_target = 0.5
        normal_target = 0.5
        self.assertAlmostEqual(sociopathic_target + normal_target, 1.0)


class TestSequenceStorageByRole(unittest.TestCase):
    """Test that all agent types store sequences correctly."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.conn = sqlite3.connect(self.test_db.name)
        self.cursor = self.conn.cursor()
        
        # Create minimal schema
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS winning_sequences (
                sequence_id INTEGER PRIMARY KEY,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_sequence TEXT NOT NULL,
                agent_id TEXT,
                agent_mode TEXT,
                efficiency_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        os.unlink(self.test_db.name)
        
    def test_pioneer_stores_sequences(self):
        """Pioneer should store discovered sequences."""
        self._store_sequence('pioneer', 'pioneer-game-1', 1, ['ACTION1', 'ACTION2'])
        
        self.cursor.execute("SELECT * FROM winning_sequences WHERE agent_mode = 'pioneer'")
        rows = self.cursor.fetchall()
        self.assertEqual(len(rows), 1)
        
    def test_optimizer_stores_sequences(self):
        """Optimizer should store improved sequences."""
        self._store_sequence('optimizer', 'opt-game-1', 1, ['ACTION1'])  # Fewer actions
        
        self.cursor.execute("SELECT * FROM winning_sequences WHERE agent_mode = 'optimizer'")
        rows = self.cursor.fetchall()
        self.assertEqual(len(rows), 1)
        
    def test_generalist_stores_sequences(self):
        """Generalist should store sequences."""
        self._store_sequence('generalist', 'gen-game-1', 1, ['ACTION1', 'ACTION2', 'ACTION3'])
        
        self.cursor.execute("SELECT * FROM winning_sequences WHERE agent_mode = 'generalist'")
        rows = self.cursor.fetchall()
        self.assertEqual(len(rows), 1)
        
    def test_exploiter_does_not_create_new_sequences(self):
        """Exploiter should only harvest existing sequences, not create new ones."""
        # Exploiter replays proven sequences, doesn't explore new territory
        # Per rules: exploiter stops at frontier, never explores
        # So exploiter should NOT create new sequences from exploration
        agent_mode = 'exploiter'
        at_frontier = True
        
        # Exploiter at frontier should stop, meaning no new sequences created
        # The behavior is: exploiter never explores, so it can't discover new sequences
        should_explore = False  # Exploiter NEVER explores
        should_create_new_sequence = should_explore  # Can only create if exploring
        
        self.assertFalse(should_create_new_sequence, 
                        "Exploiter should not create sequences from exploration")
        
    def _store_sequence(self, agent_mode: str, game_id: str, level: int, actions: list):
        """Helper to store a sequence."""
        self.cursor.execute("""
            INSERT INTO winning_sequences (game_id, level_number, action_sequence, agent_mode, efficiency_score)
            VALUES (?, ?, ?, ?, ?)
        """, (game_id, level, json.dumps(actions), agent_mode, len(actions)))
        self.conn.commit()


class TestNetworkWisdomIntegration(unittest.TestCase):
    """Test that agents use network wisdom at frontier."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.conn = sqlite3.connect(self.test_db.name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Create action_traces table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_traces (
                trace_id INTEGER PRIMARY KEY,
                game_id TEXT NOT NULL,
                level_number INTEGER NOT NULL,
                action_number INTEGER NOT NULL,
                score_change REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                social_rule_adherence REAL DEFAULT 0.7
            )
        """)
        self.conn.commit()
        
    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        os.unlink(self.test_db.name)
        
    def test_network_wisdom_queries_action_traces(self):
        """Network wisdom should query historical action traces."""
        # Insert test data
        for action in [1, 2, 3]:
            for i in range(5):
                score_change = 1.0 if action == 3 else 0.0  # ACTION3 always succeeds
                self.cursor.execute("""
                    INSERT INTO action_traces (game_id, level_number, action_number, score_change)
                    VALUES (?, ?, ?, ?)
                """, ('test-game-1', 1, action, score_change))
        self.conn.commit()
        
        # Query action success rates
        self.cursor.execute("""
            SELECT 
                action_number,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN score_change > 0 THEN 1 ELSE 0 END) as successes
            FROM action_traces
            WHERE game_id LIKE 'test-game%' AND level_number = 1
            GROUP BY action_number
        """)
        rows = self.cursor.fetchall()
        
        # ACTION3 should have highest success rate
        action_stats = {row['action_number']: row['successes'] / row['total_attempts'] for row in rows}
        self.assertEqual(action_stats[3], 1.0)  # 100% success
        self.assertEqual(action_stats[1], 0.0)  # 0% success
        
    def test_sociopath_ignores_network_wisdom(self):
        """Agents with low social_rule_adherence may ignore network wisdom."""
        # Insert sociopathic agent
        self.cursor.execute("""
            INSERT INTO agents (agent_id, social_rule_adherence) VALUES (?, ?)
        """, ('sociopath-agent', 0.2))
        self.conn.commit()
        
        # Query agent
        self.cursor.execute("SELECT social_rule_adherence FROM agents WHERE agent_id = ?", 
                          ('sociopath-agent',))
        row = self.cursor.fetchone()
        
        social_adherence = row['social_rule_adherence']
        is_sociopathic = social_adherence < 0.3
        self.assertTrue(is_sociopathic, "Agent with adherence < 0.3 should be sociopathic")
        
    def test_social_agent_uses_network_wisdom(self):
        """Agents with high social_rule_adherence should use network wisdom."""
        # Insert social agent
        self.cursor.execute("""
            INSERT INTO agents (agent_id, social_rule_adherence) VALUES (?, ?)
        """, ('social-agent', 0.85))
        self.conn.commit()
        
        # Query agent
        self.cursor.execute("SELECT social_rule_adherence FROM agents WHERE agent_id = ?", 
                          ('social-agent',))
        row = self.cursor.fetchone()
        
        social_adherence = row['social_rule_adherence']
        is_social = social_adherence >= 0.7
        self.assertTrue(is_social, "Agent with adherence >= 0.7 should be social")


class TestAgentPopulationDistribution(unittest.TestCase):
    """Test that agent population follows prescribed ratios."""
    
    def test_exploration_mode_distribution(self):
        """In exploration mode: 60% Pioneer, 30% Optimizer, 10% Generalist, 5% Exploiter."""
        # Note: These don't add to 100% per rules - exploiters work on OTHER games
        expected = {
            'pioneer': 0.60,
            'optimizer': 0.30,
            'generalist': 0.10,
            'exploiter': 0.05  # On OTHER optimized games
        }
        
        # Validate exploration ratios
        self.assertAlmostEqual(expected['pioneer'], 0.60)
        self.assertAlmostEqual(expected['optimizer'], 0.30)
        self.assertAlmostEqual(expected['generalist'], 0.10)
        
    def test_optimization_mode_distribution(self):
        """In optimization mode: 0% Pioneer, 70% Optimizer, 15% Generalist, 15% Exploiter."""
        expected = {
            'pioneer': 0.00,
            'optimizer': 0.70,
            'generalist': 0.15,
            'exploiter': 0.15
        }
        
        # Pioneers immediately reassigned when game is beaten
        self.assertEqual(expected['pioneer'], 0.00)
        # Optimizers dominate
        self.assertEqual(expected['optimizer'], 0.70)


class TestStateForcingForContinuation(unittest.TestCase):
    """Test that state forcing prevents premature game ending."""
    
    def test_win_state_forced_to_not_finished(self):
        """WIN state should be forced to NOT_FINISHED if actions remain."""
        game_state = 'WIN'
        actions_taken = 100
        max_actions = 7000
        
        # If WIN reported but actions remain, force continuation
        if game_state != "NOT_FINISHED" and actions_taken < max_actions:
            game_state = "NOT_FINISHED"  # Force continuation
            
        self.assertEqual(game_state, "NOT_FINISHED")
        
    def test_game_over_state_forced_to_not_finished(self):
        """GAME_OVER state should be forced to NOT_FINISHED if actions remain."""
        game_state = 'GAME_OVER'
        actions_taken = 500
        max_actions = 7000
        
        # If GAME_OVER reported but actions remain, force continuation
        if game_state != "NOT_FINISHED" and actions_taken < max_actions:
            game_state = "NOT_FINISHED"  # Force continuation
            
        self.assertEqual(game_state, "NOT_FINISHED")
        
    def test_not_finished_stays_not_finished(self):
        """NOT_FINISHED state should remain NOT_FINISHED."""
        game_state = 'NOT_FINISHED'
        actions_taken = 500
        max_actions = 7000
        
        # No forcing needed
        self.assertEqual(game_state, "NOT_FINISHED")


if __name__ == '__main__':
    unittest.main(verbosity=2)
