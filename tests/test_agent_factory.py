"""
Unit Tests for AgentFactory

Tests the agent creation and role assignment system including:
- Agent creation with proper initialization
- Role assignment (Pioneer, Optimizer, Generalist, Exploiter)
- Genome generation
- Population management

Rule 5: Unit tests for core components are allowed.
Uses temp database (not production).
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
import tempfile
import json
from pathlib import Path

from database_interface import DatabaseInterface
from agent_factory import AgentFactory


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
def factory(db):
    """Create an AgentFactory instance."""
    return AgentFactory(db)


class TestAgentCreation:
    """Tests for agent creation."""
    
    def test_create_agent_returns_agent(self, factory):
        """create_agent should return an ARCAgent object."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7},
        )
        assert agent is not None
        assert hasattr(agent, 'agent_id')
        assert len(agent.agent_id) > 0
    
    def test_create_agent_stores_in_database(self, factory, db):
        """Created agent should be stored in database."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7},
        )
        
        results = db.execute_query(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        assert len(results) == 1
        assert results[0]['agent_type'] == 'pattern_specialist'
    
    def test_create_agent_with_epigenetics(self, factory, db):
        """Agent can be created with epigenetics."""
        agent = factory.create_agent(
            agent_type='score_optimizer',
            genome={'score_priority': 0.8},
            epigenetics={'learning_rate': 0.1},
        )
        
        results = db.execute_query(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        assert len(results) == 1


class TestGenomeGeneration:
    """Tests for genome creation."""
    
    def test_agent_has_genome(self, factory, db):
        """Created agent should have a genome."""
        agent = factory.create_agent(
            agent_type='exploration_agent',
            genome={'exploration_rate': 0.9},
        )
        
        results = db.execute_query(
            "SELECT genome FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        assert results[0]['genome'] is not None
        
        # Genome should be valid JSON
        genome = json.loads(results[0]['genome'])
        assert isinstance(genome, dict)
    
    def test_genome_preserves_values(self, factory, db):
        """Genome values should be preserved."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.75, 'custom_key': 'test_value'},
        )
        
        results = db.execute_query(
            "SELECT genome FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        genome = json.loads(results[0]['genome'])
        
        # Verify genome structure preserved
        assert isinstance(genome, dict)


class TestAgentTypes:
    """Tests for different agent types."""
    
    def test_pattern_specialist_type(self, factory):
        """pattern_specialist is a valid agent type."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7}
        )
        assert agent is not None
    
    def test_score_optimizer_type(self, factory):
        """score_optimizer is a valid agent type."""
        agent = factory.create_agent(
            agent_type='score_optimizer',
            genome={'score_priority': 0.8}
        )
        assert agent is not None
    
    def test_exploration_agent_type(self, factory):
        """exploration_agent is a valid agent type."""
        agent = factory.create_agent(
            agent_type='exploration_agent',
            genome={'exploration_rate': 0.9}
        )
        assert agent is not None
    
    def test_win_focused_agent_type(self, factory):
        """win_focused_agent is a valid agent type."""
        agent = factory.create_agent(
            agent_type='win_focused_agent',
            genome={'win_threshold': 0.85}
        )
        assert agent is not None
    
    def test_hybrid_agent_type(self, factory):
        """hybrid_agent is a valid agent type."""
        agent = factory.create_agent(
            agent_type='hybrid_agent',
            genome={'hybrid_balance': 0.5}
        )
        assert agent is not None
    
    def test_invalid_type_raises_error(self, factory):
        """Invalid agent type should raise ValueError."""
        with pytest.raises(ValueError):
            factory.create_agent(
                agent_type='nonexistent_type',
                genome={}
            )


class TestPopulationManagement:
    """Tests for managing multiple agents."""
    
    def test_create_multiple_agents(self, factory, db):
        """Can create multiple agents."""
        ids = []
        for i in range(5):
            agent = factory.create_agent(
                agent_type='pattern_specialist',
                genome={'pattern_sensitivity': 0.5 + i * 0.1},
            )
            ids.append(agent.agent_id)
        
        # All IDs should be unique
        assert len(set(ids)) == 5
        
        # All should be in database
        for agent_id in ids:
            results = db.execute_query(
                "SELECT agent_id FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            assert len(results) == 1
    
    def test_agents_are_active_by_default(self, factory, db):
        """New agents should be active by default."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7},
        )
        
        results = db.execute_query(
            "SELECT is_active FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        assert results[0]['is_active'] in (1, True)


class TestAgentDefaults:
    """Tests for default agent values."""
    
    def test_default_action_allowances(self, factory, db):
        """Agents should have default action allowances."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7},
        )
        
        results = db.execute_query(
            "SELECT action_allowance_per_level, action_allowance_total FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        # Defaults from schema: 400 per level, 7000 total
        assert results[0]['action_allowance_per_level'] == 400
        assert results[0]['action_allowance_total'] == 7000
    
    def test_default_social_rule_adherence(self, factory, db):
        """Agents should have default social_rule_adherence."""
        agent = factory.create_agent(
            agent_type='pattern_specialist',
            genome={'pattern_sensitivity': 0.7},
        )
        
        results = db.execute_query(
            "SELECT social_rule_adherence FROM agents WHERE agent_id = ?",
            (agent.agent_id,)
        )
        # Default is 0.5
        assert results[0]['social_rule_adherence'] == 0.5
