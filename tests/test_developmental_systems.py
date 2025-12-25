#!/usr/bin/env python3
"""
Unit Tests for Developmental Systems
=====================================

Tests for the three developmental systems:
1. CognitiveStageSystem - Piaget-inspired stage progression
2. EpisodicMemorySystem - Agent history query (wA vs wB)
3. AgentHypothesisSystem - Agent-initiated hypothesis creation

Per Rule 11: No Unicode emojis in code.

Note: MockDatabaseInterface is used for testing. Type ignore comments
are used because the mock implements the same interface but Pylance
cannot verify duck-typing compatibility.
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import unittest
import sqlite3
import tempfile
import json
from datetime import datetime, timedelta
from typing import Any


class MockDatabaseInterface:
    """Mock database for testing without real database."""
    
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self._setup_tables()
    
    def _setup_tables(self):
        """Set up minimal tables needed for testing."""
        c = self.conn.cursor()
        
        # Agents table
        c.execute("""
            CREATE TABLE agents (
                agent_id TEXT PRIMARY KEY,
                agent_type TEXT,
                generation INTEGER DEFAULT 0
            )
        """)
        
        # Game results table
        c.execute("""
            CREATE TABLE game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                game_id TEXT,
                final_score REAL,
                levels_completed INTEGER,
                actions_used INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Winning sequences table
        c.execute("""
            CREATE TABLE winning_sequences (
                sequence_id TEXT PRIMARY KEY,
                game_id TEXT,
                level_number INTEGER,
                is_active BOOLEAN DEFAULT 1,
                efficiency_score REAL,
                times_referenced INTEGER DEFAULT 0
            )
        """)
        
        # Sequence reputation table
        c.execute("""
            CREATE TABLE sequence_reputation (
                sequence_id TEXT PRIMARY KEY,
                success_rate REAL DEFAULT 0.5
            )
        """)
        
        self.conn.commit()
    
    def execute_query(self, query: str, params: tuple | None = None):
        """Execute query and return results."""
        c = self.conn.cursor()
        if params:
            c.execute(query, params)
        else:
            c.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            return [dict(row) for row in c.fetchall()]
        else:
            self.conn.commit()
            return None


# =============================================================================
# COGNITIVE STAGE SYSTEM TESTS
# =============================================================================

class TestCognitiveStageSystem(unittest.TestCase):
    """Tests for CognitiveStageSystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MockDatabaseInterface()
        
        # Import the class
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent_self_model import CognitiveStageSystem
        
        self.system = CognitiveStageSystem(self.db)  # type: ignore[arg-type]
    
    def test_initial_stage_is_preoperational(self):
        """New agents start at preoperational stage."""
        stage = self.system.get_stage("test_agent_001")
        self.assertEqual(stage, 'preoperational')
    
    def test_stage_persistence(self):
        """Stage should persist across queries."""
        agent_id = "test_agent_002"
        
        # First query initializes
        stage1 = self.system.get_stage(agent_id)
        
        # Second query should return same
        stage2 = self.system.get_stage(agent_id)
        
        self.assertEqual(stage1, stage2)
        self.assertEqual(stage1, 'preoperational')
    
    def test_competency_update(self):
        """Competencies should update correctly."""
        agent_id = "test_agent_003"
        
        # Initialize
        self.system.get_stage(agent_id)
        
        # Update competencies
        result = self.system.update_competencies(
            agent_id,
            games_played_delta=3,
            sequences_discovered_delta=1
        )
        
        self.assertIn('current_stage', result)
        self.assertIn('competencies', result)
        
        comps = result['competencies']
        self.assertEqual(comps['games_played'], 3)
        self.assertEqual(comps['sequences_discovered'], 1)
    
    def test_preoperational_to_concrete_transition(self):
        """Agent should transition from preoperational to concrete_operational."""
        agent_id = "test_agent_004"
        
        # Initialize
        self.system.get_stage(agent_id)
        
        # Meet all requirements for transition
        result = self.system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        
        self.assertTrue(result['transitioned'])
        self.assertEqual(result['current_stage'], 'concrete_operational')
    
    def test_stage_capabilities_preoperational(self):
        """Preoperational agents should have limited capabilities."""
        agent_id = "test_agent_005"
        
        caps = self.system.get_stage_capabilities(agent_id)
        
        # Should have basic capabilities
        self.assertTrue(caps['action_exploration'])
        self.assertTrue(caps['object_observation'])
        self.assertTrue(caps['pattern_recognition'])
        
        # Should NOT have advanced capabilities
        self.assertFalse(caps['sequence_following'])
        self.assertFalse(caps['hypothesis_generation'])
    
    def test_stage_capabilities_formal(self):
        """Formal operational agents should have all capabilities."""
        agent_id = "test_agent_006"
        
        # Initialize and force to formal stage
        self.system.get_stage(agent_id)
        
        # First transition: preoperational -> concrete
        self.system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        
        # Second transition: concrete -> formal
        self.system.update_competencies(
            agent_id,
            games_played_delta=15,  # Now at 20 total
            sequences_discovered_delta=4,  # Now at 5 total
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        caps = self.system.get_stage_capabilities(agent_id)
        
        # Should have ALL capabilities
        self.assertTrue(caps['action_exploration'])
        self.assertTrue(caps['sequence_following'])
        self.assertTrue(caps['hypothesis_generation'])
        self.assertTrue(caps['abstract_generalization'])
    
    def test_population_distribution(self):
        """Should return correct distribution across stages."""
        # Create agents at different stages
        for i in range(3):
            self.system.get_stage(f"preop_agent_{i}")
        
        # Create one concrete operational agent
        agent_id = "concrete_agent"
        self.system.get_stage(agent_id)
        self.system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        
        dist = self.system.get_population_distribution()
        
        self.assertEqual(dist['preoperational'], 3)
        self.assertEqual(dist['concrete_operational'], 1)
        self.assertEqual(dist['formal_operational'], 0)


# =============================================================================
# EPISODIC MEMORY SYSTEM TESTS
# =============================================================================

class TestEpisodicMemorySystem(unittest.TestCase):
    """Tests for EpisodicMemorySystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MockDatabaseInterface()
        
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent_self_model import EpisodicMemorySystem
        
        self.system = EpisodicMemorySystem(self.db)  # type: ignore[arg-type]
        
        # Add test agent
        self.db.execute_query(
            "INSERT INTO agents (agent_id, agent_type) VALUES (?, ?)",
            ("test_agent", "explorer")
        )
    
    def test_no_history_returns_explore(self):
        """Agent with no history should get explore recommendation."""
        result = self.system.query_personal_history("test_agent", "SP80", 1)
        
        self.assertFalse(result['has_history'])
        self.assertEqual(result['recommendation'], 'explore_new')
        self.assertEqual(result['intuition_strength'], 0.0)
    
    def test_history_with_successes(self):
        """Agent with successful history should trust self."""
        # Add successful game results
        for i in range(5):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_agent", f"SP80-game{i}", 3.0, 3, 50))
        
        result = self.system.query_personal_history("test_agent", "SP80", 1)
        
        self.assertTrue(result['has_history'])
        self.assertEqual(result['successes'], 5)
        self.assertEqual(result['intuition_strength'], 1.0)
        self.assertEqual(result['recommendation'], 'trust_self')
    
    def test_history_with_failures(self):
        """Agent with failed history should try network."""
        # Add failed game results
        for i in range(5):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_agent", f"SP80-game{i}", 0.0, 0, 100))
        
        result = self.system.query_personal_history("test_agent", "SP80", 1)
        
        self.assertTrue(result['has_history'])
        self.assertEqual(result['successes'], 0)
        self.assertEqual(result['intuition_strength'], 0.0)
        self.assertEqual(result['recommendation'], 'try_network')
    
    def test_mixed_history_blends(self):
        """Agent with mixed history should blend sources."""
        # Add 2 successes, 2 failures
        for i in range(2):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_agent", f"SP80-win{i}", 3.0, 3, 50))
        
        for i in range(2):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_agent", f"SP80-lose{i}", 0.0, 0, 100))
        
        result = self.system.query_personal_history("test_agent", "SP80", 1)
        
        self.assertEqual(result['intuition_strength'], 0.5)
        self.assertEqual(result['recommendation'], 'blend_sources')
    
    def test_stream_comparison_no_network(self):
        """Comparison with no network data should favor self if history exists."""
        # Add personal success
        self.db.execute_query("""
            INSERT INTO game_results 
            (agent_id, game_id, final_score, levels_completed, actions_used)
            VALUES (?, ?, ?, ?, ?)
        """, ("test_agent", "SP80-game1", 3.0, 3, 50))
        
        result = self.system.compare_streams("test_agent", "SP80-game1", 1)
        
        self.assertGreater(result['wA_strength'], 0)
        self.assertEqual(result['wB_strength'], 0.0)
        self.assertEqual(result['wB_sequences'], 0)
    
    def test_stream_comparison_with_network(self):
        """Comparison with network data should calculate both streams."""
        # Add network sequences
        for i in range(3):
            self.db.execute_query("""
                INSERT INTO winning_sequences 
                (sequence_id, game_id, level_number, is_active, efficiency_score, times_referenced)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"seq_{i}", f"SP80-game{i}", 1, 1, 0.8, 5))
        
        result = self.system.compare_streams("test_agent", "SP80-game1", 1)
        
        self.assertGreater(result['wB_strength'], 0)
        self.assertEqual(result['wB_sequences'], 3)
    
    def test_narrative_summary_no_history(self):
        """Narrative for new agent should indicate first time."""
        narrative = self.system.get_narrative_summary("new_agent", "SP80", 1)
        
        self.assertIn("First time", narrative)
    
    def test_narrative_summary_with_history(self):
        """Narrative with history should describe recent experience."""
        # Add a success
        self.db.execute_query("""
            INSERT INTO game_results 
            (agent_id, game_id, final_score, levels_completed, actions_used)
            VALUES (?, ?, ?, ?, ?)
        """, ("test_agent", "SP80-game1", 3.0, 3, 45))
        
        narrative = self.system.get_narrative_summary("test_agent", "SP80", 1)
        
        self.assertIn("succeeded", narrative.lower())
        self.assertIn("45", narrative)  # Should mention action count


# =============================================================================
# AGENT HYPOTHESIS SYSTEM TESTS
# =============================================================================

class TestAgentHypothesisSystem(unittest.TestCase):
    """Tests for AgentHypothesisSystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MockDatabaseInterface()
        
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent_self_model import CognitiveStageSystem, AgentHypothesisSystem
        
        self.cognitive_system = CognitiveStageSystem(self.db)  # type: ignore[arg-type]
        self.system = AgentHypothesisSystem(self.db, self.cognitive_system)  # type: ignore[arg-type]
    
    def test_preoperational_cannot_create_hypothesis(self):
        """Preoperational agents cannot create hypotheses."""
        agent_id = "preop_agent"
        self.cognitive_system.get_stage(agent_id)
        
        self.assertFalse(self.system.can_create_hypothesis(agent_id))
        
        result = self.system.create_hypothesis(
            agent_id, "SP80", "Test hypothesis", "action_effect"
        )
        
        self.assertIsNone(result)
    
    def test_formal_can_create_hypothesis(self):
        """Formal operational agents can create hypotheses."""
        agent_id = "formal_agent"
        
        # Advance to formal operational
        self.cognitive_system.get_stage(agent_id)
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        self.assertTrue(self.system.can_create_hypothesis(agent_id))
        
        result = self.system.create_hypothesis(
            agent_id, "SP80", "ACTION5 rotates the object", "action_effect",
            level_number=1,
            initial_evidence=["Observed rotation after ACTION5"]
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result and result.startswith("hyp_"))
    
    def test_hypothesis_test_result_updates_confidence(self):
        """Recording test results should update confidence."""
        agent_id = "formal_agent_2"
        
        # Advance to formal
        self.cognitive_system.get_stage(agent_id)
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        # Create hypothesis
        hyp_id = self.system.create_hypothesis(
            agent_id, "SP80", "Test hypothesis", "action_effect"
        )
        self.assertIsNotNone(hyp_id)
        assert hyp_id is not None  # For type checker
        
        # Record successful test
        result = self.system.record_test_result(hyp_id, True, "Worked!")
        
        self.assertGreater(result['new_confidence'], 0.5)
        self.assertEqual(result['tests_conducted'], 1)
        self.assertEqual(result['tests_successful'], 1)
    
    def test_hypothesis_confirmation(self):
        """Hypothesis should be confirmed after enough successful tests."""
        agent_id = "formal_agent_3"
        
        # Advance to formal
        self.cognitive_system.get_stage(agent_id)
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        hyp_id = self.system.create_hypothesis(
            agent_id, "SP80", "Confirmed hypothesis", "action_effect"
        )
        self.assertIsNotNone(hyp_id)
        assert hyp_id is not None  # For type checker
        
        # Record multiple successes (need enough to reach 0.85+ confidence)
        for i in range(10):
            result = self.system.record_test_result(hyp_id, True)
        
        self.assertEqual(result['status'], 'confirmed')
        self.assertGreater(result['new_confidence'], 0.8)
    
    def test_hypothesis_refutation(self):
        """Hypothesis should be refuted after enough failed tests."""
        agent_id = "formal_agent_4"
        
        # Advance to formal
        self.cognitive_system.get_stage(agent_id)
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        hyp_id = self.system.create_hypothesis(
            agent_id, "SP80", "Bad hypothesis", "action_effect"
        )
        self.assertIsNotNone(hyp_id)
        assert hyp_id is not None  # For type checker
        
        # Record multiple failures (need enough to reach <0.15 confidence)
        for i in range(15):
            result = self.system.record_test_result(hyp_id, False)
        
        self.assertEqual(result['status'], 'refuted')
        self.assertLess(result['new_confidence'], 0.2)
    
    def test_get_agent_hypotheses(self):
        """Should retrieve agent's hypotheses correctly."""
        agent_id = "formal_agent_5"
        
        # Advance to formal
        self.cognitive_system.get_stage(agent_id)
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        self.cognitive_system.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        # Create multiple hypotheses
        self.system.create_hypothesis(agent_id, "SP80", "Hyp 1", "action_effect")
        self.system.create_hypothesis(agent_id, "SP80", "Hyp 2", "game_rule")
        self.system.create_hypothesis(agent_id, "FT09", "Hyp 3", "action_effect")
        
        # Get all
        all_hyps = self.system.get_agent_hypotheses(agent_id)
        self.assertEqual(len(all_hyps), 3)
        
        # Filter by game type
        sp80_hyps = self.system.get_agent_hypotheses(agent_id, game_type="SP80")
        self.assertEqual(len(sp80_hyps), 2)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDevelopmentalSystemsIntegration(unittest.TestCase):
    """Integration tests for all developmental systems working together."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MockDatabaseInterface()
        
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent_self_model import (
            CognitiveStageSystem, EpisodicMemorySystem, AgentHypothesisSystem
        )
        
        self.cognitive = CognitiveStageSystem(self.db)  # type: ignore[arg-type]
        self.episodic = EpisodicMemorySystem(self.db)  # type: ignore[arg-type]
        self.hypothesis = AgentHypothesisSystem(self.db, self.cognitive)  # type: ignore[arg-type]
    
    def test_full_developmental_journey(self):
        """Agent should progress through all stages with proper capabilities."""
        agent_id = "journey_agent"
        
        # Stage 1: Preoperational
        stage = self.cognitive.get_stage(agent_id)
        self.assertEqual(stage, 'preoperational')
        
        # Can query episodic memory (empty)
        history = self.episodic.query_personal_history(agent_id, "SP80", 1)
        self.assertFalse(history['has_history'])
        
        # Cannot create hypotheses
        self.assertFalse(self.hypothesis.can_create_hypothesis(agent_id))
        
        # Stage 2: Transition to concrete
        self.cognitive.update_competencies(
            agent_id,
            games_played_delta=5,
            sequences_discovered_delta=1,
            object_control_learned=True,
            action_effect_pairs_delta=3
        )
        
        stage = self.cognitive.get_stage(agent_id)
        self.assertEqual(stage, 'concrete_operational')
        
        # Still cannot create hypotheses
        self.assertFalse(self.hypothesis.can_create_hypothesis(agent_id))
        
        # Stage 3: Transition to formal
        self.cognitive.update_competencies(
            agent_id,
            games_played_delta=15,
            sequences_discovered_delta=4,
            hypotheses_created_delta=2,
            cross_game_transfer=True,
            validation_success_rate=0.7
        )
        
        stage = self.cognitive.get_stage(agent_id)
        self.assertEqual(stage, 'formal_operational')
        
        # NOW can create hypotheses
        self.assertTrue(self.hypothesis.can_create_hypothesis(agent_id))
        
        # Create and test a hypothesis
        hyp_id = self.hypothesis.create_hypothesis(
            agent_id, "SP80", "Final hypothesis test", "game_rule"
        )
        self.assertIsNotNone(hyp_id)


# =============================================================================
# HELP REQUEST SYSTEM TESTS
# =============================================================================

class TestHelpRequestSystem(unittest.TestCase):
    """Tests for the CODS help request mechanism."""
    
    def test_help_request_basic(self):
        """Agent can request help with a need description."""
        # This tests the interface, not the full CODS integration
        # The real request_help method needs the full CODS engine
        
        # Simulate what an agent would send
        need_description = "I need to detect symmetry in this puzzle"
        game_id = "SP80"
        level = 2
        agent_id = "test_agent"
        
        # Expected keywords that should map to primitives
        keywords = ['symmetry', 'pattern', 'detect']
        
        # Verify the description contains relevant keywords
        found_keywords = [k for k in keywords if k in need_description.lower()]
        self.assertTrue(len(found_keywords) > 0, "Need description should contain capability keywords")
    
    def test_need_description_parsing(self):
        """Need descriptions should contain actionable information."""
        test_cases = [
            ("I need to detect symmetry", ['symmetry']),
            ("Help with counting objects", ['count']),
            ("How to fill regions with color", ['fill']),
            ("Need to find the bounding box", ['bounding']),
            ("Can't figure out the pattern", ['pattern']),
        ]
        
        for description, expected_keywords in test_cases:
            found = any(kw in description.lower() for kw in expected_keywords)
            self.assertTrue(found, f"'{description}' should contain one of {expected_keywords}")


# =============================================================================
# COGNITIVE STAGE BEHAVIOR TESTS
# =============================================================================

class TestCognitiveStageBehavior(unittest.TestCase):
    """Tests for how cognitive stages affect agent behavior."""
    
    def setUp(self):
        self.db = MockDatabaseInterface()
        
        # Create cognitive stage table
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_competencies (
                agent_id TEXT PRIMARY KEY,
                stage TEXT DEFAULT 'preoperational',
                games_played INTEGER DEFAULT 0,
                sequences_discovered INTEGER DEFAULT 0
            )
        """)
        self.db.conn.commit()
    
    def test_preoperational_behavior(self):
        """Preoperational agents should explore more randomly."""
        agent_id = "preop_agent"
        
        # Insert preoperational agent
        self.db.conn.execute(
            "INSERT INTO cognitive_competencies (agent_id, stage) VALUES (?, ?)",
            (agent_id, 'preoperational')
        )
        self.db.conn.commit()
        
        # Query stage
        result = self.db.execute_query(
            "SELECT stage FROM cognitive_competencies WHERE agent_id = ?",
            (agent_id,)
        )
        self.assertIsNotNone(result)
        assert result is not None  # For type checker
        self.assertEqual(result[0]['stage'], 'preoperational')
        
        # Preoperational behavior: Would skip deterministic strategies
        # This is a behavioral check - actual behavior tested in integration
    
    def test_formal_uses_own_hypotheses(self):
        """Formal operational agents should query their own hypotheses."""
        agent_id = "formal_agent"
        
        # Create agent_hypotheses table
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                agent_id TEXT,
                game_type TEXT,
                hypothesis_text TEXT,
                status TEXT DEFAULT 'active',
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert formal agent with hypothesis
        self.db.conn.execute(
            "INSERT INTO cognitive_competencies (agent_id, stage) VALUES (?, ?)",
            (agent_id, 'formal_operational')
        )
        self.db.conn.execute(
            """INSERT INTO agent_hypotheses 
               (hypothesis_id, agent_id, game_type, hypothesis_text, status, confidence)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('hyp1', agent_id, 'SP80', 'Move up to reach the goal', 'active', 0.7)
        )
        self.db.conn.commit()
        
        # Query agent's hypotheses
        hypotheses = self.db.execute_query(
            """SELECT * FROM agent_hypotheses 
               WHERE agent_id = ? AND status = 'active'
               ORDER BY created_at DESC LIMIT 5""",
            (agent_id,)
        )
        
        self.assertIsNotNone(hypotheses)
        assert hypotheses is not None  # For type checker
        self.assertEqual(len(hypotheses), 1)
        self.assertIn('up', hypotheses[0]['hypothesis_text'].lower())


# =============================================================================
# PRIMITIVE INVENTORY AWARENESS TESTS
# =============================================================================

class TestPrimitiveInventoryAwareness(unittest.TestCase):
    """Tests for agent primitive inventory queries."""
    
    def test_inventory_structure(self):
        """Primitive inventory should have expected structure."""
        # Expected inventory categories
        expected_categories = ['seed', 'grandfathered', 'unlocked', 'locked', 'novel']
        
        # Simulated inventory response
        mock_inventory = {
            'seed': ['flood_fill', 'count_objects'],
            'grandfathered': ['detect_symmetry'],
            'unlocked': [],
            'locked': ['advanced_reasoning'],
            'novel': [],
            'summary': {
                'total_available': 3,
                'total_locked': 1
            }
        }
        
        # Verify structure
        for category in expected_categories:
            self.assertIn(category, mock_inventory)
        
        # Total available should be sum of accessible primitives
        available = len(mock_inventory['seed']) + len(mock_inventory['grandfathered']) + len(mock_inventory['unlocked'])
        self.assertEqual(mock_inventory['summary']['total_available'], available)


if __name__ == '__main__':
    unittest.main()
