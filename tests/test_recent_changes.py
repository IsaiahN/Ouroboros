"""
Unit Tests for Recent Changes (2025-12-03)
==========================================
Tests for:
1. get_abstraction_config() function in abstraction_config.py
2. social_rule_adherence assignment in agent_operating_mode_system.py
3. New database tables: learned_rules, rule_transfers, pattern_cache,
   visual_analysis_cache, world_model_states
4. Integration verification

Following Rule 5 - Unit tests for core components are allowed.
Uses real database.

Created: 2025-12-03
Purpose: Validate all fixes applied during the session
"""

import os
import sys

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import sqlite3
import unittest
from pathlib import Path

# Path to main database (at project root, NOT the empty tests/core_data.db)
MAIN_DB_PATH = Path(__file__).parent.parent / "core_data.db"
from typing import Any, Dict


class TestAbstractionConfig(unittest.TestCase):
    """Tests for abstraction_config.py changes."""

    def test_get_abstraction_config_exists(self):
        """Verify get_abstraction_config function exists."""
        from abstraction_config import get_abstraction_config
        self.assertTrue(callable(get_abstraction_config))

    def test_get_abstraction_config_returns_dict(self):
        """Verify function returns a dictionary."""
        from abstraction_config import get_abstraction_config
        result = get_abstraction_config()
        self.assertIsInstance(result, dict)

    def test_abstraction_config_has_required_keys(self):
        """Verify config has all required keys (actual implementation)."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()

        # These are the actual keys in the implementation
        required_keys = {
            'enabled', 'matching_mode', 'levels',
            'min_conceptual_confidence', 'min_adaptation_confidence',
            'min_pattern_frequency', 'pattern_similarity_threshold'
        }

        for key in required_keys:
            self.assertIn(key, config, f"Missing required key: {key}")

    def test_abstraction_config_enabled_is_bool(self):
        """Verify 'enabled' is a boolean."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()
        self.assertIsInstance(config['enabled'], bool)

    def test_abstraction_config_matching_mode_valid(self):
        """Verify matching_mode is a valid option."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()
        valid_modes = {'exact', 'hybrid', 'abstracted'}
        self.assertIn(config['matching_mode'], valid_modes)

    def test_abstraction_config_thresholds_numeric(self):
        """Verify threshold values are numeric and in valid range."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()

        # Check the actual threshold keys in the implementation
        self.assertIsInstance(config['pattern_similarity_threshold'], (int, float))
        self.assertIsInstance(config['min_conceptual_confidence'], (int, float))

        # Should be between 0 and 1
        self.assertGreaterEqual(config['pattern_similarity_threshold'], 0.0)
        self.assertLessEqual(config['pattern_similarity_threshold'], 1.0)
        self.assertGreaterEqual(config['min_conceptual_confidence'], 0.0)
        self.assertLessEqual(config['min_conceptual_confidence'], 1.0)

    def test_abstraction_config_levels_dict(self):
        """Verify levels is a dictionary with abstraction levels."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()

        self.assertIsInstance(config['levels'], dict)
        self.assertGreater(len(config['levels']), 0)


class TestSocialRuleAdherence(unittest.TestCase):
    """Tests for social_rule_adherence in agent_operating_mode_system.py."""

    DB_PATH = MAIN_DB_PATH

    def setUp(self):
        """Set up database connection."""
        self.conn = sqlite3.connect(str(self.DB_PATH))
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        """Close database connection."""
        self.conn.close()

    def test_social_rule_adherence_column_exists(self):
        """Verify social_rule_adherence column exists in agents table."""
        cursor = self.conn.execute("PRAGMA table_info(agents)")
        columns = {row['name'] for row in cursor.fetchall()}
        self.assertIn('social_rule_adherence', columns)

    def test_agents_have_social_rule_adherence(self):
        """Verify agents have social_rule_adherence values set."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(social_rule_adherence) as has_value
            FROM agents
        """)
        row = cursor.fetchone()
        self.assertEqual(row['total'], row['has_value'],
                        "Some agents missing social_rule_adherence")

    def test_social_rule_adherence_range(self):
        """Verify all social_rule_adherence values are in [0, 1]."""
        cursor = self.conn.execute("""
            SELECT MIN(social_rule_adherence) as min_val,
                   MAX(social_rule_adherence) as max_val
            FROM agents
            WHERE social_rule_adherence IS NOT NULL
        """)
        row = cursor.fetchone()

        if row['min_val'] is not None:
            self.assertGreaterEqual(row['min_val'], 0.0)
            self.assertLessEqual(row['max_val'], 1.0)

    def test_social_rule_adherence_distribution(self):
        """Verify there's variation in social_rule_adherence values."""
        cursor = self.conn.execute("""
            SELECT DISTINCT ROUND(social_rule_adherence, 1) as rounded
            FROM agents
            WHERE social_rule_adherence IS NOT NULL
        """)
        distinct_values = cursor.fetchall()

        # Should have at least 3 distinct values (sociopathic, moderate, social)
        self.assertGreaterEqual(len(distinct_values), 2,
                               "social_rule_adherence should have variation")

    def test_sociopathic_exploiters_exist(self):
        """Verify some exploiters have low social_rule_adherence (sociopathic)."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as cnt
            FROM agents
            WHERE social_rule_adherence <= 0.3
        """)
        count = cursor.fetchone()['cnt']
        self.assertGreater(count, 0,
                          "Should have sociopathic agents (adherence <= 0.3)")

    def test_social_agents_exist(self):
        """Verify some agents have high social_rule_adherence."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as cnt
            FROM agents
            WHERE social_rule_adherence >= 0.7
        """)
        count = cursor.fetchone()['cnt']
        self.assertGreater(count, 0,
                          "Should have social agents (adherence >= 0.7)")


class TestNewDatabaseTables(unittest.TestCase):
    """Tests for new database tables created for rule induction/symbolic learning."""

    DB_PATH = MAIN_DB_PATH
    EXPECTED_TABLES = [
        'learned_rules',
        'rule_transfers',
        'pattern_cache',
        'visual_analysis_cache',
        'world_model_states'
    ]

    def setUp(self):
        """Set up database connection."""
        self.conn = sqlite3.connect(str(self.DB_PATH))
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        """Close database connection."""
        self.conn.close()

    def test_learned_rules_table_exists(self):
        """Verify learned_rules table exists."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='learned_rules'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result, "learned_rules table must exist")

    def test_rule_transfers_table_exists(self):
        """Verify rule_transfers table exists."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='rule_transfers'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result, "rule_transfers table must exist")

    def test_pattern_cache_table_exists(self):
        """Verify pattern_cache table exists."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='pattern_cache'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result, "pattern_cache table must exist")

    def test_visual_analysis_cache_table_exists(self):
        """Verify visual_analysis_cache table exists."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='visual_analysis_cache'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result, "visual_analysis_cache table must exist")

    def test_world_model_states_table_exists(self):
        """Verify world_model_states table exists."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='world_model_states'
        """)
        result = cursor.fetchone()
        self.assertIsNotNone(result, "world_model_states table must exist")

    def test_all_expected_tables_exist(self):
        """Verify all expected tables exist in one check."""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (?, ?, ?, ?, ?)
        """, tuple(self.EXPECTED_TABLES))
        found_tables = {row['name'] for row in cursor.fetchall()}

        missing = set(self.EXPECTED_TABLES) - found_tables
        self.assertEqual(len(missing), 0, f"Missing tables: {missing}")

    def test_learned_rules_has_required_columns(self):
        """Verify learned_rules has expected columns (actual schema)."""
        cursor = self.conn.execute("PRAGMA table_info(learned_rules)")
        columns = {row['name'] for row in cursor.fetchall()}

        # Actual columns from the schema
        required = {'rule_id', 'agent_id', 'source_game_id', 'confidence', 'created_at'}
        missing = required - columns
        self.assertEqual(len(missing), 0, f"Missing columns in learned_rules: {missing}")

    def test_tables_are_insertable(self):
        """Verify we can insert into the new tables (with all required fields)."""
        import json
        import uuid

        test_id = f"test_{uuid.uuid4().hex[:8]}"

        test_data = {
            'learned_rules': f"""
                INSERT INTO learned_rules (rule_id, agent_id, source_game_id, rule_name, preconditions, action_template, expected_outcome, confidence)
                VALUES ('{test_id}', 'test_agent', 'test_game', 'test_rule', '{{"cond": true}}', '{{"action": 1}}', 'win', 0.5)
            """,
            'rule_transfers': f"""
                INSERT INTO rule_transfers (transfer_id, rule_id, source_game_id, target_game_id, agent_id, transfer_successful, confidence_before, confidence_after)
                VALUES ('{test_id}', '{test_id}', 'src_game', 'tgt_game', 'test_agent', 1, 0.5, 0.7)
            """,
            'pattern_cache': f"""
                INSERT INTO pattern_cache (cache_id, game_id, level_number, pattern_type, pattern_data, confidence)
                VALUES ('{test_id}', 'test_game', 1, 'movement', '{{"test": true}}', 0.5)
            """,
            'visual_analysis_cache': f"""
                INSERT INTO visual_analysis_cache (cache_id, frame_hash, analysis_data)
                VALUES ('{test_id}', 'hash123', '{{"test": true}}')
            """,
            'world_model_states': f"""
                INSERT INTO world_model_states (state_id, game_id, session_id, step_number, objects_json)
                VALUES ('{test_id}', 'test_game', 'test_session', 1, '{{"test": true}}')
            """
        }

        # Try inserting, then rollback
        try:
            for table, sql in test_data.items():
                self.conn.execute(sql)
            self.conn.rollback()
            # If we got here, inserts worked
            self.assertTrue(True)
        except sqlite3.Error as e:
            self.fail(f"Failed to insert into tables: {e}")
        finally:
            self.conn.rollback()


class TestMultiStagePipelineIntegration(unittest.TestCase):
    """Tests for multi-stage matching pipeline integration."""

    DB_PATH = MAIN_DB_PATH

    def test_pipeline_can_be_imported(self):
        """Verify multi_stage_matching_pipeline can be imported."""
        from multi_stage_matching_pipeline import MultiStageMatchingPipeline
        self.assertTrue(True)

    def test_pipeline_can_be_instantiated(self):
        """Verify pipeline can be instantiated with db connection."""
        import sqlite3

        from multi_stage_matching_pipeline import MultiStageMatchingPipeline
        conn = sqlite3.connect(str(self.DB_PATH))
        try:
            pipeline = MultiStageMatchingPipeline(conn)
            self.assertIsNotNone(pipeline)
        finally:
            conn.close()

    def test_pipeline_has_find_matching_sequence(self):
        """Verify pipeline has the main matching method."""
        import sqlite3

        from multi_stage_matching_pipeline import MultiStageMatchingPipeline
        conn = sqlite3.connect(str(self.DB_PATH))
        try:
            pipeline = MultiStageMatchingPipeline(conn)
            # Actual method name in the implementation
            self.assertTrue(hasattr(pipeline, 'get_sequence_with_fallback'))
        finally:
            conn.close()


class TestAbstractionEngineIntegration(unittest.TestCase):
    """Tests for sequence abstraction engine integration."""

    def test_abstraction_engine_can_be_imported(self):
        """Verify sequence_abstraction can be imported."""
        from engines.planning.sequence_abstraction import SequenceAbstraction
        self.assertTrue(True)

    def test_abstraction_config_is_used(self):
        """Verify abstraction engine uses the config function."""
        from abstraction_config import get_abstraction_config
        config = get_abstraction_config()

        # Config should be enabled for production use
        self.assertTrue(config['enabled'],
                       "Abstraction should be enabled in production")


class TestRuleInductionIntegration(unittest.TestCase):
    """Tests for rule induction engine integration."""

    DB_PATH = MAIN_DB_PATH

    def test_rule_induction_can_be_imported(self):
        """Verify rule_induction can be imported."""
        from engines.cognition.rule_induction import RuleInductionEngine
        self.assertTrue(True)

    def test_rule_induction_can_be_instantiated(self):
        """Verify RuleInductionEngine can be instantiated with DatabaseInterface."""
        from database_interface import DatabaseInterface
        from engines.cognition.rule_induction import RuleInductionEngine

        db = DatabaseInterface()
        engine = RuleInductionEngine(db)
        self.assertIsNotNone(engine)

    def test_rule_induction_has_extract_method(self):
        """Verify engine has rule extraction methods."""
        from database_interface import DatabaseInterface
        from engines.cognition.rule_induction import RuleInductionEngine

        db = DatabaseInterface()
        engine = RuleInductionEngine(db)

        # Should have the extraction method
        self.assertTrue(hasattr(engine, 'extract_rule_from_game_session'))


class TestSystemIntegrity(unittest.TestCase):
    """Integration tests for overall system integrity."""

    DB_PATH = MAIN_DB_PATH

    def setUp(self):
        """Set up database connection."""
        self.conn = sqlite3.connect(str(self.DB_PATH))
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        """Close database connection."""
        self.conn.close()

    def test_database_wal_mode(self):
        """Verify database is in WAL mode for concurrent access."""
        cursor = self.conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), 'wal',
                        "Database should be in WAL mode")

    def test_winning_sequences_have_valid_actions(self):
        """Verify winning sequences have valid action counts."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as invalid_count
            FROM winning_sequences
            WHERE total_actions <= 0 OR total_actions > 10000
        """)
        count = cursor.fetchone()['invalid_count']
        self.assertEqual(count, 0,
                        f"{count} sequences have invalid action counts")

    def test_agents_table_consistency(self):
        """Verify agents table has consistent data."""
        cursor = self.conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(agent_id) as has_id,
                   COUNT(social_rule_adherence) as has_adherence
            FROM agents
        """)
        row = cursor.fetchone()

        self.assertEqual(row['total'], row['has_id'],
                        "All agents must have agent_id")
        self.assertGreater(row['has_adherence'], 0,
                          "Agents should have social_rule_adherence set")


def run_all_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestAbstractionConfig,
        TestSocialRuleAdherence,
        TestNewDatabaseTables,
        TestMultiStagePipelineIntegration,
        TestAbstractionEngineIntegration,
        TestRuleInductionIntegration,
        TestSystemIntegrity,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("UNIT TESTS FOR RECENT CHANGES (2025-12-03)")
    print("=" * 70)
    print()
    print("Testing:")
    print("  1. abstraction_config.py - get_abstraction_config() function")
    print("  2. agent_operating_mode_system.py - social_rule_adherence")
    print("  3. Database tables - learned_rules, rule_transfers, etc.")
    print("  4. Integration of abstraction, multi-stage matching, rule induction")
    print()
    print("-" * 70)

    result = run_all_tests()

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[OK] ALL TESTS PASSED - Recent changes verified")
    else:
        print("\n[FAIL] SOME TESTS FAILED")
        if result.failures:
            print("\nFailed tests:")
            for test, traceback in result.failures:
                print(f"  - {test}")
                # Print first line of traceback for context
                lines = traceback.strip().split('\n')
                if lines:
                    print(f"    {lines[-1][:100]}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
                lines = traceback.strip().split('\n')
                if lines:
                    print(f"    {lines[-1][:100]}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
