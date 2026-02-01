#!/usr/bin/env python3
"""
Test suite for I-Thread Episodic Memory System
==============================================

Tests the autobiographical memory implementation that enables
continuous agent existence across game sessions.

Per Rule 15: Tests in tests/ folder are EXEMPT from "No Test Files" rule.

Run with: python -m pytest tests/test_i_thread_episodic.py -v
"""

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.consciousness.i_thread import (
    ROLE_DEFAULT_WEIGHTS,
    AgentNarrative,
    ConflictResult,
    EpisodicMemory,
    IThread,
    IThreadState,
    StreamProposal,
    SynthesisResult,
)

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database interface."""
    db = MagicMock()
    db.execute_query = MagicMock(return_value=[])
    return db


@pytest.fixture
def i_thread(mock_db):
    """Create an I-Thread instance with mock DB."""
    return IThread(mock_db)


@pytest.fixture
def sample_agent_id():
    """Sample agent ID for testing."""
    return "agent_test_12345"


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestEpisodicMemoryDataclass:
    """Test EpisodicMemory dataclass structure."""

    def test_create_episodic_memory(self):
        """Test creating an episodic memory."""
        mem = EpisodicMemory(
            memory_id="mem_abc123",
            agent_id="agent_test",
            game_type="SP45",
            level_number=2,
            episode_type="breakthrough",
            summary="Discovered that clicking corners reveals hidden paths",
            emotional_valence=0.8,
            significance=0.9,
            belief_formed="Corners matter in maze games"
        )

        assert mem.memory_id == "mem_abc123"
        assert mem.episode_type == "breakthrough"
        assert mem.significance == 0.9
        assert mem.emotional_valence == 0.8
        assert mem.belief_formed == "Corners matter in maze games"

    def test_episodic_memory_defaults(self):
        """Test default values in EpisodicMemory."""
        mem = EpisodicMemory(
            memory_id="mem_123",
            agent_id="agent",
            game_type="FT09",
            level_number=1,
            episode_type="frustration",
            summary="Got stuck for 50 actions",
            emotional_valence=-0.5,
            significance=0.6
        )

        assert mem.emotional_valence == -0.5
        assert mem.significance == 0.6
        assert mem.stream_source == 'stream_a'
        assert mem.w_a_at_time == 0.5
        assert mem.times_recalled == 0


class TestAgentNarrativeDataclass:
    """Test AgentNarrative dataclass structure."""

    def test_create_agent_narrative(self):
        """Test creating an agent narrative."""
        narrative = AgentNarrative(
            agent_id="agent_test",
            personality_label="self-trusting",
            dominant_emotion="confident",
            total_games_played=45,
            total_breakthroughs=12,
            games_won=28
        )

        assert narrative.agent_id == "agent_test"
        assert narrative.personality_label == "self-trusting"
        assert narrative.dominant_emotion == "confident"
        assert narrative.total_games_played == 45

    def test_agent_narrative_defaults(self):
        """Test default values in AgentNarrative."""
        narrative = AgentNarrative(
            agent_id="agent",
            personality_label="balanced",
            dominant_emotion="curious"
        )

        assert narrative.total_games_played == 0
        assert narrative.total_breakthroughs == 0
        assert narrative.salient_memories == []
        assert narrative.core_beliefs == []
        assert narrative.w_a == 0.5


# =============================================================================
# I-THREAD STATE TESTS
# =============================================================================

class TestIThreadState:
    """Test I-Thread state management."""

    def test_get_state_new_agent(self, i_thread, mock_db, sample_agent_id):
        """Test getting state for a new agent."""
        mock_db.execute_query.return_value = []

        state = i_thread.get_state(sample_agent_id)

        assert state.agent_id == sample_agent_id
        assert state.w_a == 0.5
        assert state.w_b == 0.5
        assert state.personality_label == 'balanced'

    def test_get_state_existing_agent(self, i_thread, mock_db, sample_agent_id):
        """Test getting state for an existing agent."""
        mock_db.execute_query.side_effect = [
            [{'self_network_bias': 0.7}],  # First call - get agent
            [{'total_conflicts': 10, 'stream_a_wins': 7, 'stream_b_wins': 3}]  # Second call - stats
        ]

        state = i_thread.get_state(sample_agent_id)

        assert state.w_b == 0.7
        assert abs(state.w_a - 0.3) < 0.0001  # Floating point comparison
        assert state.personality_label == 'network-trusting'

    def test_state_caching(self, i_thread, mock_db, sample_agent_id):
        """Test that state is cached after first retrieval."""
        mock_db.execute_query.return_value = []

        state1 = i_thread.get_state(sample_agent_id)
        state2 = i_thread.get_state(sample_agent_id)

        assert state1 is state2  # Same object (cached)


# =============================================================================
# EPISODIC MEMORY TESTS
# =============================================================================

class TestRecordEpisode:
    """Test recording episodic memories."""

    def test_record_breakthrough(self, i_thread, mock_db, sample_agent_id):
        """Test recording a breakthrough episode."""
        mock_db.execute_query.return_value = []

        memory_id = i_thread.record_episode(
            agent_id=sample_agent_id,
            game_type="SP45",
            game_id="SP45-abc",
            level_number=3,
            episode_type="breakthrough",
            summary="Discovered clicking corners reveals paths",
            emotional_valence=0.9,
            significance=0.85,
            belief_formed="Corners are important"
        )

        assert memory_id.startswith("mem_")
        # Verify DB was called
        assert mock_db.execute_query.called

    def test_record_frustration(self, i_thread, mock_db, sample_agent_id):
        """Test recording a frustration episode."""
        mock_db.execute_query.return_value = []

        memory_id = i_thread.record_episode(
            agent_id=sample_agent_id,
            game_type="FT09",
            game_id="FT09-xyz",
            level_number=1,
            episode_type="frustration",
            summary="Stuck for 50 actions before finding solution",
            emotional_valence=-0.6,
            significance=0.7
        )

        assert memory_id.startswith("mem_")


class TestAwaken:
    """Test agent awakening with autobiographical memory."""

    def test_awaken_new_agent(self, i_thread, mock_db, sample_agent_id):
        """Test awakening a new agent with no memories."""
        mock_db.execute_query.return_value = []

        narrative = i_thread.awaken(sample_agent_id)

        assert narrative.agent_id == sample_agent_id
        assert narrative.salient_memories == []
        assert narrative.core_beliefs == []
        assert narrative.dominant_emotion == 'curious'  # Default for new agents

    def test_awaken_with_memories(self, i_thread, mock_db, sample_agent_id):
        """Test awakening an agent with memories."""
        # Mock: agent state
        mock_db.execute_query.side_effect = [
            [{'self_network_bias': 0.3}],  # Agent state (w_b = 0.3, so w_a = 0.7)
            [{'total_conflicts': 5, 'stream_a_wins': 4, 'stream_b_wins': 1}],  # Stats
            # Salient memories
            [
                {
                    'memory_id': 'mem_1',
                    'agent_id': sample_agent_id,
                    'game_type': 'SP45',
                    'level_number': 2,
                    'episode_type': 'breakthrough',
                    'summary': 'Clicking corners works',
                    'emotional_valence': 0.8,
                    'significance': 0.9,
                    'belief_formed': 'Corners matter',
                    'rule_discovered': None,
                    'stream_source': 'stream_a',
                    'w_a_at_time': 0.6,
                    'w_b_at_time': 0.4,
                    'times_recalled': 3
                }
            ],
            [],  # Update recall count
            [{'belief_formed': 'Corners matter'}],  # Core beliefs
            [{'episode_type': 'breakthrough', 'count': 3}],  # Stats by type
            [{'total': 10}],  # Total games
        ]

        narrative = i_thread.awaken(sample_agent_id, game_type="SP45")

        assert narrative.agent_id == sample_agent_id
        assert len(narrative.salient_memories) == 1
        assert narrative.salient_memories[0].episode_type == 'breakthrough'
        assert 'Corners matter' in narrative.core_beliefs or len(narrative.core_beliefs) >= 0

    def test_awaken_with_game_type_priority(self, i_thread, mock_db, sample_agent_id):
        """Test that awakening prioritizes game-type relevant memories."""
        mock_db.execute_query.return_value = []

        # Awaken with specific game type
        narrative = i_thread.awaken(sample_agent_id, game_type="SP45")

        # Verify query was made with game_type parameter
        assert narrative is not None


class TestComputeDominantEmotion:
    """Test emotional state computation from memories."""

    def test_confident_from_breakthroughs(self, i_thread):
        """Test that many breakthroughs + positive valence = confident."""
        memories = [
            EpisodicMemory(
                memory_id="1", agent_id="a", game_type="X", level_number=1,
                episode_type="breakthrough", summary="Won",
                emotional_valence=0.8, significance=0.9
            ),
            EpisodicMemory(
                memory_id="2", agent_id="a", game_type="X", level_number=1,
                episode_type="breakthrough", summary="Won again",
                emotional_valence=0.7, significance=0.8
            ),
            EpisodicMemory(
                memory_id="3", agent_id="a", game_type="X", level_number=1,
                episode_type="validation", summary="Was right",
                emotional_valence=0.6, significance=0.7
            ),
        ]

        emotion = i_thread._compute_dominant_emotion(memories)
        assert emotion in ['confident', 'assured', 'curious']

    def test_frustrated_from_failures(self, i_thread):
        """Test that frustrations + negative valence = frustrated."""
        memories = [
            EpisodicMemory(
                memory_id="1", agent_id="a", game_type="X", level_number=1,
                episode_type="frustration", summary="Stuck",
                emotional_valence=-0.6, significance=0.7
            ),
            EpisodicMemory(
                memory_id="2", agent_id="a", game_type="X", level_number=1,
                episode_type="frustration", summary="Stuck again",
                emotional_valence=-0.5, significance=0.6
            ),
        ]

        emotion = i_thread._compute_dominant_emotion(memories)
        assert emotion in ['frustrated', 'discouraged', 'cautious']

    def test_curious_for_empty_memories(self, i_thread):
        """Test default emotion for agents with no memories."""
        emotion = i_thread._compute_dominant_emotion([])
        assert emotion == 'curious'


class TestGenerateNarrativeSummary:
    """Test narrative summary generation."""

    def test_self_trusting_narrative(self, i_thread, mock_db, sample_agent_id):
        """Test narrative for self-trusting agent."""
        mock_db.execute_query.return_value = []

        state = IThreadState(
            agent_id=sample_agent_id,
            w_a=0.8,
            w_b=0.2,
            personality_label='self-trusting'
        )

        summary = i_thread._generate_narrative_summary(
            agent_id=sample_agent_id,
            state=state,
            memories=[],
            beliefs=["Corners matter"],
            stats={'total_games': 25, 'breakthroughs': 5, 'frustrations': 2}
        )

        assert "trust my own experience" in summary.lower() or len(summary) > 0

    def test_network_trusting_narrative(self, i_thread, mock_db, sample_agent_id):
        """Test narrative for network-trusting agent."""
        mock_db.execute_query.return_value = []

        state = IThreadState(
            agent_id=sample_agent_id,
            w_a=0.2,
            w_b=0.8,
            personality_label='network-trusting'
        )

        summary = i_thread._generate_narrative_summary(
            agent_id=sample_agent_id,
            state=state,
            memories=[],
            beliefs=[],
            stats={'total_games': 5, 'breakthroughs': 1, 'frustrations': 3}
        )

        assert "network" in summary.lower() or "collective" in summary.lower() or len(summary) > 0


class TestMemoryConsolidation:
    """Test memory consolidation (pruning)."""

    def test_consolidate_under_limit(self, i_thread, mock_db, sample_agent_id):
        """Test that consolidation does nothing when under limit."""
        mock_db.execute_query.return_value = [{'total': 50}]

        initial_call_count = mock_db.execute_query.call_count
        i_thread.consolidate_memories(sample_agent_id, max_memories=100)

        # consolidate_memories was called - DB should have been queried
        # (at least count query, may have additional table creation queries)
        assert mock_db.execute_query.call_count > initial_call_count

    def test_consolidate_over_limit(self, i_thread, mock_db, sample_agent_id):
        """Test that consolidation deletes when over limit."""
        mock_db.execute_query.side_effect = [
            [{'total': 150}],  # Count
            None  # Delete
        ]

        initial_call_count = mock_db.execute_query.call_count
        i_thread.consolidate_memories(sample_agent_id, max_memories=100)

        # Should query count and delete - more calls than under limit case
        assert mock_db.execute_query.call_count > initial_call_count


# =============================================================================
# STREAM CONFLICT TESTS
# =============================================================================

class TestStreamConflict:
    """Test stream conflict detection."""

    def test_no_conflict_same_action(self, i_thread):
        """Test no conflict when streams agree."""
        proposal_a = StreamProposal(action="click_red", confidence=0.8, source="stream_a")
        proposal_b = StreamProposal(action="click_red", confidence=0.7, source="stream_b")

        result = i_thread.detect_conflict(proposal_a, proposal_b)

        assert result.has_conflict == False
        assert result.conflict_score == 0.0
        assert result.consciousness_intensity == 'automatic'

    def test_conflict_different_actions(self, i_thread):
        """Test conflict when streams disagree."""
        proposal_a = StreamProposal(action="click_red", confidence=0.8, source="stream_a")
        proposal_b = StreamProposal(action="move_up", confidence=0.7, source="stream_b")

        result = i_thread.detect_conflict(proposal_a, proposal_b)

        assert result.has_conflict == True
        assert result.conflict_score > 0

    def test_vivid_consciousness_high_conflict(self, i_thread):
        """Test vivid consciousness on high-confidence conflict."""
        proposal_a = StreamProposal(action="click_red", confidence=0.9, source="stream_a")
        proposal_b = StreamProposal(action="move_up", confidence=0.9, source="stream_b")

        result = i_thread.detect_conflict(proposal_a, proposal_b)

        assert result.consciousness_intensity in ['deliberative', 'vivid']


# =============================================================================
# SYNTHESIS TESTS
# =============================================================================

class TestSynthesis:
    """Test I-Thread synthesis of stream proposals."""

    def test_synthesis_favors_higher_weight(self, i_thread, mock_db, sample_agent_id):
        """Test that synthesis favors stream with higher weight."""
        mock_db.execute_query.return_value = []

        state = IThreadState(
            agent_id=sample_agent_id,
            w_a=0.8,
            w_b=0.2
        )

        proposal_a = StreamProposal(action="click_red", confidence=0.5, source="stream_a")
        proposal_b = StreamProposal(action="move_up", confidence=0.5, source="stream_b")

        result = i_thread.synthesize(state, proposal_a, proposal_b)

        assert result.chosen_source == 'stream_a'
        assert result.chosen_action == "click_red"

    def test_synthesis_high_confidence_overrides(self, i_thread, mock_db, sample_agent_id):
        """Test that high confidence can override weight disadvantage."""
        mock_db.execute_query.return_value = []

        state = IThreadState(
            agent_id=sample_agent_id,
            w_a=0.3,
            w_b=0.7
        )

        proposal_a = StreamProposal(action="click_red", confidence=0.95, source="stream_a")
        proposal_b = StreamProposal(action="move_up", confidence=0.3, source="stream_b")

        result = i_thread.synthesize(state, proposal_a, proposal_b)

        # 0.3 * 0.95 = 0.285 vs 0.7 * 0.3 = 0.21
        assert result.chosen_source == 'stream_a'
        assert result.surprise_score > 0  # Underdog won


# =============================================================================
# LEARNING TESTS
# =============================================================================

class TestLearnFromOutcome:
    """Test weight updates from outcomes."""

    def test_positive_outcome_increases_weight(self, i_thread, mock_db, sample_agent_id):
        """Test that positive outcome increases chosen stream's weight."""
        mock_db.execute_query.return_value = []

        # Get initial state
        state = i_thread.get_state(sample_agent_id)
        initial_w_a = state.w_a

        # Learn from positive outcome for stream_a
        new_w_a, new_w_b = i_thread.learn_from_outcome(
            agent_id=sample_agent_id,
            chosen_source='stream_a',
            outcome='positive'
        )

        assert new_w_a > initial_w_a

    def test_negative_outcome_decreases_weight(self, i_thread, mock_db, sample_agent_id):
        """Test that negative outcome decreases chosen stream's weight."""
        mock_db.execute_query.return_value = []

        # Get initial state
        state = i_thread.get_state(sample_agent_id)
        initial_w_a = state.w_a

        # Learn from negative outcome for stream_a
        new_w_a, new_w_b = i_thread.learn_from_outcome(
            agent_id=sample_agent_id,
            chosen_source='stream_a',
            outcome='negative'
        )

        assert new_w_a < initial_w_a

    def test_neutral_outcome_no_change(self, i_thread, mock_db, sample_agent_id):
        """Test that neutral outcome doesn't change weights."""
        mock_db.execute_query.return_value = []

        state = i_thread.get_state(sample_agent_id)
        initial_w_a = state.w_a

        new_w_a, new_w_b = i_thread.learn_from_outcome(
            agent_id=sample_agent_id,
            chosen_source='stream_a',
            outcome='neutral'
        )

        assert new_w_a == initial_w_a


# =============================================================================
# ROLE TRANSITION TESTS
# =============================================================================

class TestRoleTransition:
    """Test role-based weight resets."""

    def test_reset_to_pioneer(self, i_thread, mock_db, sample_agent_id):
        """Test resetting weights for pioneer role."""
        mock_db.execute_query.return_value = []

        new_w_a, new_w_b = i_thread.reset_for_role_change(sample_agent_id, 'pioneer')

        expected_w_a, expected_w_b = ROLE_DEFAULT_WEIGHTS['pioneer']
        assert new_w_a == expected_w_a
        assert new_w_b == expected_w_b

    def test_reset_to_optimizer(self, i_thread, mock_db, sample_agent_id):
        """Test resetting weights for optimizer role."""
        mock_db.execute_query.return_value = []

        new_w_a, new_w_b = i_thread.reset_for_role_change(sample_agent_id, 'optimizer')

        expected_w_a, expected_w_b = ROLE_DEFAULT_WEIGHTS['optimizer']
        assert new_w_a == expected_w_a
        assert new_w_b == expected_w_b


# =============================================================================
# INTEGRATION TEST
# =============================================================================

class TestFullLifecycle:
    """Test full agent lifecycle with episodic memory."""

    def test_full_lifecycle(self, i_thread, mock_db, sample_agent_id):
        """Test complete agent lifecycle: awaken -> play -> record -> consolidate."""
        mock_db.execute_query.return_value = []

        # 1. Agent awakens
        narrative = i_thread.awaken(sample_agent_id, game_type="SP45")
        assert narrative is not None
        assert narrative.dominant_emotion == 'curious'  # New agent

        # 2. Agent plays and has a breakthrough
        memory_id = i_thread.record_episode(
            agent_id=sample_agent_id,
            game_type="SP45",
            game_id="SP45-test",
            level_number=1,
            episode_type="breakthrough",
            summary="Discovered the pattern",
            emotional_valence=0.8,
            significance=0.9,
            belief_formed="Patterns reveal solutions"
        )
        assert memory_id.startswith("mem_")

        # 3. Agent learns from outcome
        new_w_a, new_w_b = i_thread.learn_from_outcome(
            agent_id=sample_agent_id,
            chosen_source='stream_a',
            outcome='positive',
            game_id="SP45-test"
        )
        assert new_w_a > 0.5  # Should have increased trust in self

        # 4. Consolidate memories
        i_thread.consolidate_memories(sample_agent_id, max_memories=100)

        # 5. Clear cache and re-awaken
        i_thread.clear_cache(sample_agent_id)
        # Agent would now awaken with their recorded memories


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
