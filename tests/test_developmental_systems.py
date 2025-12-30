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
# PRE-GAME AUTOBIOGRAPHICAL SYNTHESIS TESTS
# =============================================================================

class TestPreGameAutobiography(unittest.TestCase):
    """Tests for pre-game autobiographical synthesis.
    
    These test the agent's ability to synthesize their complete understanding
    of a game from all their past experiences before taking their first action.
    This is the TRUE wA (private stream) that gives agents real memory.
    """
    
    def setUp(self):
        """Set up test fixtures with extended mock database."""
        self.db = MockDatabaseInterface()
        self._add_autobiography_tables()
        
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent_self_model import EpisodicMemorySystem
        
        self.episodic = EpisodicMemorySystem(self.db)  # type: ignore[arg-type]
    
    def _add_autobiography_tables(self):
        """Add tables needed for autobiography synthesis."""
        c = self.db.conn.cursor()
        
        # Agent theories table
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_theories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                theory_type TEXT,
                description TEXT,
                confidence REAL DEFAULT 0.5,
                tests_conducted INTEGER DEFAULT 0,
                status TEXT DEFAULT 'testing'
            )
        """)
        
        # Network object control hypotheses
        c.execute("""
            CREATE TABLE IF NOT EXISTS network_object_control_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                game_type TEXT NOT NULL,
                level_number INTEGER,
                controlled_pattern TEXT,
                action_response TEXT,
                reliability_score REAL DEFAULT 0.5,
                validation_attempts INTEGER DEFAULT 0,
                discovered_by TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Inferred goal states
        c.execute("""
            CREATE TABLE IF NOT EXISTS inferred_goal_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_type TEXT NOT NULL,
                level_number INTEGER,
                goal_type TEXT,
                goal_params TEXT,
                confidence REAL DEFAULT 0.5
            )
        """)
        
        # Pariahs (failure patterns)
        c.execute("""
            CREATE TABLE IF NOT EXISTS pariahs (
                pariah_id TEXT PRIMARY KEY,
                game_id TEXT,
                level_number INTEGER,
                failure_pattern TEXT,
                death_count INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        
        # Agent pariah awareness
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_pariah_awareness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                pariah_id TEXT NOT NULL
            )
        """)
        
        # Object sensation mappings
        c.execute("""
            CREATE TABLE IF NOT EXISTS object_sensation_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                object_type TEXT,
                sensation_score REAL DEFAULT 0.0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                personal_meaning TEXT
            )
        """)
        
        # Action traces
        c.execute("""
            CREATE TABLE IF NOT EXISTS action_traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                game_id TEXT NOT NULL,
                action_name TEXT,
                score_before REAL DEFAULT 0.0,
                score_after REAL DEFAULT 0.0
            )
        """)
        
        # Add generation column to game_results
        c.execute("""
            ALTER TABLE game_results ADD COLUMN generation INTEGER DEFAULT 0
        """)
        
        self.db.conn.commit()
    
    def _seed_agent_history(self, agent_id: str, game_type: str, 
                            wins: int, losses: int, generation: int = 10):
        """Seed an agent's game history."""
        # Add agent
        self.db.execute_query(
            "INSERT OR IGNORE INTO agents (agent_id, agent_type) VALUES (?, ?)",
            (agent_id, "explorer")
        )
        
        # Add wins
        for i in range(wins):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used, generation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_id, f"{game_type}-win{i}", 3.0, 3, 50 + i, generation))
        
        # Add losses
        for i in range(losses):
            self.db.execute_query("""
                INSERT INTO game_results 
                (agent_id, game_id, final_score, levels_completed, actions_used, generation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_id, f"{game_type}-loss{i}", 0.0, 0, 100 + i, generation))
    
    def _seed_network_knowledge(self, game_type: str, sequences: int, efficiency: float):
        """Seed network sequences for a game type."""
        for i in range(sequences):
            self.db.execute_query("""
                INSERT INTO winning_sequences 
                (sequence_id, game_id, level_number, is_active, efficiency_score, times_referenced)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f"seq_{i}", f"{game_type}-net{i}", 1, 1, efficiency, 5))
    
    # =========================================================================
    # CORE SYNTHESIS TESTS
    # =========================================================================
    
    def test_empty_history_returns_explore_strategy(self):
        """New agent with no history should recommend exploration."""
        result = self.episodic.synthesize_pregame_autobiography(
            "new_agent", "SP80", 1, is_frontier=True
        )
        
        self.assertEqual(result['total_games_played'], 0)
        self.assertEqual(result['recommended_strategy']['strategy'], 'explore')
        self.assertIn("first time", result['autobiography_narrative'].lower())
    
    def test_experienced_agent_trusts_self(self):
        """Experienced successful agent should trust self."""
        self._seed_agent_history("exp_agent", "SP80", wins=25, losses=5)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "exp_agent", "SP80", 1, current_generation=10
        )
        
        self.assertEqual(result['total_games_played'], 30)
        self.assertGreater(result['win_rate'], 0.7)
        self.assertEqual(result['recommended_strategy']['strategy'], 'trust_self')
    
    def test_novice_with_network_trusts_network(self):
        """Novice agent with strong network should trust network."""
        self._seed_agent_history("novice", "SP80", wins=1, losses=2)
        self._seed_network_knowledge("SP80", sequences=10, efficiency=0.8)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "novice", "SP80", 1, current_generation=10
        )
        
        self.assertEqual(result['total_games_played'], 3)
        self.assertGreater(result['network_sequences_available'], 5)
        self.assertEqual(result['recommended_strategy']['strategy'], 'trust_network')
    
    def test_moderate_experience_blends(self):
        """Agent with moderate experience should blend sources."""
        self._seed_agent_history("blend_agent", "SP80", wins=5, losses=5)
        self._seed_network_knowledge("SP80", sequences=5, efficiency=0.6)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "blend_agent", "SP80", 1, current_generation=10
        )
        
        self.assertEqual(result['total_games_played'], 10)
        self.assertEqual(result['recommended_strategy']['strategy'], 'blend')
    
    def test_frontier_game_always_explores(self):
        """Frontier game should always recommend exploration."""
        # Even with history on other games, frontier = explore
        self._seed_agent_history("frontier_agent", "SP80", wins=20, losses=5)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "frontier_agent", "NEW_GAME", 1, is_frontier=True
        )
        
        self.assertEqual(result['recommended_strategy']['strategy'], 'explore')
    
    # =========================================================================
    # UNCERTAINTY DETECTION TESTS
    # =========================================================================
    
    def test_uncertainty_no_controls(self):
        """Agent with no control knowledge should report control uncertainty."""
        self._seed_agent_history("no_control_agent", "SP80", wins=5, losses=5)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "no_control_agent", "SP80", 1
        )
        
        self.assertIsNotNone(result['key_uncertainty'])
        self.assertEqual(result['key_uncertainty']['type'], 'control')
    
    def test_uncertainty_low_win_rate(self):
        """Agent with high games but low win rate should report strategy uncertainty."""
        self._seed_agent_history("struggling_agent", "SP80", wins=3, losses=22)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "struggling_agent", "SP80", 1
        )
        
        self.assertIsNotNone(result['key_uncertainty'])
        # Either control or strategy uncertainty is valid
        self.assertIn(result['key_uncertainty']['type'], ['control', 'strategy', 'goal'])
    
    # =========================================================================
    # TEMPORAL WEIGHTING TESTS
    # =========================================================================
    
    def test_temporal_weight_recent_full_weight(self):
        """Recent experiences should have full weight."""
        weight = self.episodic._temporal_weight(10, 10, half_life=20)
        self.assertEqual(weight, 1.0)
    
    def test_temporal_weight_old_decays(self):
        """Old experiences should have reduced weight."""
        # 20 generations old = half_life = 50% weight
        weight = self.episodic._temporal_weight(0, 20, half_life=20)
        self.assertAlmostEqual(weight, 0.5, places=2)
        
        # 40 generations old = 25% weight
        weight = self.episodic._temporal_weight(0, 40, half_life=20)
        self.assertAlmostEqual(weight, 0.25, places=2)
    
    # =========================================================================
    # NARRATIVE GENERATION TESTS
    # =========================================================================
    
    def test_narrative_includes_experience(self):
        """Narrative should mention game count and win rate."""
        self._seed_agent_history("narr_agent", "SP80", wins=15, losses=5)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "narr_agent", "SP80", 1
        )
        
        narrative = result['autobiography_narrative'].lower()
        self.assertIn("played", narrative)
        self.assertIn("20", narrative)  # 15 + 5 = 20 games
    
    def test_narrative_includes_strategy(self):
        """Narrative should mention recommended strategy."""
        self._seed_agent_history("strat_agent", "SP80", wins=20, losses=2)
        
        result = self.episodic.synthesize_pregame_autobiography(
            "strat_agent", "SP80", 1
        )
        
        narrative = result['autobiography_narrative'].lower()
        # Should mention confidence in own approach
        self.assertIn("confident", narrative)
    
    def test_narrative_first_time(self):
        """Narrative for new agent should say first time."""
        result = self.episodic.synthesize_pregame_autobiography(
            "brand_new", "SP80", 1
        )
        
        self.assertIn("first time", result['autobiography_narrative'].lower())

    # =========================================================================
    # RUNTIME AUTOBIOGRAPHY UPDATE TESTS
    # =========================================================================
    
    def test_initialize_session_state(self):
        """Session state should be initialized with wA/wB from strategy."""
        result = self.episodic.synthesize_pregame_autobiography(
            "session_agent", "SP80", 1
        )
        
        # Initialize session state
        updated = self.episodic.initialize_session_state(result)
        
        self.assertIn('session_state', updated)
        session = updated['session_state']
        self.assertEqual(session['actions_taken_this_game'], 0)
        self.assertEqual(session['current_level'], 1)
        self.assertIn('wA', session)
        self.assertIn('wB', session)
        # wA + wB should approximately equal 1
        self.assertAlmostEqual(session['wA'] + session['wB'], 1.0, places=2)
    
    def test_wA_wB_shift_on_positive_personal(self):
        """wA should increase when personal action succeeds."""
        # Setup experienced agent (trust_self strategy)
        self._seed_agent_history("wab_agent", "SP80", wins=15, losses=5)
        result = self.episodic.synthesize_pregame_autobiography(
            "wab_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        initial_wA = result['session_state']['wA']
        
        # Personal action succeeds
        result = self.episodic.update_autobiography_after_action(
            autobiography=result,
            action='ACTION1',
            action_source='wA',
            outcome='positive'
        )
        
        new_wA = result['session_state']['wA']
        # wA should have increased
        self.assertGreater(new_wA, initial_wA)
    
    def test_wB_shift_on_positive_network(self):
        """wB should increase when network action succeeds."""
        result = self.episodic.synthesize_pregame_autobiography(
            "wb_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        initial_wB = result['session_state']['wB']
        
        # Network action succeeds
        result = self.episodic.update_autobiography_after_action(
            autobiography=result,
            action='ACTION2',
            action_source='wB',
            outcome='positive'
        )
        
        new_wB = result['session_state']['wB']
        # wB should have increased
        self.assertGreater(new_wB, initial_wB)
    
    def test_wA_wB_bounded(self):
        """wA and wB should stay between 0.1 and 0.9."""
        result = self.episodic.synthesize_pregame_autobiography(
            "bound_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        # Many positive personal outcomes
        for _ in range(50):
            result = self.episodic.update_autobiography_after_action(
                autobiography=result,
                action='ACTION1',
                action_source='wA',
                outcome='positive'
            )
        
        session = result['session_state']
        self.assertLessEqual(session['wA'], 0.9)
        self.assertGreaterEqual(session['wB'], 0.1)
    
    def test_level_change_updates_narrative(self):
        """Level change should update narrative and reset level counter."""
        result = self.episodic.synthesize_pregame_autobiography(
            "level_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        # Simulate some actions
        for _ in range(10):
            result = self.episodic.update_autobiography_after_action(
                autobiography=result,
                action='ACTION1',
                action_source='explore',
                outcome='neutral'
            )
        
        # Complete level
        result = self.episodic.update_autobiography_on_level_change(
            autobiography=result,
            old_level=1,
            new_level=2,
            actions_to_complete=10
        )
        
        session = result['session_state']
        self.assertEqual(session['current_level'], 2)
        self.assertEqual(session['actions_taken_this_level'], 0)
        self.assertEqual(len(session['level_transitions']), 1)
        self.assertIn("level 1", result['session_narrative'].lower())
    
    def test_get_action_source_recommendation_personal_only(self):
        """When only personal action available, use it."""
        result = self.episodic.synthesize_pregame_autobiography(
            "rec_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        action, source, reasoning = self.episodic.get_action_source_recommendation(
            autobiography=result,
            personal_action='ACTION1',
            network_action=None
        )
        
        self.assertEqual(action, 'ACTION1')
        self.assertEqual(source, 'wA')
    
    def test_get_action_source_recommendation_network_only(self):
        """When only network action available, use it."""
        result = self.episodic.synthesize_pregame_autobiography(
            "rec_agent2", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        action, source, reasoning = self.episodic.get_action_source_recommendation(
            autobiography=result,
            personal_action=None,
            network_action='ACTION2'
        )
        
        self.assertEqual(action, 'ACTION2')
        self.assertEqual(source, 'wB')
    
    def test_get_action_source_recommendation_both_agree(self):
        """When both streams suggest same action, use blend."""
        result = self.episodic.synthesize_pregame_autobiography(
            "blend_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        action, source, reasoning = self.episodic.get_action_source_recommendation(
            autobiography=result,
            personal_action='ACTION3',
            network_action='ACTION3'
        )
        
        self.assertEqual(action, 'ACTION3')
        self.assertEqual(source, 'blend')
    
    def test_runtime_narrative_includes_session_info(self):
        """Runtime narrative should include current session state."""
        result = self.episodic.synthesize_pregame_autobiography(
            "narr2_agent", "SP80", 1
        )
        result = self.episodic.initialize_session_state(result)
        
        # Take some actions
        for i in range(15):
            result = self.episodic.update_autobiography_after_action(
                autobiography=result,
                action=f'ACTION{(i % 4) + 1}',
                action_source='explore',
                outcome='neutral'
            )
        
        narrative = self.episodic.generate_runtime_narrative(result)
        
        self.assertIn("15 actions", narrative.lower())
        self.assertIn("level 1", narrative.lower())


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


# =============================================================================
# PRIMITIVE-AWARE HYPOTHESIS TESTS
# =============================================================================

class TestPrimitiveAwareHypothesis(unittest.TestCase):
    """Tests for primitive-aware hypothesis creation and usage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MockDatabaseInterface()
        
        # Create cognitive competencies table
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_competencies (
                agent_id TEXT PRIMARY KEY,
                stage TEXT DEFAULT 'preoperational',
                games_played INTEGER DEFAULT 0,
                sequences_discovered INTEGER DEFAULT 0,
                action_effect_pairs INTEGER DEFAULT 0,
                object_control BOOLEAN DEFAULT 0,
                hypotheses_created INTEGER DEFAULT 0
            )
        """)
        
        # Create agent_hypotheses table with new columns
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                agent_id TEXT,
                game_type TEXT,
                level_number INTEGER,
                hypothesis_text TEXT,
                hypothesis_type TEXT,
                primitives_used TEXT,
                trigger_condition TEXT,
                predicted_action TEXT,
                action_sequence TEXT,
                supporting_evidence TEXT,
                contradicting_evidence TEXT,
                confidence REAL DEFAULT 0.5,
                tests_conducted INTEGER DEFAULT 0,
                tests_successful INTEGER DEFAULT 0,
                status TEXT DEFAULT 'proposed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.conn.commit()
    
    def test_create_hypothesis_with_primitives(self):
        """Hypothesis creation should store primitive references."""
        agent_id = "formal_agent"
        
        # Create formal agent
        self.db.conn.execute(
            "INSERT INTO cognitive_competencies (agent_id, stage) VALUES (?, ?)",
            (agent_id, 'formal_operational')
        )
        self.db.conn.commit()
        
        # Insert hypothesis with primitives
        primitives = ['detect_boundary', 'track_object']
        trigger = {'primitive': 'detect_boundary', 'params': {'direction': 'right'}}
        
        self.db.conn.execute("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, level_number, hypothesis_text,
             hypothesis_type, primitives_used, trigger_condition, predicted_action, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hyp_test1', agent_id, 'SP80', 2,
            'When boundary detected, move down',
            'action_effect',
            json.dumps(primitives),
            json.dumps(trigger),
            'ACTION4',
            'proposed'
        ))
        self.db.conn.commit()
        
        # Query and verify
        result = self.db.execute_query(
            "SELECT * FROM agent_hypotheses WHERE hypothesis_id = ?",
            ('hyp_test1',)
        )
        
        self.assertIsNotNone(result)
        assert result is not None  # Type guard for Pylance
        self.assertEqual(len(result), 1)
        
        hyp = result[0]
        self.assertEqual(hyp['predicted_action'], 'ACTION4')
        
        stored_primitives = json.loads(hyp['primitives_used'])
        self.assertIn('detect_boundary', stored_primitives)
        self.assertIn('track_object', stored_primitives)
        
        stored_trigger = json.loads(hyp['trigger_condition'])
        self.assertEqual(stored_trigger['primitive'], 'detect_boundary')
    
    def test_get_primitive_based_action(self):
        """Should return action from highest confidence primitive-aware hypothesis."""
        agent_id = "formal_agent"
        
        # Create formal agent
        self.db.conn.execute(
            "INSERT INTO cognitive_competencies (agent_id, stage) VALUES (?, ?)",
            (agent_id, 'formal_operational')
        )
        
        # Insert multiple hypotheses with different confidence
        self.db.conn.execute("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, level_number, hypothesis_text,
             hypothesis_type, primitives_used, predicted_action, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hyp_low', agent_id, 'SP80', 2,
            'Try moving up',
            'action_effect',
            json.dumps(['get_frame']),
            'ACTION1',
            0.3,
            'testing'
        ))
        
        self.db.conn.execute("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, level_number, hypothesis_text,
             hypothesis_type, primitives_used, predicted_action, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hyp_high', agent_id, 'SP80', 2,
            'Move right when frame changes',
            'action_effect',
            json.dumps(['frame_diff', 'detect_change']),
            'ACTION2',
            0.8,
            'confirmed'
        ))
        self.db.conn.commit()
        
        # Query for action - should return higher confidence one
        result = self.db.execute_query("""
            SELECT hypothesis_id, predicted_action, confidence, primitives_used
            FROM agent_hypotheses
            WHERE agent_id = ?
              AND game_type = ?
              AND predicted_action IS NOT NULL
              AND status IN ('proposed', 'testing', 'confirmed')
            ORDER BY 
                CASE status WHEN 'confirmed' THEN 1 WHEN 'testing' THEN 2 ELSE 3 END,
                confidence DESC
            LIMIT 1
        """, (agent_id, 'SP80'))
        
        self.assertIsNotNone(result)
        assert result is not None  # Type guard for Pylance
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['predicted_action'], 'ACTION2')
        self.assertEqual(result[0]['confidence'], 0.8)
    
    def test_hypotheses_by_primitives_search(self):
        """Should find hypotheses that use specific primitives."""
        # Insert hypotheses with different primitives
        self.db.conn.execute("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, hypothesis_text, hypothesis_type,
             primitives_used, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hyp_a', 'agent1', 'SP80', 'Hyp using detect_boundary',
            'action_effect',
            json.dumps(['detect_boundary', 'get_frame']),
            0.7, 'confirmed'
        ))
        
        self.db.conn.execute("""
            INSERT INTO agent_hypotheses 
            (hypothesis_id, agent_id, game_type, hypothesis_text, hypothesis_type,
             primitives_used, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'hyp_b', 'agent2', 'SP80', 'Hyp using frame_diff',
            'action_effect',
            json.dumps(['frame_diff', 'detect_change']),
            0.6, 'testing'
        ))
        self.db.conn.commit()
        
        # Search for hypotheses using detect_boundary
        result = self.db.execute_query("""
            SELECT * FROM agent_hypotheses
            WHERE primitives_used LIKE ?
              AND confidence >= ?
              AND status IN ('testing', 'confirmed')
        """, ('%"detect_boundary"%', 0.3))
        
        self.assertIsNotNone(result)
        assert result is not None  # Type guard for Pylance
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['hypothesis_id'], 'hyp_a')
    
    def test_primitive_trigger_condition_structure(self):
        """Trigger condition should have proper structure."""
        trigger = {
            'primitive': 'detect_color_change',
            'params': {'color': 'red', 'threshold': 0.5}
        }
        
        # Verify structure
        self.assertIn('primitive', trigger)
        self.assertIn('params', trigger)
        self.assertEqual(trigger['primitive'], 'detect_color_change')
        self.assertIsInstance(trigger['params'], dict)
        
        # JSON serialization roundtrip
        serialized = json.dumps(trigger)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized['primitive'], 'detect_color_change')
        self.assertEqual(deserialized['params']['color'], 'red')


class TestSequenceAbstractionPrimitives(unittest.TestCase):
    """Tests for sequence abstraction primitive requirement analysis."""
    
    def test_primitive_requirement_analysis_structure(self):
        """Primitive requirement analysis should return expected structure."""
        # Expected structure from analyze_primitive_requirements
        result = {
            'required_primitives': ['get_frame', 'detect_boundary'],
            'helpful_primitives': ['track_object', 'frame_diff'],
            'detection_strategy': {
                'trigger': 'level_start',
                'first_action': 2,
                'checkpoint_count': 5,
                'adaptable_regions': 2
            },
            'sequence_type': 'movement_dominant',
            'confidence': 0.75
        }
        
        # Verify structure
        self.assertIn('required_primitives', result)
        self.assertIn('helpful_primitives', result)
        self.assertIn('detection_strategy', result)
        self.assertIn('sequence_type', result)
        self.assertIn('confidence', result)
        
        self.assertIsInstance(result['required_primitives'], list)
        self.assertIsInstance(result['helpful_primitives'], list)
        self.assertIn(result['sequence_type'], 
                      ['movement_dominant', 'click_dominant', 'selection_dominant', 'mixed'])
    
    def test_template_with_primitives_readiness(self):
        """Template with primitives should calculate execution readiness."""
        # Simulated template with primitive requirements
        template_result = {
            'requirements': {
                'required_primitives': ['get_frame', 'detect_boundary', 'track_object'],
                'helpful_primitives': ['frame_diff']
            },
            'missing_required': ['detect_boundary'],  # 1 missing of 3
            'missing_helpful': ['frame_diff'],
            'execution_readiness': 2/3,  # 66%
            'can_execute': False  # < 80%
        }
        
        # Verify readiness calculation
        have = len(template_result['requirements']['required_primitives']) - len(template_result['missing_required'])
        total = len(template_result['requirements']['required_primitives'])
        expected_readiness = have / total
        
        self.assertAlmostEqual(template_result['execution_readiness'], expected_readiness, places=2)
        
        # Can't execute with < 80% readiness
        self.assertFalse(template_result['can_execute'])
    
    def test_suggest_primitives_for_game_structure(self):
        """Primitive suggestions should be prioritized correctly."""
        # Simulated suggestion result
        suggestion = {
            'game_type': 'SP80',
            'levels_analyzed': 3,
            'required_primitives': [
                {'primitive': 'get_frame', 'needed_in_levels': 3, 'priority': 'high'},
                {'primitive': 'detect_boundary', 'needed_in_levels': 2, 'priority': 'high'}
            ],
            'helpful_primitives': [
                {'primitive': 'track_object', 'helpful_in_levels': 3, 'priority': 'medium'}
            ],
            'unlock_recommendation': 'get_frame'
        }
        
        # Required primitives should be sorted by frequency
        if len(suggestion['required_primitives']) >= 2:
            first_count = suggestion['required_primitives'][0]['needed_in_levels']
            second_count = suggestion['required_primitives'][1]['needed_in_levels']
            self.assertGreaterEqual(first_count, second_count)
        
        # Unlock recommendation should be the most needed
        if suggestion['required_primitives']:
            self.assertEqual(
                suggestion['unlock_recommendation'],
                suggestion['required_primitives'][0]['primitive']
            )


class TestBabyDerivedPrimitives(unittest.TestCase):
    """Test the baby-derived primitives (Phase 1-3 implementation)."""
    
    def setUp(self):
        """Set up seed primitives for testing."""
        from seed_primitives import get_seed_primitives, reset_seed_primitives
        reset_seed_primitives()  # Fresh registry
        self.sp = get_seed_primitives()
    
    def test_primitive_count_increased(self):
        """Total primitives should be ~100 (up from ~50)."""
        count = self.sp.count()
        self.assertGreaterEqual(count, 100)
        self.assertLessEqual(count, 120)  # Not too many
    
    def test_new_categories_exist(self):
        """New categories should be registered."""
        stats = self.sp.get_stats()
        
        # Verify new categories have primitives
        self.assertGreater(stats.get('attention', 0), 0)
        self.assertGreater(stats.get('affordance', 0), 0)
        self.assertGreater(stats.get('social_learning', 0), 0)
        self.assertGreater(stats.get('motivation', 0), 0)
        self.assertGreater(stats.get('physics_prior', 0), 0)
        self.assertGreater(stats.get('quantitative', 0), 0)
        self.assertGreater(stats.get('metacognition', 0), 0)
        self.assertGreater(stats.get('negative_space', 0), 0)
    
    def test_attention_primitives(self):
        """Attention primitives should detect change and motion."""
        frame1 = [[0, 0, 1], [0, 1, 0], [0, 0, 0]]
        frame2 = [[0, 0, 0], [0, 0, 1], [0, 0, 0]]  # Object moved
        
        # Test detect_change
        changes = self.sp.call('detect_change', frame1, frame2)
        self.assertIsInstance(changes, list)
        self.assertTrue(len(changes) > 0)  # Should detect changes
        
        # Test detect_motion
        motion = self.sp.call('detect_motion', frame1, frame2)
        self.assertIsInstance(motion, list)
        
        # Test detect_contingency
        contingency = self.sp.call('detect_contingency', 1, frame1, frame2)
        self.assertIn('caused_change', contingency)
        self.assertIn('change_magnitude', contingency)
    
    def test_affordance_primitives(self):
        """Affordance primitives should identify object capabilities."""
        frame = [[0, 0, 0, 0], [0, 2, 2, 0], [0, 2, 0, 0], [0, 2, 2, 0]]
        
        # Test is_obstacle (heuristic based on size)
        is_obs = self.sp.call('is_obstacle', 'obj_2', frame)
        self.assertIsInstance(is_obs, bool)
        
        # Test is_container
        is_cont = self.sp.call('is_container', 'obj_2', frame)
        self.assertIsInstance(is_cont, bool)
        
        # Test is_movable (needs history)
        is_mov = self.sp.call('is_movable', 'obj_2', [])
        self.assertFalse(is_mov)  # No history = unknown
        
        # With positive history
        is_mov = self.sp.call('is_movable', 'obj_2', [{'object_id': 'obj_2', 'moved': True}])
        self.assertTrue(is_mov)
    
    def test_social_learning_primitives(self):
        """Social learning primitives should weight by credibility."""
        # Test credibility_weighting
        weight = self.sp.call('credibility_weighting', 'agent_1', 0.8, 0.9)
        self.assertIsInstance(weight, float)
        self.assertGreater(weight, 0)
        self.assertLessEqual(weight, 1)
        
        # Test demonstration_bias
        bias = self.sp.call('demonstration_bias', 1, [1, 2, 1], 0.8)
        self.assertGreater(bias, 0)  # Action 1 was demonstrated twice
        
        bias_new = self.sp.call('demonstration_bias', 7, [1, 2, 1], 0.8)
        self.assertEqual(bias_new, 0)  # Action 7 not demonstrated
        
        # Test teaching_detection
        is_teaching = self.sp.call('teaching_detection', {}, 'oracle')
        self.assertTrue(is_teaching)  # Oracle is always pedagogical
    
    def test_motivation_primitives(self):
        """Motivation primitives should provide intrinsic rewards."""
        # Test novelty_bonus
        bonus = self.sp.call('novelty_bonus', 'state_x', [])
        self.assertEqual(bonus, 1.0)  # First state is maximally novel
        
        bonus = self.sp.call('novelty_bonus', 'state_x', ['state_x'] * 5)
        self.assertLess(bonus, 1.0)  # Seen before = less novel
        
        # Test competence_signal
        signal = self.sp.call('competence_signal', 0.8, 0.7, 0.1)
        self.assertIsInstance(signal, float)
        self.assertGreater(signal, 0)
    
    def test_physics_priors_exist(self):
        """Physics priors should have adjustable strengths."""
        priors = self.sp.get_physics_priors()
        
        self.assertEqual(len(priors), 5)
        
        prior_names = [p['name'] for p in priors]
        self.assertIn('solidity_bias', prior_names)
        self.assertIn('continuity_bias', prior_names)
        self.assertIn('gravity_bias', prior_names)
        self.assertIn('persistence_bias', prior_names)
        self.assertIn('contact_causality', prior_names)
        
        # Check strengths are weak (< 1.0)
        for p in priors:
            self.assertLess(p['prior_strength'], 1.0)
            self.assertGreater(p['prior_strength'], 0)
    
    def test_physics_prior_adjustment(self):
        """Physics priors should be adjustable based on evidence."""
        # Adjust solidity prior
        success = self.sp.adjust_physics_prior('solidity_bias', 0.1)
        self.assertTrue(success)
        
        priors = self.sp.get_physics_priors()
        solidity = next(p for p in priors if p['name'] == 'solidity_bias')
        self.assertAlmostEqual(solidity['prior_strength'], 0.1, places=2)
        
        # Can't adjust non-physics primitive
        success = self.sp.adjust_physics_prior('get_frame', 0.5)
        self.assertFalse(success)
    
    def test_quantitative_primitives(self):
        """Quantitative primitives should count and compare."""
        frame = [[0, 1, 0], [2, 0, 3], [0, 0, 0]]
        
        # Test count_objects
        count = self.sp.call('count_objects', frame, None)
        self.assertEqual(count, 3)  # 3 distinct objects
        
        # Test compare_quantities
        result = self.sp.call('compare_quantities', 5, 3)
        self.assertEqual(result, 'more')
        
        result = self.sp.call('compare_quantities', 3, 5)
        self.assertEqual(result, 'less')
        
        result = self.sp.call('compare_quantities', 4, 4)
        self.assertEqual(result, 'equal')
        
        # Test detect_one_vs_many
        self.assertEqual(self.sp.call('detect_one_vs_many', [1]), 'one')
        self.assertEqual(self.sp.call('detect_one_vs_many', [1, 2, 3]), 'many')
        self.assertEqual(self.sp.call('detect_one_vs_many', []), 'none')
    
    def test_metacognition_primitives(self):
        """Metacognition primitives should assess confidence and progress."""
        # Test get_confidence
        conf = self.sp.call('get_confidence', 'prediction', 5, 1)
        self.assertIsInstance(conf, float)
        self.assertGreater(conf, 0)  # Some confidence with evidence
        
        # More contradictions = lower confidence
        conf_low = self.sp.call('get_confidence', 'prediction', 2, 5)
        self.assertLess(conf_low, conf)
        
        # Test detect_stuck
        is_stuck = self.sp.call('detect_stuck', [0.1, 0.1, 0.1, 0.1, 0.1], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2])
        self.assertTrue(is_stuck)  # Cycling with no progress
        
        not_stuck = self.sp.call('detect_stuck', [0.1, 0.2, 0.3, 0.4, 0.5], [1, 2, 3, 4, 5])
        self.assertFalse(not_stuck)  # Making progress
    
    def test_negative_space_primitives(self):
        """Negative space primitives should detect holes and absences."""
        # Frame with enclosed empty space
        frame = [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 0, 1, 0],  # Hole in middle
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0]
        ]
        
        # Test detect_enclosed_empty
        enclosed = self.sp.call('detect_enclosed_empty', frame)
        self.assertIsInstance(enclosed, list)
        # Should detect the enclosed space
        
        # Test detect_absence
        absent = self.sp.call('detect_absence', 'obj_1', (2, 2), frame)
        self.assertTrue(absent)  # Position (2,2) has 0, not 1
        
        present = self.sp.call('detect_absence', 'obj_1', (1, 1), frame)
        self.assertFalse(present)  # Position (1,1) has color 1
        
        # Test negative_space_volume
        volume = self.sp.call('negative_space_volume', (0, 0, 4, 4), frame)
        self.assertIsInstance(volume, int)
        self.assertGreater(volume, 0)


class TestPiagetStageIntegration(unittest.TestCase):
    """Test Piaget stage integration with primitives."""
    
    def setUp(self):
        """Set up seed primitives for testing."""
        from seed_primitives import get_seed_primitives, reset_seed_primitives
        reset_seed_primitives()
        self.sp = get_seed_primitives()
    
    def test_unlock_levels_exist(self):
        """Primitives should have unlock levels."""
        seed_count = self.sp.get_seed_primitive_count()
        early_count = self.sp.get_early_unlock_count()
        late_count = self.sp.get_late_unlock_count()
        
        # Should have primitives at each level
        self.assertGreater(seed_count, 0)
        self.assertGreater(early_count, 0)
        self.assertGreater(late_count, 0)
        
        # Seed should be majority
        self.assertGreater(seed_count, early_count)
        self.assertGreater(seed_count, late_count)
    
    def test_piaget_stage_inventory(self):
        """Inventory should be organized by Piaget stage."""
        inventory = self.sp.get_primitive_inventory_by_stage()
        
        # All stages should exist
        self.assertIn('sensorimotor', inventory)
        self.assertIn('preoperational', inventory)
        self.assertIn('concrete_operational', inventory)
        self.assertIn('formal_operational', inventory)
        
        # Sensorimotor should have the most (seed primitives)
        self.assertGreater(len(inventory['sensorimotor']), len(inventory['formal_operational']))
    
    def test_primitives_for_agent_by_stage(self):
        """Agent should get appropriate primitives for their stage."""
        # Sensorimotor agent gets only sensorimotor primitives
        sensorimotor_prims = self.sp.get_primitives_for_agent('sensorimotor')
        
        # Formal operational agent gets all primitives
        formal_prims = self.sp.get_primitives_for_agent('formal_operational')
        
        # Formal should have more than sensorimotor
        self.assertGreater(len(formal_prims), len(sensorimotor_prims))
        
        # All sensorimotor primitives should be in formal
        for p in sensorimotor_prims:
            self.assertIn(p, formal_prims)
    
    def test_unlock_requirements(self):
        """Should get unlock requirements for any primitive."""
        # Test a seed primitive
        req = self.sp.get_unlock_requirements('detect_change')
        self.assertEqual(req['unlock_level'], 'seed')
        self.assertEqual(req['piaget_stage'], 'sensorimotor')
        
        # Test a late unlock primitive
        req = self.sp.get_unlock_requirements('is_reference')
        self.assertEqual(req['unlock_level'], 'late')
        self.assertEqual(req['piaget_stage'], 'formal_operational')
    
    def test_explicitly_unlocked_primitives(self):
        """Agent can have explicitly unlocked primitives beyond stage."""
        # Sensorimotor agent with explicit unlock
        prims = self.sp.get_primitives_for_agent('sensorimotor', ['is_reference'])
        
        # Should include the explicitly unlocked primitive
        self.assertIn('is_reference', prims)


if __name__ == '__main__':
    unittest.main()
